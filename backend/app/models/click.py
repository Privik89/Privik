from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class ClickEvent(Base):
    __tablename__ = "click_events"
    
    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("emails.id"))
    user_id = Column(String(255), index=True)
    original_url = Column(Text)
    proxy_url = Column(String(500))  # Our secure proxy URL
    clicked_at = Column(DateTime, default=datetime.utcnow)
    
    # Analysis results
    threat_score = Column(Float, default=0.0)
    is_suspicious = Column(Boolean, default=False)
    ai_verdict = Column(String(50), nullable=True)  # safe, suspicious, malicious
    screenshot_path = Column(String(500), nullable=True)  # Path to screenshot
    
    # Relationships
    # email = relationship("Email", back_populates="click_events")  # Commented out to avoid circular import
    link_analysis = relationship("LinkAnalysis", back_populates="click_event", uselist=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LinkAnalysis(Base):
    __tablename__ = "link_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    click_event_id = Column(Integer, ForeignKey("click_events.id"))
    
    # Page analysis
    page_title = Column(String(500), nullable=True)
    page_content = Column(Text, nullable=True)
    page_screenshot = Column(String(500), nullable=True)
    
    # Security analysis
    is_login_page = Column(Boolean, default=False)
    is_phishing_page = Column(Boolean, default=False)
    has_suspicious_forms = Column(Boolean, default=False)
    redirect_chain = Column(JSON, nullable=True)  # List of redirects
    
    # AI analysis results
    ai_intent = Column(String(100), nullable=True)  # login_harvesting, c2_communication, etc.
    ai_confidence = Column(Float, default=0.0)
    ai_details = Column(JSON, nullable=True)
    
    # Technical analysis
    http_status = Column(Integer, nullable=True)
    response_headers = Column(JSON, nullable=True)
    load_time = Column(Float, nullable=True)  # in seconds
    
    # Relationships
    click_event = relationship("ClickEvent", back_populates="link_analysis")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
