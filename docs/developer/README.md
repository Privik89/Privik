# Developer Documentation

## Overview

This guide provides comprehensive information for developers working on the Privik platform. It covers development setup, code structure, testing, and contribution guidelines.

## Development Setup

### Prerequisites

- Python 3.9+
- Node.js 16+
- PostgreSQL 13+
- Redis 6+
- Docker & Docker Compose
- Git

### Quick Start

```bash
# Clone repository
git clone https://github.com/your-org/privik.git
cd privik

# Backend setup
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Frontend setup
cd ../frontend
npm install

# Start development services
docker-compose -f docker-compose.dev.yml up -d

# Run migrations
cd ../backend
alembic upgrade head

# Start development servers
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# In another terminal:
cd frontend && npm start
```

## Code Structure

### Backend Structure

```
backend/
├── app/
│   ├── api.py                 # Main API router
│   ├── main.py               # FastAPI application
│   ├── core/
│   │   ├── config.py         # Configuration management
│   │   └── database.py       # Database connection
│   ├── models/               # SQLAlchemy models
│   ├── routers/              # API route handlers
│   ├── services/             # Business logic
│   ├── security/             # Authentication & authorization
│   └── utils/                # Utility functions
├── tests/                    # Test suite
├── alembic/                  # Database migrations
└── requirements.txt          # Dependencies
```

### Frontend Structure

```
frontend/
├── src/
│   ├── components/           # React components
│   ├── pages/               # Page components
│   ├── services/            # API services
│   ├── utils/               # Utility functions
│   └── App.js               # Main application
├── public/                  # Static assets
└── package.json             # Dependencies
```

## Development Guidelines

### Code Style

#### Python (Backend)
- Follow PEP 8 style guidelines
- Use type hints for all functions
- Maximum line length: 88 characters (Black formatter)
- Use docstrings for all public functions

```python
from typing import Dict, List, Optional
import structlog

logger = structlog.get_logger()

async def process_email(
    email_data: Dict[str, Any],
    user_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Process an email for threat analysis.
    
    Args:
        email_data: Email data dictionary
        user_id: Optional user ID for context
        
    Returns:
        Analysis results dictionary
        
    Raises:
        ValidationError: If email data is invalid
    """
    try:
        # Implementation here
        pass
    except Exception as e:
        logger.error("email_processing_error", error=str(e))
        raise
```

#### JavaScript (Frontend)
- Use ESLint and Prettier for formatting
- Use functional components with hooks
- Follow React best practices
- Use TypeScript for type safety

```javascript
import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

const EmailAnalysis = ({ emailId, onAnalysisComplete }) => {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (emailId) {
      fetchAnalysis(emailId);
    }
  }, [emailId]);

  const fetchAnalysis = async (id) => {
    setLoading(true);
    try {
      const response = await api.get(`/emails/${id}/analysis`);
      setAnalysis(response.data);
      onAnalysisComplete?.(response.data);
    } catch (error) {
      console.error('Failed to fetch analysis:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="email-analysis">
      {loading ? (
        <div>Loading analysis...</div>
      ) : (
        <div>Analysis: {analysis?.verdict}</div>
      )}
    </div>
  );
};

EmailAnalysis.propTypes = {
  emailId: PropTypes.string.isRequired,
  onAnalysisComplete: PropTypes.func,
};

export default EmailAnalysis;
```

### Testing

#### Backend Testing

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.main import app
from app.database import get_db
from app.models import Email

client = TestClient(app)

@pytest.fixture
def db_session():
    """Create a test database session."""
    # Setup test database
    pass

def test_process_email_success(db_session: Session):
    """Test successful email processing."""
    email_data = {
        "message_id": "test_123",
        "subject": "Test Email",
        "sender": "test@example.com",
        "recipient": "user@company.com",
        "body": "Test content"
    }
    
    response = client.post("/api/email-gateway/process", json=email_data)
    
    assert response.status_code == 200
    assert "threat_score" in response.json()
    assert "verdict" in response.json()

def test_process_email_invalid_data():
    """Test email processing with invalid data."""
    invalid_data = {"invalid": "data"}
    
    response = client.post("/api/email-gateway/process", json=invalid_data)
    
    assert response.status_code == 422
```

#### Frontend Testing

```javascript
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import EmailAnalysis from '../EmailAnalysis';

// Mock API
jest.mock('../services/api', () => ({
  get: jest.fn(),
}));

describe('EmailAnalysis', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders loading state initially', () => {
    render(<EmailAnalysis emailId="test-123" />);
    expect(screen.getByText('Loading analysis...')).toBeInTheDocument();
  });

  it('displays analysis results after loading', async () => {
    const mockAnalysis = { verdict: 'safe', threat_score: 0.1 };
    api.get.mockResolvedValue({ data: mockAnalysis });

    render(<EmailAnalysis emailId="test-123" />);

    await waitFor(() => {
      expect(screen.getByText('Analysis: safe')).toBeInTheDocument();
    });
  });
});
```

### Database Migrations

#### Creating Migrations

```bash
# Create a new migration
alembic revision --autogenerate -m "Add user behavior tracking"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

#### Migration Example

```python
"""Add user behavior tracking

Revision ID: 001_add_user_behavior
Revises: 000_initial_migration
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '001_add_user_behavior'
down_revision = '000_initial_migration'
branch_labels = None
depends_on = None

def upgrade():
    # Create user_behavior table
    op.create_table('user_behavior',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('action_type', sa.String(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index
    op.create_index('idx_user_behavior_user_id', 'user_behavior', ['user_id'])

def downgrade():
    op.drop_index('idx_user_behavior_user_id', table_name='user_behavior')
    op.drop_table('user_behavior')
```

## API Development

### Creating New Endpoints

#### 1. Define Route Handler

```python
# app/routers/new_feature.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..database import get_db
from ..security.hmac_auth import verify_request
from ..services.new_feature_service import NewFeatureService
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.post("/new-feature/process", dependencies=[Depends(verify_request)])
async def process_new_feature(
    data: Dict[str, Any],
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Process new feature data.
    
    Args:
        data: Feature data dictionary
        db: Database session
        
    Returns:
        Processing results
    """
    try:
        service = NewFeatureService(db)
        result = await service.process_data(data)
        return result
    except Exception as e:
        logger.error("new_feature_processing_error", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process feature: {e}"
        )
```

#### 2. Create Service Class

```python
# app/services/new_feature_service.py
from sqlalchemy.orm import Session
from typing import Dict, Any
import structlog

logger = structlog.get_logger()

class NewFeatureService:
    def __init__(self, db: Session):
        self.db = db
    
    async def process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process feature data."""
        try:
            # Business logic here
            result = await self._perform_processing(data)
            
            # Log the operation
            logger.info("feature_processed", 
                       data_id=data.get("id"), 
                       result=result)
            
            return result
        except Exception as e:
            logger.error("feature_processing_failed", 
                        data_id=data.get("id"), 
                        error=str(e))
            raise
    
    async def _perform_processing(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Internal processing logic."""
        # Implementation here
        pass
```

#### 3. Add to Main Router

```python
# app/api.py
from .routers import new_feature

api_router.include_router(new_feature.router, prefix="/api/new-feature", tags=["new-feature"])
```

### Authentication & Authorization

#### HMAC Authentication

```python
# app/security/hmac_auth.py
import hmac
import hashlib
import time
from fastapi import HTTPException, status, Request
from ..core.config import settings

def verify_request(request: Request) -> bool:
    """Verify HMAC signature for API requests."""
    # Extract headers
    api_key_id = request.headers.get("X-API-Key-ID")
    timestamp = request.headers.get("X-API-Timestamp")
    nonce = request.headers.get("X-API-Nonce")
    signature = request.headers.get("X-API-Signature")
    
    # Validate headers
    if not all([api_key_id, timestamp, nonce, signature]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required authentication headers"
        )
    
    # Verify timestamp (prevent replay attacks)
    if not _is_timestamp_valid(timestamp):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid timestamp"
        )
    
    # Verify nonce (prevent replay attacks)
    if not _is_nonce_valid(nonce):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid nonce"
        )
    
    # Verify signature
    expected_signature = _generate_signature(
        request.method,
        request.url.path,
        request.body,
        timestamp,
        nonce,
        settings.HMAC_API_SECRET
    )
    
    if not hmac.compare_digest(signature, expected_signature):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature"
        )
    
    return True
```

#### JWT Authorization

```python
# app/security/jwt_auth.py
import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ..core.config import settings

security = HTTPBearer()

def verify_jwt_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

def require_role(required_role: str):
    """Decorator to require specific role."""
    def role_checker(token: Dict[str, Any] = Depends(verify_jwt_token)):
        if required_role not in token.get("roles", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return token
    return role_checker
```

## Frontend Development

### Component Development

#### Creating React Components

```javascript
// src/components/NewFeature.js
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { toast } from 'react-toastify';
import api from '../services/api';

const NewFeature = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (id) {
      fetchData(id);
    }
  }, [id]);

  const fetchData = async (featureId) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await api.get(`/new-feature/${featureId}`);
      setData(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to fetch data');
      toast.error('Failed to load feature data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (formData) => {
    setLoading(true);
    
    try {
      await api.post('/new-feature/process', formData);
      toast.success('Feature processed successfully');
      navigate('/features');
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to process feature');
      toast.error('Failed to process feature');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  return (
    <div className="new-feature">
      <h1>New Feature</h1>
      {/* Component content */}
    </div>
  );
};

export default NewFeature;
```

#### API Service Layer

```javascript
// src/services/api.js
import axios from 'axios';
import { toast } from 'react-toastify';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for authentication
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    } else if (error.response?.status >= 500) {
      toast.error('Server error. Please try again later.');
    }
    return Promise.reject(error);
  }
);

export default api;
```

## Testing

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/ -v --cov=app --cov-report=html

# Frontend tests
cd frontend
npm test

# Integration tests
pytest tests/integration/ -v

# Security tests
pytest tests/security/ -v

# Performance tests
pytest tests/performance/ -v
```

### Test Configuration

#### Backend Test Configuration

```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base
from app.core.config import settings

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            db_session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
```

#### Frontend Test Configuration

```javascript
// src/setupTests.js
import '@testing-library/jest-dom';

// Mock API
jest.mock('./services/api', () => ({
  get: jest.fn(),
  post: jest.fn(),
  put: jest.fn(),
  delete: jest.fn(),
}));

// Mock router
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => jest.fn(),
  useParams: () => ({ id: 'test-id' }),
}));
```

## Performance Optimization

### Backend Optimization

#### Database Optimization

```python
# app/database/optimization.py
from sqlalchemy import Index, text
from sqlalchemy.orm import Session

def create_indexes(db: Session):
    """Create database indexes for performance."""
    indexes = [
        Index('idx_emails_timestamp', 'emails', 'created_at'),
        Index('idx_emails_sender', 'emails', 'sender'),
        Index('idx_emails_recipient', 'emails', 'recipient'),
        Index('idx_threat_analysis_email_id', 'threat_analysis', 'email_id'),
        Index('idx_user_behavior_user_id', 'user_behavior', 'user_id'),
    ]
    
    for index in indexes:
        try:
            index.create(db.bind)
        except Exception as e:
            print(f"Failed to create index {index.name}: {e}")

def optimize_queries():
    """Optimize common queries."""
    # Use select_related for foreign keys
    # Use prefetch_related for many-to-many relationships
    # Use database-level filtering instead of Python filtering
    pass
```

#### Caching Strategy

```python
# app/services/cache_manager.py
import redis
import json
from typing import Any, Optional
from ..core.config import settings

class CacheManager:
    def __init__(self):
        self.redis = redis.from_url(settings.REDIS_URL)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = self.redis.get(key)
            return json.loads(value) if value else None
        except Exception:
            return None
    
    async def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Set value in cache with TTL."""
        try:
            self.redis.setex(key, ttl, json.dumps(value))
            return True
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            self.redis.delete(key)
            return True
        except Exception:
            return False
```

### Frontend Optimization

#### Code Splitting

```javascript
// src/App.js
import React, { Suspense, lazy } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Lazy load components
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Incidents = lazy(() => import('./pages/Incidents'));
const Settings = lazy(() => import('./pages/Settings'));

const App = () => {
  return (
    <Router>
      <Suspense fallback={<div>Loading...</div>}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/incidents" element={<Incidents />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </Suspense>
    </Router>
  );
};

export default App;
```

#### Performance Monitoring

```javascript
// src/utils/performance.js
export const measurePerformance = (name, fn) => {
  const start = performance.now();
  const result = fn();
  const end = performance.now();
  
  console.log(`${name} took ${end - start} milliseconds`);
  return result;
};

// Usage
const expensiveOperation = () => {
  // Expensive operation
};

const result = measurePerformance('Expensive Operation', expensiveOperation);
```

## Security Best Practices

### Input Validation

```python
# app/utils/validation.py
from pydantic import BaseModel, validator, EmailStr
from typing import Optional, List
import re

class EmailData(BaseModel):
    message_id: str
    subject: str
    sender: EmailStr
    recipient: EmailStr
    body: str
    attachments: Optional[List[dict]] = []
    links: Optional[List[str]] = []
    
    @validator('message_id')
    def validate_message_id(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Invalid message ID format')
        return v
    
    @validator('links')
    def validate_links(cls, v):
        if v:
            for link in v:
                if not link.startswith(('http://', 'https://')):
                    raise ValueError('Invalid link format')
        return v
```

### Output Sanitization

```python
# app/utils/sanitization.py
import html
import re
from typing import Any

def sanitize_html(content: str) -> str:
    """Sanitize HTML content."""
    # Remove script tags
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove javascript: URLs
    content = re.sub(r'javascript:', '', content, flags=re.IGNORECASE)
    
    # Escape HTML entities
    content = html.escape(content)
    
    return content

def sanitize_output(data: Any) -> Any:
    """Sanitize output data."""
    if isinstance(data, str):
        return sanitize_html(data)
    elif isinstance(data, dict):
        return {k: sanitize_output(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_output(item) for item in data]
    else:
        return data
```

## Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/new-feature`
3. **Make changes**: Follow coding standards and add tests
4. **Run tests**: Ensure all tests pass
5. **Commit changes**: Use conventional commit messages
6. **Push to fork**: `git push origin feature/new-feature`
7. **Create pull request**: Provide detailed description

### Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

Examples:
- `feat(api): add new email processing endpoint`
- `fix(ui): resolve login form validation issue`
- `docs(readme): update installation instructions`
- `test(backend): add unit tests for email analyzer`

### Pull Request Guidelines

1. **Clear description**: Explain what the PR does and why
2. **Link issues**: Reference related issues
3. **Add tests**: Include tests for new functionality
4. **Update documentation**: Update relevant documentation
5. **Screenshots**: Include screenshots for UI changes

### Code Review Process

1. **Automated checks**: CI/CD pipeline runs tests and linting
2. **Peer review**: At least one team member reviews the code
3. **Security review**: Security-sensitive changes require security review
4. **Approval**: Maintainer approval required for merge

This developer documentation provides comprehensive guidance for contributing to the Privik platform. For additional questions or support, please contact the development team.
