"""
Email Service Integrations
Gmail, Microsoft 365, and IMAP/POP3 connectors for real-time email monitoring
"""

import asyncio
import json
import base64
import email
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime, timedelta
import structlog
import aiohttp
import imaplib
import poplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from ..database import SessionLocal
from ..models.integration_state import IntegrationState

logger = structlog.get_logger()


class EmailIntegrationBase:
    """Base class for email service integrations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.is_connected = False
        self.last_sync = None
        self.error_count = 0
        self.retry_backoff = 1  # seconds
        self._state_name = config.get('name') or self.__class__.__name__.lower()
        self._cursor = None
        
    async def connect(self) -> bool:
        """Connect to email service"""
        raise NotImplementedError
        
    async def disconnect(self):
        """Disconnect from email service"""
        raise NotImplementedError
        
    async def fetch_emails(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch recent emails"""
        raise NotImplementedError
        
    async def monitor_emails(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Monitor emails in real-time"""
        raise NotImplementedError

    def _load_state(self):
        db = SessionLocal()
        try:
            st = db.query(IntegrationState).filter(IntegrationState.name == self._state_name).first()
            if st:
                self._cursor = st.cursor
                self.last_sync = st.last_sync
        finally:
            db.close()

    def _save_state(self):
        db = SessionLocal()
        try:
            st = db.query(IntegrationState).filter(IntegrationState.name == self._state_name).first()
            if not st:
                st = IntegrationState(name=self._state_name)
                db.add(st)
            st.cursor = self._cursor
            st.last_sync = self.last_sync
            db.commit()
        finally:
            db.close()


class GmailIntegration(EmailIntegrationBase):
    """Gmail API integration using OAuth2"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.refresh_token = config.get('refresh_token')
        self.access_token = None
        self.session = None
        
        # Gmail API endpoints
        self.base_url = "https://gmail.googleapis.com/gmail/v1"
        self.oauth_url = "https://oauth2.googleapis.com/token"
        
    async def connect(self) -> bool:
        """Connect to Gmail using OAuth2"""
        try:
            self._load_state()
            if not self.refresh_token:
                logger.error("Gmail refresh token not provided")
                return False
                
            # Get access token
            await self._refresh_access_token()
            
            # Create HTTP session
            self.session = aiohttp.ClientSession()
            
            # Test connection (get profile)
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with self.session.get(f"{self.base_url}/users/me/profile", headers=headers) as response:
                if response.status == 200:
                    self.is_connected = True
                    logger.info("Connected to Gmail successfully")
                    return True
                else:
                    logger.error(f"Failed to connect to Gmail: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error connecting to Gmail: {e}")
            self.error_count += 1
            return False
    
    async def _refresh_access_token(self):
        """Refresh Gmail access token"""
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': self.refresh_token,
                'grant_type': 'refresh_token'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.oauth_url, data=data) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        self.access_token = token_data['access_token']
                        logger.info("Gmail access token refreshed")
                    else:
                        logger.error(f"Failed to refresh Gmail token: {response.status}")
                        self.error_count += 1
                        
        except Exception as e:
            logger.error(f"Error refreshing Gmail token: {e}")
            self.error_count += 1
    
    async def _get_profile(self) -> Optional[Dict[str, Any]]:
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with self.session.get(f"{self.base_url}/users/me/profile", headers=headers) as resp:
                if resp.status == 200:
                    return await resp.json()
                return None
        except Exception:
            return None
    
    async def fetch_emails(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch recent emails from Gmail (history-based when cursor is present)"""
        try:
            if not self.is_connected:
                await self.connect()
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            emails: List[Dict[str, Any]] = []
            
            if self._cursor:
                # Use history-based incremental sync
                params = {
                    'startHistoryId': self._cursor,
                    'historyTypes': 'messageAdded',
                    'maxResults': min(limit, 500)
                }
                async with self.session.get(f"{self.base_url}/users/me/history", headers=headers, params=params) as response:
                    if response.status == 404:
                        # Invalid startHistoryId; reset cursor to current profile historyId
                        logger.warning("Gmail history cursor invalid, resetting to current profile")
                        prof = await self._get_profile()
                        if prof and prof.get('historyId'):
                            self._cursor = prof['historyId']
                            self._save_state()
                        return []
                    if response.status != 200:
                        logger.error(f"Failed to fetch Gmail history: {response.status}")
                        self.error_count += 1
                        await asyncio.sleep(self.retry_backoff)
                        self.retry_backoff = min(self.retry_backoff * 2, 60)
                        return []
                    hist_data = await response.json()
                
                history = hist_data.get('history', [])
                message_ids: List[str] = []
                for h in history:
                    for added in h.get('messagesAdded', []) or []:
                        msg = added.get('message') or {}
                        if msg.get('id'):
                            message_ids.append(msg['id'])
                
                # Fetch full message details (dedupe)
                seen = set()
                for mid in message_ids:
                    if mid in seen:
                        continue
                    seen.add(mid)
                    email_data = await self._fetch_message_details(mid)
                    if email_data:
                        emails.append(email_data)
                
                # Update cursor to the latest historyId or profile's
                max_hist = None
                for h in history:
                    try:
                        hid = int(h.get('id') or h.get('historyId') or 0)
                        if not max_hist or hid > max_hist:
                            max_hist = hid
                    except Exception:
                        continue
                if max_hist:
                    self._cursor = str(max_hist)
                else:
                    prof = await self._get_profile()
                    if prof and prof.get('historyId'):
                        self._cursor = prof['historyId']
                self.last_sync = datetime.utcnow()
                self._save_state()
                return emails
            
            # Fallback: initial fetch via messages.list, then set cursor from profile
            params = {
                'maxResults': limit,
                'q': 'in:inbox'
            }
            async with self.session.get(f"{self.base_url}/users/me/messages", headers=headers, params=params) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch Gmail messages: {response.status}")
                    self.error_count += 1
                    await asyncio.sleep(self.retry_backoff)
                    self.retry_backoff = min(self.retry_backoff * 2, 60)
                    return []
                messages_data = await response.json()
            messages = messages_data.get('messages', [])
            for message in messages[:limit]:
                email_data = await self._fetch_message_details(message['id'])
                if email_data:
                    emails.append(email_data)
            logger.info(f"Fetched {len(emails)} emails from Gmail")
            self.last_sync = datetime.utcnow()
            # Set cursor to current profile historyId for next time
            prof = await self._get_profile()
            if prof and prof.get('historyId'):
                self._cursor = prof['historyId']
            self._save_state()
            return emails
        
        except Exception as e:
            logger.error(f"Error fetching Gmail emails: {e}")
            self.error_count += 1
            await asyncio.sleep(self.retry_backoff)
            self.retry_backoff = min(self.retry_backoff * 2, 60)
            return []
    
    async def _fetch_message_details(self, message_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed message information"""
        try:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            
            async with self.session.get(f"{self.base_url}/users/me/messages/{message_id}",
                                      headers=headers) as response:
                if response.status != 200:
                    return None
                    
                message_data = await response.json()
                
                # Parse email headers
                headers = {}
                for header in message_data.get('payload', {}).get('headers', []):
                    headers[header['name'].lower()] = header['value']
                
                # Extract email content
                body_text = ""
                body_html = ""
                attachments = []
                
                payload = message_data.get('payload', {})
                if 'parts' in payload:
                    for part in payload['parts']:
                        if part['mimeType'] == 'text/plain':
                            body_text = self._decode_body(part.get('body', {}).get('data', ''))
                        elif part['mimeType'] == 'text/html':
                            body_html = self._decode_body(part.get('body', {}).get('data', ''))
                        elif part['filename']:
                            attachments.append({
                                'filename': part['filename'],
                                'mime_type': part['mimeType'],
                                'size': part.get('body', {}).get('size', 0)
                            })
                else:
                    # Single part message
                    if payload['mimeType'] == 'text/plain':
                        body_text = self._decode_body(payload.get('body', {}).get('data', ''))
                    elif payload['mimeType'] == 'text/html':
                        body_html = self._decode_body(payload.get('body', {}).get('data', ''))
                
                return {
                    'message_id': headers.get('message-id', message_id),
                    'subject': headers.get('subject', ''),
                    'sender': headers.get('from', ''),
                    'recipients': headers.get('to', ''),
                    'date': headers.get('date', ''),
                    'body_text': body_text,
                    'body_html': body_html,
                    'attachments': attachments,
                    'source': 'gmail',
                    'raw_data': message_data
                }
                
        except Exception as e:
            logger.error(f"Error fetching Gmail message details: {e}")
            return None
    
    def _decode_body(self, encoded_data: str) -> str:
        """Decode base64 email body"""
        try:
            if not encoded_data:
                return ""
            return base64.urlsafe_b64decode(encoded_data).decode('utf-8')
        except Exception as e:
            logger.error(f"Error decoding email body: {e}")
            return ""
    
    async def monitor_emails(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Monitor Gmail for new emails"""
        try:
            last_check = datetime.utcnow()
            
            while True:
                # Check for new emails every 30 seconds
                await asyncio.sleep(30)
                
                # Fetch emails from last check
                emails = await self.fetch_emails(limit=50)
                
                for email_data in emails:
                    # Check if email is newer than last check
                    email_date = datetime.fromisoformat(
                        email_data['date'].replace('Z', '+00:00')
                    ) if email_data['date'] else datetime.utcnow()
                    
                    if email_date > last_check:
                        yield email_data
                
                last_check = datetime.utcnow()
                
        except Exception as e:
            logger.error(f"Error monitoring Gmail: {e}")
    
    async def disconnect(self):
        """Disconnect from Gmail"""
        if self.session:
            await self.session.close()
        self.is_connected = False
        logger.info("Disconnected from Gmail")


class Microsoft365Integration(EmailIntegrationBase):
    """Microsoft 365/Exchange integration using Microsoft Graph API"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.client_id = config.get('client_id')
        self.client_secret = config.get('client_secret')
        self.tenant_id = config.get('tenant_id')
        self.access_token = None
        self.session = None
        
        # Microsoft Graph API endpoints
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.oauth_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        
    async def connect(self) -> bool:
        """Connect to Microsoft 365 using client credentials or refresh token if provided"""
        try:
            # Prefer on-behalf-of/user delegated token if supplied
            self.refresh_token = self.config.get('refresh_token')
            self._load_state()
            if self.refresh_token:
                await self._get_access_token_with_refresh()
            else:
                # Get access token using client credentials flow
                await self._get_access_token()
            
            # Create HTTP session
            self.session = aiohttp.ClientSession()
            
            # Test connection
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with self.session.get(f"{self.base_url}/me", headers=headers) as response:
                if response.status == 200:
                    self.is_connected = True
                    logger.info("Connected to Microsoft 365 successfully")
                    return True
                else:
                    logger.error(f"Failed to connect to Microsoft 365: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error connecting to Microsoft 365: {e}")
            self.error_count += 1
            return False
    
    async def _get_access_token(self):
        """Get Microsoft 365 access token"""
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'https://graph.microsoft.com/.default',
                'grant_type': 'client_credentials'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.oauth_url, data=data) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        self.access_token = token_data['access_token']
                        logger.info("Microsoft 365 access token obtained")
                    else:
                        logger.error(f"Failed to get Microsoft 365 token: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error getting Microsoft 365 token: {e}")
    
    async def _get_access_token_with_refresh(self):
        """Use a refresh token to acquire an access token for Microsoft Graph."""
        try:
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'scope': 'https://graph.microsoft.com/.default offline_access'
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(self.oauth_url, data=data) as response:
                    if response.status == 200:
                        token_data = await response.json()
                        self.access_token = token_data['access_token']
                        logger.info("Microsoft 365 access token obtained via refresh token")
                    else:
                        logger.error(f"Failed to refresh Microsoft 365 token: {response.status}")
        except Exception as e:
            logger.error(f"Error refreshing Microsoft 365 token: {e}")
    
    async def fetch_emails(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch recent emails from Microsoft 365 using delta sync when available"""
        try:
            if not self.is_connected:
                await self.connect()
            
            headers = {"Authorization": f"Bearer {self.access_token}"}
            # Determine URL: use stored delta cursor if available; otherwise start a new delta query
            delta_url = self._cursor or f"{self.base_url}/me/mailFolders/inbox/messages/delta?$top={limit}&$orderby=receivedDateTime desc"
            
            async with self.session.get(delta_url, headers=headers) as response:
                if response.status != 200:
                    # Handle invalid delta (410) by resetting cursor and trying a fresh delta start next time
                    if response.status == 410:
                        logger.warning("Delta token invalid, resetting state")
                        self._cursor = None
                        self._save_state()
                    else:
                        logger.error(f"Failed to fetch Microsoft 365 messages (delta): {response.status}")
                    self.error_count += 1
                    await asyncio.sleep(self.retry_backoff)
                    self.retry_backoff = min(self.retry_backoff * 2, 60)
                    return []
                messages_data = await response.json()
            
            messages = messages_data.get('value', [])
            emails: List[Dict[str, Any]] = []
            for message in messages:
                email_data = self._process_message(message)
                if email_data:
                    emails.append(email_data)
            
            logger.info(f"Fetched {len(emails)} emails from Microsoft 365")
            self.last_sync = datetime.utcnow()
            # Update cursor from Graph response
            self._cursor = messages_data.get('@odata.deltaLink') or messages_data.get('@odata.nextLink') or self._cursor
            self._save_state()
            return emails
        except Exception as e:
            logger.error(f"Error fetching Microsoft 365 emails: {e}")
            self.error_count += 1
            await asyncio.sleep(self.retry_backoff)
            self.retry_backoff = min(self.retry_backoff * 2, 60)
            return []
    
    def _process_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Process Microsoft 365 message data"""
        try:
            return {
                'message_id': message.get('internetMessageId', ''),
                'subject': message.get('subject', ''),
                'sender': message.get('from', {}).get('emailAddress', {}).get('address', ''),
                'recipients': ', '.join([
                    recipient.get('emailAddress', {}).get('address', '')
                    for recipient in message.get('toRecipients', [])
                ]),
                'date': message.get('receivedDateTime', ''),
                'body_text': message.get('body', {}).get('content', ''),
                'body_html': message.get('body', {}).get('content', '') if message.get('body', {}).get('contentType') == 'html' else '',
                'attachments': [
                    {
                        'filename': att.get('name', ''),
                        'mime_type': att.get('contentType', ''),
                        'size': att.get('size', 0)
                    }
                    for att in message.get('attachments', [])
                ],
                'source': 'microsoft365',
                'raw_data': message
            }
            
        except Exception as e:
            logger.error(f"Error processing Microsoft 365 message: {e}")
            return None
    
    async def monitor_emails(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Monitor Microsoft 365 for new emails"""
        try:
            last_check = datetime.utcnow()
            
            while True:
                # Check for new emails every 30 seconds
                await asyncio.sleep(30)
                
                # Fetch emails from last check
                emails = await self.fetch_emails(limit=50)
                
                for email_data in emails:
                    # Check if email is newer than last check
                    email_date = datetime.fromisoformat(
                        email_data['date'].replace('Z', '+00:00')
                    ) if email_data['date'] else datetime.utcnow()
                    
                    if email_date > last_check:
                        yield email_data
                
                last_check = datetime.utcnow()
                
        except Exception as e:
            logger.error(f"Error monitoring Microsoft 365: {e}")
    
    async def disconnect(self):
        """Disconnect from Microsoft 365"""
        if self.session:
            await self.session.close()
        self.is_connected = False
        logger.info("Disconnected from Microsoft 365")


class IMAPIntegration(EmailIntegrationBase):
    """IMAP email integration for generic email servers"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.host = config.get('host')
        self.port = config.get('port', 993)
        self.username = config.get('username')
        self.password = config.get('password')
        self.use_ssl = config.get('use_ssl', True)
        self.mailbox = config.get('mailbox', 'INBOX')
        self.connection = None
        
    async def connect(self) -> bool:
        """Connect to IMAP server"""
        try:
            self._load_state()
            if self.use_ssl:
                self.connection = imaplib.IMAP4_SSL(self.host, self.port)
            else:
                self.connection = imaplib.IMAP4(self.host, self.port)
            
            self.connection.login(self.username, self.password)
            self.connection.select(self.mailbox)
            
            self.is_connected = True
            logger.info(f"Connected to IMAP server {self.host}")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to IMAP server: {e}")
            self.error_count += 1
            return False
    
    async def fetch_emails(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch recent emails from IMAP server"""
        try:
            if not self.is_connected:
                await self.connect()
            
            # Search for recent emails
            status, messages = self.connection.search(None, 'ALL')
            if status != 'OK':
                logger.error("Failed to search IMAP mailbox")
                return []
            
            message_ids = messages[0].split()
            recent_ids = message_ids[-limit:] if len(message_ids) > limit else message_ids
            
            emails = []
            for msg_id in recent_ids:
                email_data = await self._fetch_imap_message(msg_id)
                if email_data:
                    emails.append(email_data)
            
            logger.info(f"Fetched {len(emails)} emails from IMAP")
            self.last_sync = datetime.utcnow()
            self._cursor = None
            self._save_state()
            return emails
            
        except Exception as e:
            logger.error(f"Error fetching IMAP emails: {e}")
            self.error_count += 1
            await asyncio.sleep(self.retry_backoff)
            self.retry_backoff = min(self.retry_backoff * 2, 60)
            return []
    
    async def _fetch_imap_message(self, msg_id: bytes) -> Optional[Dict[str, Any]]:
        """Fetch individual IMAP message"""
        try:
            status, msg_data = self.connection.fetch(msg_id, '(RFC822)')
            if status != 'OK':
                return None
            
            # Parse email
            raw_email = msg_data[0][1]
            email_message = email.message_from_bytes(raw_email)
            
            # Extract headers
            subject = email_message.get('Subject', '')
            sender = email_message.get('From', '')
            recipients = email_message.get('To', '')
            date = email_message.get('Date', '')
            message_id = email_message.get('Message-ID', '')
            
            # Extract body
            body_text = ""
            body_html = ""
            attachments = []
            
            if email_message.is_multipart():
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get('Content-Disposition', ''))
                    
                    if 'attachment' in content_disposition:
                        filename = part.get_filename()
                        if filename:
                            attachments.append({
                                'filename': filename,
                                'mime_type': content_type,
                                'size': len(part.get_payload(decode=True) or b'')
                            })
                    elif content_type == 'text/plain':
                        body_text = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                    elif content_type == 'text/html':
                        body_html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
            else:
                content_type = email_message.get_content_type()
                if content_type == 'text/plain':
                    body_text = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
                elif content_type == 'text/html':
                    body_html = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
            
            return {
                'message_id': message_id,
                'subject': subject,
                'sender': sender,
                'recipients': recipients,
                'date': date,
                'body_text': body_text,
                'body_html': body_html,
                'attachments': attachments,
                'source': 'imap',
                'raw_data': str(email_message)
            }
            
        except Exception as e:
            logger.error(f"Error fetching IMAP message: {e}")
            return None
    
    async def monitor_emails(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Monitor IMAP for new emails"""
        try:
            last_check = datetime.utcnow()
            
            while True:
                # Check for new emails every 30 seconds
                await asyncio.sleep(30)
                
                # Fetch emails from last check
                emails = await self.fetch_emails(limit=50)
                
                for email_data in emails:
                    # Check if email is newer than last check
                    try:
                        email_date = datetime.strptime(
                            email_data['date'], '%a, %d %b %Y %H:%M:%S %z'
                        )
                    except:
                        email_date = datetime.utcnow()
                    
                    if email_date > last_check:
                        yield email_data
                
                last_check = datetime.utcnow()
                
        except Exception as e:
            logger.error(f"Error monitoring IMAP: {e}")
    
    async def disconnect(self):
        """Disconnect from IMAP server"""
        if self.connection:
            self.connection.close()
            self.connection.logout()
        self.is_connected = False
        logger.info("Disconnected from IMAP server")


class EmailIntegrationManager:
    """Manages multiple email service integrations"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.integrations = {}
        self.monitoring_tasks = []
        
    async def initialize(self):
        """Initialize all configured email integrations"""
        try:
            # Initialize Gmail integration
            if self.config.get('gmail', {}).get('enabled', False):
                gmail_config = self.config['gmail']
                self.integrations['gmail'] = GmailIntegration(gmail_config)
                await self.integrations['gmail'].connect()
            
            # Initialize Microsoft 365 integration
            if self.config.get('microsoft365', {}).get('enabled', False):
                o365_config = self.config['microsoft365']
                self.integrations['microsoft365'] = Microsoft365Integration(o365_config)
                await self.integrations['microsoft365'].connect()
            
            # Initialize IMAP integration
            if self.config.get('imap', {}).get('enabled', False):
                imap_config = self.config['imap']
                self.integrations['imap'] = IMAPIntegration(imap_config)
                await self.integrations['imap'].connect()
            
            logger.info(f"Initialized {len(self.integrations)} email integrations")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing email integrations: {e}")
            return False
    
    async def start_monitoring(self):
        """Start monitoring all email integrations"""
        try:
            for name, integration in self.integrations.items():
                if integration.is_connected:
                    task = asyncio.create_task(self._monitor_integration(name, integration))
                    self.monitoring_tasks.append(task)
                    logger.info(f"Started monitoring {name}")
            
        except Exception as e:
            logger.error(f"Error starting email monitoring: {e}")
    
    async def _monitor_integration(self, name: str, integration: EmailIntegrationBase):
        """Monitor a single email integration"""
        try:
            async for email_data in integration.monitor_emails():
                # Process email through Privik's threat detection
                await self._process_email(email_data, name)
                
        except Exception as e:
            logger.error(f"Error monitoring {name}: {e}")
    
    async def _process_email(self, email_data: Dict[str, Any], source: str):
        """Process email through Privik's threat detection system"""
        try:
            # This would integrate with the main email processing pipeline
            logger.info(f"Processing email from {source}: {email_data.get('subject', 'No Subject')}")
            
            # TODO: Integrate with email analyzer and threat detection
            # await email_analyzer.analyze_email(email_data)
            
        except Exception as e:
            logger.error(f"Error processing email: {e}")
    
    async def fetch_all_emails(self, limit: int = 100) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch emails from all integrations"""
        all_emails = {}
        
        for name, integration in self.integrations.items():
            if integration.is_connected:
                emails = await integration.fetch_emails(limit)
                all_emails[name] = emails
        
        return all_emails
    
    async def cleanup(self):
        """Cleanup all email integrations"""
        try:
            # Stop monitoring tasks
            for task in self.monitoring_tasks:
                task.cancel()
            
            # Disconnect all integrations
            for integration in self.integrations.values():
                await integration.disconnect()
            
            logger.info("Email integrations cleaned up")
            
        except Exception as e:
            logger.error(f"Error cleaning up email integrations: {e}")
