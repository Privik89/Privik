from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Email(Base):
    __tablename__ = "emails"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(255), unique=True, index=True)
    subject = Column(String(500))
    sender = Column(String(255))
    recipients = Column(JSON)  # List of recipient emails
    received_at = Column(DateTime, default=datetime.utcnow)
    content_type = Column(String(50))  # text/plain, text/html, multipart
    body_text = Column(Text, nullable=True)
    body_html = Column(Text, nullable=True)
    
    # Analysis results
    threat_score = Column(Float, default=0.0)
    is_suspicious = Column(Boolean, default=False)
    ai_verdict = Column(String(50), nullable=True)  # safe, suspicious, malicious
    static_scan_result = Column(JSON, nullable=True)
    
    # Relationships
    attachments = relationship("EmailAttachment", back_populates="email")
    # click_events = relationship("ClickEvent", back_populates="email")  # Commented out to avoid circular import
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EmailAttachment(Base):
    __tablename__ = "email_attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"))
    filename = Column(String(255))
    content_type = Column(String(100))
    file_size = Column(Integer)
    s3_key = Column(String(500))  # Storage location in S3/MinIO
    
    # Analysis results
    threat_score = Column(Float, default=0.0)
    sandbox_verdict = Column(String(50), nullable=True)  # allow, block, suspicious
    static_scan_result = Column(JSON, nullable=True)
    sandbox_analysis_id = Column(Integer, ForeignKey("sandbox_analyses.id"), nullable=True)
    
    # Relationships
    email = relationship("Email", back_populates="attachments")
    # sandbox_analysis = relationship("SandboxAnalysis", back_populates="attachment")  # Commented out to avoid circular import
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
