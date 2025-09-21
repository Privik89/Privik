"""
Unit tests for Email Analyzer Service
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from app.services.email_analyzer import EmailAnalyzer
from app.services.domain_reputation import DomainReputationService


class TestEmailAnalyzer:
    """Test cases for EmailAnalyzer service"""
    
    @pytest.fixture
    def email_analyzer(self):
        """Create EmailAnalyzer instance for testing."""
        return EmailAnalyzer()
    
    @pytest.fixture
    def sample_email_data(self):
        """Sample email data for testing."""
        return {
            "message_id": "test_123",
            "subject": "Urgent: Verify Your Account",
            "sender": "noreply@suspicious-domain.com",
            "recipient": "user@company.com",
            "body": "Please click the link to verify your account immediately.",
            "headers": {
                "From": "noreply@suspicious-domain.com",
                "To": "user@company.com",
                "Subject": "Urgent: Verify Your Account",
                "Date": datetime.now().isoformat()
            },
            "attachments": [
                {
                    "filename": "invoice.pdf",
                    "content_type": "application/pdf",
                    "size": 1024000
                }
            ],
            "links": [
                "https://suspicious-domain.com/verify",
                "https://legitimate-site.com/help"
            ]
        }
    
    @pytest.mark.asyncio
    async def test_analyze_email_basic(self, email_analyzer, sample_email_data):
        """Test basic email analysis."""
        with patch.object(email_analyzer, '_perform_email_analysis') as mock_analysis:
            mock_analysis.return_value = {
                "threat_score": 0.75,
                "verdict": "suspicious",
                "indicators": ["urgent_language", "suspicious_domain"]
            }
            
            result = await email_analyzer.analyze_email(sample_email_data)
            
            assert result is not None
            assert "threat_score" in result
            assert "verdict" in result
            assert "indicators" in result
            mock_analysis.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_email_with_attachments(self, email_analyzer, sample_email_data):
        """Test email analysis with attachments."""
        with patch.object(email_analyzer, '_analyze_attachments') as mock_attachments:
            mock_attachments.return_value = {
                "attachment_count": 1,
                "suspicious_attachments": 1,
                "total_size": 1024000
            }
            
            with patch.object(email_analyzer, '_perform_email_analysis') as mock_analysis:
                mock_analysis.return_value = {
                    "threat_score": 0.85,
                    "verdict": "malicious",
                    "indicators": ["suspicious_attachment"]
                }
                
                result = await email_analyzer.analyze_email(sample_email_data)
                
                assert result["threat_score"] > 0.8
                mock_attachments.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_analyze_email_with_links(self, email_analyzer, sample_email_data):
        """Test email analysis with links."""
        with patch.object(email_analyzer, '_analyze_links') as mock_links:
            mock_links.return_value = {
                "link_count": 2,
                "suspicious_links": 1,
                "domains": ["suspicious-domain.com", "legitimate-site.com"]
            }
            
            with patch.object(email_analyzer, '_perform_email_analysis') as mock_analysis:
                mock_analysis.return_value = {
                    "threat_score": 0.70,
                    "verdict": "suspicious",
                    "indicators": ["suspicious_link"]
                }
                
                result = await email_analyzer.analyze_email(sample_email_data)
                
                assert result["threat_score"] > 0.6
                mock_links.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_domain_reputation_analysis(self, email_analyzer, sample_email_data):
        """Test domain reputation analysis integration."""
        with patch.object(DomainReputationService, 'get_domain_score') as mock_reputation:
            mock_reputation.return_value = {
                "domain": "suspicious-domain.com",
                "reputation_score": 0.15,
                "threat_indicators": 8,
                "sources": ["virustotal", "google_safe_browsing"]
            }
            
            with patch.object(email_analyzer, '_perform_email_analysis') as mock_analysis:
                mock_analysis.return_value = {
                    "threat_score": 0.80,
                    "verdict": "malicious",
                    "indicators": ["low_domain_reputation"]
                }
                
                result = await email_analyzer.analyze_email(sample_email_data)
                
                assert result["threat_score"] > 0.7
                mock_reputation.assert_called()
    
    def test_extract_email_features(self, email_analyzer, sample_email_data):
        """Test email feature extraction."""
        features = email_analyzer._extract_email_features(sample_email_data)
        
        assert "subject_length" in features
        assert "body_length" in features
        assert "attachment_count" in features
        assert "link_count" in features
        assert "urgent_keywords" in features
        assert features["attachment_count"] == 1
        assert features["link_count"] == 2
    
    def test_detect_urgent_keywords(self, email_analyzer):
        """Test urgent keyword detection."""
        urgent_subjects = [
            "URGENT: Action Required",
            "Immediate attention needed",
            "Your account will be closed",
            "Verify your account now"
        ]
        
        for subject in urgent_subjects:
            email_data = {"subject": subject, "body": "Test body"}
            features = email_analyzer._extract_email_features(email_data)
            assert features["urgent_keywords"] > 0
    
    def test_calculate_threat_score(self, email_analyzer):
        """Test threat score calculation."""
        features = {
            "urgent_keywords": 2,
            "attachment_count": 1,
            "link_count": 3,
            "suspicious_domain": True,
            "low_reputation_score": 0.2
        }
        
        threat_score = email_analyzer._calculate_email_threat_score(features)
        
        assert 0 <= threat_score <= 1
        assert threat_score > 0.5  # Should be high due to multiple indicators
    
    @pytest.mark.asyncio
    async def test_analyze_email_error_handling(self, email_analyzer):
        """Test error handling in email analysis."""
        invalid_email_data = None
        
        with pytest.raises(Exception):
            await email_analyzer.analyze_email(invalid_email_data)
    
    def test_sender_domain_extraction(self, email_analyzer):
        """Test sender domain extraction."""
        test_cases = [
            ("user@example.com", "example.com"),
            ("test.user@subdomain.example.com", "subdomain.example.com"),
            ("invalid-email", None),
            ("", None)
        ]
        
        for email, expected_domain in test_cases:
            domain = email_analyzer._extract_domain_from_email(email)
            assert domain == expected_domain
    
    def test_link_domain_extraction(self, email_analyzer):
        """Test link domain extraction."""
        links = [
            "https://example.com/path",
            "http://subdomain.example.com/page",
            "https://example.com:8080/api",
            "invalid-url"
        ]
        
        domains = email_analyzer._extract_link_domains(links)
        
        assert "example.com" in domains
        assert "subdomain.example.com" in domains
        assert len(domains) >= 2
    
    @pytest.mark.asyncio
    async def test_analyze_attachments(self, email_analyzer):
        """Test attachment analysis."""
        attachments = [
            {
                "filename": "document.pdf",
                "content_type": "application/pdf",
                "size": 1024000
            },
            {
                "filename": "script.exe",
                "content_type": "application/x-executable",
                "size": 2048000
            }
        ]
        
        result = await email_analyzer._analyze_attachments(attachments)
        
        assert result["attachment_count"] == 2
        assert result["total_size"] == 3072000
        assert result["suspicious_attachments"] >= 1  # .exe file should be suspicious
    
    @pytest.mark.asyncio
    async def test_analyze_links(self, email_analyzer):
        """Test link analysis."""
        links = [
            "https://legitimate-site.com",
            "https://suspicious-domain.com/malware",
            "http://phishing-site.com/login"
        ]
        
        result = await email_analyzer._analyze_links(links)
        
        assert result["link_count"] == 3
        assert len(result["domains"]) == 3
        assert result["suspicious_links"] >= 0  # Depends on domain reputation
    
    def test_generate_verdict(self, email_analyzer):
        """Test verdict generation based on threat score."""
        test_cases = [
            (0.95, "malicious"),
            (0.75, "suspicious"),
            (0.45, "potentially_unwanted"),
            (0.15, "clean")
        ]
        
        for threat_score, expected_verdict in test_cases:
            verdict = email_analyzer._generate_verdict(threat_score)
            assert verdict == expected_verdict
    
    @pytest.mark.asyncio
    async def test_performance_large_email(self, email_analyzer):
        """Test performance with large email data."""
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
        
        with patch.object(email_analyzer, '_perform_email_analysis') as mock_analysis:
            mock_analysis.return_value = {
                "threat_score": 0.1,
                "verdict": "clean",
                "indicators": []
            }
            
            import time
            start_time = time.time()
            result = await email_analyzer.analyze_email(large_email_data)
            end_time = time.time()
            
            assert result is not None
            assert (end_time - start_time) < 5.0  # Should complete within 5 seconds
    
    def test_feature_normalization(self, email_analyzer):
        """Test feature normalization for ML models."""
        raw_features = {
            "subject_length": 150,
            "body_length": 5000,
            "attachment_count": 3,
            "link_count": 5,
            "urgent_keywords": 2
        }
        
        normalized_features = email_analyzer._normalize_features(raw_features)
        
        # Check that features are within expected ranges
        assert 0 <= normalized_features["subject_length"] <= 1
        assert 0 <= normalized_features["body_length"] <= 1
        assert normalized_features["attachment_count"] >= 0
        assert normalized_features["link_count"] >= 0
        assert normalized_features["urgent_keywords"] >= 0
