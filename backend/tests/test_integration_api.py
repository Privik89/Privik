"""
Integration tests for API endpoints
"""

import pytest
import json
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock, AsyncMock


class TestEmailGatewayAPI:
    """Integration tests for email gateway API endpoints"""
    
    def test_process_email_endpoint(self, client, mock_email_data):
        """Test email processing endpoint."""
        with patch('app.services.email_gateway_service.EmailGatewayService.process_email') as mock_process:
            mock_process.return_value = {
                "message_id": mock_email_data["message_id"],
                "threat_score": 0.75,
                "verdict": "suspicious",
                "indicators": ["urgent_language", "suspicious_domain"]
            }
            
            response = client.post(
                "/api/email-gateway/process",
                json=mock_email_data,
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "threat_score" in data
            assert "verdict" in data
            assert data["message_id"] == mock_email_data["message_id"]
    
    def test_process_email_async_endpoint(self, client, mock_email_data):
        """Test async email processing endpoint."""
        with patch('app.services.email_gateway_service.EmailGatewayService.process_email_async') as mock_process:
            mock_process.return_value = {"task_id": "task_123"}
            
            response = client.post(
                "/api/email-gateway/process-async",
                json=mock_email_data,
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 202
            data = response.json()
            assert "task_id" in data
    
    def test_gateway_statistics_endpoint(self, client):
        """Test gateway statistics endpoint."""
        with patch('app.services.email_gateway_service.EmailGatewayService.get_statistics') as mock_stats:
            mock_stats.return_value = {
                "total_emails_processed": 1000,
                "threats_detected": 50,
                "false_positives": 5,
                "processing_time_avg": 0.5
            }
            
            response = client.get(
                "/api/email-gateway/statistics",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "total_emails_processed" in data
            assert data["total_emails_processed"] == 1000
    
    def test_gateway_start_stop_endpoints(self, client):
        """Test gateway start/stop endpoints."""
        # Test start endpoint
        with patch('app.services.email_gateway_service.EmailGatewayService.start') as mock_start:
            mock_start.return_value = {"status": "started"}
            
            response = client.post(
                "/api/email-gateway/start",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "started"
        
        # Test stop endpoint
        with patch('app.services.email_gateway_service.EmailGatewayService.stop') as mock_stop:
            mock_stop.return_value = {"status": "stopped"}
            
            response = client.post(
                "/api/email-gateway/stop",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "stopped"


class TestSandboxAPI:
    """Integration tests for sandbox API endpoints"""
    
    def test_sandbox_status_endpoint(self, client):
        """Test sandbox status endpoint."""
        with patch('app.services.real_time_sandbox.RealTimeSandbox.get_status') as mock_status:
            mock_status.return_value = {
                "status": "active",
                "active_analyses": 5,
                "completed_analyses": 100,
                "failed_analyses": 2
            }
            
            response = client.get(
                "/api/sandbox/status",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "active"
            assert "active_analyses" in data
    
    def test_sandbox_detonate_test_endpoint(self, client):
        """Test sandbox detonation test endpoint."""
        with patch('app.services.real_time_sandbox.RealTimeSandbox.analyze_attachment') as mock_analyze:
            mock_analyze.return_value = {
                "analysis_id": "test_123",
                "verdict": "clean",
                "threat_score": 0.1
            }
            
            response = client.post(
                "/api/sandbox/detonate-test",
                json={"file_path": "/tmp/test_file.pdf"},
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "analysis_id" in data
            assert data["verdict"] == "clean"


class TestSOCAPI:
    """Integration tests for SOC API endpoints"""
    
    def test_soc_incidents_endpoint(self, client):
        """Test SOC incidents endpoint."""
        with patch('app.services.sandbox_poller.SandboxPoller.get_incidents') as mock_incidents:
            mock_incidents.return_value = [
                {
                    "incident_id": "inc_123",
                    "threat_type": "malware",
                    "severity": "high",
                    "timestamp": datetime.now().isoformat(),
                    "status": "investigating"
                }
            ]
            
            response = client.get(
                "/api/soc/incidents",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) > 0
            assert "incident_id" in data[0]
    
    def test_soc_incident_detail_endpoint(self, client):
        """Test SOC incident detail endpoint."""
        with patch('app.services.sandbox_poller.SandboxPoller.get_incident_details') as mock_details:
            mock_details.return_value = {
                "incident_id": "inc_123",
                "threat_type": "malware",
                "severity": "high",
                "analysis_results": {
                    "verdict": "malicious",
                    "threat_score": 0.95,
                    "malware_family": "Trojan.Generic"
                },
                "artifacts": {
                    "screenshots": ["screenshot1.png"],
                    "reports": ["analysis_report.json"]
                }
            }
            
            response = client.get(
                "/api/soc/incidents/inc_123",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["incident_id"] == "inc_123"
            assert "analysis_results" in data
            assert "artifacts" in data


class TestIntegrationsAPI:
    """Integration tests for integrations API endpoints"""
    
    def test_integrations_start_endpoint(self, client):
        """Test integrations start endpoint."""
        with patch('app.services.email_integrations.EmailIntegrations.start_integration') as mock_start:
            mock_start.return_value = {"status": "started", "integration": "gmail"}
            
            response = client.post(
                "/api/integrations/start",
                json={"integration": "gmail"},
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "started"
            assert data["integration"] == "gmail"
    
    def test_integrations_status_endpoint(self, client):
        """Test integrations status endpoint."""
        with patch('app.services.email_integrations.EmailIntegrations.get_integration_status') as mock_status:
            mock_status.return_value = {
                "gmail": {"status": "active", "last_sync": datetime.now().isoformat()},
                "o365": {"status": "inactive", "last_sync": None}
            }
            
            response = client.get(
                "/api/integrations/status",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "gmail" in data
            assert "o365" in data
            assert data["gmail"]["status"] == "active"


class TestAI_MLAPI:
    """Integration tests for AI/ML API endpoints"""
    
    def test_ml_train_endpoint(self, client):
        """Test ML training endpoint."""
        with patch('app.services.ml_training_pipeline.MLTrainingPipeline.run_full_training_pipeline') as mock_train:
            mock_train.return_value = {
                "success": True,
                "training_data_counts": {"emails": 1000, "domains": 500},
                "model_results": {"email_classifier": {"accuracy": 0.95}}
            }
            
            response = client.post(
                "/api/ai-ml/ml/train?days_back=30",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "training_data_counts" in data
    
    def test_ml_models_status_endpoint(self, client):
        """Test ML models status endpoint."""
        with patch('app.services.ml_training_pipeline.MLTrainingPipeline.load_models') as mock_load:
            mock_load.return_value = None
            
            with patch.object(Mock(), 'models', {
                'email_classifier': Mock(),
                'domain_classifier': None,
                'behavior_classifier': Mock()
            }):
                response = client.get(
                    "/api/ai-ml/ml/models/status",
                    headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert "models" in data
                assert "total_models" in data
    
    def test_behavior_anomalies_endpoint(self, client):
        """Test behavioral anomalies endpoint."""
        with patch('app.services.behavioral_analysis.BehavioralAnalyzer.detect_behavioral_anomalies') as mock_detect:
            mock_detect.return_value = {
                "anomalies": [
                    {
                        "user_id": "user_123",
                        "anomaly_score": 0.85,
                        "risk_level": "high",
                        "metrics": {"suspicious_click_rate": 0.4}
                    }
                ],
                "total_users_analyzed": 100
            }
            
            response = client.get(
                "/api/ai-ml/behavior/anomalies",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "anomalies" in data
            assert len(data["anomalies"]) > 0
            assert data["anomalies"][0]["risk_level"] == "high"
    
    def test_threat_hunting_campaign_endpoint(self, client):
        """Test threat hunting campaign endpoint."""
        with patch('app.services.threat_hunting.ThreatHunter.run_threat_hunting_campaign') as mock_campaign:
            mock_campaign.return_value = {
                "campaign_id": "campaign_123",
                "campaign_name": "Test Campaign",
                "findings": [
                    {
                        "type": "suspicious_email",
                        "title": "Suspicious Email Detected",
                        "confidence": 0.9
                    }
                ],
                "threat_indicators": [
                    {"type": "email_address", "value": "phishing@malicious.com"}
                ]
            }
            
            response = client.post(
                "/api/ai-ml/threat-hunting/campaign?campaign_name=Test%20Campaign&time_range=7",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "campaign_id" in data
            assert "findings" in data
            assert len(data["findings"]) > 0


class TestComplianceAPI:
    """Integration tests for compliance API endpoints"""
    
    def test_compliance_report_generation(self, client):
        """Test compliance report generation."""
        with patch('app.services.compliance_reporting.ComplianceReportGenerator.generate_compliance_report') as mock_report:
            mock_report.return_value = {
                "report_metadata": {
                    "framework": "soc2_type_ii",
                    "report_id": "report_123",
                    "compliance_score": 0.92
                },
                "executive_summary": {
                    "overall_score": 0.92,
                    "key_highlights": ["Strong security controls"]
                }
            }
            
            response = client.post(
                "/api/compliance/reports/generate",
                json={
                    "framework": "soc2_type_ii",
                    "start_date": (datetime.now() - timedelta(days=30)).isoformat(),
                    "end_date": datetime.now().isoformat()
                },
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "report_metadata" in data
            assert data["report_metadata"]["compliance_score"] == 0.92


class TestWebhookAPI:
    """Integration tests for webhook API endpoints"""
    
    def test_webhook_creation(self, client):
        """Test webhook creation."""
        with patch('app.services.webhook_system.WebhookSystem.create_webhook') as mock_create:
            mock_create.return_value = {
                "success": True,
                "webhook_id": "webhook_123",
                "webhook_secret": "secret_key_123"
            }
            
            webhook_config = {
                "name": "Test Webhook",
                "url": "https://example.com/webhook",
                "events": ["email_threat_detected", "user_behavior_anomaly"],
                "timeout": 30
            }
            
            response = client.post(
                "/api/webhooks",
                json=webhook_config,
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "webhook_id" in data
    
    def test_webhook_trigger(self, client):
        """Test webhook triggering."""
        with patch('app.services.webhook_system.WebhookSystem.trigger_webhook') as mock_trigger:
            mock_trigger.return_value = {
                "success": True,
                "event_type": "email_threat_detected",
                "subscribed_webhooks": 2
            }
            
            event_data = {
                "email_id": "email_123",
                "threat_type": "phishing",
                "threat_score": 0.85
            }
            
            response = client.post(
                "/api/webhooks/trigger/email_threat_detected",
                json=event_data,
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["event_type"] == "email_threat_detected"


class TestErrorHandling:
    """Integration tests for error handling"""
    
    def test_invalid_json_request(self, client):
        """Test handling of invalid JSON requests."""
        response = client.post(
            "/api/email-gateway/process",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_missing_required_fields(self, client):
        """Test handling of missing required fields."""
        incomplete_data = {
            "subject": "Test Email",
            # Missing required fields like sender, recipient
        }
        
        response = client.post(
            "/api/email-gateway/process",
            json=incomplete_data,
            headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
        )
        
        assert response.status_code == 422
    
    def test_authentication_failure(self, client):
        """Test authentication failure handling."""
        response = client.get(
            "/api/email-gateway/statistics",
            headers={"X-API-Key": "invalid_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
        )
        
        assert response.status_code == 401  # Unauthorized
    
    def test_rate_limiting(self, client):
        """Test rate limiting functionality."""
        # Make multiple requests quickly
        for i in range(10):
            response = client.get(
                "/api/email-gateway/statistics",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            if response.status_code == 429:  # Too Many Requests
                break
        
        # Should eventually hit rate limit
        assert response.status_code in [200, 429]


class TestPerformance:
    """Integration tests for performance"""
    
    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests."""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = client.get(
                "/api/email-gateway/statistics",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            results.append(response.status_code)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # Start all threads
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        
        # All requests should complete successfully
        assert all(status == 200 for status in results)
        # Should complete within reasonable time
        assert (end_time - start_time) < 10.0
    
    def test_large_payload_handling(self, client):
        """Test handling of large payloads."""
        large_email_data = {
            "message_id": "large_test_123",
            "subject": "Large Email Test",
            "sender": "sender@example.com",
            "recipient": "recipient@example.com",
            "body": "x" * 1000000,  # 1MB body
            "headers": {"From": "sender@example.com"},
            "attachments": [],
            "links": []
        }
        
        with patch('app.services.email_gateway_service.EmailGatewayService.process_email') as mock_process:
            mock_process.return_value = {
                "message_id": large_email_data["message_id"],
                "threat_score": 0.1,
                "verdict": "clean"
            }
            
            import time
            start_time = time.time()
            response = client.post(
                "/api/email-gateway/process",
                json=large_email_data,
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            end_time = time.time()
            
            assert response.status_code == 200
            assert (end_time - start_time) < 30.0  # Should complete within 30 seconds
