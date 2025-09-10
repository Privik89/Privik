#!/usr/bin/env python3
"""
Complete System Test for Privik Email Security Platform
Tests all components: API, email processing, threat detection, and integrations
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
from typing import Dict, Any, List


class PrivikSystemTester:
    """Comprehensive system tester for Privik platform"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
        self.test_results = {}
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all system tests"""
        print("🚀 Starting Privik Complete System Test")
        print("=" * 60)
        
        # Test 1: Health Check
        await self.test_health_check()
        
        # Test 2: Database Connection
        await self.test_database_connection()
        
        # Test 3: Email Gateway API
        await self.test_email_gateway_api()
        
        # Test 4: Email Processing Pipeline
        await self.test_email_processing_pipeline()
        
        # Test 5: Threat Detection
        await self.test_threat_detection()
        
        # Test 6: Zero-Trust Policies
        await self.test_zero_trust_policies()
        
        # Test 7: SOC Dashboard
        await self.test_soc_dashboard()
        
        # Test 8: Performance Test
        await self.test_performance()
        
        # Generate report
        return self.generate_test_report()
    
    async def test_health_check(self):
        """Test basic health check endpoints"""
        print("\n📋 Test 1: Health Check")
        print("-" * 30)
        
        try:
            # Test main health endpoint
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Main Health Check: {data.get('status', 'unknown')}")
                    self.test_results['health_check'] = {'status': 'PASS', 'data': data}
                else:
                    print(f"❌ Main Health Check: HTTP {response.status}")
                    self.test_results['health_check'] = {'status': 'FAIL', 'error': f'HTTP {response.status}'}
            
            # Test email gateway health
            async with self.session.get(f"{self.base_url}/api/email-gateway/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Email Gateway Health: {data.get('status', 'unknown')}")
                    self.test_results['email_gateway_health'] = {'status': 'PASS', 'data': data}
                else:
                    print(f"❌ Email Gateway Health: HTTP {response.status}")
                    self.test_results['email_gateway_health'] = {'status': 'FAIL', 'error': f'HTTP {response.status}'}
                    
        except Exception as e:
            print(f"❌ Health Check Error: {e}")
            self.test_results['health_check'] = {'status': 'ERROR', 'error': str(e)}
    
    async def test_database_connection(self):
        """Test database connectivity"""
        print("\n📋 Test 2: Database Connection")
        print("-" * 30)
        
        try:
            # Test by creating a test email
            test_email = {
                "message_id": f"test-{int(time.time())}",
                "subject": "Database Test Email",
                "sender": "test@example.com",
                "recipients": "user@company.com",
                "body_text": "This is a test email for database connectivity.",
                "content_type": "text/plain"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/ingest/email",
                json=test_email
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Database Connection: Email created with ID {data.get('email_id')}")
                    self.test_results['database_connection'] = {'status': 'PASS', 'email_id': data.get('email_id')}
                else:
                    error_text = await response.text()
                    print(f"❌ Database Connection: HTTP {response.status} - {error_text}")
                    self.test_results['database_connection'] = {'status': 'FAIL', 'error': f'HTTP {response.status}'}
                    
        except Exception as e:
            print(f"❌ Database Connection Error: {e}")
            self.test_results['database_connection'] = {'status': 'ERROR', 'error': str(e)}
    
    async def test_email_gateway_api(self):
        """Test email gateway API endpoints"""
        print("\n📋 Test 3: Email Gateway API")
        print("-" * 30)
        
        try:
            # Test gateway status
            async with self.session.get(f"{self.base_url}/api/email-gateway/status") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Gateway Status: Running={data.get('is_running')}, Integrations={data.get('integrations_connected')}")
                    self.test_results['gateway_status'] = {'status': 'PASS', 'data': data}
                else:
                    print(f"❌ Gateway Status: HTTP {response.status}")
                    self.test_results['gateway_status'] = {'status': 'FAIL', 'error': f'HTTP {response.status}'}
            
            # Test statistics
            async with self.session.get(f"{self.base_url}/api/email-gateway/statistics") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Gateway Statistics: Emails processed={data.get('emails_processed')}")
                    self.test_results['gateway_statistics'] = {'status': 'PASS', 'data': data}
                else:
                    print(f"❌ Gateway Statistics: HTTP {response.status}")
                    self.test_results['gateway_statistics'] = {'status': 'FAIL', 'error': f'HTTP {response.status}'}
                    
        except Exception as e:
            print(f"❌ Email Gateway API Error: {e}")
            self.test_results['email_gateway_api'] = {'status': 'ERROR', 'error': str(e)}
    
    async def test_email_processing_pipeline(self):
        """Test complete email processing pipeline"""
        print("\n📋 Test 4: Email Processing Pipeline")
        print("-" * 30)
        
        test_emails = [
            {
                "message_id": f"test-safe-{int(time.time())}",
                "subject": "Meeting Reminder",
                "sender": "colleague@company.com",
                "recipients": "user@company.com",
                "body_text": "Don't forget about our meeting tomorrow at 2 PM.",
                "source": "test"
            },
            {
                "message_id": f"test-phishing-{int(time.time())}",
                "subject": "URGENT: Verify Your Account",
                "sender": "security@fake-bank.com",
                "recipients": "user@company.com",
                "body_text": "Click here to verify your account: http://fake-bank.com/login",
                "source": "test"
            },
            {
                "message_id": f"test-bec-{int(time.time())}",
                "subject": "Wire Transfer Request",
                "sender": "ceo@company.com",
                "recipients": "finance@company.com",
                "body_text": "I need you to process a wire transfer for $50,000 immediately.",
                "source": "test"
            }
        ]
        
        for i, email in enumerate(test_emails, 1):
            try:
                async with self.session.post(
                    f"{self.base_url}/api/email-gateway/process",
                    json=email
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ Email {i} Processed: {data.get('action')} (threat_score: {data.get('threat_score', 0):.3f})")
                        self.test_results[f'email_processing_{i}'] = {'status': 'PASS', 'data': data}
                    else:
                        error_text = await response.text()
                        print(f"❌ Email {i} Processing: HTTP {response.status} - {error_text}")
                        self.test_results[f'email_processing_{i}'] = {'status': 'FAIL', 'error': f'HTTP {response.status}'}
                        
            except Exception as e:
                print(f"❌ Email {i} Processing Error: {e}")
                self.test_results[f'email_processing_{i}'] = {'status': 'ERROR', 'error': str(e)}
    
    async def test_threat_detection(self):
        """Test threat detection capabilities"""
        print("\n📋 Test 5: Threat Detection")
        print("-" * 30)
        
        try:
            # Test with a known phishing email
            phishing_email = {
                "message_id": f"test-phishing-detection-{int(time.time())}",
                "subject": "URGENT: Your Account Will Be Suspended",
                "sender": "noreply@suspicious-site.com",
                "recipients": "user@company.com",
                "body_text": "Your account will be suspended in 24 hours. Click here to verify: http://suspicious-site.com/verify",
                "source": "test"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/email-gateway/process",
                json=phishing_email
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    threat_score = data.get('threat_score', 0)
                    threat_type = data.get('threat_type', 'unknown')
                    indicators = data.get('indicators', [])
                    
                    print(f"✅ Threat Detection: {threat_type} (score: {threat_score:.3f})")
                    print(f"   Indicators: {', '.join(indicators)}")
                    
                    self.test_results['threat_detection'] = {
                        'status': 'PASS',
                        'threat_score': threat_score,
                        'threat_type': threat_type,
                        'indicators': indicators
                    }
                else:
                    error_text = await response.text()
                    print(f"❌ Threat Detection: HTTP {response.status} - {error_text}")
                    self.test_results['threat_detection'] = {'status': 'FAIL', 'error': f'HTTP {response.status}'}
                    
        except Exception as e:
            print(f"❌ Threat Detection Error: {e}")
            self.test_results['threat_detection'] = {'status': 'ERROR', 'error': str(e)}
    
    async def test_zero_trust_policies(self):
        """Test zero-trust policy enforcement"""
        print("\n📋 Test 6: Zero-Trust Policies")
        print("-" * 30)
        
        try:
            # Get current policies
            async with self.session.get(f"{self.base_url}/api/email-gateway/policies") as response:
                if response.status == 200:
                    policies = await response.json()
                    print(f"✅ Current Policies: Default action = {policies.get('default_action', 'unknown')}")
                    self.test_results['get_policies'] = {'status': 'PASS', 'data': policies}
                else:
                    print(f"❌ Get Policies: HTTP {response.status}")
                    self.test_results['get_policies'] = {'status': 'FAIL', 'error': f'HTTP {response.status}'}
            
            # Update policies
            policy_update = {
                "threat_thresholds": {
                    "block": 0.8,
                    "quarantine": 0.5,
                    "sandbox": 0.3
                },
                "suspicious_keywords": ["urgent", "verify", "suspended", "wire transfer"]
            }
            
            async with self.session.post(
                f"{self.base_url}/api/email-gateway/policies/update",
                json=policy_update
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Policy Update: {data.get('message', 'success')}")
                    self.test_results['update_policies'] = {'status': 'PASS', 'data': data}
                else:
                    error_text = await response.text()
                    print(f"❌ Policy Update: HTTP {response.status} - {error_text}")
                    self.test_results['update_policies'] = {'status': 'FAIL', 'error': f'HTTP {response.status}'}
                    
        except Exception as e:
            print(f"❌ Zero-Trust Policies Error: {e}")
            self.test_results['zero_trust_policies'] = {'status': 'ERROR', 'error': str(e)}
    
    async def test_soc_dashboard(self):
        """Test SOC dashboard endpoints"""
        print("\n📋 Test 7: SOC Dashboard")
        print("-" * 30)
        
        try:
            # Test SOC dashboard data
            async with self.session.get(f"{self.base_url}/api/soc/dashboard") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ SOC Dashboard: {len(data.get('recent_threats', []))} recent threats")
                    self.test_results['soc_dashboard'] = {'status': 'PASS', 'data': data}
                else:
                    print(f"❌ SOC Dashboard: HTTP {response.status}")
                    self.test_results['soc_dashboard'] = {'status': 'FAIL', 'error': f'HTTP {response.status}'}
            
            # Test threat intelligence
            async with self.session.get(f"{self.base_url}/api/soc/threat-intel") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ Threat Intelligence: {len(data.get('indicators', []))} indicators")
                    self.test_results['threat_intelligence'] = {'status': 'PASS', 'data': data}
                else:
                    print(f"❌ Threat Intelligence: HTTP {response.status}")
                    self.test_results['threat_intelligence'] = {'status': 'FAIL', 'error': f'HTTP {response.status}'}
                    
        except Exception as e:
            print(f"❌ SOC Dashboard Error: {e}")
            self.test_results['soc_dashboard'] = {'status': 'ERROR', 'error': str(e)}
    
    async def test_performance(self):
        """Test system performance"""
        print("\n📋 Test 8: Performance Test")
        print("-" * 30)
        
        try:
            # Test processing time for multiple emails
            start_time = time.time()
            test_emails = []
            
            for i in range(5):
                email = {
                    "message_id": f"perf-test-{i}-{int(time.time())}",
                    "subject": f"Performance Test Email {i}",
                    "sender": f"test{i}@example.com",
                    "recipients": "user@company.com",
                    "body_text": f"This is performance test email number {i}.",
                    "source": "performance_test"
                }
                test_emails.append(email)
            
            # Process emails concurrently
            tasks = []
            for email in test_emails:
                task = self.session.post(
                    f"{self.base_url}/api/email-gateway/process",
                    json=email
                )
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            end_time = time.time()
            total_time = end_time - start_time
            avg_time = total_time / len(test_emails)
            
            successful_requests = sum(1 for r in responses if not isinstance(r, Exception) and r.status == 200)
            
            print(f"✅ Performance Test: {successful_requests}/{len(test_emails)} emails processed")
            print(f"   Total time: {total_time:.2f}s, Average: {avg_time:.2f}s per email")
            
            self.test_results['performance'] = {
                'status': 'PASS',
                'total_time': total_time,
                'avg_time': avg_time,
                'successful_requests': successful_requests,
                'total_requests': len(test_emails)
            }
            
        except Exception as e:
            print(f"❌ Performance Test Error: {e}")
            self.test_results['performance'] = {'status': 'ERROR', 'error': str(e)}
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 TEST REPORT SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'PASS')
        failed_tests = sum(1 for result in self.test_results.values() if result['status'] == 'FAIL')
        error_tests = sum(1 for result in self.test_results.values() if result['status'] == 'ERROR')
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"⚠️  Errors: {error_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Detailed results
        print("\n📋 DETAILED RESULTS:")
        print("-" * 30)
        for test_name, result in self.test_results.items():
            status_icon = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "⚠️"
            print(f"{status_icon} {test_name}: {result['status']}")
            if result['status'] != 'PASS' and 'error' in result:
                print(f"   Error: {result['error']}")
        
        return {
            'summary': {
                'total_tests': total_tests,
                'passed': passed_tests,
                'failed': failed_tests,
                'errors': error_tests,
                'success_rate': (passed_tests/total_tests)*100
            },
            'results': self.test_results,
            'timestamp': datetime.utcnow().isoformat()
        }


async def main():
    """Main test function"""
    async with PrivikSystemTester() as tester:
        report = await tester.run_all_tests()
        
        # Save report to file
        with open('test_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: test_report.json")
        
        # Return exit code based on results
        if report['summary']['success_rate'] >= 80:
            print("\n🎉 System test PASSED! Privik is ready for production.")
            return 0
        else:
            print("\n⚠️  System test FAILED! Please review the issues above.")
            return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
