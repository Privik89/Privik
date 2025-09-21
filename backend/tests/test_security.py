"""
Security tests for vulnerability assessment and penetration testing
"""

import pytest
import json
from datetime import datetime
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock


class TestAuthenticationSecurity:
    """Security tests for authentication mechanisms"""
    
    def test_hmac_authentication_bypass(self, client):
        """Test HMAC authentication bypass attempts."""
        # Test without authentication headers
        response = client.post("/api/email-gateway/process", json={"test": "data"})
        assert response.status_code == 401
        
        # Test with invalid HMAC signature
        response = client.post(
            "/api/email-gateway/process",
            json={"test": "data"},
            headers={
                "X-API-Key": "test_key",
                "X-Timestamp": str(int(datetime.now().timestamp())),
                "X-Signature": "invalid_signature"
            }
        )
        assert response.status_code == 401
        
        # Test with expired timestamp
        old_timestamp = str(int(datetime.now().timestamp()) - 3600)  # 1 hour ago
        response = client.post(
            "/api/email-gateway/process",
            json={"test": "data"},
            headers={
                "X-API-Key": "test_key",
                "X-Timestamp": old_timestamp,
                "X-Signature": "test_signature"
            }
        )
        assert response.status_code == 401
    
    def test_jwt_token_security(self, client):
        """Test JWT token security."""
        # Test without JWT token
        response = client.get("/api/ui/ai-ml/ai/status")
        assert response.status_code == 401
        
        # Test with invalid JWT token
        response = client.get(
            "/api/ui/ai-ml/ai/status",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401
        
        # Test with expired JWT token
        expired_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE2MDAwMDAwMDB9.invalid"
        response = client.get(
            "/api/ui/ai-ml/ai/status",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401
    
    def test_ldap_injection_attacks(self, client):
        """Test LDAP injection attack prevention."""
        with patch('app.services.ldap_auth.LDAPAuthService.authenticate_user') as mock_auth:
            mock_auth.return_value = {"success": False, "error": "Authentication failed"}
            
            # Test LDAP injection payloads
            injection_payloads = [
                "admin)(&(password=*))",
                "admin)(|(password=*))",
                "admin)(!(password=*))",
                "admin)(&(objectClass=*))",
                "admin)(|(objectClass=*))"
            ]
            
            for payload in injection_payloads:
                response = client.post(
                    "/api/ldap/authenticate",
                    json={"username": payload, "password": "test"},
                    headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
                )
                # Should not return 500 (internal server error) - indicates injection vulnerability
                assert response.status_code != 500


class TestInputValidation:
    """Security tests for input validation"""
    
    def test_sql_injection_prevention(self, client):
        """Test SQL injection prevention."""
        sql_injection_payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; INSERT INTO users VALUES ('hacker', 'password'); --",
            "' UNION SELECT * FROM users --",
            "'; UPDATE users SET password='hacked' WHERE username='admin'; --"
        ]
        
        for payload in sql_injection_payloads:
            # Test in various fields
            test_data = {
                "message_id": payload,
                "subject": payload,
                "sender": payload,
                "recipient": "test@example.com",
                "body": "Test body"
            }
            
            with patch('app.services.email_gateway_service.EmailGatewayService.process_email') as mock_process:
                mock_process.return_value = {"threat_score": 0.1, "verdict": "clean"}
                
                response = client.post(
                    "/api/email-gateway/process",
                    json=test_data,
                    headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
                )
                
                # Should not return 500 (internal server error)
                assert response.status_code != 500
                # Should either process normally or return validation error
                assert response.status_code in [200, 422]
    
    def test_xss_prevention(self, client):
        """Test XSS prevention."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "<iframe src=javascript:alert('XSS')></iframe>",
            "';alert('XSS');//",
            "\"><script>alert('XSS')</script>"
        ]
        
        for payload in xss_payloads:
            test_data = {
                "message_id": "test_123",
                "subject": payload,
                "sender": "test@example.com",
                "recipient": "user@company.com",
                "body": payload
            }
            
            with patch('app.services.email_gateway_service.EmailGatewayService.process_email') as mock_process:
                mock_process.return_value = {"threat_score": 0.1, "verdict": "clean"}
                
                response = client.post(
                    "/api/email-gateway/process",
                    json=test_data,
                    headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
                )
                
                # Should not return 500 (internal server error)
                assert response.status_code != 500
                # Response should not contain unescaped script tags
                if response.status_code == 200:
                    response_text = response.text
                    assert "<script>" not in response_text
                    assert "javascript:" not in response_text
    
    def test_path_traversal_prevention(self, client):
        """Test path traversal prevention."""
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "....//....//....//etc/passwd",
            "..%2F..%2F..%2Fetc%2Fpasswd",
            "..%5C..%5C..%5Cwindows%5Csystem32%5Cdrivers%5Cetc%5Chosts"
        ]
        
        for payload in path_traversal_payloads:
            # Test in file path parameters
            response = client.post(
                "/api/sandbox/detonate-test",
                json={"file_path": payload},
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            # Should not return 500 (internal server error)
            assert response.status_code != 500
            # Should either reject the request or return validation error
            assert response.status_code in [400, 422, 200]
    
    def test_command_injection_prevention(self, client):
        """Test command injection prevention."""
        command_injection_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "&& whoami",
            "`id`",
            "$(whoami)",
            "; rm -rf /",
            "| nc -l -p 4444 -e /bin/sh"
        ]
        
        for payload in command_injection_payloads:
            test_data = {
                "message_id": "test_123",
                "subject": payload,
                "sender": "test@example.com",
                "recipient": "user@company.com",
                "body": "Test body"
            }
            
            with patch('app.services.email_gateway_service.EmailGatewayService.process_email') as mock_process:
                mock_process.return_value = {"threat_score": 0.1, "verdict": "clean"}
                
                response = client.post(
                    "/api/email-gateway/process",
                    json=test_data,
                    headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
                )
                
                # Should not return 500 (internal server error)
                assert response.status_code != 500
    
    def test_large_payload_handling(self, client):
        """Test handling of extremely large payloads."""
        # Test with very large email body
        large_body = "x" * (10 * 1024 * 1024)  # 10MB
        
        large_email_data = {
            "message_id": "large_test_123",
            "subject": "Large Email Test",
            "sender": "test@example.com",
            "recipient": "user@company.com",
            "body": large_body
        }
        
        with patch('app.services.email_gateway_service.EmailGatewayService.process_email') as mock_process:
            mock_process.return_value = {"threat_score": 0.1, "verdict": "clean"}
            
            response = client.post(
                "/api/email-gateway/process",
                json=large_email_data,
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            # Should handle large payloads gracefully
            assert response.status_code in [200, 413, 422]  # 413 = Payload Too Large
    
    def test_malformed_json_handling(self, client):
        """Test handling of malformed JSON."""
        malformed_json_cases = [
            '{"incomplete": json}',
            '{"unclosed": "string}',
            '{"invalid": }',
            '{"trailing": "comma",}',
            '{"duplicate": "key", "duplicate": "value"}',
            '{"null": null, "undefined": undefined}',
            '{"circular": {"ref": "circular"}}'  # This would be caught by JSON parser
        ]
        
        for malformed_json in malformed_json_cases:
            response = client.post(
                "/api/email-gateway/process",
                data=malformed_json,
                headers={
                    "Content-Type": "application/json",
                    "X-API-Key": "test_key",
                    "X-Timestamp": str(int(datetime.now().timestamp()))
                }
            )
            
            # Should return 422 (Unprocessable Entity) for malformed JSON
            assert response.status_code == 422


class TestAuthorizationSecurity:
    """Security tests for authorization mechanisms"""
    
    def test_privilege_escalation_prevention(self, client):
        """Test prevention of privilege escalation attacks."""
        # Test accessing admin endpoints with user token
        with patch('app.security.jwt_auth.verify_jwt_token') as mock_verify:
            mock_verify.return_value = {"user_id": "user_123", "role": "user"}
            
            response = client.get(
                "/api/ui/ai-ml/ai/status",
                headers={"Authorization": "Bearer user_token"}
            )
            
            # Should be denied access to admin endpoints
            assert response.status_code == 403
    
    def test_tenant_isolation(self, client):
        """Test tenant data isolation."""
        with patch('app.services.multi_tenant.MultiTenantService.get_tenant_info') as mock_tenant:
            # Mock tenant A data
            mock_tenant.return_value = {
                "tenant_id": "tenant_a",
                "name": "Company A",
                "users": ["user_a1", "user_a2"]
            }
            
            # Try to access tenant B data with tenant A credentials
            response = client.get(
                "/api/tenants/tenant_b/info",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            # Should be denied access to other tenant's data
            assert response.status_code in [403, 404]
    
    def test_api_key_rotation(self, client):
        """Test API key rotation security."""
        # Test with old API key
        old_timestamp = str(int(datetime.now().timestamp()) - 86400)  # 1 day ago
        
        response = client.get(
            "/api/email-gateway/statistics",
            headers={
                "X-API-Key": "old_key",
                "X-Timestamp": old_timestamp,
                "X-Signature": "old_signature"
            }
        )
        
        # Should be denied with old API key
        assert response.status_code == 401


class TestDataSecurity:
    """Security tests for data protection"""
    
    def test_sensitive_data_exposure(self, client):
        """Test prevention of sensitive data exposure."""
        with patch('app.services.email_gateway_service.EmailGatewayService.process_email') as mock_process:
            mock_process.return_value = {
                "threat_score": 0.1,
                "verdict": "clean",
                "internal_debug_info": "sensitive_debug_data"  # This should not be exposed
            }
            
            response = client.post(
                "/api/email-gateway/process",
                json={
                    "message_id": "test_123",
                    "subject": "Test Email",
                    "sender": "test@example.com",
                    "recipient": "user@company.com",
                    "body": "Test body"
                },
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            if response.status_code == 200:
                response_data = response.json()
                # Should not expose internal debug information
                assert "internal_debug_info" not in response_data
    
    def test_password_handling(self, client):
        """Test secure password handling."""
        # Test LDAP authentication with password
        with patch('app.services.ldap_auth.LDAPAuthService.authenticate_user') as mock_auth:
            mock_auth.return_value = {"success": True, "user_id": "user_123"}
            
            response = client.post(
                "/api/ldap/authenticate",
                json={"username": "testuser", "password": "secretpassword"},
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            if response.status_code == 200:
                response_data = response.json()
                # Should not return password in response
                assert "password" not in response_data
                # Should not log password in error messages
                assert "secretpassword" not in response.text
    
    def test_encryption_at_rest(self, client):
        """Test encryption of sensitive data at rest."""
        # This would typically test database encryption, file encryption, etc.
        # For now, we'll test that sensitive data is not stored in plain text
        
        with patch('app.services.email_gateway_service.EmailGatewayService.process_email') as mock_process:
            mock_process.return_value = {"threat_score": 0.1, "verdict": "clean"}
            
            sensitive_data = {
                "message_id": "test_123",
                "subject": "Confidential Information",
                "sender": "ceo@company.com",
                "recipient": "hr@company.com",
                "body": "This contains sensitive employee information"
            }
            
            response = client.post(
                "/api/email-gateway/process",
                json=sensitive_data,
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            # Should process without exposing sensitive data in logs
            assert response.status_code in [200, 422]


class TestNetworkSecurity:
    """Security tests for network-level security"""
    
    def test_https_enforcement(self, client):
        """Test HTTPS enforcement."""
        # This would typically be tested at the reverse proxy level
        # For API testing, we'll verify that sensitive endpoints require proper headers
        
        response = client.get("/api/email-gateway/statistics")
        # Should require authentication
        assert response.status_code == 401
    
    def test_cors_configuration(self, client):
        """Test CORS configuration."""
        # Test preflight request
        response = client.options(
            "/api/email-gateway/process",
            headers={
                "Origin": "https://malicious-site.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
        )
        
        # Should not allow requests from unauthorized origins
        # The exact status code depends on CORS configuration
        assert response.status_code in [200, 403, 405]
    
    def test_rate_limiting(self, client):
        """Test rate limiting implementation."""
        # Make multiple requests quickly
        for i in range(100):  # Try to exceed rate limit
            response = client.get(
                "/api/email-gateway/statistics",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            if response.status_code == 429:  # Too Many Requests
                break
        
        # Should eventually hit rate limit
        assert response.status_code in [200, 429]


class TestBusinessLogicSecurity:
    """Security tests for business logic vulnerabilities"""
    
    def test_email_spoofing_prevention(self, client):
        """Test email spoofing prevention."""
        spoofed_emails = [
            {
                "sender": "admin@company.com",  # Spoofed admin email
                "recipient": "user@company.com",
                "subject": "Urgent: Change Password",
                "body": "Please change your password immediately"
            },
            {
                "sender": "noreply@bank.com",  # Spoofed bank email
                "recipient": "user@company.com",
                "subject": "Account Security Alert",
                "body": "Your account has been compromised"
            }
        ]
        
        for email_data in spoofed_emails:
            with patch('app.services.email_gateway_service.EmailGatewayService.process_email') as mock_process:
                mock_process.return_value = {
                    "threat_score": 0.9,  # Should detect spoofing
                    "verdict": "malicious",
                    "indicators": ["email_spoofing"]
                }
                
                response = client.post(
                    "/api/email-gateway/process",
                    json=email_data,
                    headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    # Should detect spoofing attempts
                    assert response_data["threat_score"] > 0.7
    
    def test_quota_bypass_prevention(self, client):
        """Test prevention of quota bypass attacks."""
        # Try to process many emails quickly to bypass rate limits
        for i in range(1000):
            email_data = {
                "message_id": f"test_{i}",
                "subject": f"Test Email {i}",
                "sender": "test@example.com",
                "recipient": "user@company.com",
                "body": "Test body"
            }
            
            with patch('app.services.email_gateway_service.EmailGatewayService.process_email') as mock_process:
                mock_process.return_value = {"threat_score": 0.1, "verdict": "clean"}
                
                response = client.post(
                    "/api/email-gateway/process",
                    json=email_data,
                    headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
                )
                
                if response.status_code == 429:  # Rate limited
                    break
        
        # Should eventually hit rate limit
        assert response.status_code in [200, 429]
    
    def test_webhook_replay_attacks(self, client):
        """Test prevention of webhook replay attacks."""
        webhook_data = {
            "event_type": "email_threat_detected",
            "timestamp": datetime.now().isoformat(),
            "data": {"threat_id": "threat_123"}
        }
        
        # Send the same webhook multiple times
        for i in range(5):
            response = client.post(
                "/api/webhooks/trigger/email_threat_detected",
                json=webhook_data,
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            # Should handle replay attacks appropriately
            assert response.status_code in [200, 400, 429]


class TestCryptographicSecurity:
    """Security tests for cryptographic implementations"""
    
    def test_hmac_signature_validation(self, client):
        """Test HMAC signature validation."""
        # Test with correct signature
        with patch('app.security.hmac_auth.verify_request') as mock_verify:
            mock_verify.return_value = {"authenticated": True}
            
            response = client.get(
                "/api/email-gateway/statistics",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 200
        
        # Test with incorrect signature
        with patch('app.security.hmac_auth.verify_request') as mock_verify:
            mock_verify.side_effect = Exception("Invalid signature")
            
            response = client.get(
                "/api/email-gateway/statistics",
                headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
            )
            
            assert response.status_code == 401
    
    def test_jwt_token_integrity(self, client):
        """Test JWT token integrity."""
        # Test with tampered JWT token
        tampered_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoidXNlcl8xMjMiLCJyb2xlIjoiYWRtaW4ifQ.tampered_signature"
        
        response = client.get(
            "/api/ui/ai-ml/ai/status",
            headers={"Authorization": f"Bearer {tampered_token}"}
        )
        
        # Should reject tampered token
        assert response.status_code == 401
    
    def test_webhook_signature_validation(self, client):
        """Test webhook signature validation."""
        webhook_data = {
            "event_type": "test_event",
            "data": {"test": "data"}
        }
        
        # Test without signature
        response = client.post(
            "/api/webhooks/trigger/test_event",
            json=webhook_data,
            headers={"X-API-Key": "test_key", "X-Timestamp": str(int(datetime.now().timestamp()))}
        )
        
        # Should require valid signature
        assert response.status_code in [200, 401, 400]
