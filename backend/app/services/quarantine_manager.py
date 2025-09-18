"""
Quarantine Manager Service
Manages email quarantine operations and automated quarantine rules
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import structlog
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models.quarantine import EmailQuarantine, QuarantineAction, QuarantineRule
from ..models.email import Email
from .bulk_domain_manager import BulkDomainManager

logger = structlog.get_logger()

class QuarantineManager:
    """Manages email quarantine operations"""
    
    def __init__(self):
        self.db = SessionLocal()
        
    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()
    
    async def quarantine_email(
        self,
        email_id: int,
        reason: str,
        threat_score: float,
        confidence: float,
        quarantined_by: str = "system",
        quarantine_duration: int = 7,
        analysis_details: Optional[Dict] = None
    ) -> EmailQuarantine:
        """Quarantine an email"""
        try:
            # Check if email is already quarantined
            existing = self.db.query(EmailQuarantine).filter(
                EmailQuarantine.email_id == email_id,
                EmailQuarantine.status == 'quarantined'
            ).first()
            
            if existing:
                logger.warning("Email already quarantined", email_id=email_id)
                return existing
            
            # Create quarantine record
            quarantine = EmailQuarantine(
                email_id=email_id,
                quarantine_reason=reason,
                threat_score=threat_score,
                confidence=confidence,
                quarantined_by=quarantined_by,
                quarantine_duration=quarantine_duration,
                analysis_details=analysis_details
            )
            
            self.db.add(quarantine)
            self.db.commit()
            self.db.refresh(quarantine)
            
            logger.info("Email quarantined", 
                       email_id=email_id, 
                       reason=reason,
                       threat_score=threat_score)
            
            return quarantine
            
        except Exception as e:
            logger.error("Error quarantining email", email_id=email_id, error=str(e))
            self.db.rollback()
            raise
    
    async def release_email(
        self,
        quarantine_id: int,
        released_by: str,
        release_reason: Optional[str] = None
    ) -> bool:
        """Release an email from quarantine"""
        try:
            quarantine = self.db.query(EmailQuarantine).filter(
                EmailQuarantine.id == quarantine_id
            ).first()
            
            if not quarantine:
                raise ValueError("Quarantine record not found")
            
            # Update quarantine status
            quarantine.status = 'released'
            quarantine.reviewed_at = datetime.utcnow()
            quarantine.reviewed_by = released_by
            quarantine.action_taken = 'release'
            quarantine.action_reason = release_reason
            quarantine.action_taken_at = datetime.utcnow()
            quarantine.action_taken_by = released_by
            
            # Create action record
            action = QuarantineAction(
                quarantine_id=quarantine_id,
                action_type='release',
                action_reason=release_reason,
                performed_by=released_by,
                action_data={'email_id': quarantine.email_id}
            )
            
            self.db.add(action)
            self.db.commit()
            
            logger.info("Email released from quarantine", 
                       quarantine_id=quarantine_id,
                       released_by=released_by)
            
            return True
            
        except Exception as e:
            logger.error("Error releasing email", quarantine_id=quarantine_id, error=str(e))
            self.db.rollback()
            raise
    
    async def delete_quarantined_email(
        self,
        quarantine_id: int,
        deleted_by: str,
        delete_reason: Optional[str] = None
    ) -> bool:
        """Delete a quarantined email"""
        try:
            quarantine = self.db.query(EmailQuarantine).filter(
                EmailQuarantine.id == quarantine_id
            ).first()
            
            if not quarantine:
                raise ValueError("Quarantine record not found")
            
            # Update quarantine status
            quarantine.status = 'deleted'
            quarantine.reviewed_at = datetime.utcnow()
            quarantine.reviewed_by = deleted_by
            quarantine.action_taken = 'delete'
            quarantine.action_reason = delete_reason
            quarantine.action_taken_at = datetime.utcnow()
            quarantine.action_taken_by = deleted_by
            
            # Create action record
            action = QuarantineAction(
                quarantine_id=quarantine_id,
                action_type='delete',
                action_reason=delete_reason,
                performed_by=deleted_by,
                action_data={'email_id': quarantine.email_id}
            )
            
            self.db.add(action)
            self.db.commit()
            
            logger.info("Quarantined email deleted", 
                       quarantine_id=quarantine_id,
                       deleted_by=deleted_by)
            
            return True
            
        except Exception as e:
            logger.error("Error deleting quarantined email", quarantine_id=quarantine_id, error=str(e))
            self.db.rollback()
            raise
    
    async def whitelist_sender(
        self,
        quarantine_id: int,
        whitelisted_by: str,
        whitelist_reason: Optional[str] = None
    ) -> bool:
        """Whitelist sender and release email"""
        try:
            quarantine = self.db.query(EmailQuarantine).filter(
                EmailQuarantine.id == quarantine_id
            ).first()
            
            if not quarantine:
                raise ValueError("Quarantine record not found")
            
            # Get email to extract sender
            email = self.db.query(Email).filter(Email.id == quarantine.email_id).first()
            if not email:
                raise ValueError("Email not found")
            
            # Extract sender domain
            sender_domain = email.sender.split('@')[1] if '@' in email.sender else None
            
            if sender_domain:
                # Add to whitelist using bulk domain manager
                bulk_manager = BulkDomainManager()
                await bulk_manager.import_domains_from_json(
                    json_content=f'[{{"domain": "{sender_domain}", "reason": "{whitelist_reason or "Whitelisted from quarantine"}"}}]',
                    list_type='whitelist',
                    created_by=f"quarantine_{quarantine_id}"
                )
            
            # Update quarantine status
            quarantine.status = 'released'
            quarantine.reviewed_at = datetime.utcnow()
            quarantine.reviewed_by = whitelisted_by
            quarantine.action_taken = 'whitelist_sender'
            quarantine.action_reason = whitelist_reason
            quarantine.action_taken_at = datetime.utcnow()
            quarantine.action_taken_by = whitelisted_by
            
            # Create action record
            action = QuarantineAction(
                quarantine_id=quarantine_id,
                action_type='whitelist',
                action_reason=whitelist_reason,
                performed_by=whitelisted_by,
                action_data={'email_id': quarantine.email_id, 'sender_domain': sender_domain}
            )
            
            self.db.add(action)
            self.db.commit()
            
            logger.info("Sender whitelisted and email released", 
                       quarantine_id=quarantine_id,
                       sender_domain=sender_domain,
                       whitelisted_by=whitelisted_by)
            
            return True
            
        except Exception as e:
            logger.error("Error whitelisting sender", quarantine_id=quarantine_id, error=str(e))
            self.db.rollback()
            raise
    
    async def blacklist_sender(
        self,
        quarantine_id: int,
        blacklisted_by: str,
        blacklist_reason: Optional[str] = None
    ) -> bool:
        """Blacklist sender and delete email"""
        try:
            quarantine = self.db.query(EmailQuarantine).filter(
                EmailQuarantine.id == quarantine_id
            ).first()
            
            if not quarantine:
                raise ValueError("Quarantine record not found")
            
            # Get email to extract sender
            email = self.db.query(Email).filter(Email.id == quarantine.email_id).first()
            if not email:
                raise ValueError("Email not found")
            
            # Extract sender domain
            sender_domain = email.sender.split('@')[1] if '@' in email.sender else None
            
            if sender_domain:
                # Add to blacklist using bulk domain manager
                bulk_manager = BulkDomainManager()
                await bulk_manager.import_domains_from_json(
                    json_content=f'[{{"domain": "{sender_domain}", "reason": "{blacklist_reason or "Blacklisted from quarantine"}"}}]',
                    list_type='blacklist',
                    created_by=f"quarantine_{quarantine_id}"
                )
            
            # Update quarantine status
            quarantine.status = 'deleted'
            quarantine.reviewed_at = datetime.utcnow()
            quarantine.reviewed_by = blacklisted_by
            quarantine.action_taken = 'blacklist_sender'
            quarantine.action_reason = blacklist_reason
            quarantine.action_taken_at = datetime.utcnow()
            quarantine.action_taken_by = blacklisted_by
            
            # Create action record
            action = QuarantineAction(
                quarantine_id=quarantine_id,
                action_type='blacklist',
                action_reason=blacklist_reason,
                performed_by=blacklisted_by,
                action_data={'email_id': quarantine.email_id, 'sender_domain': sender_domain}
            )
            
            self.db.add(action)
            self.db.commit()
            
            logger.info("Sender blacklisted and email deleted", 
                       quarantine_id=quarantine_id,
                       sender_domain=sender_domain,
                       blacklisted_by=blacklisted_by)
            
            return True
            
        except Exception as e:
            logger.error("Error blacklisting sender", quarantine_id=quarantine_id, error=str(e))
            self.db.rollback()
            raise
    
    async def bulk_quarantine_action(
        self,
        quarantine_ids: List[int],
        action: str,
        performed_by: str,
        action_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """Perform bulk action on quarantined emails"""
        result = {
            "total_processed": len(quarantine_ids),
            "successful_actions": 0,
            "failed_actions": 0,
            "errors": []
        }
        
        try:
            for quarantine_id in quarantine_ids:
                try:
                    if action == 'release':
                        await self.release_email(quarantine_id, performed_by, action_reason)
                    elif action == 'delete':
                        await self.delete_quarantined_email(quarantine_id, performed_by, action_reason)
                    elif action == 'whitelist':
                        await self.whitelist_sender(quarantine_id, performed_by, action_reason)
                    elif action == 'blacklist':
                        await self.blacklist_sender(quarantine_id, performed_by, action_reason)
                    else:
                        raise ValueError(f"Unknown action: {action}")
                    
                    result["successful_actions"] += 1
                    
                except Exception as e:
                    result["failed_actions"] += 1
                    result["errors"].append(f"Quarantine {quarantine_id}: {str(e)}")
            
            logger.info("Bulk quarantine action completed", 
                       action=action,
                       successful=result["successful_actions"],
                       failed=result["failed_actions"])
            
        except Exception as e:
            logger.error("Error in bulk quarantine action", error=str(e))
            result["errors"].append(f"Bulk action failed: {str(e)}")
        
        return result
    
    async def get_quarantine_statistics(self) -> Dict[str, Any]:
        """Get quarantine statistics"""
        try:
            total_quarantined = self.db.query(EmailQuarantine).count()
            active_quarantined = self.db.query(EmailQuarantine).filter(
                EmailQuarantine.status == 'quarantined'
            ).count()
            
            # Get statistics by reason
            reason_stats = {}
            for reason in ['suspicious', 'malicious', 'policy_violation']:
                count = self.db.query(EmailQuarantine).filter(
                    EmailQuarantine.quarantine_reason == reason
                ).count()
                reason_stats[reason] = count
            
            # Get statistics by status
            status_stats = {}
            for status in ['quarantined', 'released', 'deleted']:
                count = self.db.query(EmailQuarantine).filter(
                    EmailQuarantine.status == status
                ).count()
                status_stats[status] = count
            
            # Get recent activity (last 24 hours)
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_quarantined = self.db.query(EmailQuarantine).filter(
                EmailQuarantine.created_at >= recent_cutoff
            ).count()
            
            return {
                "total_quarantined": total_quarantined,
                "active_quarantined": active_quarantined,
                "recent_quarantined": recent_quarantined,
                "reason_statistics": reason_stats,
                "status_statistics": status_stats
            }
            
        except Exception as e:
            logger.error("Error getting quarantine statistics", error=str(e))
            return {"error": str(e)}
    
    async def auto_quarantine_email(
        self,
        email_id: int,
        email_data: Dict[str, Any]
    ) -> Optional[EmailQuarantine]:
        """Automatically quarantine email based on rules"""
        try:
            # Get active quarantine rules
            rules = self.db.query(QuarantineRule).filter(
                QuarantineRule.is_active == True
            ).order_by(QuarantineRule.priority.desc()).all()
            
            for rule in rules:
                if self._evaluate_quarantine_rule(rule, email_data):
                    # Rule matched, quarantine the email
                    quarantine = await self.quarantine_email(
                        email_id=email_id,
                        reason=rule.name,
                        threat_score=email_data.get('threat_score', 0.0),
                        confidence=email_data.get('confidence', 0.0),
                        quarantined_by='auto_rule',
                        quarantine_duration=rule.quarantine_duration,
                        analysis_details=email_data
                    )
                    
                    # Update rule statistics
                    rule.last_triggered = datetime.utcnow()
                    rule.trigger_count += 1
                    self.db.commit()
                    
                    logger.info("Email auto-quarantined by rule", 
                               email_id=email_id,
                               rule_name=rule.name)
                    
                    return quarantine
            
            return None
            
        except Exception as e:
            logger.error("Error in auto-quarantine", email_id=email_id, error=str(e))
            return None
    
    def _evaluate_quarantine_rule(self, rule: QuarantineRule, email_data: Dict[str, Any]) -> bool:
        """Evaluate if email matches quarantine rule conditions"""
        try:
            conditions = rule.conditions
            
            # Check threat score condition
            if 'min_threat_score' in conditions:
                if email_data.get('threat_score', 0) < conditions['min_threat_score']:
                    return False
            
            # Check sender domain condition
            if 'sender_domains' in conditions:
                sender = email_data.get('sender', '')
                sender_domain = sender.split('@')[1] if '@' in sender else ''
                if sender_domain not in conditions['sender_domains']:
                    return False
            
            # Check subject keywords
            if 'subject_keywords' in conditions:
                subject = email_data.get('subject', '').lower()
                keywords = [kw.lower() for kw in conditions['subject_keywords']]
                if not any(keyword in subject for keyword in keywords):
                    return False
            
            # Check content keywords
            if 'content_keywords' in conditions:
                content = email_data.get('content', '').lower()
                keywords = [kw.lower() for kw in conditions['content_keywords']]
                if not any(keyword in content for keyword in keywords):
                    return False
            
            return True
            
        except Exception as e:
            logger.error("Error evaluating quarantine rule", rule_name=rule.name, error=str(e))
            return False
