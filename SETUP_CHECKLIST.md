# 🚀 Privik Setup Checklist

## ❌ **CRITICAL ISSUES TO FIX FIRST**

### 1. **Backend Import Errors** 🔴
- **Problem**: `ImportError: cannot import name 'SandboxService' from 'backend.app.services.sandbox'`
- **Status**: ❌ **BLOCKING** - Backend won't start
- **Fix Needed**: The `sandbox.py` file doesn't have a `SandboxService` class

### 2. **Database Not Initialized** 🔴
- **Problem**: Database tables don't exist
- **Status**: ❌ **BLOCKING** - All database operations will fail
- **Fix Needed**: Run database initialization

### 3. **Missing Dependencies** 🔴
- **Problem**: Some services reference non-existent classes
- **Status**: ❌ **BLOCKING** - Import errors prevent startup

---

## 📋 **COMPLETE SETUP CHECKLIST**

### **Phase 1: Fix Critical Errors** 🔴

#### **1.1 Fix Backend Import Issues**
- [ ] **Fix SandboxService import error**
  - Either create `SandboxService` class in `sandbox.py`
  - Or remove the import from `email_gateway_service.py`
- [ ] **Fix any other missing class imports**
- [ ] **Test backend startup** - `./venv/bin/python -m uvicorn backend.app.main:app --reload`

#### **1.2 Initialize Database**
- [ ] **Create database tables**
  - Run: `./venv/bin/python -c "from backend.app.database import create_tables; create_tables()"`
- [ ] **Verify database file exists** - `ls -la privik.db`
- [ ] **Test database connection**

#### **1.3 Fix Service Dependencies**
- [ ] **Check all service imports**
- [ ] **Fix missing class references**
- [ ] **Ensure all services can be imported**

### **Phase 2: Core Infrastructure** 🟡

#### **2.1 Database Setup**
- [ ] **Choose database type**:
  - [ ] SQLite (for development) - ✅ Already configured
  - [ ] PostgreSQL (for production) - Requires Docker setup
- [ ] **Create database schema**
- [ ] **Test database operations**

#### **2.2 Email Service Integrations**
- [ ] **Configure Gmail API** (optional):
  - [ ] Get Gmail API credentials
  - [ ] Set `GMAIL_CLIENT_ID` and `GMAIL_CLIENT_SECRET` environment variables
- [ ] **Configure Microsoft 365** (optional):
  - [ ] Get O365 API credentials
  - [ ] Set `O365_CLIENT_ID` and `O365_CLIENT_SECRET` environment variables
- [ ] **Configure IMAP** (optional):
  - [ ] Set IMAP server details in config

#### **2.3 AI/ML Models** (You're handling this)
- [ ] **Implement real AI models** (your responsibility)
- [ ] **Train models with real data**
- [ ] **Test model predictions**

### **Phase 3: External Services** 🟡

#### **3.1 Object Storage (MinIO)**
- [ ] **Start MinIO service**:
  ```bash
  docker run -p 9000:9000 -p 9001:9001 \
    -e MINIO_ROOT_USER=minioadmin \
    -e MINIO_ROOT_PASSWORD=minioadmin \
    minio/minio server /data --console-address ":9001"
  ```
- [ ] **Test MinIO connection**
- [ ] **Create buckets for file storage**

#### **3.2 Redis (for queues)**
- [ ] **Start Redis service**:
  ```bash
  docker run -p 6379:6379 redis:7-alpine
  ```
- [ ] **Test Redis connection**

#### **3.3 PostgreSQL (for production)**
- [ ] **Start PostgreSQL**:
  ```bash
  docker run -p 5432:5432 \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=postgres \
    -e POSTGRES_DB=privik \
    postgres:16
  ```
- [ ] **Update database URL** to use PostgreSQL

### **Phase 4: Frontend Setup** 🟡

#### **4.1 Frontend Dependencies**
- [ ] **Install Node.js dependencies**:
  ```bash
  cd frontend
  npm install
  ```
- [ ] **Verify React app starts**:
  ```bash
  cd frontend
  npm start
  ```

#### **4.2 Frontend Configuration**
- [ ] **Configure API endpoints**
- [ ] **Test frontend-backend communication**
- [ ] **Verify dashboard loads**

### **Phase 5: Testing & Validation** 🟢

#### **5.1 Basic System Test**
- [ ] **Test backend health endpoint**: `curl http://localhost:8000/health`
- [ ] **Test frontend loads**: `http://localhost:3000`
- [ ] **Test API documentation**: `http://localhost:8000/docs`

#### **5.2 Email Processing Test**
- [ ] **Test email ingestion API**
- [ ] **Test threat detection pipeline**
- [ ] **Test zero-trust policies**

#### **5.3 Integration Tests**
- [ ] **Test email service integrations** (if configured)
- [ ] **Test sandbox functionality**
- [ ] **Test SOC dashboard**

---

## 🚀 **QUICK START (Minimal Setup)**

### **Step 1: Fix Critical Errors**
```bash
# 1. Fix the SandboxService import issue
# Edit backend/app/services/email_gateway_service.py
# Remove or comment out: from .sandbox import SandboxService

# 2. Initialize database
./venv/bin/python -c "from backend.app.database import create_tables; create_tables()"

# 3. Test backend startup
./venv/bin/python -m uvicorn backend.app.main:app --reload
```

### **Step 2: Start Frontend**
```bash
cd frontend
npm install
npm start
```

### **Step 3: Basic Test**
```bash
# Test backend
curl http://localhost:8000/health

# Test frontend
# Open http://localhost:3000 in browser
```

---

## 🔧 **CONFIGURATION FILES NEEDED**

### **Environment Variables (.env)**
```bash
# Database
DATABASE_URL=sqlite:///./privik.db

# Email Integrations (optional)
GMAIL_CLIENT_ID=your_gmail_client_id
GMAIL_CLIENT_SECRET=your_gmail_client_secret
O365_CLIENT_ID=your_o365_client_id
O365_CLIENT_SECRET=your_o365_client_secret

# AI/ML (optional)
OPENAI_API_KEY=your_openai_key
VIRUSTOTAL_API_KEY=your_virustotal_key

# Security
SECRET_KEY=your_secret_key_here
```

### **Docker Compose (for full setup)**
```yaml
# Use the existing docker-compose.yml
# Start with: docker-compose up -d
```

---

## 📊 **CURRENT STATUS**

| Component | Status | Notes |
|-----------|--------|-------|
| Backend API | ❌ **BROKEN** | Import errors prevent startup |
| Database | ❌ **NOT SETUP** | Tables don't exist |
| Frontend | ⚠️ **PARTIAL** | Dependencies not installed |
| Email Integrations | ⚠️ **NOT CONFIGURED** | Optional, but not set up |
| AI Models | ⚠️ **PLACEHOLDER** | You're implementing real ones |
| Sandbox | ⚠️ **INCOMPLETE** | Missing SandboxService class |
| SOC Dashboard | ⚠️ **NOT TESTED** | Depends on other components |

---

## 🎯 **PRIORITY ORDER**

1. **🔴 CRITICAL**: Fix backend import errors
2. **🔴 CRITICAL**: Initialize database
3. **🟡 HIGH**: Install frontend dependencies
4. **🟡 HIGH**: Test basic functionality
5. **🟢 MEDIUM**: Configure email integrations
6. **🟢 MEDIUM**: Set up external services
7. **🟢 LOW**: Full system testing

---

## 💡 **RECOMMENDATIONS**

### **For Development**
- Start with SQLite database (already configured)
- Fix import errors first
- Test basic API functionality
- Add integrations gradually

### **For Production**
- Use PostgreSQL database
- Set up proper environment variables
- Configure email service integrations
- Implement real AI models
- Set up monitoring and logging

---

**Next Steps**: Start with Phase 1 to fix the critical errors, then move through the phases systematically.
