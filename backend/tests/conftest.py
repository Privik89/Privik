"""
Pytest configuration and fixtures for testing
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, AsyncMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Import your application
from app.main import app
from app.database import get_db, Base
from app.core.config import settings

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture(scope="function")
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)

@pytest.fixture(scope="function")
def mock_email_data():
    """Mock email data for testing."""
    return {
        "message_id": "test_message_123",
        "subject": "Test Email Subject",
        "sender": "test@example.com",
        "recipient": "user@company.com",
        "body": "This is a test email body",
        "headers": {
            "From": "test@example.com",
            "To": "user@company.com",
            "Subject": "Test Email Subject",
            "Date": datetime.now().isoformat()
        },
        "attachments": [],
        "links": ["https://example.com"],
        "timestamp": datetime.now().isoformat()
    }

@pytest.fixture(scope="function")
def mock_threat_data():
    """Mock threat data for testing."""
    return {
        "threat_id": "threat_123",
        "threat_type": "phishing",
        "threat_score": 0.85,
        "indicators": ["suspicious_domain", "urgent_language"],
        "verdict": "malicious",
        "confidence": 0.92,
        "timestamp": datetime.now().isoformat()
    }

@pytest.fixture(scope="function")
def mock_user_data():
    """Mock user data for testing."""
    return {
        "user_id": "user_123",
        "email": "testuser@company.com",
        "name": "Test User",
        "role": "user",
        "tenant_id": "tenant_123",
        "permissions": ["read_emails", "view_reports"],
        "created_at": datetime.now().isoformat()
    }

@pytest.fixture(scope="function")
def mock_tenant_data():
    """Mock tenant data for testing."""
    return {
        "tenant_id": "tenant_123",
        "name": "Test Company",
        "domain": "testcompany.com",
        "tenant_type": "enterprise",
        "plan": "professional",
        "status": "active",
        "created_at": datetime.now().isoformat()
    }

@pytest.fixture(scope="function")
def mock_sandbox_data():
    """Mock sandbox analysis data for testing."""
    return {
        "analysis_id": "analysis_123",
        "file_hash": "a1b2c3d4e5f6...",
        "filename": "test_file.pdf",
        "verdict": "malicious",
        "threat_score": 0.95,
        "malware_family": "Trojan.Generic",
        "behavior_indicators": ["suspicious_network_activity", "file_encryption"],
        "timestamp": datetime.now().isoformat()
    }

@pytest.fixture(scope="function")
def mock_behavioral_data():
    """Mock behavioral analysis data for testing."""
    return {
        "user_id": "user_123",
        "anomaly_score": 0.75,
        "risk_level": "high",
        "behavioral_indicators": {
            "unusual_login_time": True,
            "high_email_volume": True,
            "suspicious_click_rate": 0.4
        },
        "timestamp": datetime.now().isoformat()
    }

@pytest.fixture(scope="function")
def mock_compliance_data():
    """Mock compliance data for testing."""
    return {
        "framework": "soc2_type_ii",
        "compliance_score": 0.92,
        "requirements_met": 45,
        "requirements_total": 49,
        "last_assessment": datetime.now().isoformat(),
        "next_assessment": (datetime.now() + timedelta(days=30)).isoformat()
    }

@pytest.fixture(scope="function")
def mock_webhook_data():
    """Mock webhook data for testing."""
    return {
        "webhook_id": "webhook_123",
        "name": "Test Webhook",
        "url": "https://example.com/webhook",
        "events": ["email_threat_detected", "user_behavior_anomaly"],
        "secret": "test_secret_key",
        "status": "active",
        "created_at": datetime.now().isoformat()
    }

@pytest.fixture(scope="function")
def mock_ldap_config():
    """Mock LDAP configuration for testing."""
    return {
        "server_name": "Test LDAP Server",
        "server_host": "ldap.test.com",
        "server_type": "active_directory",
        "port": 389,
        "use_ssl": False,
        "use_tls": True,
        "bind_dn": "CN=admin,DC=test,DC=com",
        "bind_password": "test_password",
        "user_search_base": "CN=Users,DC=test,DC=com",
        "domain": "test.com"
    }

@pytest.fixture(scope="function")
def mock_siem_config():
    """Mock SIEM configuration for testing."""
    return {
        "provider": "splunk",
        "host": "splunk.test.com",
        "port": 8089,
        "token": "test_splunk_token",
        "index": "privik_events",
        "verify_ssl": True
    }

@pytest.fixture(scope="function")
def mock_backup_config():
    """Mock backup configuration for testing."""
    return {
        "name": "Test Backup Job",
        "backup_type": "full",
        "destination": "local",
        "destination_config": {
            "path": "/tmp/backups"
        },
        "sources": ["database", "files", "configurations"],
        "schedule": "0 2 * * *",  # Daily at 2 AM
        "retention_days": 30,
        "compression": True,
        "encryption": True
    }

# Async fixtures for testing async functions
@pytest.fixture(scope="function")
async def async_mock():
    """Async mock for testing async functions."""
    return AsyncMock()

@pytest.fixture(scope="function")
def mock_cache_manager():
    """Mock cache manager for testing."""
    cache_data = {}
    
    class MockCacheManager:
        async def get(self, key: str, namespace: str = "default"):
            return cache_data.get(f"{namespace}:{key}")
        
        async def set(self, key: str, value: Any, ttl: int = 3600, namespace: str = "default"):
            cache_data[f"{namespace}:{key}"] = value
        
        async def delete(self, key: str, namespace: str = "default"):
            cache_data.pop(f"{namespace}:{key}", None)
        
        async def exists(self, key: str, namespace: str = "default"):
            return f"{namespace}:{key}" in cache_data
    
    return MockCacheManager()

@pytest.fixture(scope="function")
def mock_logging_service():
    """Mock logging service for testing."""
    class MockLoggingService:
        async def log_audit_event(self, event):
            pass
        
        async def log_application_event(self, level, message, **kwargs):
            pass
        
        async def log_error_event(self, error, context=None):
            pass
    
    return MockLoggingService()

# Test data generators
@pytest.fixture(scope="function")
def email_generator():
    """Generate test email data."""
    def _generate_email(**kwargs):
        default_email = {
            "message_id": f"msg_{datetime.now().timestamp()}",
            "subject": "Test Email",
            "sender": "sender@example.com",
            "recipient": "recipient@example.com",
            "body": "Test email body",
            "timestamp": datetime.now().isoformat()
        }
        default_email.update(kwargs)
        return default_email
    return _generate_email

@pytest.fixture(scope="function")
def user_generator():
    """Generate test user data."""
    def _generate_user(**kwargs):
        default_user = {
            "user_id": f"user_{datetime.now().timestamp()}",
            "email": f"user{datetime.now().timestamp()}@example.com",
            "name": "Test User",
            "role": "user",
            "created_at": datetime.now().isoformat()
        }
        default_user.update(kwargs)
        return default_user
    return _generate_user

# Performance testing fixtures
@pytest.fixture(scope="function")
def performance_timer():
    """Timer for performance testing."""
    class PerformanceTimer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = datetime.now()
        
        def stop(self):
            self.end_time = datetime.now()
        
        @property
        def duration(self):
            if self.start_time and self.end_time:
                return (self.end_time - self.start_time).total_seconds()
            return None
    
    return PerformanceTimer()

# Security testing fixtures
@pytest.fixture(scope="function")
def security_test_data():
    """Security test data for vulnerability testing."""
    return {
        "sql_injection_payloads": [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --"
        ],
        "xss_payloads": [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>"
        ],
        "path_traversal_payloads": [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "....//....//....//etc/passwd"
        ]
    }

# Mock external services
@pytest.fixture(scope="function")
def mock_virustotal():
    """Mock VirusTotal service."""
    with patch('app.services.virustotal.VirusTotalService') as mock:
        mock_instance = mock.return_value
        mock_instance.lookup_file.return_value = {
            "detections": 5,
            "engines": 67,
            "malware_family": "Trojan.Generic"
        }
        mock_instance.lookup_domain.return_value = {
            "reputation_score": 0.15,
            "detections": 3,
            "categories": ["phishing"]
        }
        yield mock_instance

@pytest.fixture(scope="function")
def mock_cape_sandbox():
    """Mock CAPE sandbox service."""
    with patch('app.services.real_time_sandbox.RealTimeSandbox') as mock:
        mock_instance = mock.return_value
        mock_instance.analyze_attachment.return_value = {
            "analysis_id": "cape_123",
            "verdict": "malicious",
            "threat_score": 0.95
        }
        yield mock_instance

@pytest.fixture(scope="function")
def mock_minio():
    """Mock MinIO object storage."""
    with patch('app.services.object_storage.ObjectStorage') as mock:
        mock_instance = mock.return_value
        mock_instance.upload_file.return_value = "test_file_key"
        mock_instance.get_object_url.return_value = "https://minio.test.com/bucket/test_file_key"
        yield mock_instance
