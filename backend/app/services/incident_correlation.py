"""
Incident Correlation Service
Manages security incident correlation and timeline analysis
"""

import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import structlog
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models.incident_correlation import SecurityIncident, IncidentTimelineEvent, IncidentCorrelation, ThreatCampaign
from ..models.email import Email
from ..models.sandbox import SandboxAnalysis
from ..models.quarantine import EmailQuarantine
import uuid

logger = structlog.get_logger()

class IncidentCorrelationService:
    """Manages security incident correlation and analysis"""
    
    def __init__(self):
        self.db = SessionLocal()
        
    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()
    
    async def correlate_new_email(self, email: Email, analysis_result: Dict[str, Any]) -> Optional[SecurityIncident]:
        """Correlate a new email with existing incidents or create new incident"""
        try:
            # Extract correlation indicators
            indicators = self._extract_correlation_indicators(email, analysis_result)
            
            # Find existing incidents that match
            matching_incidents = await self._find_matching_incidents(indicators)
            
            if matching_incidents:
                # Correlate with existing incident
                incident = matching_incidents[0]  # Use highest confidence match
                await self._add_email_to_incident(incident, email, indicators)
                logger.info("Email correlated with existing incident", 
                           email_id=email.id, 
                           incident_id=incident.incident_id)
                return incident
            else:
                # Create new incident
                incident = await self._create_new_incident(email, analysis_result, indicators)
                logger.info("New incident created", 
                           email_id=email.id, 
                           incident_id=incident.incident_id)
                return incident
                
        except Exception as e:
            logger.error("Error correlating email", email_id=email.id, error=str(e))
            return None
    
    def _extract_correlation_indicators(self, email: Email, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """Extract correlation indicators from email and analysis"""
        indicators = {
            'sender': email.sender,
            'sender_domain': email.sender.split('@')[1] if '@' in email.sender else None,
            'recipients': email.recipients,
            'subject_keywords': self._extract_keywords(email.subject),
            'content_keywords': self._extract_keywords(email.content),
            'threat_score': analysis_result.get('threat_score', 0.0),
            'threat_type': analysis_result.get('ai_verdict', 'safe'),
            'domain_reputation': analysis_result.get('static_scan_result', {}).get('domain_reputation', {}),
            'attachments': []
        }
        
        # Extract attachment indicators
        if hasattr(email, 'attachments'):
            for attachment in email.attachments:
                if attachment:
                    indicators['attachments'].append({
                        'filename': attachment.filename,
                        'content_type': attachment.content_type,
                        'file_size': attachment.file_size
                    })
        
        return indicators
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text for correlation"""
        if not text:
            return []
        
        # Simple keyword extraction (can be enhanced with NLP)
        keywords = []
        text_lower = text.lower()
        
        # Common phishing keywords
        phishing_keywords = [
            'urgent', 'verify', 'account', 'suspended', 'security', 'login',
            'password', 'update', 'confirm', 'expired', 'unauthorized'
        ]
        
        for keyword in phishing_keywords:
            if keyword in text_lower:
                keywords.append(keyword)
        
        return keywords
    
    async def _find_matching_incidents(self, indicators: Dict[str, Any]) -> List[SecurityIncident]:
        """Find existing incidents that match the indicators"""
        try:
            matching_incidents = []
            
            # Search by sender domain
            if indicators.get('sender_domain'):
                domain_incidents = self.db.query(SecurityIncident).join(IncidentCorrelation).filter(
                    IncidentCorrelation.correlation_type == 'domain_match',
                    IncidentCorrelation.correlation_value == indicators['sender_domain'],
                    SecurityIncident.status.in_(['open', 'investigating'])
                ).all()
                matching_incidents.extend(domain_incidents)
            
            # Search by subject keywords
            if indicators.get('subject_keywords'):
                for keyword in indicators['subject_keywords']:
                    keyword_incidents = self.db.query(SecurityIncident).join(IncidentCorrelation).filter(
                        IncidentCorrelation.correlation_type == 'keyword_match',
                        IncidentCorrelation.correlation_value.like(f'%{keyword}%'),
                        SecurityIncident.status.in_(['open', 'investigating'])
                    ).all()
                    matching_incidents.extend(keyword_incidents)
            
            # Remove duplicates and calculate confidence scores
            unique_incidents = {}
            for incident in matching_incidents:
                if incident.id not in unique_incidents:
                    confidence = self._calculate_correlation_confidence(incident, indicators)
                    unique_incidents[incident.id] = (incident, confidence)
            
            # Sort by confidence and return top matches
            sorted_incidents = sorted(unique_incidents.values(), key=lambda x: x[1], reverse=True)
            return [incident for incident, confidence in sorted_incidents if confidence > 0.3]
            
        except Exception as e:
            logger.error("Error finding matching incidents", error=str(e))
            return []
    
    def _calculate_correlation_confidence(self, incident: SecurityIncident, indicators: Dict[str, Any]) -> float:
        """Calculate confidence score for incident correlation"""
        confidence = 0.0
        
        # Domain match (high weight)
        if indicators.get('sender_domain'):
            domain_correlations = [c for c in incident.correlations 
                                 if c.correlation_type == 'domain_match' 
                                 and c.correlation_value == indicators['sender_domain']]
            if domain_correlations:
                confidence += 0.4
        
        # Keyword matches (medium weight)
        if indicators.get('subject_keywords'):
            for keyword in indicators['subject_keywords']:
                keyword_correlations = [c for c in incident.correlations 
                                      if c.correlation_type == 'keyword_match' 
                                      and keyword in c.correlation_value]
                if keyword_correlations:
                    confidence += 0.2
        
        # Threat type match (medium weight)
        if indicators.get('threat_type') == incident.incident_type:
            confidence += 0.3
        
        # Time proximity (low weight)
        time_diff = datetime.utcnow() - incident.last_seen
        if time_diff.total_seconds() < 86400:  # Within 24 hours
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    async def _add_email_to_incident(self, incident: SecurityIncident, email: Email, indicators: Dict[str, Any]):
        """Add email to existing incident and update correlations"""
        try:
            # Add email to incident
            incident.emails.append(email)
            
            # Update incident metadata
            incident.last_seen = datetime.utcnow()
            incident.total_emails = len(incident.emails)
            
            # Add new correlations
            await self._add_correlations(incident, indicators, email)
            
            # Add timeline event
            await self._add_timeline_event(
                incident=incident,
                event_type='email_received',
                event_title=f'New Email Added: {email.subject}',
                event_description=f'Email from {email.sender} added to incident',
                event_data={'email_id': email.id, 'indicators': indicators}
            )
            
            self.db.commit()
            
        except Exception as e:
            logger.error("Error adding email to incident", incident_id=incident.id, error=str(e))
            self.db.rollback()
    
    async def _create_new_incident(self, email: Email, analysis_result: Dict[str, Any], indicators: Dict[str, Any]) -> SecurityIncident:
        """Create a new security incident"""
        try:
            # Generate incident ID
            incident_id = f"INC-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            
            # Determine incident type and severity
            incident_type = self._determine_incident_type(analysis_result)
            severity = self._determine_severity(analysis_result)
            
            # Create incident
            incident = SecurityIncident(
                incident_id=incident_id,
                incident_type=incident_type,
                severity=severity,
                title=f"{incident_type.title()} Incident - {email.subject[:50]}",
                description=f"Security incident involving email from {email.sender}",
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow(),
                confidence_score=analysis_result.get('threat_score', 0.0),
                status='open'
            )
            
            self.db.add(incident)
            self.db.flush()  # Get incident ID
            
            # Add email to incident
            incident.emails.append(email)
            
            # Add correlations
            await self._add_correlations(incident, indicators, email)
            
            # Add initial timeline event
            await self._add_timeline_event(
                incident=incident,
                event_type='incident_created',
                event_title='Incident Created',
                event_description=f'New {incident_type} incident created',
                event_data={'email_id': email.id, 'indicators': indicators}
            )
            
            self.db.commit()
            return incident
            
        except Exception as e:
            logger.error("Error creating new incident", error=str(e))
            self.db.rollback()
            raise
    
    def _determine_incident_type(self, analysis_result: Dict[str, Any]) -> str:
        """Determine incident type from analysis result"""
        threat_score = analysis_result.get('threat_score', 0.0)
        ai_verdict = analysis_result.get('ai_verdict', 'safe')
        
        if threat_score > 0.8:
            return 'malware'
        elif threat_score > 0.6:
            return 'phishing'
        elif ai_verdict == 'bec_attack':
            return 'bec'
        else:
            return 'suspicious'
    
    def _determine_severity(self, analysis_result: Dict[str, Any]) -> str:
        """Determine incident severity from analysis result"""
        threat_score = analysis_result.get('threat_score', 0.0)
        
        if threat_score > 0.9:
            return 'critical'
        elif threat_score > 0.7:
            return 'high'
        elif threat_score > 0.5:
            return 'medium'
        else:
            return 'low'
    
    async def _add_correlations(self, incident: SecurityIncident, indicators: Dict[str, Any], email: Email):
        """Add correlation records for incident"""
        try:
            correlations = []
            
            # Domain correlation
            if indicators.get('sender_domain'):
                correlation = IncidentCorrelation(
                    incident_id=incident.id,
                    correlation_type='domain_match',
                    correlation_value=indicators['sender_domain'],
                    correlation_confidence=0.9,
                    related_email_id=email.id
                )
                correlations.append(correlation)
            
            # Keyword correlations
            for keyword in indicators.get('subject_keywords', []):
                correlation = IncidentCorrelation(
                    incident_id=incident.id,
                    correlation_type='keyword_match',
                    correlation_value=keyword,
                    correlation_confidence=0.6,
                    related_email_id=email.id
                )
                correlations.append(correlation)
            
            # Sender correlation
            if indicators.get('sender'):
                correlation = IncidentCorrelation(
                    incident_id=incident.id,
                    correlation_type='sender_match',
                    correlation_value=indicators['sender'],
                    correlation_confidence=0.8,
                    related_email_id=email.id
                )
                correlations.append(correlation)
            
            # Add correlations to database
            for correlation in correlations:
                self.db.add(correlation)
                
        except Exception as e:
            logger.error("Error adding correlations", incident_id=incident.id, error=str(e))
    
    async def _add_timeline_event(
        self,
        incident: SecurityIncident,
        event_type: str,
        event_title: str,
        event_description: str,
        event_data: Dict[str, Any] = None
    ):
        """Add timeline event to incident"""
        try:
            event = IncidentTimelineEvent(
                incident_id=incident.id,
                event_type=event_type,
                event_title=event_title,
                event_description=event_description,
                event_data=event_data or {},
                event_source='system',
                event_time=datetime.utcnow()
            )
            
            self.db.add(event)
            
        except Exception as e:
            logger.error("Error adding timeline event", incident_id=incident.id, error=str(e))
    
    async def get_incident_timeline(self, incident_id: str) -> Dict[str, Any]:
        """Get timeline for a specific incident"""
        try:
            incident = self.db.query(SecurityIncident).filter(
                SecurityIncident.incident_id == incident_id
            ).first()
            
            if not incident:
                return {"error": "Incident not found"}
            
            # Get timeline events
            events = self.db.query(IncidentTimelineEvent).filter(
                IncidentTimelineEvent.incident_id == incident.id
            ).order_by(IncidentTimelineEvent.event_time.desc()).all()
            
            # Get related incidents
            related_incidents = self.db.query(IncidentCorrelation).filter(
                IncidentCorrelation.incident_id == incident.id,
                IncidentCorrelation.related_incident_id.isnot(None)
            ).all()
            
            return {
                "incident": {
                    "id": incident.incident_id,
                    "type": incident.incident_type,
                    "severity": incident.severity,
                    "status": incident.status,
                    "title": incident.title,
                    "description": incident.description,
                    "first_seen": incident.first_seen.isoformat(),
                    "last_seen": incident.last_seen.isoformat(),
                    "confidence_score": incident.confidence_score
                },
                "timeline_events": [
                    {
                        "id": event.id,
                        "type": event.event_type,
                        "title": event.event_title,
                        "description": event.event_description,
                        "event_time": event.event_time.isoformat(),
                        "event_source": event.event_source,
                        "event_data": event.event_data
                    }
                    for event in events
                ],
                "related_incidents": [
                    {
                        "incident_id": corr.related_incident.incident_id,
                        "correlation_type": corr.correlation_type,
                        "correlation_value": corr.correlation_value,
                        "confidence": corr.correlation_confidence
                    }
                    for corr in related_incidents
                ]
            }
            
        except Exception as e:
            logger.error("Error getting incident timeline", incident_id=incident_id, error=str(e))
            return {"error": str(e)}
    
    async def get_incident_statistics(self) -> Dict[str, Any]:
        """Get overall incident statistics"""
        try:
            total_incidents = self.db.query(SecurityIncident).count()
            open_incidents = self.db.query(SecurityIncident).filter(
                SecurityIncident.status == 'open'
            ).count()
            
            # Statistics by type
            type_stats = {}
            for incident_type in ['phishing', 'malware', 'bec', 'suspicious']:
                count = self.db.query(SecurityIncident).filter(
                    SecurityIncident.incident_type == incident_type
                ).count()
                type_stats[incident_type] = count
            
            # Statistics by severity
            severity_stats = {}
            for severity in ['low', 'medium', 'high', 'critical']:
                count = self.db.query(SecurityIncident).filter(
                    SecurityIncident.severity == severity
                ).count()
                severity_stats[severity] = count
            
            # Recent incidents (last 24 hours)
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_incidents = self.db.query(SecurityIncident).filter(
                SecurityIncident.created_at >= recent_cutoff
            ).count()
            
            return {
                "total_incidents": total_incidents,
                "open_incidents": open_incidents,
                "recent_incidents": recent_incidents,
                "type_statistics": type_stats,
                "severity_statistics": severity_stats
            }
            
        except Exception as e:
            logger.error("Error getting incident statistics", error=str(e))
            return {"error": str(e)}
