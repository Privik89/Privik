"""
Email Gateway Service
Real-time email processing and threat detection pipeline
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import structlog
from dataclasses import dataclass
from enum import Enum

from .email_integrations import EmailIntegrationManager
from .ai_threat_detection import AIThreatDetection
from .email_authentication import email_auth_service
from .reputation_service import reputation_service
from .link_rewriter import get_link_rewriter
from .email_header_analyzer import email_header_analyzer
from .attachment_validator import get_attachment_validator
# from .sandbox import SandboxService  # TODO: Implement SandboxService class
from ..models.email import Email, EmailAttachment
from ..models.click import ClickEvent
from ..models.threat import ThreatIntel, ThreatIndicator
from ..database import get_db

logger = structlog.get_logger()


class EmailAction(Enum):
    """Email processing actions"""
    ALLOW = "allow"
    QUARANTINE = "quarantine"
    BLOCK = "block"
    SANDBOX = "sandbox"


@dataclass
class EmailProcessingResult:
    """Result of email processing"""
    email_id: str
    action: EmailAction
    threat_score: float
    threat_type: str
    confidence: float
    indicators: List[str]
    processing_time: float
    sandbox_result: Optional[Dict[str, Any]] = None
    ai_analysis: Optional[Dict[str, Any]] = None


class EmailGatewayService:
    """Main email gateway service for real-time email processing"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.email_integrations = None
        self.ai_threat_detection = None
        self.link_rewriter = None
        self.attachment_validator = None
        # self.sandbox_service = None  # TODO: Implement SandboxService
        self.processing_queue = asyncio.Queue()
        self.is_running = False
        
        # Processing statistics
        self.stats = {
            'emails_processed': 0,
            'threats_detected': 0,
            'emails_quarantined': 0,
            'emails_blocked': 0,
            'processing_time_avg': 0.0
        }
        
        # Zero-trust policies
        self.zero_trust_policies = {
            'default_action': EmailAction.SANDBOX,
            'threat_thresholds': {
                'block': 0.8,
                'quarantine': 0.5,
                'sandbox': 0.3
            },
            'whitelist_domains': [],
            'blacklist_domains': [],
            'suspicious_keywords': [
                'urgent', 'verify', 'suspended', 'wire transfer',
                'bank transfer', 'click here', 'login now'
            ]
        }
    
    async def initialize(self) -> bool:
        """Initialize the email gateway service"""
        try:
            logger.info("Initializing Email Gateway Service")
            
            # Initialize email integrations
            self.email_integrations = EmailIntegrationManager(self.config.get('email_integrations', {}))
            await self.email_integrations.initialize()
            
            # Initialize AI threat detection
            ai_config = self.config.get('ai_threat_detection', {})
            self.ai_threat_detection = AIThreatDetection(ai_config)
            await self.ai_threat_detection.initialize()
            
            # Initialize link rewriter
            link_config = self.config.get('link_rewriter', {})
            self.link_rewriter = get_link_rewriter(link_config)
            
            # Initialize attachment validator
            attachment_config = self.config.get('attachment_validator', {})
            self.attachment_validator = get_attachment_validator(attachment_config)
            
            # Initialize sandbox service (TODO: Implement SandboxService)
            # sandbox_config = self.config.get('sandbox', {})
            # self.sandbox_service = SandboxService(sandbox_config)
            # await self.sandbox_service.initialize()
            
            logger.info("Email Gateway Service initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Email Gateway Service: {e}")
            return False
    
    async def start(self):
        """Start the email gateway service"""
        try:
            if not self.is_running:
                self.is_running = True
                
                # Start email monitoring
                await self.email_integrations.start_monitoring()
                
                # Start processing queue
                processing_task = asyncio.create_task(self._process_email_queue())
                
                # Start statistics reporting
                stats_task = asyncio.create_task(self._report_statistics())
                
                logger.info("Email Gateway Service started")
                
                # Wait for tasks
                await asyncio.gather(processing_task, stats_task)
                
        except Exception as e:
            logger.error(f"Error starting Email Gateway Service: {e}")
    
    async def stop(self):
        """Stop the email gateway service"""
        try:
            self.is_running = False
            
            # Cleanup integrations
            if self.email_integrations:
                await self.email_integrations.cleanup()
            
            # Cleanup AI threat detection
            if self.ai_threat_detection:
                await self.ai_threat_detection.cleanup()
            
            # Cleanup sandbox service (TODO: Implement SandboxService)
            # if self.sandbox_service:
            #     await self.sandbox_service.cleanup()
            
            logger.info("Email Gateway Service stopped")
            
        except Exception as e:
            logger.error(f"Error stopping Email Gateway Service: {e}")
    
    async def process_email(self, email_data: Dict[str, Any]) -> EmailProcessingResult:
        """Process a single email through the comprehensive threat detection pipeline"""
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Processing email: {email_data.get('subject', 'No Subject')}")
            
            # Step 1: Store email in database
            email_record = await self._store_email(email_data)
            
            # Step 2: Email authentication validation (DMARC, DKIM, SPF)
            auth_result = await self._validate_email_authentication(email_data)
            
            # Step 3: Reputation checking
            reputation_result = await self._check_reputation(email_data)
            
            # Step 4: Header analysis
            header_result = await self._analyze_headers(email_data)
            
            # Step 5: Link rewriting and analysis
            link_result = await self._rewrite_links(email_data, str(email_record.id))
            
            # Step 6: Attachment validation
            attachment_result = await self._validate_attachments(email_data)
            
            # Step 7: AI threat detection
            ai_result = await self.ai_threat_detection.predict_email_threat(email_data)
            
            # Step 8: Calculate combined threat score
            combined_threat_score = self._calculate_combined_threat_score(
                auth_result, reputation_result, header_result, attachment_result, ai_result
            )
            
            # Step 9: Apply zero-trust policies
            action = self._apply_zero_trust_policies(email_data, combined_threat_score)
            
            # Step 10: Sandbox analysis if needed
            sandbox_result = None
            if action == EmailAction.SANDBOX and email_data.get('attachments'):
                sandbox_result = await self._sandbox_attachments(email_data['attachments'])
            
            # Step 11: Update email record with results
            await self._update_email_record(email_record, combined_threat_score, action, sandbox_result)
            
            # Step 12: Take action based on result
            await self._execute_action(email_record, action, combined_threat_score, sandbox_result)
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Update statistics
            self._update_statistics(processing_time, action, combined_threat_score)
            
            result = EmailProcessingResult(
                email_id=str(email_record.id),
                action=action,
                threat_score=combined_threat_score,
                threat_type=ai_result.threat_type,
                confidence=ai_result.confidence,
                indicators=ai_result.indicators,
                processing_time=processing_time,
                sandbox_result=sandbox_result,
                ai_analysis={
                    'threat_type': ai_result.threat_type,
                    'confidence': ai_result.confidence,
                    'indicators': ai_result.indicators,
                    'model_version': ai_result.model_version,
                    'authentication_score': auth_result.authentication_score if auth_result else 0.0,
                    'reputation_score': reputation_result.get('score', 0.0) if reputation_result else 0.0,
                    'header_risk': header_result.risk_score if header_result else 0.0
                }
            )
            
            logger.info(f"Email processed: {action.value} (threat_score: {combined_threat_score:.3f})")
            return result
            
        except Exception as e:
            logger.error(f"Error processing email: {e}")
            return EmailProcessingResult(
                email_id="error",
                action=EmailAction.QUARANTINE,
                threat_score=1.0,
                threat_type="error",
                confidence=1.0,
                indicators=["processing_error"],
                processing_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    async def _store_email(self, email_data: Dict[str, Any]) -> Email:
        """Store email in database"""
        try:
            db = next(get_db())
            
            email_record = Email(
                message_id=email_data.get('message_id', ''),
                subject=email_data.get('subject', ''),
                sender=email_data.get('sender', ''),
                recipients=email_data.get('recipients', ''),
                content_type=email_data.get('content_type', 'text/plain'),
                body_text=email_data.get('body_text', ''),
                body_html=email_data.get('body_html', ''),
                received_at=datetime.utcnow()
            )
            
            db.add(email_record)
            db.commit()
            db.refresh(email_record)
            
            # Store attachments if any
            for attachment_data in email_data.get('attachments', []):
                attachment = EmailAttachment(
                    email_id=email_record.id,
                    filename=attachment_data.get('filename', ''),
                    content_type=attachment_data.get('mime_type', ''),
                    file_size=attachment_data.get('size', 0),
                    file_path=None  # Will be set when file is stored
                )
                db.add(attachment)
            
            db.commit()
            return email_record
            
        except Exception as e:
            logger.error(f"Error storing email: {e}")
            raise
    
    async def _validate_email_authentication(self, email_data: Dict[str, Any]):
        """Validate email authentication (DMARC, DKIM, SPF)"""
        try:
            # Mock headers for authentication check
            headers = {
                'From': email_data.get('sender', ''),
                'Return-Path': email_data.get('sender', ''),
                'Received': f'from {email_data.get("source_ip", "unknown")} by privik-gateway'
            }
            
            return await email_auth_service.validate_email_authentication(
                headers, 
                email_data.get('source_ip', '127.0.0.1'),
                email_data.get('sender_domain', 'unknown.com')
            )
        except Exception as e:
            logger.error(f"Error validating email authentication: {e}")
            return None
    
    async def _check_reputation(self, email_data: Dict[str, Any]):
        """Check domain and IP reputation"""
        try:
            sender_domain = email_data.get('sender_domain', 'unknown.com')
            source_ip = email_data.get('source_ip', '127.0.0.1')
            
            # Run reputation checks in parallel
            domain_task = reputation_service.check_domain_reputation(sender_domain)
            ip_task = reputation_service.check_ip_reputation(source_ip)
            
            domain_result, ip_result = await asyncio.gather(domain_task, ip_task, return_exceptions=True)
            
            return {
                'domain_reputation': domain_result if not isinstance(domain_result, Exception) else None,
                'ip_reputation': ip_result if not isinstance(ip_result, Exception) else None,
                'score': min(
                    domain_result.score if not isinstance(domain_result, Exception) else 0.5,
                    ip_result.score if not isinstance(ip_result, Exception) else 0.5
                )
            }
        except Exception as e:
            logger.error(f"Error checking reputation: {e}")
            return {'score': 0.5}
    
    async def _analyze_headers(self, email_data: Dict[str, Any]):
        """Analyze email headers"""
        try:
            headers = email_data.get('headers', {})
            return await email_header_analyzer.analyze_headers(headers)
        except Exception as e:
            logger.error(f"Error analyzing headers: {e}")
            return None
    
    async def _rewrite_links(self, email_data: Dict[str, Any], email_id: str):
        """Rewrite links in email content"""
        try:
            if not self.link_rewriter:
                return None
            
            # Combine text and HTML content
            content = email_data.get('body_html', '') or email_data.get('body_text', '')
            if not content:
                return None
            
            return await self.link_rewriter.rewrite_email_links(content, email_id)
        except Exception as e:
            logger.error(f"Error rewriting links: {e}")
            return None
    
    async def _validate_attachments(self, email_data: Dict[str, Any]):
        """Validate email attachments"""
        try:
            if not self.attachment_validator or not email_data.get('attachments'):
                return []
            
            validation_results = []
            for attachment in email_data['attachments']:
                filename = attachment.get('filename', 'unknown')
                content = attachment.get('content', b'')
                mime_type = attachment.get('mime_type')
                
                result = await self.attachment_validator.validate_attachment(
                    filename, content, mime_type
                )
                validation_results.append(result)
            
            return validation_results
        except Exception as e:
            logger.error(f"Error validating attachments: {e}")
            return []
    
    def _calculate_combined_threat_score(self, auth_result, reputation_result, header_result, attachment_result, ai_result):
        """Calculate combined threat score from all analysis results"""
        try:
            scores = []
            weights = []
            
            # Authentication score (weight: 0.2)
            if auth_result:
                scores.append(1.0 - auth_result.authentication_score)  # Convert to threat score
                weights.append(0.2)
            
            # Reputation score (weight: 0.2)
            if reputation_result:
                scores.append(1.0 - reputation_result.get('score', 0.5))
                weights.append(0.2)
            
            # Header analysis score (weight: 0.2)
            if header_result:
                scores.append(header_result.risk_score)
                weights.append(0.2)
            
            # Attachment validation score (weight: 0.2)
            if attachment_result:
                attachment_scores = []
                for result in attachment_result:
                    if result.risk_level.value == 'safe':
                        attachment_scores.append(0.0)
                    elif result.risk_level.value == 'low':
                        attachment_scores.append(0.2)
                    elif result.risk_level.value == 'medium':
                        attachment_scores.append(0.5)
                    elif result.risk_level.value == 'high':
                        attachment_scores.append(0.8)
                    else:  # critical
                        attachment_scores.append(1.0)
                
                if attachment_scores:
                    scores.append(max(attachment_scores))  # Use highest threat score
                    weights.append(0.2)
            
            # AI threat detection score (weight: 0.2)
            if ai_result:
                scores.append(ai_result.threat_score)
                weights.append(0.2)
            
            # Calculate weighted average
            if scores and weights:
                total_weight = sum(weights)
                weighted_score = sum(score * weight for score, weight in zip(scores, weights)) / total_weight
                return min(1.0, max(0.0, weighted_score))
            else:
                return 0.5  # Default neutral score
            
        except Exception as e:
            logger.error(f"Error calculating combined threat score: {e}")
            return 0.5
    
    def _apply_zero_trust_policies(self, email_data: Dict[str, Any], threat_score: float) -> EmailAction:
        """Apply zero-trust policies to determine email action"""
        try:
            # Check whitelist/blacklist domains
            sender_domain = self._extract_domain(email_data.get('sender', ''))
            
            if sender_domain in self.zero_trust_policies['blacklist_domains']:
                return EmailAction.BLOCK
            
            if sender_domain in self.zero_trust_policies['whitelist_domains']:
                return EmailAction.ALLOW
            
            # Check threat score thresholds
            threat_score = threat_score
            
            if threat_score >= self.zero_trust_policies['threat_thresholds']['block']:
                return EmailAction.BLOCK
            elif threat_score >= self.zero_trust_policies['threat_thresholds']['quarantine']:
                return EmailAction.QUARANTINE
            elif threat_score >= self.zero_trust_policies['threat_thresholds']['sandbox']:
                return EmailAction.SANDBOX
            else:
                return EmailAction.ALLOW
                
        except Exception as e:
            logger.error(f"Error applying zero-trust policies: {e}")
            return EmailAction.QUARANTINE
    
    def _extract_domain(self, email_address: str) -> str:
        """Extract domain from email address"""
        try:
            if '@' in email_address:
                return email_address.split('@')[1].lower()
            return email_address.lower()
        except:
            return email_address.lower()
    
    async def _sandbox_attachments(self, attachments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Sandbox email attachments"""
        try:
            sandbox_results = {}
            
            for attachment in attachments:
                filename = attachment.get('filename', '')
                if filename:
                    # For MVP, simulate sandbox analysis
                    sandbox_results[filename] = {
                        'verdict': 'safe',
                        'threat_score': 0.1,
                        'indicators': [],
                        'analysis_time': 2.5
                    }
            
            return sandbox_results
            
        except Exception as e:
            logger.error(f"Error sandboxing attachments: {e}")
            return {}
    
    async def _update_email_record(self, email_record: Email, ai_result, action: EmailAction, sandbox_result: Optional[Dict[str, Any]]):
        """Update email record with analysis results"""
        try:
            db = next(get_db())
            
            email_record.threat_score = ai_result.threat_score
            email_record.is_suspicious = ai_result.threat_score > 0.5
            email_record.ai_verdict = ai_result.threat_type
            email_record.static_scan_result = json.dumps({
                'action': action.value,
                'confidence': ai_result.confidence,
                'indicators': ai_result.indicators,
                'sandbox_result': sandbox_result
            })
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Error updating email record: {e}")
    
    async def _execute_action(self, email_record: Email, action: EmailAction, ai_result, sandbox_result: Optional[Dict[str, Any]]):
        """Execute the determined action for the email"""
        try:
            if action == EmailAction.BLOCK:
                await self._block_email(email_record, ai_result)
            elif action == EmailAction.QUARANTINE:
                await self._quarantine_email(email_record, ai_result)
            elif action == EmailAction.SANDBOX:
                await self._sandbox_email(email_record, ai_result, sandbox_result)
            else:  # ALLOW
                await self._allow_email(email_record, ai_result)
                
        except Exception as e:
            logger.error(f"Error executing action {action.value}: {e}")
    
    async def _block_email(self, email_record: Email, ai_result):
        """Block email and notify security team"""
        logger.warning(f"BLOCKED email: {email_record.subject} (threat_score: {ai_result.threat_score})")
        # TODO: Implement email blocking logic
        # TODO: Send alert to security team
    
    async def _quarantine_email(self, email_record: Email, ai_result):
        """Quarantine email for manual review"""
        logger.warning(f"QUARANTINED email: {email_record.subject} (threat_score: {ai_result.threat_score})")
        # TODO: Implement email quarantine logic
        # TODO: Send notification to security team
    
    async def _sandbox_email(self, email_record: Email, ai_result, sandbox_result: Optional[Dict[str, Any]]):
        """Sandbox email for further analysis"""
        logger.info(f"SANDBOXED email: {email_record.subject} (threat_score: {ai_result.threat_score})")
        # TODO: Implement email sandboxing logic
        # TODO: Schedule for further analysis
    
    async def _allow_email(self, email_record: Email, ai_result):
        """Allow email to proceed"""
        logger.info(f"ALLOWED email: {email_record.subject} (threat_score: {ai_result.threat_score})")
        # TODO: Implement email delivery logic
    
    def _update_statistics(self, processing_time: float, action: EmailAction, threat_score: float):
        """Update processing statistics"""
        self.stats['emails_processed'] += 1
        
        if threat_score > 0.5:
            self.stats['threats_detected'] += 1
        
        if action == EmailAction.QUARANTINE:
            self.stats['emails_quarantined'] += 1
        elif action == EmailAction.BLOCK:
            self.stats['emails_blocked'] += 1
        
        # Update average processing time
        current_avg = self.stats['processing_time_avg']
        total_emails = self.stats['emails_processed']
        self.stats['processing_time_avg'] = ((current_avg * (total_emails - 1)) + processing_time) / total_emails
    
    async def _process_email_queue(self):
        """Process emails from the queue"""
        try:
            while self.is_running:
                try:
                    # Get email from queue (with timeout)
                    email_data = await asyncio.wait_for(
                        self.processing_queue.get(), 
                        timeout=1.0
                    )
                    
                    # Process email
                    await self.process_email(email_data)
                    
                except asyncio.TimeoutError:
                    # No emails in queue, continue
                    continue
                except Exception as e:
                    logger.error(f"Error processing email from queue: {e}")
                    
        except Exception as e:
            logger.error(f"Error in email processing queue: {e}")
    
    async def _report_statistics(self):
        """Report processing statistics periodically"""
        try:
            while self.is_running:
                await asyncio.sleep(300)  # Report every 5 minutes
                
                logger.info("Email Gateway Statistics", **self.stats)
                
        except Exception as e:
            logger.error(f"Error reporting statistics: {e}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        return self.stats.copy()
    
    async def update_zero_trust_policies(self, policies: Dict[str, Any]):
        """Update zero-trust policies"""
        try:
            self.zero_trust_policies.update(policies)
            logger.info("Zero-trust policies updated")
        except Exception as e:
            logger.error(f"Error updating zero-trust policies: {e}")
    
    async def add_to_processing_queue(self, email_data: Dict[str, Any]):
        """Add email to processing queue"""
        try:
            await self.processing_queue.put(email_data)
        except Exception as e:
            logger.error(f"Error adding email to processing queue: {e}")


# Global email gateway service instance
email_gateway_service = None


async def get_email_gateway_service() -> EmailGatewayService:
    """Get the global email gateway service instance"""
    global email_gateway_service
    if email_gateway_service is None:
        # Initialize with default config
        config = {
            'email_integrations': {
                'gmail': {'enabled': False},
                'microsoft365': {'enabled': False},
                'imap': {'enabled': False}
            },
            'ai_threat_detection': {
                'model_storage_path': './models',
                'retrain_interval': 7
            },
            'sandbox': {
                'timeout': 30,
                'max_file_size': '50MB'
            }
        }
        email_gateway_service = EmailGatewayService(config)
        await email_gateway_service.initialize()
    return email_gateway_service
