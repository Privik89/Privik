"""
SMTP Gateway Service
Implements real SMTP email gateway for email interception and processing
"""

import asyncio
import smtplib
import email
import email.mime.text
import email.mime.multipart
import structlog
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import socket
import ssl
from datetime import datetime
import json
import re
from email.header import decode_header
from email.utils import parseaddr

from .email_authentication import email_auth_service, EmailAuthenticationResult
from .reputation_service import reputation_service, DomainReputationResult, IPReputationResult
from .email_gateway_service import EmailGatewayService, EmailAction
from ..models.email import Email, EmailAttachment
from ..database import get_db

logger = structlog.get_logger()


class SMTPAction(Enum):
    """SMTP processing actions"""
    ACCEPT = "accept"
    REJECT = "reject"
    QUARANTINE = "quarantine"
    DEFER = "defer"


@dataclass
class SMTPProcessingResult:
    """Result of SMTP email processing"""
    action: SMTPAction
    reason: str
    authentication_result: Optional[EmailAuthenticationResult] = None
    domain_reputation: Optional[DomainReputationResult] = None
    ip_reputation: Optional[IPReputationResult] = None
    threat_score: float = 0.0
    processing_time: float = 0.0


class SMTPGateway:
    """SMTP Gateway for email interception and processing"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.host = config.get('host', '0.0.0.0')
        self.port = config.get('port', 25)
        self.max_connections = config.get('max_connections', 100)
        self.timeout = config.get('timeout', 30)
        self.max_message_size = config.get('max_message_size', 50 * 1024 * 1024)  # 50MB
        
        # Security policies
        self.policies = {
            'require_authentication': config.get('require_authentication', True),
            'block_disposable_emails': config.get('block_disposable_emails', True),
            'block_typosquat_domains': config.get('block_typosquat_domains', True),
            'min_authentication_score': config.get('min_authentication_score', 0.5),
            'min_reputation_score': config.get('min_reputation_score', 0.3),
            'max_recipients': config.get('max_recipients', 100),
            'rate_limit_per_ip': config.get('rate_limit_per_ip', 100),  # per hour
        }
        
        # Rate limiting
        self.rate_limits = {}
        self.connections = {}
        self.is_running = False
        
        # Email gateway service
        self.email_gateway_service = None
    
    async def initialize(self, email_gateway_service: EmailGatewayService):
        """Initialize the SMTP gateway"""
        try:
            self.email_gateway_service = email_gateway_service
            logger.info(f"SMTP Gateway initialized on {self.host}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize SMTP Gateway: {e}")
            return False
    
    async def start(self):
        """Start the SMTP gateway server"""
        try:
            self.is_running = True
            
            # Create server socket
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen(self.max_connections)
            server_socket.settimeout(1.0)  # Non-blocking
            
            logger.info(f"SMTP Gateway started on {self.host}:{self.port}")
            
            # Accept connections
            while self.is_running:
                try:
                    client_socket, client_address = server_socket.accept()
                    client_socket.settimeout(self.timeout)
                    
                    # Handle client connection
                    asyncio.create_task(self._handle_client(client_socket, client_address))
                    
                except socket.timeout:
                    continue
                except Exception as e:
                    if self.is_running:
                        logger.error(f"Error accepting connection: {e}")
                    continue
            
            server_socket.close()
            logger.info("SMTP Gateway stopped")
            
        except Exception as e:
            logger.error(f"Error starting SMTP Gateway: {e}")
    
    async def stop(self):
        """Stop the SMTP gateway server"""
        self.is_running = False
        logger.info("SMTP Gateway stopping...")
    
    async def _handle_client(self, client_socket: socket.socket, client_address: Tuple[str, int]):
        """Handle individual client connection"""
        client_ip = client_address[0]
        session_id = f"{client_ip}:{datetime.utcnow().timestamp()}"
        
        try:
            logger.info(f"New SMTP connection from {client_ip}")
            
            # Check rate limiting
            if not await self._check_rate_limit(client_ip):
                await self._send_response(client_socket, "421 Rate limit exceeded")
                return
            
            # Send welcome message
            await self._send_response(client_socket, "220 Privik SMTP Gateway ready")
            
            # SMTP conversation
            await self._smtp_conversation(client_socket, client_ip, session_id)
            
        except Exception as e:
            logger.error(f"Error handling client {client_ip}: {e}")
        finally:
            try:
                client_socket.close()
            except:
                pass
    
    async def _smtp_conversation(self, client_socket: socket.socket, client_ip: str, session_id: str):
        """Handle SMTP conversation"""
        try:
            # EHLO/HELO
            command = await self._receive_command(client_socket)
            if not command.startswith(('EHLO', 'HELO')):
                await self._send_response(client_socket, "500 Syntax error, command unrecognized")
                return
            
            await self._send_response(client_socket, "250 Privik SMTP Gateway")
            
            # MAIL FROM
            command = await self._receive_command(client_socket)
            if not command.startswith('MAIL FROM:'):
                await self._send_response(client_socket, "500 Syntax error in MAIL FROM")
                return
            
            sender = self._parse_email_address(command[10:])
            if not sender:
                await self._send_response(client_socket, "501 Syntax error in sender address")
                return
            
            # Validate sender
            sender_result = await self._validate_sender(sender, client_ip)
            if sender_result.action == SMTPAction.REJECT:
                await self._send_response(client_socket, f"550 {sender_result.reason}")
                return
            
            await self._send_response(client_socket, "250 Sender OK")
            
            # RCPT TO
            recipients = []
            while True:
                command = await self._receive_command(client_socket)
                if command.startswith('RCPT TO:'):
                    recipient = self._parse_email_address(command[8:])
                    if recipient:
                        recipients.append(recipient)
                        await self._send_response(client_socket, "250 Recipient OK")
                    else:
                        await self._send_response(client_socket, "501 Syntax error in recipient address")
                elif command == 'DATA':
                    break
                else:
                    await self._send_response(client_socket, "500 Syntax error")
                    return
            
            # Check recipient limit
            if len(recipients) > self.policies['max_recipients']:
                await self._send_response(client_socket, "550 Too many recipients")
                return
            
            # DATA
            await self._send_response(client_socket, "354 Start mail input; end with <CRLF>.<CRLF>")
            
            # Receive email data
            email_data = await self._receive_email_data(client_socket)
            
            # Process email
            processing_result = await self._process_email(
                sender, recipients, email_data, client_ip, session_id
            )
            
            # Send response based on processing result
            if processing_result.action == SMTPAction.ACCEPT:
                await self._send_response(client_socket, "250 Message accepted")
            elif processing_result.action == SMTPAction.REJECT:
                await self._send_response(client_socket, f"550 {processing_result.reason}")
            elif processing_result.action == SMTPAction.QUARANTINE:
                await self._send_response(client_socket, "250 Message quarantined")
            else:  # DEFER
                await self._send_response(client_socket, "450 Temporary failure")
            
        except Exception as e:
            logger.error(f"Error in SMTP conversation: {e}")
            await self._send_response(client_socket, "421 Service unavailable")
    
    async def _validate_sender(self, sender: str, client_ip: str) -> SMTPProcessingResult:
        """Validate sender email and IP"""
        try:
            start_time = datetime.utcnow()
            
            # Extract domain from sender
            sender_domain = sender.split('@')[1] if '@' in sender else sender
            
            # Run validation checks in parallel
            tasks = [
                self._check_authentication(sender, client_ip, sender_domain),
                self._check_domain_reputation(sender_domain),
                self._check_ip_reputation(client_ip)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            auth_result = results[0] if not isinstance(results[0], Exception) else None
            domain_reputation = results[1] if not isinstance(results[1], Exception) else None
            ip_reputation = results[2] if not isinstance(results[2], Exception) else None
            
            # Calculate overall threat score
            threat_score = 0.0
            if auth_result:
                threat_score += (1.0 - auth_result.authentication_score) * 0.4
            if domain_reputation:
                threat_score += (1.0 - domain_reputation.score) * 0.3
            if ip_reputation:
                threat_score += (1.0 - ip_reputation.score) * 0.3
            
            # Determine action
            action = SMTPAction.ACCEPT
            reason = "Sender validated"
            
            # Check policies
            if self.policies['require_authentication'] and auth_result:
                if auth_result.authentication_score < self.policies['min_authentication_score']:
                    action = SMTPAction.REJECT
                    reason = "Authentication failed"
            
            if self.policies['block_disposable_emails'] and domain_reputation:
                if domain_reputation.is_disposable:
                    action = SMTPAction.REJECT
                    reason = "Disposable email domain not allowed"
            
            if self.policies['block_typosquat_domains'] and domain_reputation:
                if domain_reputation.is_typosquat:
                    action = SMTPAction.REJECT
                    reason = "Typosquatting domain detected"
            
            if domain_reputation and domain_reputation.score < self.policies['min_reputation_score']:
                action = SMTPAction.QUARANTINE
                reason = "Low domain reputation"
            
            if ip_reputation and ip_reputation.score < self.policies['min_reputation_score']:
                action = SMTPAction.QUARANTINE
                reason = "Low IP reputation"
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            return SMTPProcessingResult(
                action=action,
                reason=reason,
                authentication_result=auth_result,
                domain_reputation=domain_reputation,
                ip_reputation=ip_reputation,
                threat_score=threat_score,
                processing_time=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error validating sender: {e}")
            return SMTPProcessingResult(
                action=SMTPAction.DEFER,
                reason="Validation error",
                threat_score=1.0
            )
    
    async def _check_authentication(self, sender: str, client_ip: str, sender_domain: str) -> Optional[EmailAuthenticationResult]:
        """Check email authentication"""
        try:
            # Mock email headers for authentication check
            email_headers = {
                'From': sender,
                'Return-Path': sender,
                'Received': f'from {client_ip} by privik-gateway'
            }
            
            return await email_auth_service.validate_email_authentication(
                email_headers, client_ip, sender_domain
            )
        except Exception as e:
            logger.error(f"Error checking authentication: {e}")
            return None
    
    async def _check_domain_reputation(self, domain: str) -> Optional[DomainReputationResult]:
        """Check domain reputation"""
        try:
            return await reputation_service.check_domain_reputation(domain)
        except Exception as e:
            logger.error(f"Error checking domain reputation: {e}")
            return None
    
    async def _check_ip_reputation(self, ip_address: str) -> Optional[IPReputationResult]:
        """Check IP reputation"""
        try:
            return await reputation_service.check_ip_reputation(ip_address)
        except Exception as e:
            logger.error(f"Error checking IP reputation: {e}")
            return None
    
    async def _process_email(
        self, 
        sender: str, 
        recipients: List[str], 
        email_data: str, 
        client_ip: str, 
        session_id: str
    ) -> SMTPProcessingResult:
        """Process email through the gateway"""
        try:
            # Parse email
            email_message = email.message_from_string(email_data)
            
            # Extract email content
            email_content = {
                'message_id': email_message.get('Message-ID', f'<{session_id}@privik>'),
                'subject': email_message.get('Subject', ''),
                'sender': sender,
                'recipients': recipients,
                'body_text': self._extract_text_content(email_message),
                'body_html': self._extract_html_content(email_message),
                'headers': dict(email_message.items()),
                'attachments': self._extract_attachments(email_message),
                'source': 'smtp_gateway'
            }
            
            # Process through email gateway service
            if self.email_gateway_service:
                gateway_result = await self.email_gateway_service.process_email(email_content)
                
                # Convert gateway action to SMTP action
                if gateway_result.action == EmailAction.ALLOW:
                    smtp_action = SMTPAction.ACCEPT
                elif gateway_result.action == EmailAction.BLOCK:
                    smtp_action = SMTPAction.REJECT
                elif gateway_result.action == EmailAction.QUARANTINE:
                    smtp_action = SMTPAction.QUARANTINE
                else:  # SANDBOX
                    smtp_action = SMTPAction.QUARANTINE
                
                return SMTPProcessingResult(
                    action=smtp_action,
                    reason=f"Gateway processing: {gateway_result.threat_type}",
                    threat_score=gateway_result.threat_score,
                    processing_time=gateway_result.processing_time
                )
            else:
                return SMTPProcessingResult(
                    action=SMTPAction.ACCEPT,
                    reason="No gateway service available"
                )
                
        except Exception as e:
            logger.error(f"Error processing email: {e}")
            return SMTPProcessingResult(
                action=SMTPAction.DEFER,
                reason="Processing error"
            )
    
    def _extract_text_content(self, email_message) -> str:
        """Extract text content from email"""
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        return part.get_payload(decode=True).decode('utf-8', errors='ignore')
            else:
                if email_message.get_content_type() == "text/plain":
                    return email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
            return ""
        except Exception:
            return ""
    
    def _extract_html_content(self, email_message) -> str:
        """Extract HTML content from email"""
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/html":
                        return part.get_payload(decode=True).decode('utf-8', errors='ignore')
            else:
                if email_message.get_content_type() == "text/html":
                    return email_message.get_payload(decode=True).decode('utf-8', errors='ignore')
            return ""
        except Exception:
            return ""
    
    def _extract_attachments(self, email_message) -> List[Dict[str, Any]]:
        """Extract attachment information from email"""
        attachments = []
        try:
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_filename():
                        attachments.append({
                            'filename': part.get_filename(),
                            'mime_type': part.get_content_type(),
                            'size': len(part.get_payload(decode=True) or b''),
                            'content': part.get_payload(decode=True)
                        })
            return attachments
        except Exception:
            return []
    
    async def _check_rate_limit(self, client_ip: str) -> bool:
        """Check rate limiting for client IP"""
        try:
            current_time = datetime.utcnow()
            hour_key = current_time.replace(minute=0, second=0, microsecond=0)
            
            if client_ip not in self.rate_limits:
                self.rate_limits[client_ip] = {}
            
            if hour_key not in self.rate_limits[client_ip]:
                self.rate_limits[client_ip][hour_key] = 0
            
            self.rate_limits[client_ip][hour_key] += 1
            
            # Clean old entries
            for ip in list(self.rate_limits.keys()):
                for hour in list(self.rate_limits[ip].keys()):
                    if (current_time - hour).total_seconds() > 3600:
                        del self.rate_limits[ip][hour]
                if not self.rate_limits[ip]:
                    del self.rate_limits[ip]
            
            return self.rate_limits[client_ip][hour_key] <= self.policies['rate_limit_per_ip']
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True  # Allow on error
    
    def _parse_email_address(self, address: str) -> Optional[str]:
        """Parse email address from SMTP command"""
        try:
            # Remove angle brackets and whitespace
            address = address.strip('<> \t\n\r')
            
            # Parse using email.utils
            name, email_addr = parseaddr(address)
            
            if email_addr and '@' in email_addr:
                return email_addr.lower()
            return None
        except Exception:
            return None
    
    async def _receive_command(self, client_socket: socket.socket) -> str:
        """Receive SMTP command from client"""
        try:
            data = client_socket.recv(1024).decode('utf-8', errors='ignore')
            return data.strip()
        except Exception as e:
            logger.error(f"Error receiving command: {e}")
            return ""
    
    async def _receive_email_data(self, client_socket: socket.socket) -> str:
        """Receive email data from client"""
        try:
            email_data = ""
            while True:
                data = client_socket.recv(4096).decode('utf-8', errors='ignore')
                if not data:
                    break
                
                email_data += data
                
                # Check for end of data marker
                if email_data.endswith('\r\n.\r\n'):
                    break
                
                # Check message size limit
                if len(email_data) > self.max_message_size:
                    raise Exception("Message too large")
            
            # Remove end of data marker
            if email_data.endswith('\r\n.\r\n'):
                email_data = email_data[:-5]
            
            return email_data
        except Exception as e:
            logger.error(f"Error receiving email data: {e}")
            return ""
    
    async def _send_response(self, client_socket: socket.socket, response: str):
        """Send SMTP response to client"""
        try:
            client_socket.send(f"{response}\r\n".encode('utf-8'))
        except Exception as e:
            logger.error(f"Error sending response: {e}")


# Global instance
smtp_gateway = None


async def get_smtp_gateway(config: Dict[str, Any] = None) -> SMTPGateway:
    """Get the global SMTP gateway instance"""
    global smtp_gateway
    if smtp_gateway is None:
        default_config = {
            'host': '0.0.0.0',
            'port': 25,
            'max_connections': 100,
            'timeout': 30,
            'max_message_size': 50 * 1024 * 1024,
            'require_authentication': True,
            'block_disposable_emails': True,
            'block_typosquat_domains': True,
            'min_authentication_score': 0.5,
            'min_reputation_score': 0.3,
            'max_recipients': 100,
            'rate_limit_per_ip': 100
        }
        config = config or default_config
        smtp_gateway = SMTPGateway(config)
    return smtp_gateway
