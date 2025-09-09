# Privik — AI-powered, zero-trust email security platform

**"Just because it's clean now doesn't mean it's safe. We sandbox and score everything — at the moment it matters."**

Privik is the world's first execution-aware, AI-powered email security platform that behaviorally analyzes every link and file at the moment of user interaction — even if it appears clean — and protects users through real-time sandboxing, AI threat scoring, and user behavior analysis.

## 🚀 Core Features

### Zero-Trust Email Security
- **Execution-Aware Protection**: Sandbox and analyze links/attachments at click-time, not just pre-delivery
- **AI-Powered Threat Detection**: Advanced ML models for phishing, BEC, and malware detection
- **Real-Time Behavioral Analysis**: Monitor user interactions and detect suspicious patterns
- **SOC Dashboard**: Comprehensive security operations center for threat monitoring

### Key Differentiators
- ✅ **Post-delivery sandboxing** (vs. pre-delivery only in traditional solutions)
- ✅ **AI-based behavioral verdicts** (vs. rule/reputation-based)
- ✅ **Execution-aware link handling** (vs. static analysis)
- ✅ **User behavior profiling** (vs. no user risk assessment)
- ✅ **SOC copilot with LLM support** (vs. manual triage)

## 🏗️ Architecture

### Platform Modules
1. **Email Gateway** - Ingests mail, rewrites links, scans attachments
2. **Static Threat Scanner** - Virus scan, CTI enrichment, YARA rules
3. **Link Catchpoint Engine** - Redirects every link at click-time to secure analysis proxy
4. **File Detonation Engine** - Opens attachments in sandbox upon user click
5. **Behavior-Based Verdict Engine** - Converts detonation logs to block/allow verdict
6. **SOC Dashboard** - Analyst UI to triage alerts, track users, export logs
7. **User Risk Engine** - Tracks risky behavior across organization

### Tech Stack
- **Backend**: FastAPI, Python 3.11, SQLAlchemy, PostgreSQL
- **Frontend**: React 18, Tailwind CSS, Heroicons, Recharts
- **AI/ML**: Scikit-learn, PyTorch, Transformers (HuggingFace), OpenAI APIs
- **Infrastructure**: Docker, Kubernetes, Redis, MinIO (S3-compatible)
- **Security**: OAuth2, TLS, customer data isolation

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ (for backend)
- Node.js 16+ and npm (for frontend)
- Docker and Docker Compose (optional, for production)

### **One-Command Setup**

#### **Linux/macOS:**
```bash
# Clone and setup
git clone <repository-url>
cd Privik
chmod +x setup_linux.sh
./setup_linux.sh

# Start the platform
./start_privik.sh
```

#### **Windows:**
```cmd
# Clone and setup
git clone <repository-url>
cd Privik
setup_windows.bat

# Start the platform
start_privik_windows.bat
```

### **Access Points**
- **Frontend Dashboard**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Option 2: Manual Setup

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd Privik
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Start Backend**
   ```bash
   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

4. **Frontend Setup (in new terminal)**
   ```bash
   cd frontend
   npm install
   npm start
   ```

5. **Access the platform**
   - Frontend Dashboard: http://localhost:3000
   - API Documentation: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

### Option 3: Docker Compose (Production-like)

1. **Environment Configuration**
   ```bash
   cp backend/.env.example backend/.env
   nano backend/.env
   ```

2. **Start with Docker Compose**
   ```bash
   docker compose up --build
   ```

## 📊 API Endpoints

### Email Ingestion
- `POST /api/ingest/email` - Ingest and analyze email
- `POST /api/ingest/attachment/{email_id}` - Upload and analyze attachment
- `GET /api/ingest/email/{email_id}` - Get email details and analysis

### Click Analysis
- `POST /api/click/redirect` - Handle click redirection and queue analysis
- `GET /api/click/analysis/{analysis_id}` - Get link analysis status

### SOC Dashboard
- `GET /api/soc/dashboard` - Get threat summary
- `GET /api/soc/users/risk` - Get user risk profiles
- `GET /api/soc/timeline` - Get threat timeline
- `GET /api/soc/alerts` - Get active security alerts
- `GET /api/soc/stats/hourly` - Get hourly threat statistics

## ⚙️ Configuration

### Environment Variables
```bash
# App Settings
APP_NAME=Privik Email Security API
ENVIRONMENT=development
DEBUG=true
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql+psycopg2://postgres:postgres@db:5432/privik

# Object Storage (S3-compatible)
S3_ENDPOINT_URL=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET_NAME=privik-artifacts

# AI/ML Services
OPENAI_API_KEY=your-openai-api-key
VIRUSTOTAL_API_KEY=your-virustotal-api-key

# Security Settings
SANDBOX_TIMEOUT=30
MAX_FILE_SIZE=50MB
ALLOWED_FILE_TYPES=.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.zip,.rar,.7z
```

## 🔧 Development

### Project Structure
```
Privik/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── core/      # Configuration and settings
│   │   ├── models/    # Database models
│   │   ├── routers/   # API endpoints
│   │   ├── services/  # Business logic
│   │   ├── database.py # Database connection
│   │   ├── main.py    # FastAPI application
│   │   └── api.py     # API router
│   ├── requirements.txt # Python dependencies
│   └── Dockerfile     # Container configuration
├── frontend/          # React frontend
│   ├── src/
│   │   ├── components/ # Reusable UI components
│   │   ├── pages/     # Main application pages
│   │   ├── App.js     # Main application component
│   │   └── index.js   # Application entry point
│   ├── package.json   # Node.js dependencies
│   └── tailwind.config.js # Tailwind CSS configuration
├── start_privik_full.sh # Full stack startup script
└── README.md          # Project documentation
```

### Database Models
- **Email** - Email messages and metadata
- **EmailAttachment** - File attachments and analysis results
- **ClickEvent** - User click tracking
- **LinkAnalysis** - Link analysis results
- **SandboxAnalysis** - File detonation results
- **User** - User profiles and risk assessment
- **ThreatIntel** - Threat intelligence data

### Adding New Features
1. Create database models in `app/models/`
2. Add business logic in `app/services/`
3. Create API endpoints in `app/routers/`
4. Update tests and documentation

## 🧪 Testing

### Run Tests
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests
pytest backend/tests/

# Run with coverage
pytest --cov=backend/app backend/tests/
```

### API Testing
```bash
# Test email ingestion
curl -X POST "http://localhost:8000/api/ingest/email" \
  -H "Content-Type: application/json" \
  -d '{
    "message_id": "test-123",
    "subject": "Test Email",
    "sender": "test@example.com",
    "recipients": ["user@company.com"],
    "body_text": "This is a test email"
  }'

# Test click analysis
curl -X POST "http://localhost:8000/api/click/redirect" \
  -H "Content-Type: application/json" \
  -d '{
    "original_url": "https://example.com",
    "user_id": "user123",
    "message_id": "test-123"
  }'
```

## 🚀 Deployment

### Production Deployment
```bash
# Build production image
docker build -t privik:latest ./backend

# Run with production settings
docker run -d \
  --name privik \
  -p 8000:8000 \
  --env-file backend/.env.prod \
  privik:latest
```

### Kubernetes Deployment
```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods -l app=privik
```

## 📈 Monitoring

### Health Checks
- Application: `GET /health`
- Database: `GET /health/db`
- External services: `GET /health/external`

### Logging
- Structured JSON logging with structlog
- Log levels: DEBUG, INFO, WARNING, ERROR
- Centralized logging with ELK stack support

### Metrics
- Prometheus metrics endpoint: `/metrics`
- Custom metrics for threat detection
- Grafana dashboards for visualization

## 🔒 Security

### Data Protection
- All data encrypted at rest and in transit
- Customer data isolation
- GDPR compliance features
- Audit logging for all operations

### Access Control
- OAuth2 authentication
- Role-based access control (RBAC)
- API key management
- Session management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Guidelines
- Follow PEP 8 style guide
- Add type hints to all functions
- Write comprehensive docstrings
- Include unit tests for new features

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📚 Documentation

### **User Guides**
- **[User Guide](USER_GUIDE.md)** - Comprehensive setup and usage instructions
- **[Troubleshooting Guide](TROUBLESHOOTING.md)** - Common issues and solutions
- **[Cross-Platform Setup](CROSS_PLATFORM_SETUP.md)** - Platform-specific installation guides
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Production deployment instructions

### **Technical Documentation**
- **[Changelog](CHANGELOG.md)** - Version history and updates
- **[API Documentation](http://localhost:8000/docs)** - Interactive API documentation
- **[Implementation Guide](IMPLEMENTATION_GUIDE.md)** - Technical implementation details

### **Quick Reference**
- **Setup Scripts**: `setup_linux.sh`, `setup_windows.bat`
- **Start Scripts**: `start_privik.sh`, `start_privik_windows.bat`
- **Test Scripts**: `test_system.py`, `test_system_windows.bat`

## 🆘 Support

- **Documentation**: Check the guides above first
- **Issues**: [GitHub Issues](https://github.com/privik/privik/issues)
- **Discussions**: [GitHub Discussions](https://github.com/privik/privik/discussions)
- **Email**: support@privik.com

## 🎯 Roadmap

### MVP (6 Months)
- [x] Email ingestion and analysis
- [x] Link click tracking and analysis
- [x] File attachment sandboxing
- [x] Basic AI threat detection
- [x] SOC dashboard
- [ ] Email gateway integration
- [ ] Advanced ML models

### Future Features
- [ ] Threat emulation lab
- [ ] Automated phishing simulations
- [ ] Endpoint agent integration
- [ ] Cross-channel support (SMS, Slack)
- [ ] AI-generated threat reports
- [ ] Advanced user behavior analytics

---

**Built with ❤️ for a safer digital world**


