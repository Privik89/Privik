"""
End-to-end testing scenarios
"""

import pytest
import time
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock


class TestEmailSecurityWorkflow:
    """End-to-end tests for email security workflow"""
    
    def test_malicious_email_detection_workflow(self, client):
        """Test complete workflow for malicious email detection."""
        # Step 1: Submit malicious email
        malicious_email = {
            "message_id": "malicious_123",
            "subject": "URGENT: Verify Your Account Now!",
            "sender": "noreply@suspicious-bank.com",
            "recipient": "user@company.com",
            "body": "Your account will be closed in 24 hours. Click here to verify: https://fake-bank.com/verify",
            "headers": {
                "From": "noreply@suspicious-bank.com",
                "To": "user@company.com",
                "Subject": "URGENT: Verify Your Account Now!"
            },
            "attachments": [],
            "links": ["https://fake-bank.com/verify"]
        }
        
        with patch('app.services.email_gateway_service.EmailGatewayService.process_email') as mock_process:
            mock_process.return_value = {
                "message_id": malicious_email["message_id"],
                "threat_score": 0.95,
                "verdict": "malicious",
                "indicators": ["urgent_language", "suspicious_domain", "phishing_attempt"],
                "action": "quarantine"
            }
            
            # Process email
            response = client.post(
                "/api/email-gateway/process",
                json=malicious_email,
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result["verdict"] == "malicious"
            assert result["threat_score"] > 0.9
        
        # Step 2: Check if incident was created
        with patch('app.services.sandbox_poller.SandboxPoller.get_incidents') as mock_incidents:
            mock_incidents.return_value = [
                {
                    "incident_id": "inc_123",
                    "threat_type": "phishing",
                    "severity": "high",
                    "email_id": malicious_email["message_id"],
                    "timestamp": datetime.now().isoformat(),
                    "status": "investigating"
                }
            ]
            
            response = client.get(
                "/api/soc/incidents",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            incidents = response.json()
            assert len(incidents) > 0
            assert incidents[0]["threat_type"] == "phishing"
        
        # Step 3: Verify webhook was triggered
        with patch('app.services.webhook_system.WebhookSystem.trigger_webhook') as mock_webhook:
            mock_webhook.return_value = {
                "success": True,
                "event_type": "email_threat_detected",
                "subscribed_webhooks": 2
            }
            
            # This would typically be triggered automatically
            response = client.post(
                "/api/webhooks/trigger/email_threat_detected",
                json={
                    "email_id": malicious_email["message_id"],
                    "threat_type": "phishing",
                    "threat_score": 0.95
                },
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            webhook_result = response.json()
            assert webhook_result["success"] is True
    
    def test_attachment_analysis_workflow(self, client):
        """Test complete workflow for attachment analysis."""
        # Step 1: Submit email with suspicious attachment
        email_with_attachment = {
            "message_id": "attachment_123",
            "subject": "Invoice for Payment",
            "sender": "billing@fake-company.com",
            "recipient": "user@company.com",
            "body": "Please find attached invoice for payment.",
            "headers": {"From": "billing@fake-company.com"},
            "attachments": [
                {
                    "filename": "invoice.pdf",
                    "content_type": "application/pdf",
                    "size": 1024000,
                    "file_path": "/tmp/suspicious_invoice.pdf"
                }
            ],
            "links": []
        }
        
        with patch('app.services.email_gateway_service.EmailGatewayService.process_email') as mock_process:
            mock_process.return_value = {
                "message_id": email_with_attachment["message_id"],
                "threat_score": 0.7,
                "verdict": "suspicious",
                "indicators": ["suspicious_attachment"],
                "action": "quarantine_for_analysis"
            }
            
            response = client.post(
                "/api/email-gateway/process",
                json=email_with_attachment,
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            result = response.json()
            assert result["action"] == "quarantine_for_analysis"
        
        # Step 2: Submit attachment for sandbox analysis
        with patch('app.services.real_time_sandbox.RealTimeSandbox.analyze_attachment') as mock_analyze:
            mock_analyze.return_value = {
                "analysis_id": "analysis_123",
                "verdict": "malicious",
                "threat_score": 0.95,
                "malware_family": "Trojan.Generic",
                "behavior_indicators": ["suspicious_network_activity", "file_encryption"]
            }
            
            response = client.post(
                "/api/sandbox/detonate-test",
                json={"file_path": "/tmp/suspicious_invoice.pdf"},
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            analysis_result = response.json()
            assert analysis_result["verdict"] == "malicious"
        
        # Step 3: Check sandbox status
        with patch('app.services.real_time_sandbox.RealTimeSandbox.get_status') as mock_status:
            mock_status.return_value = {
                "status": "active",
                "active_analyses": 1,
                "completed_analyses": 100,
                "failed_analyses": 2
            }
            
            response = client.get(
                "/api/sandbox/status",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            status = response.json()
            assert status["status"] == "active"
    
    def test_user_behavior_anomaly_workflow(self, client):
        """Test complete workflow for user behavior anomaly detection."""
        # Step 1: Update user behavior (simulate suspicious activity)
        behavior_events = [
            {
                "user_id": "user_123",
                "event_type": "email_received",
                "data": {"email_count": 1}
            },
            {
                "user_id": "user_123",
                "event_type": "link_clicked",
                "data": {"suspicious": True, "url": "https://malicious-site.com"}
            },
            {
                "user_id": "user_123",
                "event_type": "link_clicked",
                "data": {"suspicious": True, "url": "https://phishing-site.com"}
            }
        ]
        
        for event in behavior_events:
            with patch('app.services.behavioral_analysis.BehavioralAnalyzer.update_user_behavior') as mock_update:
                mock_update.return_value = None
                
                response = client.post(
                    "/api/ai-ml/behavior/update",
                    json={"user_id": event["user_id"], "behavior_event": event},
                    headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
                )
                
                assert response.status_code == 200
        
        # Step 2: Detect behavioral anomalies
        with patch('app.services.behavioral_analysis.BehavioralAnalyzer.detect_behavioral_anomalies') as mock_detect:
            mock_detect.return_value = {
                "anomalies": [
                    {
                        "user_id": "user_123",
                        "anomaly_score": 0.85,
                        "risk_level": "high",
                        "metrics": {
                            "suspicious_click_rate": 0.8,
                            "emails_per_day": 200,
                            "time_variance": 15.2
                        }
                    }
                ],
                "total_users_analyzed": 100
            }
            
            response = client.get(
                "/api/ai-ml/behavior/anomalies",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            anomalies = response.json()
            assert len(anomalies["anomalies"]) > 0
            assert anomalies["anomalies"][0]["risk_level"] == "high"
        
        # Step 3: Get user risk prediction
        with patch('app.services.behavioral_analysis.BehavioralAnalyzer.predict_user_risk') as mock_predict:
            mock_predict.return_value = {
                "user_id": "user_123",
                "risk_level": "high",
                "anomaly_score": 0.85,
                "risk_factors": [
                    "High suspicious link click rate (80%)",
                    "Unusually high email volume (200 emails/day)",
                    "Unusual activity timing patterns (variance: 15.2)"
                ],
                "last_updated": datetime.now().isoformat()
            }
            
            response = client.get(
                "/api/ai-ml/behavior/user/user_123/risk",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            risk_prediction = response.json()
            assert risk_prediction["risk_level"] == "high"
            assert len(risk_prediction["risk_factors"]) > 0


class TestThreatHuntingWorkflow:
    """End-to-end tests for threat hunting workflow"""
    
    def test_threat_hunting_campaign_workflow(self, client):
        """Test complete threat hunting campaign workflow."""
        # Step 1: Start threat hunting campaign
        with patch('app.services.threat_hunting.ThreatHunter.run_threat_hunting_campaign') as mock_campaign:
            mock_campaign.return_value = {
                "campaign_id": "campaign_123",
                "campaign_name": "E2E Test Campaign",
                "findings": [
                    {
                        "type": "suspicious_email",
                        "title": "Suspicious Email: Phishing Attempt",
                        "description": "Email from phishing@malicious.com with phishing verdict",
                        "evidence": {
                            "email_id": "email_123",
                            "sender": "phishing@malicious.com",
                            "threat_score": 0.95
                        },
                        "confidence": 0.95,
                        "recommended_action": "quarantine_and_investigate"
                    },
                    {
                        "type": "domain_reputation_drop",
                        "title": "Domain Reputation Drop: malicious-domain.com",
                        "description": "Reputation dropped from 0.65 to 0.15",
                        "evidence": {
                            "domain": "malicious-domain.com",
                            "current_reputation": 0.15,
                            "previous_reputation": 0.65
                        },
                        "confidence": 0.8,
                        "recommended_action": "block_domain_and_investigate"
                    }
                ],
                "threat_indicators": [
                    {
                        "type": "email_address",
                        "value": "phishing@malicious.com",
                        "confidence": 0.95,
                        "source": "suspicious_email_patterns"
                    },
                    {
                        "type": "domain",
                        "value": "malicious-domain.com",
                        "confidence": 0.8,
                        "source": "domain_reputation_drop"
                    }
                ],
                "recommendations": [
                    {
                        "priority": "high",
                        "action": "immediate_response",
                        "description": "Take immediate action on 2 critical findings",
                        "steps": [
                            "Review critical findings immediately",
                            "Implement blocking measures",
                            "Notify security team"
                        ]
                    }
                ]
            }
            
            response = client.post(
                "/api/ai-ml/threat-hunting/campaign?campaign_name=E2E%20Test%20Campaign&time_range=7",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            campaign_result = response.json()
            assert campaign_result["campaign_id"] == "campaign_123"
            assert len(campaign_result["findings"]) > 0
            assert len(campaign_result["threat_indicators"]) > 0
        
        # Step 2: Get threat hunting campaigns
        with patch('app.services.threat_hunting.ThreatHunter.get_hunting_campaigns') as mock_campaigns:
            mock_campaigns.return_value = [
                {
                    "campaign_id": "campaign_123",
                    "campaign_name": "E2E Test Campaign",
                    "start_time": datetime.now().isoformat(),
                    "findings_count": 2,
                    "status": "completed"
                }
            ]
            
            response = client.get(
                "/api/ai-ml/threat-hunting/campaigns?limit=10",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            campaigns = response.json()
            assert len(campaigns["campaigns"]) > 0
            assert campaigns["campaigns"][0]["campaign_name"] == "E2E Test Campaign"
        
        # Step 3: Get threat hunting rules
        with patch('app.services.threat_hunting.ThreatHunter.hunting_rules') as mock_rules:
            mock_rules.return_value = {
                "suspicious_email_patterns": {
                    "id": "suspicious_email_patterns",
                    "name": "Suspicious Email Patterns",
                    "category": "email_analysis",
                    "description": "Detect emails with suspicious patterns",
                    "severity": "high",
                    "enabled": True
                }
            }
            
            response = client.get(
                "/api/ai-ml/threat-hunting/rules",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            rules = response.json()
            assert len(rules["rules"]) > 0


class TestComplianceWorkflow:
    """End-to-end tests for compliance workflow"""
    
    def test_compliance_report_generation_workflow(self, client):
        """Test complete compliance report generation workflow."""
        # Step 1: Generate compliance report
        with patch('app.services.compliance_reporting.ComplianceReportGenerator.generate_compliance_report') as mock_report:
            mock_report.return_value = {
                "report_metadata": {
                    "framework": "soc2_type_ii",
                    "framework_name": "SOC 2 Type II",
                    "report_id": "soc2_report_20240115_143022",
                    "generated_at": datetime.now().isoformat(),
                    "reporting_period": {
                        "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
                        "end_date": datetime.now().isoformat()
                    },
                    "compliance_score": 0.92
                },
                "executive_summary": {
                    "overall_score": 0.92,
                    "score_interpretation": "Excellent - Fully compliant with minor improvements needed",
                    "key_highlights": [
                        "Compliance score: 92%",
                        "Strong security controls implementation",
                        "Effective incident response procedures"
                    ],
                    "areas_of_strength": [
                        "Access control management",
                        "Data encryption and protection",
                        "Security monitoring and alerting"
                    ],
                    "improvement_areas": [
                        "Vendor risk management",
                        "Business continuity planning"
                    ]
                },
                "report_sections": {
                    "control_activities": {
                        "access_controls": {
                            "description": "User access management and authentication controls",
                            "implementation_status": "fully_implemented",
                            "effectiveness": "high"
                        }
                    }
                },
                "recommendations": [
                    {
                        "category": "access_controls",
                        "priority": "medium",
                        "recommendation": "Implement automated access provisioning",
                        "rationale": "Reduce manual errors and ensure timely access management"
                    }
                ]
            }
            
            response = client.post(
                "/api/compliance/reports/generate",
                json={
                    "framework": "soc2_type_ii",
                    "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
                    "end_date": datetime.now().isoformat(),
                    "include_recommendations": True
                },
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            report = response.json()
            assert report["report_metadata"]["compliance_score"] == 0.92
            assert len(report["recommendations"]) > 0


class TestIntegrationWorkflow:
    """End-to-end tests for integration workflows"""
    
    def test_siem_integration_workflow(self, client):
        """Test complete SIEM integration workflow."""
        # Step 1: Establish SIEM connection
        with patch('app.services.enhanced_siem_integration.EnhancedSIEMIntegration.establish_siem_connection') as mock_connect:
            mock_connect.return_value = {
                "success": True,
                "connection_id": "splunk_conn_123",
                "provider": "splunk",
                "established_at": datetime.now().isoformat()
            }
            
            response = client.post(
                "/api/siem/connect",
                json={
                    "provider": "splunk",
                    "host": "splunk.company.com",
                    "port": 8089,
                    "token": "splunk_token_123"
                },
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            connection_result = response.json()
            assert connection_result["success"] is True
            assert connection_result["connection_id"] == "splunk_conn_123"
        
        # Step 2: Stream event to SIEM
        with patch('app.services.enhanced_siem_integration.EnhancedSIEMIntegration.stream_event_to_siem') as mock_stream:
            mock_stream.return_value = {
                "success": True,
                "event_id": "event_123",
                "streamed_to": 1,
                "total_targets": 1,
                "results": {
                    "splunk_conn_123": {
                        "success": True,
                        "provider": "splunk",
                        "response_time": 120
                    }
                }
            }
            
            event_data = {
                "event_type": "email_threat_detected",
                "timestamp": datetime.now().isoformat(),
                "data": {
                    "email_id": "email_123",
                    "threat_type": "phishing",
                    "threat_score": 0.95
                }
            }
            
            response = client.post(
                "/api/siem/stream-event",
                json={
                    "event_data": event_data,
                    "connection_ids": ["splunk_conn_123"]
                },
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            stream_result = response.json()
            assert stream_result["success"] is True
            assert stream_result["streamed_to"] == 1
        
        # Step 3: Get SIEM connections
        with patch('app.services.enhanced_siem_integration.EnhancedSIEMIntegration.get_siem_connections') as mock_connections:
            mock_connections.return_value = [
                {
                    "connection_id": "splunk_conn_123",
                    "provider": "splunk",
                    "provider_name": "Splunk Enterprise Security",
                    "status": "active",
                    "established_at": datetime.now().isoformat(),
                    "events_sent": 150
                }
            ]
            
            response = client.get(
                "/api/siem/connections",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            connections = response.json()
            assert len(connections) > 0
            assert connections[0]["status"] == "active"
    
    def test_ldap_integration_workflow(self, client):
        """Test complete LDAP integration workflow."""
        # Step 1: Configure LDAP server
        with patch('app.services.ldap_auth.LDAPAuthService.configure_ldap_server') as mock_configure:
            mock_configure.return_value = {
                "success": True,
                "server_id": "ldap_server_123",
                "server_name": "Company AD",
                "configured_at": datetime.now().isoformat()
            }
            
            ldap_config = {
                "server_name": "Company AD",
                "server_host": "ldap.company.com",
                "server_type": "active_directory",
                "port": 389,
                "use_ssl": False,
                "use_tls": True,
                "bind_dn": "CN=admin,DC=company,DC=com",
                "bind_password": "admin_password",
                "user_search_base": "CN=Users,DC=company,DC=com",
                "domain": "company.com"
            }
            
            response = client.post(
                "/api/ldap/configure",
                json=ldap_config,
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            config_result = response.json()
            assert config_result["success"] is True
            assert config_result["server_id"] == "ldap_server_123"
        
        # Step 2: Authenticate user via LDAP
        with patch('app.services.ldap_auth.LDAPAuthService.authenticate_user') as mock_auth:
            mock_auth.return_value = {
                "success": True,
                "username": "john.doe",
                "user_details": {
                    "cn": "John Doe",
                    "mail": "john.doe@company.com",
                    "department": "IT"
                },
                "user_groups": ["IT_Users", "Email_Users"],
                "server_id": "ldap_server_123"
            }
            
            response = client.post(
                "/api/ldap/authenticate",
                json={
                    "username": "john.doe",
                    "password": "user_password",
                    "server_id": "ldap_server_123"
                },
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            auth_result = response.json()
            assert auth_result["success"] is True
            assert auth_result["username"] == "john.doe"
            assert len(auth_result["user_groups"]) > 0
        
        # Step 3: Search users in LDAP
        with patch('app.services.ldap_auth.LDAPAuthService.search_users') as mock_search:
            mock_search.return_value = [
                {
                    "cn": "John Doe",
                    "uid": "john.doe",
                    "mail": "john.doe@company.com",
                    "department": "IT"
                },
                {
                    "cn": "Jane Smith",
                    "uid": "jane.smith",
                    "mail": "jane.smith@company.com",
                    "department": "HR"
                }
            ]
            
            response = client.get(
                "/api/ldap/search-users?query=john&server_id=ldap_server_123&limit=10",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            search_results = response.json()
            assert len(search_results) > 0
            assert search_results[0]["cn"] == "John Doe"


class TestMultiTenantWorkflow:
    """End-to-end tests for multi-tenant workflow"""
    
    def test_tenant_management_workflow(self, client):
        """Test complete tenant management workflow."""
        # Step 1: Create tenant
        with patch('app.services.multi_tenant.MultiTenantService.create_tenant') as mock_create:
            mock_create.return_value = {
                "success": True,
                "tenant_id": "tenant_123",
                "created_at": datetime.now().isoformat(),
                "trial_ends_at": (datetime.now() + timedelta(days=30)).isoformat()
            }
            
            tenant_config = {
                "name": "Test Company",
                "domain": "testcompany.com",
                "tenant_type": "enterprise",
                "plan": "professional",
                "admin_contact": {
                    "name": "Admin User",
                    "email": "admin@testcompany.com"
                }
            }
            
            response = client.post(
                "/api/tenants",
                json=tenant_config,
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            create_result = response.json()
            assert create_result["success"] is True
            assert create_result["tenant_id"] == "tenant_123"
        
        # Step 2: Add user to tenant
        with patch('app.services.multi_tenant.MultiTenantService.add_user_to_tenant') as mock_add_user:
            mock_add_user.return_value = {
                "success": True,
                "user_id": "user_123",
                "tenant_id": "tenant_123"
            }
            
            user_data = {
                "email": "user@testcompany.com",
                "name": "Test User",
                "role": "user",
                "permissions": ["read_emails", "view_reports"]
            }
            
            response = client.post(
                "/api/tenants/tenant_123/users",
                json=user_data,
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            add_user_result = response.json()
            assert add_user_result["success"] is True
            assert add_user_result["user_id"] == "user_123"
        
        # Step 3: Get tenant information
        with patch('app.services.multi_tenant.MultiTenantService.get_tenant_info') as mock_info:
            mock_info.return_value = {
                "tenant_id": "tenant_123",
                "name": "Test Company",
                "domain": "testcompany.com",
                "tenant_type": "enterprise",
                "status": "active",
                "plan": "professional",
                "user_count": 1,
                "resources": {
                    "max_users": 100,
                    "current_users": 1,
                    "max_emails_per_month": 50000,
                    "current_emails_this_month": 0
                }
            }
            
            response = client.get(
                "/api/tenants/tenant_123",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            tenant_info = response.json()
            assert tenant_info["tenant_id"] == "tenant_123"
            assert tenant_info["user_count"] == 1
            assert tenant_info["resources"]["max_users"] == 100


class TestBackupRecoveryWorkflow:
    """End-to-end tests for backup and recovery workflow"""
    
    def test_backup_workflow(self, client):
        """Test complete backup workflow."""
        # Step 1: Create backup job
        with patch('app.services.backup_recovery.BackupRecoveryService.create_backup_job') as mock_create:
            mock_create.return_value = {
                "success": True,
                "job_id": "backup_job_123",
                "created_at": datetime.now().isoformat()
            }
            
            backup_config = {
                "name": "E2E Test Backup",
                "backup_type": "full",
                "destination": "local",
                "destination_config": {
                    "path": "/tmp/backups"
                },
                "sources": ["database", "files", "configurations"],
                "schedule": "0 2 * * *",
                "retention_days": 30
            }
            
            response = client.post(
                "/api/backup/jobs",
                json=backup_config,
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            create_result = response.json()
            assert create_result["success"] is True
            assert create_result["job_id"] == "backup_job_123"
        
        # Step 2: Execute backup job
        with patch('app.services.backup_recovery.BackupRecoveryService.execute_backup_job') as mock_execute:
            mock_execute.return_value = {
                "success": True,
                "files_backed_up": 150,
                "bytes_backed_up": 104857600,  # 100MB
                "session_id": "backup_session_123"
            }
            
            response = client.post(
                "/api/backup/jobs/backup_job_123/execute",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            execute_result = response.json()
            assert execute_result["success"] is True
            assert execute_result["files_backed_up"] == 150
        
        # Step 3: Get backup jobs
        with patch('app.services.backup_recovery.BackupRecoveryService.get_backup_jobs') as mock_jobs:
            mock_jobs.return_value = [
                {
                    "job_id": "backup_job_123",
                    "name": "E2E Test Backup",
                    "backup_type": "full",
                    "destination": "local",
                    "status": "completed",
                    "last_run": datetime.now().isoformat(),
                    "success_count": 1,
                    "failure_count": 0
                }
            ]
            
            response = client.get(
                "/api/backup/jobs",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            jobs = response.json()
            assert len(jobs) > 0
            assert jobs[0]["status"] == "completed"
