#!/usr/bin/env python3
"""
Privik System Test Script
Tests all components on Linux system
"""

import asyncio
import sys
import os
import subprocess
import json
import time
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent / "backend"))

async def test_dependencies():
    """Test if all required dependencies are installed"""
    print("🔍 Testing Dependencies...")
    
    required_packages = [
        'fastapi', 'uvicorn', 'sqlalchemy', 'pandas', 'numpy', 
        'scikit-learn', 'joblib', 'structlog', 'aiohttp', 'playwright'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ All dependencies installed")
    return True

async def test_playwright():
    """Test Playwright browser installation"""
    print("\n🔍 Testing Playwright...")
    
    try:
        from playwright.async_api import async_playwright
        
        # Test if Chromium is installed
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://example.com")
        title = await page.title()
        await browser.close()
        await playwright.stop()
        
        print("  ✅ Playwright Chromium working")
        return True
        
    except Exception as e:
        print(f"  ❌ Playwright error: {e}")
        print("  Install with: playwright install chromium")
        return False

async def test_database():
    """Test database connection"""
    print("\n🔍 Testing Database...")
    
    try:
        from backend.app.database import create_tables, SessionLocal
        
        # Test table creation
        create_tables()
        print("  ✅ Database tables created")
        
        # Test connection
        db = SessionLocal()
        db.close()
        print("  ✅ Database connection working")
        return True
        
    except Exception as e:
        print(f"  ❌ Database error: {e}")
        return False

async def test_ai_models():
    """Test AI model initialization"""
    print("\n🔍 Testing AI Models...")
    
    try:
        from backend.app.services.ai_threat_detection import AIThreatDetection
        
        config = {
            'model_storage_path': './models',
            'retrain_interval': 7,
            'min_training_samples': 1000
        }
        
        ai_detection = AIThreatDetection(config)
        await ai_detection.initialize()
        print("  ✅ AI models initialized")
        
        # Test prediction
        email_data = {
            'subject': 'Test email',
            'body_text': 'This is a test email',
            'sender': 'test@example.com'
        }
        
        prediction = await ai_detection.predict_email_threat(email_data)
        print(f"  ✅ Email prediction working: {prediction.threat_type}")
        
        await ai_detection.cleanup()
        return True
        
    except Exception as e:
        print(f"  ❌ AI models error: {e}")
        return False

async def test_sandbox():
    """Test sandbox functionality"""
    print("\n🔍 Testing Sandbox...")
    
    try:
        from backend.app.services.real_time_sandbox import RealTimeSandbox
        
        config = {
            'max_concurrent_sandboxes': 5,
            'sandbox_timeout': 30
        }
        
        sandbox = RealTimeSandbox(config)
        await sandbox.initialize()
        print("  ✅ Sandbox initialized")
        
        # Test link analysis
        result = await sandbox.analyze_link_click("https://example.com", {})
        print(f"  ✅ Link analysis working: {result.verdict}")
        
        await sandbox.cleanup()
        return True
        
    except Exception as e:
        print(f"  ❌ Sandbox error: {e}")
        return False

async def test_email_gateway():
    """Test email gateway"""
    print("\n🔍 Testing Email Gateway...")
    
    try:
        from backend.app.services.email_gateway import EmailGateway
        
        config = {
            'link_rewrite_domain': 'links.privik.com',
            'attachment_storage': '/tmp/attachments',
            'zero_trust_policies': {
                'internal_domains': ['company.com'],
                'high_risk_users': ['ceo@company.com']
            }
        }
        
        gateway = EmailGateway(config)
        await gateway.initialize()
        print("  ✅ Email gateway initialized")
        
        # Test email processing
        email_data = {
            'message_id': 'test-123',
            'subject': 'Test email',
            'sender': 'test@example.com',
            'recipients': ['user@company.com'],
            'body_text': 'Test content'
        }
        
        result = await gateway.process_incoming_email(email_data)
        print(f"  ✅ Email processing working: {result['status']}")
        
        await gateway.cleanup()
        return True
        
    except Exception as e:
        print(f"  ❌ Email gateway error: {e}")
        return False

async def test_zero_trust_orchestrator():
    """Test zero-trust orchestrator"""
    print("\n🔍 Testing Zero-Trust Orchestrator...")
    
    try:
        from backend.app.services.zero_trust_orchestrator import ZeroTrustOrchestrator
        
        config = {
            'email_gateway': {
                'link_rewrite_domain': 'links.privik.com',
                'attachment_storage': '/tmp/attachments',
                'zero_trust_policies': {
                    'internal_domains': ['company.com'],
                    'high_risk_users': ['ceo@company.com']
                }
            },
            'sandbox': {
                'max_concurrent_sandboxes': 5,
                'sandbox_timeout': 30
            },
            'ai_detection': {
                'model_storage_path': './models',
                'retrain_interval': 7,
                'min_training_samples': 1000
            }
        }
        
        orchestrator = ZeroTrustOrchestrator(config)
        await orchestrator.initialize()
        print("  ✅ Zero-trust orchestrator initialized")
        
        # Test email processing
        email_data = {
            'message_id': 'test-123',
            'subject': 'Test email',
            'sender': 'test@example.com',
            'recipients': ['user@company.com'],
            'body_text': 'Test content'
        }
        
        result = await orchestrator.process_email(email_data)
        print(f"  ✅ Email processing working: {result.action}")
        
        # Test statistics
        stats = await orchestrator.get_statistics()
        print(f"  ✅ Statistics working: {stats.get('total_processed', 0)} processed")
        
        await orchestrator.cleanup()
        return True
        
    except Exception as e:
        print(f"  ❌ Zero-trust orchestrator error: {e}")
        return False

async def test_api_endpoints():
    """Test API endpoints"""
    print("\n🔍 Testing API Endpoints...")
    
    try:
        import requests
        import time
        
        # Start the server in background
        print("  Starting server...")
        server_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "backend.app.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ], cwd=Path(__file__).parent)
        
        # Wait for server to start
        time.sleep(5)
        
        # Test health endpoint
        try:
            response = requests.get("http://localhost:8000/health", timeout=10)
            if response.status_code == 200:
                print("  ✅ Health endpoint working")
            else:
                print(f"  ❌ Health endpoint error: {response.status_code}")
                return False
        except Exception as e:
            print(f"  ❌ Health endpoint error: {e}")
            return False
        
        # Test zero-trust endpoint
        try:
            test_data = {
                "message_id": "test-123",
                "subject": "Test email",
                "sender": "test@example.com",
                "recipients": ["user@company.com"],
                "body_text": "Test content"
            }
            
            response = requests.post(
                "http://localhost:8000/api/zero-trust/email/process",
                json=test_data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"  ✅ Zero-trust endpoint working: {result['action']}")
            else:
                print(f"  ❌ Zero-trust endpoint error: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"  ❌ Zero-trust endpoint error: {e}")
            return False
        
        # Stop server
        server_process.terminate()
        server_process.wait()
        
        return True
        
    except Exception as e:
        print(f"  ❌ API testing error: {e}")
        return False

async def test_file_permissions():
    """Test file permissions and directories"""
    print("\n🔍 Testing File Permissions...")
    
    try:
        # Test model directory
        model_dir = Path("./models")
        model_dir.mkdir(exist_ok=True)
        print("  ✅ Models directory created")
        
        # Test attachment directory
        attachment_dir = Path("/tmp/attachments")
        attachment_dir.mkdir(exist_ok=True)
        print("  ✅ Attachment directory created")
        
        # Test write permissions
        test_file = model_dir / "test.txt"
        test_file.write_text("test")
        test_file.unlink()
        print("  ✅ Write permissions working")
        
        return True
        
    except Exception as e:
        print(f"  ❌ File permissions error: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Privik System Test - Linux Compatibility Check")
    print("=" * 60)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("File Permissions", test_file_permissions),
        ("Playwright", test_playwright),
        ("Database", test_database),
        ("AI Models", test_ai_models),
        ("Sandbox", test_sandbox),
        ("Email Gateway", test_email_gateway),
        ("Zero-Trust Orchestrator", test_zero_trust_orchestrator),
        ("API Endpoints", test_api_endpoints),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results[test_name] = result
        except Exception as e:
            print(f"  ❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(tests)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System is ready for deployment.")
        return 0
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
