from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class IntegrationState(Base):
    __tablename__ = "integration_states"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True)  # e.g., gmail, microsoft365, imap
    cursor = Column(Text, nullable=True)  # provider-specific cursor token/state
    last_sync = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


