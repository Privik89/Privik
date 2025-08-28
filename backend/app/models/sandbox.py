from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class SandboxAnalysis(Base):
    __tablename__ = "sandbox_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    attachment_id = Column(Integer, ForeignKey("email_attachments.id"))
    
    # Analysis metadata
    sandbox_id = Column(String(255), unique=True)  # External sandbox ID
    analysis_started = Column(DateTime, default=datetime.utcnow)
    analysis_completed = Column(DateTime, nullable=True)
    analysis_duration = Column(Float, nullable=True)  # in seconds
    
    # File information
    file_hash = Column(String(64), nullable=True)  # SHA256
    file_type = Column(String(100), nullable=True)
    file_size = Column(Integer, nullable=True)
    
    # Analysis results
    threat_score = Column(Float, default=0.0)
    verdict = Column(String(50), nullable=True)  # allow, block, suspicious
    confidence = Column(Float, default=0.0)
    
    # Behavioral analysis
    process_created = Column(JSON, nullable=True)  # List of processes
    files_created = Column(JSON, nullable=True)  # List of files
    registry_changes = Column(JSON, nullable=True)  # Registry modifications
    network_connections = Column(JSON, nullable=True)  # Network activity
    api_calls = Column(JSON, nullable=True)  # API calls made
    
    # AI analysis
    ai_verdict = Column(String(50), nullable=True)
    ai_confidence = Column(Float, default=0.0)
    ai_details = Column(JSON, nullable=True)
    
    # Relationships
    # attachment = relationship("EmailAttachment", back_populates="sandbox_analysis")  # Commented out to avoid circular import
    verdicts = relationship("SandboxVerdict", back_populates="analysis")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SandboxVerdict(Base):
    __tablename__ = "sandbox_verdicts"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("sandbox_analyses.id"))
    
    # Verdict details
    verdict_type = Column(String(50))  # static, behavioral, ai, final
    verdict = Column(String(50))  # allow, block, suspicious
    confidence = Column(Float, default=0.0)
    details = Column(JSON, nullable=True)
    
    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    analysis = relationship("SandboxAnalysis", back_populates="verdicts")
