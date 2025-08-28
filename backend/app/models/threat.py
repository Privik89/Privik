from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ThreatIntel(Base):
    __tablename__ = "threat_intel"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Indicator details
    indicator_type = Column(String(50))  # url, domain, ip, hash, email
    indicator_value = Column(String(500), index=True)
    confidence = Column(Float, default=0.0)
    
    # Threat information
    threat_type = Column(String(100), nullable=True)  # phishing, malware, c2, etc.
    threat_family = Column(String(100), nullable=True)
    severity = Column(String(50), default="medium")  # low, medium, high, critical
    
    # Source information
    source = Column(String(100))  # virustotal, alienvault, custom, etc.
    source_url = Column(String(500), nullable=True)
    first_seen = Column(DateTime, nullable=True)
    last_seen = Column(DateTime, nullable=True)
    
    # Metadata
    tags = Column(JSON, nullable=True)
    description = Column(Text, nullable=True)
    
    # Relationships
    indicators = relationship("ThreatIndicator", back_populates="threat_intel")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ThreatIndicator(Base):
    __tablename__ = "threat_indicators"
    
    id = Column(Integer, primary_key=True, index=True)
    threat_intel_id = Column(Integer, ForeignKey("threat_intel.id"))
    
    # Indicator details
    indicator_type = Column(String(50))  # url, domain, ip, hash, email
    indicator_value = Column(String(500), index=True)
    
    # Detection context
    detected_in = Column(String(50))  # email, click, sandbox, etc.
    detection_time = Column(DateTime, default=datetime.utcnow)
    
    # Analysis results
    is_matched = Column(Boolean, default=False)
    match_confidence = Column(Float, default=0.0)
    match_details = Column(JSON, nullable=True)
    
    # Relationships
    threat_intel = relationship("ThreatIntel", back_populates="indicators")
    
    created_at = Column(DateTime, default=datetime.utcnow)
