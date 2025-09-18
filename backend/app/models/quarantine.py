"""
Email Quarantine Models
Manages quarantined emails and quarantine actions
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class EmailQuarantine(Base):
    __tablename__ = "email_quarantine"
    
    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"), nullable=False, index=True)
    
    # Quarantine details
    quarantine_reason = Column(String(100), nullable=False)  # 'suspicious', 'malicious', 'policy_violation'
    threat_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    
    # Quarantine metadata
    quarantined_at = Column(DateTime, default=datetime.utcnow)
    quarantined_by = Column(String(100), nullable=True)  # 'system', 'admin', 'user'
    quarantine_duration = Column(Integer, default=7)  # days
    
    # Status tracking
    status = Column(String(20), default='quarantined')  # 'quarantined', 'released', 'deleted', 'reviewed'
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Action tracking
    action_taken = Column(String(50), nullable=True)  # 'release', 'delete', 'whitelist_sender', 'blacklist_sender'
    action_reason = Column(Text, nullable=True)
    action_taken_at = Column(DateTime, nullable=True)
    action_taken_by = Column(String(100), nullable=True)
    
    # Additional data
    analysis_details = Column(JSON, nullable=True)  # Detailed analysis results
    user_notified = Column(Boolean, default=False)
    notification_sent_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    email = relationship("Email", back_populates="quarantine")
    
    def __repr__(self):
        return f"<EmailQuarantine(email_id={self.email_id}, reason='{self.quarantine_reason}')>"

class QuarantineAction(Base):
    __tablename__ = "quarantine_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    quarantine_id = Column(Integer, ForeignKey("email_quarantine.id"), nullable=False)
    
    # Action details
    action_type = Column(String(50), nullable=False)  # 'release', 'delete', 'whitelist', 'blacklist'
    action_reason = Column(Text, nullable=True)
    performed_by = Column(String(100), nullable=False)
    
    # Action metadata
    action_data = Column(JSON, nullable=True)  # Additional action-specific data
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    performed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    quarantine = relationship("EmailQuarantine")
    
    def __repr__(self):
        return f"<QuarantineAction(type='{self.action_type}', performed_by='{self.performed_by}')>"

class QuarantineRule(Base):
    __tablename__ = "quarantine_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Rule conditions
    conditions = Column(JSON, nullable=False)  # Rule conditions (threat_score, sender_domain, etc.)
    
    # Rule actions
    action = Column(String(50), nullable=False)  # 'quarantine', 'release', 'delete'
    quarantine_duration = Column(Integer, default=7)  # days
    notify_user = Column(Boolean, default=True)
    
    # Rule status
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=100)  # Higher number = higher priority
    
    # Rule metadata
    created_by = Column(String(100), nullable=True)
    last_triggered = Column(DateTime, nullable=True)
    trigger_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<QuarantineRule(name='{self.name}', action='{self.action}')>"
