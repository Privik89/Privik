from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), unique=True, index=True)
    email = Column(String(255), unique=True, index=True)
    organization = Column(String(255), nullable=True)
    department = Column(String(255), nullable=True)
    
    # Risk profile
    risk_score = Column(Float, default=0.0)
    risk_level = Column(String(50), default="low")  # low, medium, high, critical
    is_high_risk = Column(Boolean, default=False)
    
    # Behavior tracking
    total_clicks = Column(Integer, default=0)
    suspicious_clicks = Column(Integer, default=0)
    blocked_clicks = Column(Integer, default=0)
    last_activity = Column(DateTime, nullable=True)
    
    # AI analysis
    behavior_pattern = Column(String(100), nullable=True)  # cautious, normal, risky
    ai_risk_factors = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class UserRiskProfile(Base):
    __tablename__ = "user_risk_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(255), index=True)
    
    # Risk factors
    click_frequency = Column(Float, default=0.0)  # clicks per day
    suspicious_click_ratio = Column(Float, default=0.0)
    time_of_day_risk = Column(JSON, nullable=True)  # Risk by hour
    day_of_week_risk = Column(JSON, nullable=True)  # Risk by day
    
    # Behavioral patterns
    typical_senders = Column(JSON, nullable=True)  # List of trusted senders
    typical_domains = Column(JSON, nullable=True)  # List of trusted domains
    unusual_behavior_flags = Column(JSON, nullable=True)
    
    # AI analysis
    ml_risk_score = Column(Float, default=0.0)
    ml_confidence = Column(Float, default=0.0)
    ml_factors = Column(JSON, nullable=True)
    
    # Timestamps
    profile_created = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
