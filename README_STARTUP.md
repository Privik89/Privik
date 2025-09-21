# 🚀 Privik Email Security Platform - Quick Start

## 🎯 **PERMANENT SOLUTION - No More Directory Issues!**

I've created startup scripts that handle all the directory navigation automatically. **No more manual directory changes needed!**

## 📋 **Three Easy Ways to Start the Platform:**

### **Option 1: Start Both Servers at Once (RECOMMENDED)**
Double-click on either:
- `start_both.bat` (Windows Batch)
- `start_both.ps1` (PowerShell)

This will automatically:
- Start the backend server in one window
- Start the frontend server in another window
- Handle all directory navigation automatically

### **Option 2: Start Servers Individually**
- **Backend only**: Double-click `start_backend.bat`
- **Frontend only**: Double-click `start_frontend.bat`

### **Option 3: Manual Commands (if you prefer)**
If you still want to use manual commands, here they are:

**Backend:**
```powershell
cd C:\Users\USER\Desktop\PRIVIK_EMAIL_GATEWAY\Privik
.\venv\Scripts\Activate.ps1
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```powershell
cd C:\Users\USER\Desktop\PRIVIK_EMAIL_GATEWAY\Privik\frontend
npm start
```

## 🌐 **Access URLs:**
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## ✅ **What the Scripts Do:**
1. **Automatically navigate to correct directories**
2. **Activate virtual environment**
3. **Start servers with proper configuration**
4. **Open separate windows for each server**
5. **Display helpful URLs and status**

## 🔧 **Troubleshooting:**
- If scripts don't work, make sure you're running them from the project root directory
- If you get permission errors, right-click and "Run as Administrator"
- If PowerShell scripts don't work, use the `.bat` files instead

## 🎉 **That's It!**
No more directory navigation issues. Just double-click and go!
