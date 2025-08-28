"""
Privik Endpoint Agent Email Monitor
Monitors email clients for threats and suspicious content
"""

import asyncio
import time
import os
import re
import email
import base64
from typing import Dict, Any, List, Optional
from pathlib import Path
import structlog

from ..config import AgentConfig
from ..security import SecurityManager
from ..communication import ServerCommunicator

logger = structlog.get_logger()

class EmailMonitor:
    """Monitors email clients for threats and suspicious content."""
    
    def __init__(self, config: AgentConfig, security_manager: SecurityManager, 
                 communicator: ServerCommunicator):
        """Initialize the email monitor."""
        self.config = config
        self.security_manager = security_manager
        self.communicator = communicator
        self.running = False
        self.last_scan_time = 0
        self.scanned_emails = set()
        
        # Threat patterns
        self.suspicious_patterns = [
            r'urgent.*action.*required',
            r'account.*suspended',
            r'password.*expired',
            r'verify.*account',
            r'click.*here.*login',
            r'bank.*security.*alert',
            r'payment.*failed',
            r'invoice.*attached',
            r'wire.*transfer',
            r'gift.*card.*code',
        ]
        
        # File extensions to monitor
        self.dangerous_extensions = [
            '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
            '.jar', '.msi', '.dmg', '.app', '.deb', '.rpm', '.sh'
        ]
    
    async def initialize(self) -> bool:
        """Initialize the email monitor."""
        try:
            logger.info("Initializing email monitor")
            
            # Verify email client paths exist
            valid_clients = []
            for client_path in self.config.email_clients:
                if os.path.exists(client_path):
                    valid_clients.append(client_path)
                else:
                    logger.warning("Email client path not found", path=client_path)
            
            if not valid_clients:
                logger.warning("No valid email client paths found")
                return False
            
            logger.info("Email monitor initialized", client_count=len(valid_clients))
            return True
            
        except Exception as e:
            logger.error("Failed to initialize email monitor", error=str(e))
            return False
    
    async def start_monitoring(self):
        """Start email monitoring loop."""
        try:
            self.running = True
            logger.info("Starting email monitoring")
            
            while self.running:
                try:
                    await self._scan_emails()
                    await asyncio.sleep(self.config.email_scan_interval)
                except Exception as e:
                    logger.error("Error in email monitoring loop", error=str(e))
                    await asyncio.sleep(30)  # Wait before retrying
            
        except Exception as e:
            logger.error("Email monitoring error", error=str(e))
        finally:
            self.running = False
            logger.info("Email monitoring stopped")
    
    async def _scan_emails(self):
        """Scan emails for threats."""
        try:
            current_time = time.time()
            
            # Scan each email client
            for client_path in self.config.email_clients:
                if not os.path.exists(client_path):
                    continue
                
                await self._scan_email_client(client_path)
            
            self.last_scan_time = current_time
            
        except Exception as e:
            logger.error("Error scanning emails", error=str(e))
    
    async def _scan_email_client(self, client_path: str):
        """Scan a specific email client."""
        try:
            # Detect email client type
            client_type = self._detect_email_client(client_path)
            
            if client_type == "thunderbird":
                await self._scan_thunderbird(client_path)
            elif client_type == "outlook":
                await self._scan_outlook(client_path)
            elif client_type == "apple_mail":
                await self._scan_apple_mail(client_path)
            else:
                logger.debug("Unsupported email client", path=client_path)
                
        except Exception as e:
            logger.error("Error scanning email client", path=client_path, error=str(e))
    
    def _detect_email_client(self, client_path: str) -> str:
        """Detect the type of email client."""
        path_lower = client_path.lower()
        
        if "thunderbird" in path_lower:
            return "thunderbird"
        elif "outlook" in path_lower or "microsoft" in path_lower:
            return "outlook"
        elif "mail" in path_lower and "apple" in path_lower:
            return "apple_mail"
        else:
            return "unknown"
    
    async def _scan_thunderbird(self, client_path: str):
        """Scan Thunderbird email client."""
        try:
            # Thunderbird stores emails in .msf files
            profile_path = os.path.join(client_path, "Profiles")
            if not os.path.exists(profile_path):
                return
            
            # Find profile directories
            for profile_dir in os.listdir(profile_path):
                profile_path_full = os.path.join(profile_path, profile_dir)
                if not os.path.isdir(profile_path_full):
                    continue
                
                # Look for mail folders
                await self._scan_thunderbird_profile(profile_path_full)
                
        except Exception as e:
            logger.error("Error scanning Thunderbird", error=str(e))
    
    async def _scan_thunderbird_profile(self, profile_path: str):
        """Scan a Thunderbird profile directory."""
        try:
            # Common mail folder locations
            mail_locations = [
                os.path.join(profile_path, "Mail"),
                os.path.join(profile_path, "ImapMail"),
            ]
            
            for mail_location in mail_locations:
                if not os.path.exists(mail_location):
                    continue
                
                # Recursively scan for .eml files
                for root, dirs, files in os.walk(mail_location):
                    for file in files:
                        if file.endswith('.eml'):
                            file_path = os.path.join(root, file)
                            await self._analyze_email_file(file_path)
                            
        except Exception as e:
            logger.error("Error scanning Thunderbird profile", error=str(e))
    
    async def _scan_outlook(self, client_path: str):
        """Scan Outlook email client."""
        try:
            # Outlook stores emails in .pst/.ost files
            # This is a simplified implementation
            # In a real implementation, you'd need to use libraries like pywin32
            # to properly read Outlook data
            
            logger.debug("Outlook scanning not fully implemented", path=client_path)
            
        except Exception as e:
            logger.error("Error scanning Outlook", error=str(e))
    
    async def _scan_apple_mail(self, client_path: str):
        """Scan Apple Mail client."""
        try:
            # Apple Mail stores emails in .emlx files
            for root, dirs, files in os.walk(client_path):
                for file in files:
                    if file.endswith('.emlx'):
                        file_path = os.path.join(root, file)
                        await self._analyze_email_file(file_path)
                        
        except Exception as e:
            logger.error("Error scanning Apple Mail", error=str(e))
    
    async def _analyze_email_file(self, file_path: str):
        """Analyze an email file for threats."""
        try:
            # Check if we've already scanned this file
            file_hash = self.security_manager.hash_file(file_path)
            if file_hash in self.scanned_emails:
                return
            
            # Parse email
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                email_content = f.read()
            
            # Parse email structure
            email_message = email.message_from_string(email_content)
            
            # Analyze email
            analysis_result = await self._analyze_email_content(email_message)
            
            if analysis_result['threat_score'] > 0:
                # Send analysis to server
                await self.communicator.send_email_analysis(analysis_result)
                logger.info("Threat detected in email", 
                           file=file_path,
                           threat_score=analysis_result['threat_score'])
            
            # Mark as scanned
            self.scanned_emails.add(file_hash)
            
        except Exception as e:
            logger.error("Error analyzing email file", file=file_path, error=str(e))
    
    async def _analyze_email_content(self, email_message) -> Dict[str, Any]:
        """Analyze email content for threats."""
        try:
            analysis = {
                'subject': email_message.get('subject', ''),
                'from': email_message.get('from', ''),
                'to': email_message.get('to', ''),
                'date': email_message.get('date', ''),
                'message_id': email_message.get('message-id', ''),
                'threat_score': 0,
                'threat_indicators': [],
                'attachments': [],
                'links': [],
                'suspicious_content': [],
            }
            
            # Analyze subject line
            subject_score, subject_indicators = self._analyze_text(
                analysis['subject'], 'subject'
            )
            analysis['threat_score'] += subject_score
            analysis['threat_indicators'].extend(subject_indicators)
            
            # Analyze email body
            body_content = self._extract_email_body(email_message)
            body_score, body_indicators = self._analyze_text(body_content, 'body')
            analysis['threat_score'] += body_score
            analysis['threat_indicators'].extend(body_indicators)
            
            # Extract and analyze links
            links = self._extract_links(body_content)
            analysis['links'] = links
            
            for link in links:
                link_score, link_indicators = self._analyze_link(link)
                analysis['threat_score'] += link_score
                analysis['threat_indicators'].extend(link_indicators)
            
            # Analyze attachments
            attachments = self._extract_attachments(email_message)
            analysis['attachments'] = attachments
            
            for attachment in attachments:
                attachment_score, attachment_indicators = self._analyze_attachment(attachment)
                analysis['threat_score'] += attachment_score
                analysis['threat_indicators'].extend(attachment_indicators)
            
            # Analyze sender
            sender_score, sender_indicators = self._analyze_sender(analysis['from'])
            analysis['threat_score'] += sender_score
            analysis['threat_indicators'].extend(sender_indicators)
            
            return analysis
            
        except Exception as e:
            logger.error("Error analyzing email content", error=str(e))
            return {'threat_score': 0, 'error': str(e)}
    
    def _extract_email_body(self, email_message) -> str:
        """Extract email body content."""
        try:
            body = ""
            
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        body += part.get_payload(decode=True).decode('utf-8', errors='ignore')
            else:
                body = email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
            
            return body
            
        except Exception as e:
            logger.error("Error extracting email body", error=str(e))
            return ""
    
    def _analyze_text(self, text: str, context: str) -> tuple:
        """Analyze text for suspicious patterns."""
        score = 0
        indicators = []
        
        try:
            text_lower = text.lower()
            
            # Check for suspicious patterns
            for pattern in self.suspicious_patterns:
                if re.search(pattern, text_lower):
                    score += 10
                    indicators.append(f"suspicious_pattern_{pattern}")
            
            # Check for urgency indicators
            urgency_words = ['urgent', 'immediate', 'now', 'asap', 'critical']
            urgency_count = sum(1 for word in urgency_words if word in text_lower)
            if urgency_count > 2:
                score += 5
                indicators.append("high_urgency")
            
            # Check for financial terms
            financial_words = ['bank', 'account', 'password', 'login', 'verify', 'payment']
            financial_count = sum(1 for word in financial_words if word in text_lower)
            if financial_count > 3:
                score += 5
                indicators.append("financial_terms")
            
            return score, indicators
            
        except Exception as e:
            logger.error("Error analyzing text", error=str(e))
            return 0, []
    
    def _extract_links(self, text: str) -> List[str]:
        """Extract links from text."""
        try:
            # Simple URL regex pattern
            url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            links = re.findall(url_pattern, text)
            return links
            
        except Exception as e:
            logger.error("Error extracting links", error=str(e))
            return []
    
    def _analyze_link(self, link: str) -> tuple:
        """Analyze a link for threats."""
        score = 0
        indicators = []
        
        try:
            link_lower = link.lower()
            
            # Check for suspicious domains
            suspicious_domains = ['bit.ly', 'tinyurl.com', 'goo.gl', 't.co']
            for domain in suspicious_domains:
                if domain in link_lower:
                    score += 15
                    indicators.append(f"suspicious_domain_{domain}")
            
            # Check for IP addresses
            ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
            if re.search(ip_pattern, link):
                score += 10
                indicators.append("ip_address_in_url")
            
            # Check for suspicious TLDs
            suspicious_tlds = ['.tk', '.ml', '.ga', '.cf']
            for tld in suspicious_tlds:
                if link_lower.endswith(tld):
                    score += 10
                    indicators.append(f"suspicious_tld_{tld}")
            
            return score, indicators
            
        except Exception as e:
            logger.error("Error analyzing link", error=str(e))
            return 0, []
    
    def _extract_attachments(self, email_message) -> List[Dict[str, Any]]:
        """Extract attachment information."""
        attachments = []
        
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_filename():
                        attachment = {
                            'filename': part.get_filename(),
                            'content_type': part.get_content_type(),
                            'size': len(part.get_payload()),
                        }
                        attachments.append(attachment)
            
            return attachments
            
        except Exception as e:
            logger.error("Error extracting attachments", error=str(e))
            return []
    
    def _analyze_attachment(self, attachment: Dict[str, Any]) -> tuple:
        """Analyze an attachment for threats."""
        score = 0
        indicators = []
        
        try:
            filename = attachment.get('filename', '').lower()
            content_type = attachment.get('content_type', '').lower()
            
            # Check for dangerous file extensions
            for ext in self.dangerous_extensions:
                if filename.endswith(ext):
                    score += 20
                    indicators.append(f"dangerous_extension_{ext}")
            
            # Check for executable content types
            executable_types = ['application/x-executable', 'application/x-msdownload']
            if content_type in executable_types:
                score += 25
                indicators.append(f"executable_content_type_{content_type}")
            
            # Check for large attachments
            size = attachment.get('size', 0)
            if size > 10 * 1024 * 1024:  # 10MB
                score += 5
                indicators.append("large_attachment")
            
            return score, indicators
            
        except Exception as e:
            logger.error("Error analyzing attachment", error=str(e))
            return 0, []
    
    def _analyze_sender(self, sender: str) -> tuple:
        """Analyze sender information."""
        score = 0
        indicators = []
        
        try:
            sender_lower = sender.lower()
            
            # Check for suspicious sender patterns
            suspicious_patterns = [
                r'noreply@',
                r'no-reply@',
                r'security@',
                r'admin@',
                r'support@',
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, sender_lower):
                    score += 5
                    indicators.append(f"suspicious_sender_{pattern}")
            
            # Check for generic domains
            generic_domains = ['gmail.com', 'yahoo.com', 'hotmail.com']
            for domain in generic_domains:
                if domain in sender_lower:
                    score += 2
                    indicators.append(f"generic_domain_{domain}")
            
            return score, indicators
            
        except Exception as e:
            logger.error("Error analyzing sender", error=str(e))
            return 0, []
    
    async def get_status(self) -> Dict[str, Any]:
        """Get email monitor status."""
        return {
            'running': self.running,
            'last_scan_time': self.last_scan_time,
            'scanned_emails_count': len(self.scanned_emails),
            'email_clients': self.config.email_clients,
            'scan_interval': self.config.email_scan_interval,
        }
    
    async def stop(self):
        """Stop the email monitor."""
        self.running = False
        logger.info("Email monitor stopped")
