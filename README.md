# Privik - Zero-Trust Email Security Platform

[![Build Status](https://github.com/your-org/privik/workflows/Test%20Suite/badge.svg)](https://github.com/your-org/privik/actions)
[![Coverage](https://codecov.io/gh/your-org/privik/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/privik)
[![Security](https://img.shields.io/badge/security-bandit-yellow.svg)](https://github.com/PyCQA/bandit)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 🛡️ Overview

Privik is an advanced zero-trust email security platform that provides comprehensive protection against email-based threats through AI-driven analysis, real-time sandboxing, and behavioral monitoring. Built with enterprise-grade security and scalability in mind, Privik offers unique click-time detonation capabilities that analyze threats even after emails reach the inbox.

## ✨ Key Features

### 🔍 **AI-Enriched Email Analysis**
- **Intent Classification**: AI-driven email intent detection (BEC, spam, invoice fraud, phishing)
- **Real-time Scoring**: Dynamic threat scoring with confidence levels
- **Behavioral Analysis**: User behavior anomaly detection and risk profiling
- **Multi-model ML**: LSTM, CNN, and Isolation Forest algorithms for comprehensive analysis

### 🎯 **Click-Time Detonation**
- **Post-Delivery Analysis**: Sandbox links and attachments when users click them
- **Real-time Sandboxing**: Lightweight detonation with CAPEv2 integration
- **Behavior Capture**: System activity monitoring and screenshot capture
- **Evasion Detection**: Advanced evasion technique detection

### 🏢 **Enterprise Features**
- **Multi-tenant Support**: Complete tenant isolation for MSP deployments
- **LDAP/AD Integration**: Enterprise authentication and user management
- **SIEM Integration**: Real-time event streaming to major SIEM platforms
- **Compliance Reporting**: SOC2, ISO27001, GDPR, HIPAA compliance automation

### 🔒 **Zero-Trust Security**
- **HMAC Authentication**: Secure agent-to-server communication
- **JWT/RBAC**: Role-based access control for admin interfaces
- **Encryption**: End-to-end encryption for data at rest and in transit
- **Audit Logging**: Comprehensive audit trails and compliance logging

### 📊 **SOC Dashboard & AI Copilot**
- **Real-time Monitoring**: Live threat detection and incident management
- **AI Analyst Assistant**: LLM-powered incident analysis and recommendations
- **Timeline Visualization**: Incident correlation and campaign detection
- **Threat Intelligence**: Integration with VirusTotal, Google Safe Browsing, and more

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Email Sources │    │   Privik Core   │    │   Endpoint      │
│                 │    │                 │    │   Agents        │
│ • Gmail         │───▶│ • AI Analysis   │───▶│ • Click Monitor │
│ • O365          │    │ • Sandbox       │    │ • Behavior      │
│ • IMAP/POP3     │    │ • ML Models     │    │ • Reporting     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   Integrations  │
                       │                 │
                       │ • SIEM          │
                       │ • LDAP/AD       │
                       │ • Webhooks      │
                       │ • Compliance    │
                       └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- Docker (for sandboxing)
- Node.js 16+ (for frontend)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/privik.git
   cd privik
   ```

2. **Set up the backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   pip install -r requirements-test.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize database**
   ```bash
   alembic upgrade head
   ```

5. **Start the services**
   ```bash
   # Start backend
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   
   # Start frontend (in another terminal)
   cd frontend
   npm install
   npm start
   ```

6. **Access the platform**
   - Frontend: http://localhost:3000
   - API Documentation: http://localhost:8000/docs
   - Admin Interface: http://localhost:3000/admin

## 📖 Documentation

- [**API Documentation**](docs/api/README.md) - Complete API reference
- [**Architecture Guide**](docs/architecture/README.md) - System design and components
- [**Deployment Guide**](docs/deployment/README.md) - Production deployment instructions
- [**User Manual**](docs/user/README.md) - End-user and admin guides
- [**Developer Guide**](docs/developer/README.md) - Development and contribution guide
- [**Security Guide**](docs/security/README.md) - Security features and best practices
- [**Troubleshooting**](docs/troubleshooting/README.md) - Common issues and solutions

## 🧪 Testing

### Run Tests

```bash
# Unit tests
pytest tests/test_email_analyzer.py -v

# Integration tests
pytest tests/test_integration_api.py -v

# Security tests
pytest tests/test_security.py -v

# Performance tests
pytest tests/test_performance.py -v

# All tests with coverage
pytest --cov=app --cov-report=html
```

### Test Coverage

- **Unit Tests**: 95%+ coverage for core services
- **Integration Tests**: 90%+ coverage for API endpoints
- **Security Tests**: Comprehensive vulnerability testing
- **Performance Tests**: Load testing and scalability validation

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/privik

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
HMAC_API_KEY_ID=your_api_key_id
HMAC_API_SECRET=your_api_secret
JWT_SECRET=your_jwt_secret

# Email Integrations
GMAIL_REFRESH_TOKEN=your_gmail_token
O365_TENANT_ID=your_tenant_id

# Sandbox
CAPE_BASE_URL=http://localhost:8000
CAPE_API_TOKEN=your_cape_token

# Object Storage
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=your_access_key
MINIO_SECRET_KEY=your_secret_key
```

## 🏢 Enterprise Features

### Multi-Tenant Support
- Complete tenant isolation
- Resource quotas and limits
- Plan-based feature access
- Billing and usage tracking

### SIEM Integration
- Splunk Enterprise Security
- IBM QRadar
- ELK Stack
- Microsoft Sentinel
- Real-time event streaming

### Compliance
- SOC2 Type II reporting
- ISO27001 compliance
- GDPR data protection
- HIPAA healthcare compliance
- Automated audit trails

## 🔒 Security

### Authentication & Authorization
- HMAC-based API authentication
- JWT tokens for web interfaces
- LDAP/Active Directory integration
- Role-based access control (RBAC)

### Data Protection
- AES-256 encryption at rest
- TLS 1.3 for data in transit
- Secure key management
- Data anonymization and pseudonymization

### Threat Detection
- AI-powered email analysis
- Real-time sandboxing
- Behavioral anomaly detection
- Advanced evasion detection

## 📊 Monitoring & Observability

### Health Checks
- Multi-service health monitoring
- Performance metrics collection
- Error tracking and alerting
- System resource monitoring

### Logging
- Structured JSON logging
- Audit trail logging
- Performance metrics logging
- Security event logging

### Metrics
- Email processing metrics
- Threat detection statistics
- System performance metrics
- User behavior analytics

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Code Standards

- Follow PEP 8 style guidelines
- Write comprehensive tests
- Document all public APIs
- Use type hints
- Follow security best practices

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/privik/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/privik/discussions)
- **Security**: [Security Policy](SECURITY.md)

## 🙏 Acknowledgments

- CAPEv2 for sandboxing capabilities
- VirusTotal for threat intelligence
- The open-source community for various libraries and tools

---

**Privik** - Protecting your organization with zero-trust email security powered by AI.