"""
Email Gateway Service for Zero-Trust Email Routing
Implements email routing, link rewriting, and attachment processing
"""

import asyncio
import smtplib
import email
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import structlog
from urllib.parse import urlparse, quote_plus
import hashlib
import uuid

from ..core.config import get_settings
from .real_time_sandbox import RealTimeSandbox
from .email_analyzer import analyze_email_content

logger = structlog.get_logger()
settings = get_settings()


class EmailGateway:
    """Zero-trust email gateway with link rewriting and attachment processing"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # Pass CAPE settings into sandbox
        sandbox_cfg = config.get('sandbox', {})
        for key in ['cape_enabled', 'cape_base_url', 'cape_api_token']:
            if key in config:
                sandbox_cfg[key] = config[key]
        self.sandbox = RealTimeSandbox(sandbox_cfg)
        self.link_rewrite_domain = config.get('link_rewrite_domain', 'links.privik.com')
        self.attachment_storage = config.get('attachment_storage', '/tmp/attachments')
        self.zero_trust_policies = config.get('zero_trust_policies', {})
        
        # Email routing configuration
        self.smtp_host = config.get('smtp_host', 'localhost')
        self.smtp_port = config.get('smtp_port', 587)
        self.smtp_username = config.get('smtp_username', '')
        self.smtp_password = config.get('smtp_password', '')
        
        # Link tracking
        self.link_tracking = {}
        self.attachment_tracking = {}
        
    async def initialize(self):
        """Initialize email gateway"""
        try:
            # Initialize sandbox
            await self.sandbox.initialize()
            
            # Create attachment storage directory
            import os
            os.makedirs(self.attachment_storage, exist_ok=True)
            
            logger.info("Email gateway initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize email gateway", error=str(e))
            return False
    
    async def process_incoming_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming email through zero-trust pipeline"""
        try:
            logger.info("Processing incoming email", message_id=email_data.get('message_id'))
            
            # 1. Initial email analysis
            initial_analysis = await self._analyze_email(email_data)
            
            # 2. Apply zero-trust policies
            policy_result = await self._apply_zero_trust_policies(email_data, initial_analysis)
            
            # 3. Process based on policy decision
            if policy_result['action'] == 'block':
                return await self._block_email(email_data, policy_result)
            elif policy_result['action'] == 'quarantine':
                return await self._quarantine_email(email_data, policy_result)
            elif policy_result['action'] == 'rewrite':
                return await self._rewrite_and_deliver(email_data, initial_analysis, policy_result)
            else:
                return await self._deliver_email(email_data, initial_analysis)
                
        except Exception as e:
            logger.error("Error processing incoming email", error=str(e))
            return {
                'status': 'error',
                'action': 'block',
                'reason': 'processing_error',
                'error': str(e)
            }
    
    async def _analyze_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze email for threats"""
        try:
            # Extract email content
            subject = email_data.get('subject', '')
            body = email_data.get('body_text', '') or email_data.get('body_html', '')
            sender = email_data.get('sender', '')
            
            # Perform AI analysis
            analysis_result = await analyze_email_content(
                email_id=0,  # Will be set when stored in database
                content=body,
                subject=subject
            )
            
            # Extract links
            links = self._extract_links(body)
            
            # Extract attachments
            attachments = email_data.get('attachments', [])
            
            return {
                'threat_score': analysis_result.get('threat_score', 0.0),
                'ai_verdict': analysis_result.get('ai_verdict', 'safe'),
                'is_suspicious': analysis_result.get('is_suspicious', False),
                'links': links,
                'attachments': attachments,
                'analysis_details': analysis_result
            }
            
        except Exception as e:
            logger.error("Error analyzing email", error=str(e))
            return {
                'threat_score': 0.0,
                'ai_verdict': 'error',
                'is_suspicious': False,
                'links': [],
                'attachments': [],
                'analysis_details': {'error': str(e)}
            }
    
    async def _apply_zero_trust_policies(self, email_data: Dict[str, Any], 
                                       analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Apply zero-trust policies to email"""
        try:
            # Default policy: never trust, always verify
            action = 'rewrite'  # Default to rewriting for zero-trust
            
            # Check threat score
            if analysis['threat_score'] > 0.8:
                action = 'block'
                reason = 'high_threat_score'
            elif analysis['threat_score'] > 0.5:
                action = 'quarantine'
                reason = 'suspicious_content'
            elif analysis['ai_verdict'] == 'malicious':
                action = 'block'
                reason = 'ai_malicious_verdict'
            elif analysis['is_suspicious']:
                action = 'quarantine'
                reason = 'suspicious_indicators'
            
            # Check for links - always rewrite in zero-trust
            if analysis['links']:
                action = 'rewrite'
                reason = 'contains_links'
            
            # Check for attachments - always process in zero-trust
            if analysis['attachments']:
                action = 'rewrite'
                reason = 'contains_attachments'
            
            # Apply custom policies
            custom_policy = await self._check_custom_policies(email_data, analysis)
            if custom_policy:
                action = custom_policy['action']
                reason = custom_policy['reason']
            
            return {
                'action': action,
                'reason': reason,
                'confidence': analysis.get('threat_score', 0.0),
                'policy_applied': 'zero_trust'
            }
            
        except Exception as e:
            logger.error("Error applying zero-trust policies", error=str(e))
            return {
                'action': 'block',
                'reason': 'policy_error',
                'confidence': 1.0,
                'policy_applied': 'error'
            }
    
    async def _check_custom_policies(self, email_data: Dict[str, Any], 
                                   analysis: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check custom zero-trust policies"""
        try:
            sender = email_data.get('sender', '')
            recipients = email_data.get('recipients', [])
            
            # Policy 1: Block known malicious senders
            if sender in self.zero_trust_policies.get('blocked_senders', []):
                return {'action': 'block', 'reason': 'blocked_sender'}
            
            # Policy 2: Quarantine emails to high-risk users
            high_risk_users = self.zero_trust_policies.get('high_risk_users', [])
            if any(recipient in high_risk_users for recipient in recipients):
                return {'action': 'quarantine', 'reason': 'high_risk_recipient'}
            
            # Policy 3: Always rewrite emails with external links
            external_links = [link for link in analysis['links'] 
                            if not self._is_internal_domain(link)]
            if external_links:
                return {'action': 'rewrite', 'reason': 'external_links'}
            
            return None
            
        except Exception as e:
            logger.error("Error checking custom policies", error=str(e))
            return None
    
    async def _rewrite_and_deliver(self, email_data: Dict[str, Any], 
                                 analysis: Dict[str, Any], 
                                 policy_result: Dict[str, Any]) -> Dict[str, Any]:
        """Rewrite email with zero-trust modifications and deliver"""
        try:
            logger.info("Rewriting email for zero-trust delivery")
            
            # Create rewritten email
            rewritten_email = email_data.copy()
            
            # Rewrite links
            if analysis['links']:
                rewritten_email = await self._rewrite_links(rewritten_email, analysis['links'])
            
            # Process attachments
            if analysis['attachments']:
                rewritten_email = await self._process_attachments(rewritten_email, analysis['attachments'])
            
            # Add zero-trust headers
            rewritten_email = self._add_zero_trust_headers(rewritten_email, analysis, policy_result)
            
            # Deliver rewritten email
            delivery_result = await self._deliver_email(rewritten_email, analysis)
            
            return {
                'status': 'success',
                'action': 'rewrite_deliver',
                'delivery_result': delivery_result,
                'links_rewritten': len(analysis['links']),
                'attachments_processed': len(analysis['attachments'])
            }
            
        except Exception as e:
            logger.error("Error rewriting and delivering email", error=str(e))
            return {
                'status': 'error',
                'action': 'rewrite_deliver',
                'error': str(e)
            }
    
    async def _rewrite_links(self, email_data: Dict[str, Any], links: List[str]) -> Dict[str, Any]:
        """Rewrite links for click-time analysis"""
        try:
            body_text = email_data.get('body_text', '')
            body_html = email_data.get('body_html', '')
            
            # Rewrite links in text body
            if body_text:
                for link in links:
                    rewritten_link = await self._create_rewritten_link(link, email_data)
                    body_text = body_text.replace(link, rewritten_link)
                email_data['body_text'] = body_text
            
            # Rewrite links in HTML body
            if body_html:
                for link in links:
                    rewritten_link = await self._create_rewritten_link(link, email_data)
                    body_html = body_html.replace(link, rewritten_link)
                email_data['body_html'] = body_html
            
            return email_data
            
        except Exception as e:
            logger.error("Error rewriting links", error=str(e))
            return email_data
    
    async def _create_rewritten_link(self, original_url: str, email_data: Dict[str, Any]) -> str:
        """Create rewritten link for click-time analysis"""
        try:
            # Generate unique tracking ID
            tracking_id = str(uuid.uuid4())
            
            # Create tracking record
            self.link_tracking[tracking_id] = {
                'original_url': original_url,
                'email_id': email_data.get('message_id'),
                'sender': email_data.get('sender'),
                'recipients': email_data.get('recipients', []),
                'created_at': datetime.utcnow(),
                'clicks': 0
            }
            
            # Create rewritten URL
            rewritten_url = f"https://{self.link_rewrite_domain}/click/{tracking_id}"
            
            logger.info("Created rewritten link", 
                       original_url=original_url, 
                       rewritten_url=rewritten_url,
                       tracking_id=tracking_id)
            
            return rewritten_url
            
        except Exception as e:
            logger.error("Error creating rewritten link", error=str(e))
            return original_url
    
    async def _process_attachments(self, email_data: Dict[str, Any], 
                                 attachments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process attachments for zero-trust delivery"""
        try:
            processed_attachments = []
            
            for attachment in attachments:
                # Generate unique attachment ID
                attachment_id = str(uuid.uuid4())
                
                # Create tracking record
                self.attachment_tracking[attachment_id] = {
                    'original_filename': attachment.get('filename'),
                    'content_type': attachment.get('content_type'),
                    'size': attachment.get('size'),
                    'email_id': email_data.get('message_id'),
                    'created_at': datetime.utcnow(),
                    'downloads': 0
                }
                
                # Create processed attachment
                processed_attachment = {
                    'filename': f"secure_{attachment.get('filename')}",
                    'content_type': attachment.get('content_type'),
                    'size': attachment.get('size'),
                    'attachment_id': attachment_id,
                    'download_url': f"https://{self.link_rewrite_domain}/attachment/{attachment_id}"
                }
                
                processed_attachments.append(processed_attachment)
            
            # Replace original attachments with processed ones
            email_data['attachments'] = processed_attachments
            
            return email_data
            
        except Exception as e:
            logger.error("Error processing attachments", error=str(e))
            return email_data
    
    def _add_zero_trust_headers(self, email_data: Dict[str, Any], 
                              analysis: Dict[str, Any], 
                              policy_result: Dict[str, Any]) -> Dict[str, Any]:
        """Add zero-trust headers to email"""
        try:
            headers = email_data.get('headers', {})
            
            # Add Privik security headers
            headers['X-Privik-Security'] = 'Zero-Trust'
            headers['X-Privik-Threat-Score'] = str(analysis.get('threat_score', 0.0))
            headers['X-Privik-AI-Verdict'] = analysis.get('ai_verdict', 'safe')
            headers['X-Privik-Policy'] = policy_result.get('policy_applied', 'zero_trust')
            headers['X-Privik-Processed'] = datetime.utcnow().isoformat()
            
            # Add warning for suspicious emails
            if analysis.get('is_suspicious', False):
                headers['X-Privik-Warning'] = 'This email has been flagged as suspicious'
            
            email_data['headers'] = headers
            return email_data
            
        except Exception as e:
            logger.error("Error adding zero-trust headers", error=str(e))
            return email_data
    
    async def _deliver_email(self, email_data: Dict[str, Any], 
                           analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Deliver email to recipients"""
        try:
            # For MVP, log delivery
            # In production, integrate with actual SMTP server
            
            logger.info("Delivering email", 
                       message_id=email_data.get('message_id'),
                       recipients=email_data.get('recipients', []))
            
            return {
                'status': 'delivered',
                'delivery_time': datetime.utcnow(),
                'recipients': email_data.get('recipients', [])
            }
            
        except Exception as e:
            logger.error("Error delivering email", error=str(e))
            return {
                'status': 'delivery_failed',
                'error': str(e)
            }
    
    async def _block_email(self, email_data: Dict[str, Any], 
                         policy_result: Dict[str, Any]) -> Dict[str, Any]:
        """Block email based on policy"""
        try:
            logger.info("Blocking email", 
                       message_id=email_data.get('message_id'),
                       reason=policy_result.get('reason'))
            
            return {
                'status': 'blocked',
                'action': 'block',
                'reason': policy_result.get('reason'),
                'blocked_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error("Error blocking email", error=str(e))
            return {
                'status': 'error',
                'action': 'block',
                'error': str(e)
            }
    
    async def _quarantine_email(self, email_data: Dict[str, Any], 
                              policy_result: Dict[str, Any]) -> Dict[str, Any]:
        """Quarantine email for review"""
        try:
            logger.info("Quarantining email", 
                       message_id=email_data.get('message_id'),
                       reason=policy_result.get('reason'))
            
            # Store in quarantine for review
            # In production, integrate with quarantine system
            
            return {
                'status': 'quarantined',
                'action': 'quarantine',
                'reason': policy_result.get('reason'),
                'quarantined_at': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error("Error quarantining email", error=str(e))
            return {
                'status': 'error',
                'action': 'quarantine',
                'error': str(e)
            }
    
    def _extract_links(self, content: str) -> List[str]:
        """Extract links from email content"""
        try:
            # URL regex pattern
            url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
            links = re.findall(url_pattern, content)
            
            # Remove duplicates and filter
            unique_links = list(set(links))
            filtered_links = [link for link in unique_links if self._is_valid_url(link)]
            
            return filtered_links
            
        except Exception as e:
            logger.error("Error extracting links", error=str(e))
            return []
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except:
            return False
    
    def _is_internal_domain(self, url: str) -> bool:
        """Check if URL is from internal domain"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Check against internal domains
            internal_domains = self.zero_trust_policies.get('internal_domains', [])
            return any(domain.endswith(internal_domain.lower()) for internal_domain in internal_domains)
            
        except:
            return False
    
    async def handle_link_click(self, tracking_id: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle click on rewritten link"""
        try:
            # Get tracking information
            tracking_info = self.link_tracking.get(tracking_id)
            if not tracking_info:
                return {'status': 'error', 'reason': 'tracking_id_not_found'}
            
            # Update click count
            tracking_info['clicks'] += 1
            tracking_info['last_click'] = datetime.utcnow()
            tracking_info['user_context'] = user_context
            
            # Perform real-time analysis
            original_url = tracking_info['original_url']
            sandbox_result = await self.sandbox.analyze_link_click(original_url, user_context)
            
            # Log click event
            logger.info("Link click analyzed", 
                       tracking_id=tracking_id,
                       original_url=original_url,
                       verdict=sandbox_result.verdict,
                       confidence=sandbox_result.confidence)
            
            # Return result
            if sandbox_result.verdict == 'safe':
                return {
                    'status': 'safe',
                    'redirect_url': original_url,
                    'verdict': sandbox_result.verdict,
                    'confidence': sandbox_result.confidence
                }
            else:
                return {
                    'status': 'blocked',
                    'reason': sandbox_result.verdict,
                    'confidence': sandbox_result.confidence,
                    'threat_indicators': sandbox_result.threat_indicators
                }
                
        except Exception as e:
            logger.error("Error handling link click", error=str(e))
            return {
                'status': 'error',
                'reason': 'analysis_error',
                'error': str(e)
            }
    
    async def handle_attachment_download(self, attachment_id: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle attachment download request"""
        try:
            # Get tracking information
            tracking_info = self.attachment_tracking.get(attachment_id)
            if not tracking_info:
                return {'status': 'error', 'reason': 'attachment_id_not_found'}
            
            # Update download count
            tracking_info['downloads'] += 1
            tracking_info['last_download'] = datetime.utcnow()
            tracking_info['user_context'] = user_context
            
            # Perform real-time analysis
            file_path = f"{self.attachment_storage}/{attachment_id}"
            file_type = tracking_info.get('content_type', '')
            
            sandbox_result = await self.sandbox.analyze_attachment(file_path, file_type)
            
            # Log download event
            logger.info("Attachment download analyzed", 
                       attachment_id=attachment_id,
                       filename=tracking_info.get('original_filename'),
                       verdict=sandbox_result.verdict,
                       confidence=sandbox_result.confidence)
            
            # Return result
            if sandbox_result.verdict == 'safe':
                return {
                    'status': 'safe',
                    'download_url': f"https://{self.link_rewrite_domain}/download/{attachment_id}",
                    'verdict': sandbox_result.verdict,
                    'confidence': sandbox_result.confidence
                }
            else:
                return {
                    'status': 'blocked',
                    'reason': sandbox_result.verdict,
                    'confidence': sandbox_result.confidence,
                    'threat_indicators': sandbox_result.threat_indicators
                }
                
        except Exception as e:
            logger.error("Error handling attachment download", error=str(e))
            return {
                'status': 'error',
                'reason': 'analysis_error',
                'error': str(e)
            }
    
    async def cleanup(self):
        """Cleanup email gateway resources"""
        try:
            await self.sandbox.cleanup()
            logger.info("Email gateway cleaned up")
        except Exception as e:
            logger.error("Error cleaning up email gateway", error=str(e))
