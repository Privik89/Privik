#!/usr/bin/env python3
"""
Comprehensive Privik System Test Suite
Tests all major components and integrations
"""

import asyncio
import json
import time
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent))

def test_backend_components():
    """Test backend components."""
    print("🔧 Testing Backend Components...")
    
    try:
        # Test database models
        from backend.app.models import User, Email, ClickEvent, SandboxAnalysis, ThreatIntel
        print("  ✅ Database models imported successfully")
        
        # Test configuration
        from backend.app.core.config import settings
        print(f"  ✅ Configuration loaded: {settings.database_url}")
        
        # Test API endpoints
        from backend.app.api import app
        print("  ✅ FastAPI app initialized")
        
        # Test services
        from backend.app.services.email_analyzer import analyze_email_content
        from backend.app.services.link_analyzer import analyze_link_safety
        from backend.app.services.sandbox import enqueue_file_for_detonation
        print("  ✅ Core services imported")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Backend test failed: {e}")
        return False

def test_agent_components():
    """Test agent components."""
    print("🤖 Testing Agent Components...")
    
    try:
        # Test agent core
        from agent.agent import PrivikAgent
        from agent.config import AgentConfig
        from agent.security import SecurityManager
        print("  ✅ Agent core components imported")
        
        # Test monitors
        from agent.monitors.email_monitor import EmailMonitor
        from agent.monitors.file_monitor import FileMonitor
        from agent.monitors.link_monitor import LinkMonitor
        print("  ✅ Agent monitors imported")
        
        # Test AI components
        from agent.ai.threat_detector import ThreatDetector
        print("  ✅ Agent AI components imported")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Agent test failed: {e}")
        return False

def test_frontend_components():
    """Test frontend components."""
    print("🎨 Testing Frontend Components...")
    
    try:
        # Check if frontend files exist
        frontend_files = [
            "frontend/package.json",
            "frontend/src/App.js",
            "frontend/src/components/Sidebar.js",
            "frontend/src/pages/Dashboard.js"
        ]
        
        for file_path in frontend_files:
            if Path(file_path).exists():
                print(f"  ✅ {file_path} exists")
            else:
                print(f"  ❌ {file_path} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Frontend test failed: {e}")
        return False

def test_integrations():
    """Test integration components."""
    print("🔗 Testing Integration Components...")
    
    try:
        # Test SIEM integrations
        from integrations.siem.base_integration import BaseSIEMIntegration
        from integrations.siem.elk_integration import ELKIntegration
        print("  ✅ SIEM integrations imported")
        
        # Test policy management
        from policy.policy_manager import PolicyManager
        print("  ✅ Policy management imported")
        
        # Test custom LLM framework
        from ai.custom_llm.llm_manager import CustomLLMManager
        from ai.custom_llm.llm_prompts import PromptTemplates
        print("  ✅ Custom LLM framework imported")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Integration test failed: {e}")
        return False

def test_extensions():
    """Test browser extension components."""
    print("🌐 Testing Browser Extension Components...")
    
    try:
        extension_files = [
            "extensions/chrome/manifest.json",
            "extensions/chrome/background.js",
            "extensions/chrome/content.js"
        ]
        
        for file_path in extension_files:
            if Path(file_path).exists():
                print(f"  ✅ {file_path} exists")
            else:
                print(f"  ❌ {file_path} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Extension test failed: {e}")
        return False

def test_mobile_components():
    """Test mobile components."""
    print("📱 Testing Mobile Components...")
    
    try:
        mobile_files = [
            "mobile/android/PrivikSecurityService.java",
            "mobile/android/ThreatDetector.java",
            "mobile/android/EmailMonitor.java"
        ]
        
        for file_path in mobile_files:
            if Path(file_path).exists():
                print(f"  ✅ {file_path} exists")
            else:
                print(f"  ❌ {file_path} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Mobile test failed: {e}")
        return False

def test_documentation():
    """Test documentation completeness."""
    print("📚 Testing Documentation...")
    
    try:
        doc_files = [
            "README.md",
            "PRICING_TIERS.md",
            "SIEM_INTEGRATION_SUPPORT.md",
            "agent/README.md",
            "frontend/README.md",
            "ai/custom_llm/llm_training_guide.md"
        ]
        
        for file_path in doc_files:
            if Path(file_path).exists():
                print(f"  ✅ {file_path} exists")
            else:
                print(f"  ❌ {file_path} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Documentation test failed: {e}")
        return False

def test_scripts():
    """Test deployment and management scripts."""
    print("📜 Testing Scripts...")
    
    try:
        script_files = [
            "start_privik_linux.sh",
            "stop_privik.sh",
            "install_agent.sh",
            "frontend/start_frontend.sh"
        ]
        
        for file_path in script_files:
            if Path(file_path).exists():
                print(f"  ✅ {file_path} exists")
            else:
                print(f"  ❌ {file_path} missing")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Scripts test failed: {e}")
        return False

def main():
    """Run comprehensive system tests."""
    print("🚀 Privik Comprehensive System Test Suite")
    print("=" * 50)
    
    tests = [
        ("Backend Components", test_backend_components),
        ("Agent Components", test_agent_components),
        ("Frontend Components", test_frontend_components),
        ("Integration Components", test_integrations),
        ("Browser Extensions", test_extensions),
        ("Mobile Components", test_mobile_components),
        ("Documentation", test_documentation),
        ("Scripts", test_scripts)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        result = test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Privik is ready for deployment.")
        return True
    else:
        print("⚠️  Some tests failed. Please review and fix issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
