"""
Threat Feed Models
Manages threat intelligence feeds and their data
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ThreatFeed(Base):
    __tablename__ = "threat_feeds"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    source_type = Column(String(50), nullable=False)  # 'webhook', 'api', 'file'
    feed_url = Column(String(500), nullable=True)
    webhook_url = Column(String(500), nullable=True)
    api_key = Column(String(200), nullable=True)
    
    # Feed configuration
    update_interval = Column(Integer, default=3600)  # seconds
    last_updated = Column(DateTime, nullable=True)
    next_update = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Feed metadata
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # 'malware', 'phishing', 'botnet', 'custom'
    confidence_threshold = Column(Float, default=0.7)
    
    # Status tracking
    status = Column(String(20), default='active')  # 'active', 'paused', 'error'
    error_count = Column(Integer, default=0)
    last_error = Column(Text, nullable=True)
    total_records = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ThreatFeedRecord(Base):
    __tablename__ = "threat_feed_records"
    
    id = Column(Integer, primary_key=True, index=True)
    feed_id = Column(Integer, nullable=False, index=True)
    
    # Threat data
    indicator = Column(String(255), nullable=False, index=True)  # domain, IP, URL
    indicator_type = Column(String(20), nullable=False)  # 'domain', 'ip', 'url', 'hash'
    threat_type = Column(String(50), nullable=True)  # 'malware', 'phishing', 'botnet'
    
    # Metadata
    confidence = Column(Float, default=0.5)
    severity = Column(String(20), default='medium')  # 'low', 'medium', 'high', 'critical'
    description = Column(Text, nullable=True)
    source_reference = Column(String(255), nullable=True)
    
    # Additional data
    tags = Column(JSON, nullable=True)  # List of tags
    raw_data = Column(JSON, nullable=True)  # Original feed data
    
    # Timestamps
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<ThreatFeedRecord(indicator='{self.indicator}', type='{self.indicator_type}')>"

class ThreatFeedSubscription(Base):
    __tablename__ = "threat_feed_subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    feed_id = Column(Integer, nullable=False, index=True)
    user_email = Column(String(255), nullable=False)
    
    # Subscription preferences
    notify_on_updates = Column(Boolean, default=True)
    notify_on_errors = Column(Boolean, default=True)
    notification_frequency = Column(String(20), default='daily')  # 'immediate', 'hourly', 'daily'
    
    # Timestamps
    subscribed_at = Column(DateTime, default=datetime.utcnow)
    last_notification = Column(DateTime, nullable=True)
