"""
Zero-Trust Orchestrator
Coordinates all zero-trust security components for comprehensive threat protection
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog
from dataclasses import dataclass

from .email_gateway import EmailGateway
from .real_time_sandbox import RealTimeSandbox
from .ai_threat_detection import AIThreatDetection
from .email_analyzer import analyze_email_content
from .link_analyzer import analyze_link_safety
from .sandbox import enqueue_file_for_detonation

logger = structlog.get_logger()


@dataclass
class ZeroTrustResult:
    action: str  # allow, block, quarantine, rewrite
    confidence: float
    threat_score: float
    threat_type: str
    indicators: List[str]
    analysis_details: Dict[str, Any]
    processing_time: float


class ZeroTrustOrchestrator:
    """Orchestrates zero-trust security across all components"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Initialize components
        self.email_gateway = EmailGateway(config.get('email_gateway', {}))
        self.sandbox = RealTimeSandbox(config.get('sandbox', {}))
        self.ai_detection = AIThreatDetection(config.get('ai_detection', {}))
        
        # Zero-trust policies
        self.policies = config.get('zero_trust_policies', {})
        self.enforcement_level = config.get('enforcement_level', 'strict')
        
        # Performance tracking
        self.analysis_times = []
        self.threat_counts = {
            'blocked': 0,
            'quarantined': 0,
            'rewritten': 0,
            'allowed': 0
        }
        
    async def initialize(self):
        """Initialize zero-trust orchestrator and all components"""
        try:
            logger.info("Initializing Zero-Trust Orchestrator")
            
            # Initialize all components
            components = [
                self.email_gateway.initialize(),
                self.sandbox.initialize(),
                self.ai_detection.initialize()
            ]
            
            results = await asyncio.gather(*components, return_exceptions=True)
            
            # Check for initialization errors
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Component {i} failed to initialize", error=str(result))
                    return False
            
            logger.info("Zero-Trust Orchestrator initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize Zero-Trust Orchestrator", error=str(e))
            return False
    
    async def process_email(self, email_data: Dict[str, Any]) -> ZeroTrustResult:
        """Process email through complete zero-trust pipeline"""
        start_time = datetime.utcnow()
        
        try:
            logger.info("Processing email through zero-trust pipeline", 
                       message_id=email_data.get('message_id'))
            
            # Phase 1: Initial AI Analysis
            ai_prediction = await self.ai_detection.predict_email_threat(email_data)
            
            # Phase 2: Email Gateway Processing
            gateway_result = await self.email_gateway.process_incoming_email(email_data)
            
            # Phase 3: Apply Zero-Trust Policies
            policy_result = await self._apply_zero_trust_policies(
                email_data, ai_prediction, gateway_result
            )
            
            # Phase 4: Determine Final Action
            final_action = await self._determine_final_action(
                ai_prediction, gateway_result, policy_result
            )
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Create result
            result = ZeroTrustResult(
                action=final_action['action'],
                confidence=final_action['confidence'],
                threat_score=final_action['threat_score'],
                threat_type=final_action['threat_type'],
                indicators=final_action['indicators'],
                analysis_details={
                    'ai_prediction': ai_prediction,
                    'gateway_result': gateway_result,
                    'policy_result': policy_result,
                    'processing_time': processing_time
                },
                processing_time=processing_time
            )
            
            # Update statistics
            self._update_statistics(result)
            
            logger.info("Email processed through zero-trust pipeline",
                       action=result.action,
                       threat_score=result.threat_score,
                       processing_time=processing_time)
            
            return result
            
        except Exception as e:
            logger.error("Error processing email through zero-trust pipeline", error=str(e))
            return ZeroTrustResult(
                action='block',
                confidence=1.0,
                threat_score=1.0,
                threat_type='error',
                indicators=['processing_error'],
                analysis_details={'error': str(e)},
                processing_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    async def process_link_click(self, click_data: Dict[str, Any]) -> ZeroTrustResult:
        """Process link click through zero-trust pipeline"""
        start_time = datetime.utcnow()
        
        try:
            logger.info("Processing link click through zero-trust pipeline",
                       url=click_data.get('url'))
            
            # Phase 1: AI Link Analysis
            ai_prediction = await self.ai_detection.predict_link_threat(
                click_data.get('url', ''), click_data
            )
            
            # Phase 2: Real-Time Sandbox Analysis
            sandbox_result = await self.sandbox.analyze_link_click(
                click_data.get('url', ''), click_data
            )
            
            # Phase 3: Apply Zero-Trust Policies
            policy_result = await self._apply_link_policies(
                click_data, ai_prediction, sandbox_result
            )
            
            # Phase 4: Determine Final Action
            final_action = await self._determine_link_action(
                ai_prediction, sandbox_result, policy_result
            )
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Create result
            result = ZeroTrustResult(
                action=final_action['action'],
                confidence=final_action['confidence'],
                threat_score=final_action['threat_score'],
                threat_type=final_action['threat_type'],
                indicators=final_action['indicators'],
                analysis_details={
                    'ai_prediction': ai_prediction,
                    'sandbox_result': sandbox_result,
                    'policy_result': policy_result,
                    'processing_time': processing_time
                },
                processing_time=processing_time
            )
            
            # Update statistics
            self._update_statistics(result)
            
            logger.info("Link click processed through zero-trust pipeline",
                       action=result.action,
                       threat_score=result.threat_score,
                       processing_time=processing_time)
            
            return result
            
        except Exception as e:
            logger.error("Error processing link click through zero-trust pipeline", error=str(e))
            return ZeroTrustResult(
                action='block',
                confidence=1.0,
                threat_score=1.0,
                threat_type='error',
                indicators=['processing_error'],
                analysis_details={'error': str(e)},
                processing_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    async def process_attachment(self, attachment_data: Dict[str, Any]) -> ZeroTrustResult:
        """Process attachment through zero-trust pipeline"""
        start_time = datetime.utcnow()
        
        try:
            logger.info("Processing attachment through zero-trust pipeline",
                       filename=attachment_data.get('filename'))
            
            # Phase 1: AI File Analysis
            ai_prediction = await self.ai_detection.predict_file_threat(attachment_data)
            
            # Phase 2: Real-Time Sandbox Analysis
            sandbox_result = await self.sandbox.analyze_attachment(
                attachment_data.get('file_path', ''),
                attachment_data.get('file_type', '')
            )
            
            # Phase 3: Apply Zero-Trust Policies
            policy_result = await self._apply_attachment_policies(
                attachment_data, ai_prediction, sandbox_result
            )
            
            # Phase 4: Determine Final Action
            final_action = await self._determine_attachment_action(
                ai_prediction, sandbox_result, policy_result
            )
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Create result
            result = ZeroTrustResult(
                action=final_action['action'],
                confidence=final_action['confidence'],
                threat_score=final_action['threat_score'],
                threat_type=final_action['threat_type'],
                indicators=final_action['indicators'],
                analysis_details={
                    'ai_prediction': ai_prediction,
                    'sandbox_result': sandbox_result,
                    'policy_result': policy_result,
                    'processing_time': processing_time
                },
                processing_time=processing_time
            )
            
            # Update statistics
            self._update_statistics(result)
            
            logger.info("Attachment processed through zero-trust pipeline",
                       action=result.action,
                       threat_score=result.threat_score,
                       processing_time=processing_time)
            
            return result
            
        except Exception as e:
            logger.error("Error processing attachment through zero-trust pipeline", error=str(e))
            return ZeroTrustResult(
                action='block',
                confidence=1.0,
                threat_score=1.0,
                threat_type='error',
                indicators=['processing_error'],
                analysis_details={'error': str(e)},
                processing_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    async def _apply_zero_trust_policies(self, email_data: Dict[str, Any], 
                                       ai_prediction: Any, 
                                       gateway_result: Dict[str, Any]) -> Dict[str, Any]:
        """Apply zero-trust policies to email processing"""
        try:
            # Default zero-trust policy: never trust, always verify
            policy_result = {
                'action': 'rewrite',  # Default to rewriting for zero-trust
                'confidence': 1.0,
                'reason': 'zero_trust_policy',
                'policies_applied': []
            }
            
            # Policy 1: High threat score - block
            if ai_prediction.threat_score > 0.8:
                policy_result['action'] = 'block'
                policy_result['reason'] = 'high_threat_score'
                policy_result['policies_applied'].append('high_threat_block')
            
            # Policy 2: Malicious AI verdict - block
            elif ai_prediction.threat_type in ['malware', 'phishing'] and ai_prediction.confidence > 0.8:
                policy_result['action'] = 'block'
                policy_result['reason'] = 'ai_malicious_verdict'
                policy_result['policies_applied'].append('ai_malicious_block')
            
            # Policy 3: Suspicious content - quarantine
            elif ai_prediction.threat_score > 0.5:
                policy_result['action'] = 'quarantine'
                policy_result['reason'] = 'suspicious_content'
                policy_result['policies_applied'].append('suspicious_quarantine')
            
            # Policy 4: Contains links - always rewrite
            elif email_data.get('has_links', False):
                policy_result['action'] = 'rewrite'
                policy_result['reason'] = 'contains_links'
                policy_result['policies_applied'].append('link_rewrite')
            
            # Policy 5: Contains attachments - always process
            elif email_data.get('has_attachments', False):
                policy_result['action'] = 'rewrite'
                policy_result['reason'] = 'contains_attachments'
                policy_result['policies_applied'].append('attachment_process')
            
            # Policy 6: External sender - additional verification
            elif not self._is_internal_sender(email_data.get('sender', '')):
                policy_result['action'] = 'rewrite'
                policy_result['reason'] = 'external_sender'
                policy_result['policies_applied'].append('external_sender_verify')
            
            # Policy 7: High-risk user - additional protection
            elif self._is_high_risk_user(email_data.get('recipients', [])):
                policy_result['action'] = 'quarantine'
                policy_result['reason'] = 'high_risk_user'
                policy_result['policies_applied'].append('high_risk_protection')
            
            return policy_result
            
        except Exception as e:
            logger.error("Error applying zero-trust policies", error=str(e))
            return {
                'action': 'block',
                'confidence': 1.0,
                'reason': 'policy_error',
                'policies_applied': ['error_fallback']
            }
    
    async def _apply_link_policies(self, click_data: Dict[str, Any], 
                                 ai_prediction: Any, 
                                 sandbox_result: Any) -> Dict[str, Any]:
        """Apply zero-trust policies to link clicks"""
        try:
            policy_result = {
                'action': 'block',  # Default to blocking for zero-trust
                'confidence': 1.0,
                'reason': 'zero_trust_link_policy',
                'policies_applied': []
            }
            
            # Policy 1: Safe sandbox result - allow
            if sandbox_result.verdict == 'safe' and sandbox_result.confidence > 0.8:
                policy_result['action'] = 'allow'
                policy_result['reason'] = 'safe_sandbox_verdict'
                policy_result['policies_applied'].append('safe_sandbox_allow')
            
            # Policy 2: Suspicious sandbox result - block
            elif sandbox_result.verdict in ['suspicious', 'malicious']:
                policy_result['action'] = 'block'
                policy_result['reason'] = 'suspicious_sandbox_verdict'
                policy_result['policies_applied'].append('suspicious_sandbox_block')
            
            # Policy 3: High AI threat score - block
            elif ai_prediction.threat_score > 0.7:
                policy_result['action'] = 'block'
                policy_result['reason'] = 'high_ai_threat_score'
                policy_result['policies_applied'].append('high_ai_threat_block')
            
            # Policy 4: External domain - additional verification
            elif not self._is_internal_domain(click_data.get('url', '')):
                policy_result['action'] = 'block'
                policy_result['reason'] = 'external_domain'
                policy_result['policies_applied'].append('external_domain_block')
            
            return policy_result
            
        except Exception as e:
            logger.error("Error applying link policies", error=str(e))
            return {
                'action': 'block',
                'confidence': 1.0,
                'reason': 'policy_error',
                'policies_applied': ['error_fallback']
            }
    
    async def _apply_attachment_policies(self, attachment_data: Dict[str, Any], 
                                       ai_prediction: Any, 
                                       sandbox_result: Any) -> Dict[str, Any]:
        """Apply zero-trust policies to attachments"""
        try:
            policy_result = {
                'action': 'block',  # Default to blocking for zero-trust
                'confidence': 1.0,
                'reason': 'zero_trust_attachment_policy',
                'policies_applied': []
            }
            
            # Policy 1: Safe sandbox result - allow
            if sandbox_result.verdict == 'safe' and sandbox_result.confidence > 0.8:
                policy_result['action'] = 'allow'
                policy_result['reason'] = 'safe_sandbox_verdict'
                policy_result['policies_applied'].append('safe_sandbox_allow')
            
            # Policy 2: Malicious sandbox result - block
            elif sandbox_result.verdict == 'malicious':
                policy_result['action'] = 'block'
                policy_result['reason'] = 'malicious_sandbox_verdict'
                policy_result['policies_applied'].append('malicious_sandbox_block')
            
            # Policy 3: Suspicious file type - block
            elif attachment_data.get('file_type', '') in ['.exe', '.bat', '.cmd', '.ps1']:
                policy_result['action'] = 'block'
                policy_result['reason'] = 'suspicious_file_type'
                policy_result['policies_applied'].append('suspicious_file_type_block')
            
            # Policy 4: Large file size - quarantine
            elif attachment_data.get('file_size', 0) > 50 * 1024 * 1024:  # 50MB
                policy_result['action'] = 'quarantine'
                policy_result['reason'] = 'large_file_size'
                policy_result['policies_applied'].append('large_file_quarantine')
            
            return policy_result
            
        except Exception as e:
            logger.error("Error applying attachment policies", error=str(e))
            return {
                'action': 'block',
                'confidence': 1.0,
                'reason': 'policy_error',
                'policies_applied': ['error_fallback']
            }
    
    async def _determine_final_action(self, ai_prediction: Any, 
                                    gateway_result: Dict[str, Any], 
                                    policy_result: Dict[str, Any]) -> Dict[str, Any]:
        """Determine final action based on all analysis results"""
        try:
            # Combine threat scores
            ai_score = ai_prediction.threat_score
            gateway_score = gateway_result.get('threat_score', 0.0)
            policy_score = 0.8 if policy_result['action'] == 'block' else 0.5 if policy_result['action'] == 'quarantine' else 0.2
            
            # Weighted average
            final_threat_score = (ai_score * 0.4 + gateway_score * 0.3 + policy_score * 0.3)
            
            # Determine action based on policy result
            action = policy_result['action']
            
            # Determine threat type
            threat_type = ai_prediction.threat_type
            
            # Calculate confidence
            confidence = (ai_prediction.confidence + policy_result['confidence']) / 2
            
            # Combine indicators
            indicators = list(set(
                ai_prediction.indicators + 
                gateway_result.get('indicators', []) + 
                policy_result.get('policies_applied', [])
            ))
            
            return {
                'action': action,
                'threat_score': final_threat_score,
                'threat_type': threat_type,
                'confidence': confidence,
                'indicators': indicators
            }
            
        except Exception as e:
            logger.error("Error determining final action", error=str(e))
            return {
                'action': 'block',
                'threat_score': 1.0,
                'threat_type': 'error',
                'confidence': 1.0,
                'indicators': ['error']
            }
    
    async def _determine_link_action(self, ai_prediction: Any, 
                                   sandbox_result: Any, 
                                   policy_result: Dict[str, Any]) -> Dict[str, Any]:
        """Determine final action for link clicks"""
        try:
            # Combine threat scores
            ai_score = ai_prediction.threat_score
            sandbox_score = 0.9 if sandbox_result.verdict == 'malicious' else 0.7 if sandbox_result.verdict == 'suspicious' else 0.1
            policy_score = 0.8 if policy_result['action'] == 'block' else 0.2
            
            # Weighted average
            final_threat_score = (ai_score * 0.3 + sandbox_score * 0.5 + policy_score * 0.2)
            
            # Determine action
            action = policy_result['action']
            
            # Determine threat type
            threat_type = ai_prediction.threat_type
            
            # Calculate confidence
            confidence = (ai_prediction.confidence + sandbox_result.confidence + policy_result['confidence']) / 3
            
            # Combine indicators
            indicators = list(set(
                ai_prediction.indicators + 
                sandbox_result.threat_indicators + 
                policy_result.get('policies_applied', [])
            ))
            
            return {
                'action': action,
                'threat_score': final_threat_score,
                'threat_type': threat_type,
                'confidence': confidence,
                'indicators': indicators
            }
            
        except Exception as e:
            logger.error("Error determining link action", error=str(e))
            return {
                'action': 'block',
                'threat_score': 1.0,
                'threat_type': 'error',
                'confidence': 1.0,
                'indicators': ['error']
            }
    
    async def _determine_attachment_action(self, ai_prediction: Any, 
                                         sandbox_result: Any, 
                                         policy_result: Dict[str, Any]) -> Dict[str, Any]:
        """Determine final action for attachments"""
        try:
            # Combine threat scores
            ai_score = ai_prediction.threat_score
            sandbox_score = 0.9 if sandbox_result.verdict == 'malicious' else 0.7 if sandbox_result.verdict == 'suspicious' else 0.1
            policy_score = 0.8 if policy_result['action'] == 'block' else 0.2
            
            # Weighted average
            final_threat_score = (ai_score * 0.3 + sandbox_score * 0.5 + policy_score * 0.2)
            
            # Determine action
            action = policy_result['action']
            
            # Determine threat type
            threat_type = ai_prediction.threat_type
            
            # Calculate confidence
            confidence = (ai_prediction.confidence + sandbox_result.confidence + policy_result['confidence']) / 3
            
            # Combine indicators
            indicators = list(set(
                ai_prediction.indicators + 
                sandbox_result.threat_indicators + 
                policy_result.get('policies_applied', [])
            ))
            
            return {
                'action': action,
                'threat_score': final_threat_score,
                'threat_type': threat_type,
                'confidence': confidence,
                'indicators': indicators
            }
            
        except Exception as e:
            logger.error("Error determining attachment action", error=str(e))
            return {
                'action': 'block',
                'threat_score': 1.0,
                'threat_type': 'error',
                'confidence': 1.0,
                'indicators': ['error']
            }
    
    def _is_internal_sender(self, sender: str) -> bool:
        """Check if sender is from internal domain"""
        try:
            internal_domains = self.policies.get('internal_domains', [])
            domain = sender.split('@')[-1].lower()
            return any(domain.endswith(internal_domain.lower()) for internal_domain in internal_domains)
        except:
            return False
    
    def _is_high_risk_user(self, recipients: List[str]) -> bool:
        """Check if any recipient is a high-risk user"""
        try:
            high_risk_users = self.policies.get('high_risk_users', [])
            return any(recipient in high_risk_users for recipient in recipients)
        except:
            return False
    
    def _is_internal_domain(self, url: str) -> bool:
        """Check if URL is from internal domain"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            internal_domains = self.policies.get('internal_domains', [])
            return any(domain.endswith(internal_domain.lower()) for internal_domain in internal_domains)
        except:
            return False
    
    def _update_statistics(self, result: ZeroTrustResult):
        """Update processing statistics"""
        try:
            self.threat_counts[result.action] += 1
            self.analysis_times.append(result.processing_time)
            
            # Keep only last 1000 analysis times
            if len(self.analysis_times) > 1000:
                self.analysis_times = self.analysis_times[-1000:]
                
        except Exception as e:
            logger.error("Error updating statistics", error=str(e))
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics"""
        try:
            total_processed = sum(self.threat_counts.values())
            avg_processing_time = sum(self.analysis_times) / len(self.analysis_times) if self.analysis_times else 0
            
            return {
                'total_processed': total_processed,
                'threat_counts': self.threat_counts,
                'average_processing_time': avg_processing_time,
                'enforcement_level': self.enforcement_level,
                'policies_active': len(self.policies),
                'components_status': {
                    'email_gateway': 'active',
                    'sandbox': 'active',
                    'ai_detection': 'active'
                }
            }
            
        except Exception as e:
            logger.error("Error getting statistics", error=str(e))
            return {}
    
    async def update_policies(self, new_policies: Dict[str, Any]):
        """Update zero-trust policies"""
        try:
            self.policies.update(new_policies)
            logger.info("Zero-trust policies updated", new_policies=new_policies)
        except Exception as e:
            logger.error("Error updating policies", error=str(e))
    
    async def cleanup(self):
        """Cleanup zero-trust orchestrator resources"""
        try:
            await self.email_gateway.cleanup()
            await self.sandbox.cleanup()
            await self.ai_detection.cleanup()
            logger.info("Zero-Trust Orchestrator cleaned up")
        except Exception as e:
            logger.error("Error cleaning up Zero-Trust Orchestrator", error=str(e))
