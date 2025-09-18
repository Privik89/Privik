"""
Incident Correlation Models
Manages security incident correlation and timeline tracking
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Float, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# Association table for many-to-many relationships
incident_emails = Table(
    'incident_emails',
    Base.metadata,
    Column('incident_id', Integer, ForeignKey('security_incidents.id'), primary_key=True),
    Column('email_id', Integer, ForeignKey('emails.id'), primary_key=True)
)

incident_domains = Table(
    'incident_domains',
    Base.metadata,
    Column('incident_id', Integer, ForeignKey('security_incidents.id'), primary_key=True),
    Column('domain', String(255), primary_key=True)
)

incident_attachments = Table(
    'incident_attachments',
    Base.metadata,
    Column('incident_id', Integer, ForeignKey('security_incidents.id'), primary_key=True),
    Column('attachment_id', Integer, ForeignKey('email_attachments.id'), primary_key=True)
)

class SecurityIncident(Base):
    __tablename__ = "security_incidents"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String(50), unique=True, nullable=False, index=True)  # Human-readable ID
    
    # Incident classification
    severity = Column(String(20), nullable=False, default='medium')  # 'low', 'medium', 'high', 'critical'
    incident_type = Column(String(50), nullable=False)  # 'phishing', 'malware', 'bec', 'data_exfiltration'
    status = Column(String(20), default='open')  # 'open', 'investigating', 'resolved', 'false_positive'
    
    # Incident details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    
    # Threat intelligence
    threat_actors = Column(JSON, nullable=True)  # List of suspected threat actors
    attack_vectors = Column(JSON, nullable=True)  # List of attack vectors used
    indicators = Column(JSON, nullable=True)  # IOCs associated with incident
    
    # Correlation data
    confidence_score = Column(Float, default=0.0)  # How confident we are in the correlation
    correlation_factors = Column(JSON, nullable=True)  # Factors that led to correlation
    
    # Timeline data
    first_seen = Column(DateTime, nullable=False)
    last_seen = Column(DateTime, nullable=False)
    incident_duration = Column(Integer, nullable=True)  # Duration in minutes
    
    # Assignment and tracking
    assigned_to = Column(String(100), nullable=True)
    assigned_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(String(100), nullable=True)
    
    # Additional metadata
    tags = Column(JSON, nullable=True)  # Custom tags for categorization
    notes = Column(Text, nullable=True)  # Investigation notes
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    emails = relationship("Email", secondary=incident_emails, back_populates="incidents")
    timeline_events = relationship("IncidentTimelineEvent", back_populates="incident")
    correlations = relationship("IncidentCorrelation", back_populates="incident")
    
    def __repr__(self):
        return f"<SecurityIncident(incident_id='{self.incident_id}', type='{self.incident_type}')>"

class IncidentTimelineEvent(Base):
    __tablename__ = "incident_timeline_events"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("security_incidents.id"), nullable=False)
    
    # Event details
    event_type = Column(String(50), nullable=False)  # 'email_received', 'attachment_analyzed', 'domain_checked', 'quarantine_action'
    event_title = Column(String(200), nullable=False)
    event_description = Column(Text, nullable=True)
    
    # Event data
    event_data = Column(JSON, nullable=True)  # Structured event data
    event_source = Column(String(100), nullable=False)  # 'email_analysis', 'sandbox', 'domain_reputation', 'user_action'
    
    # Event metadata
    severity = Column(String(20), default='medium')  # Event severity level
    confidence = Column(Float, default=0.0)  # Confidence in event accuracy
    
    # Timestamps
    event_time = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    incident = relationship("SecurityIncident", back_populates="timeline_events")
    
    def __repr__(self):
        return f"<IncidentTimelineEvent(type='{self.event_type}', title='{self.event_title}')>"

class IncidentCorrelation(Base):
    __tablename__ = "incident_correlations"
    
    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(Integer, ForeignKey("security_incidents.id"), nullable=False)
    
    # Correlation details
    correlation_type = Column(String(50), nullable=False)  # 'domain_match', 'sender_match', 'attachment_hash', 'ip_address', 'campaign'
    correlation_value = Column(String(500), nullable=False)  # The actual value being correlated
    correlation_confidence = Column(Float, default=0.0)  # How confident we are in this correlation
    
    # Related entities
    related_incident_id = Column(Integer, ForeignKey("security_incidents.id"), nullable=True)
    related_email_id = Column(Integer, ForeignKey("emails.id"), nullable=True)
    related_domain = Column(String(255), nullable=True)
    related_ip = Column(String(45), nullable=True)  # IPv4 or IPv6
    
    # Correlation metadata
    correlation_strength = Column(Float, default=0.0)  # Strength of correlation (0.0-1.0)
    correlation_factors = Column(JSON, nullable=True)  # Factors contributing to correlation
    
    # Timestamps
    first_correlated = Column(DateTime, default=datetime.utcnow)
    last_correlated = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    incident = relationship("SecurityIncident", back_populates="correlations", foreign_keys=[incident_id])
    related_incident = relationship("SecurityIncident", foreign_keys=[related_incident_id])
    
    def __repr__(self):
        return f"<IncidentCorrelation(type='{self.correlation_type}', value='{self.correlation_value}')>"

class ThreatCampaign(Base):
    __tablename__ = "threat_campaigns"
    
    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Campaign details
    campaign_name = Column(String(200), nullable=False)
    campaign_description = Column(Text, nullable=True)
    campaign_type = Column(String(50), nullable=False)  # 'phishing', 'malware', 'bec', 'mixed'
    
    # Campaign metadata
    threat_actor = Column(String(100), nullable=True)  # Suspected threat actor
    attack_vector = Column(String(100), nullable=True)  # Primary attack vector
    target_industry = Column(String(100), nullable=True)  # Targeted industry
    
    # Campaign statistics
    total_incidents = Column(Integer, default=0)
    total_emails = Column(Integer, default=0)
    total_domains = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)  # Percentage of successful attacks
    
    # Campaign timeline
    campaign_start = Column(DateTime, nullable=False)
    campaign_end = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Campaign indicators
    indicators = Column(JSON, nullable=True)  # Campaign-specific IOCs
    tactics = Column(JSON, nullable=True)  # TTPs used in campaign
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ThreatCampaign(campaign_id='{self.campaign_id}', name='{self.campaign_name}')>"
