"""
Domain List Models for Whitelist/Blacklist Management
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class DomainList(Base):
    __tablename__ = "domain_lists"
    
    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(255), nullable=False, index=True)
    list_type = Column(String(20), nullable=False)  # 'whitelist' or 'blacklist'
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    
    def __repr__(self):
        return f"<DomainList(domain='{self.domain}', type='{self.list_type}')>"
