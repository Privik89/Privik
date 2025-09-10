"""
Email Header Analyzer Service
Comprehensive email header analysis for security detection
"""

import re
import structlog
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import email.utils
import ipaddress
import base64
import quopri

logger = structlog.get_logger()


class HeaderRisk(Enum):
    """Header risk levels"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HeaderAnomaly(Enum):
    """Header anomaly types"""
    MISSING_HEADERS = "missing_headers"
    INVALID_FORMAT = "invalid_format"
    SUSPICIOUS_VALUES = "suspicious_values"
    SPOOFING_ATTEMPT = "spoofing_attempt"
    ROUTING_ANOMALY = "routing_anomaly"
    TIMING_ANOMALY = "timing_anomaly"
    ENCODING_ANOMALY = "encoding_anomaly"


@dataclass
class HeaderAnalysis:
    """Header analysis result"""
    header_name: str
    header_value: str
    is_valid: bool
    risk_level: HeaderRisk
    anomalies: List[HeaderAnomaly]
    indicators: List[str]
    metadata: Dict[str, Any]


@dataclass
class EmailHeaderAnalysis:
    """Complete email header analysis"""
    overall_risk: HeaderRisk
    risk_score: float
    header_analyses: List[HeaderAnalysis]
    anomalies: List[HeaderAnomaly]
    indicators: List[str]
    recommendations: List[str]
    analysis_time: float


class EmailHeaderAnalyzer:
    """Service for comprehensive email header analysis"""
    
    def __init__(self):
        # Required headers
        self.required_headers = {
            'from', 'to', 'subject', 'date', 'message-id'
        }
        
        # Suspicious patterns
        self.suspicious_patterns = {
            'email': [
                r'[a-z]{20,}@[a-z]{20,}',  # Very long random emails
                r'\d{10,}@',  # Many numbers in email
                r'[a-z]+\d+[a-z]+@',  # Mixed random pattern
            ],
            'domain': [
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',  # IP in domain
                r'[a-z]{15,}\.(tk|ml|ga|cf)',  # Random + suspicious TLD
            ],
            'subject': [
                r'urgent.*action.*required',
                r'verify.*account.*now',
                r'password.*expired',
                r'click.*here.*immediately',
                r'bank.*security.*alert',
            ]
        }
        
        # Known malicious headers
        self.malicious_headers = {
            'x-priority': ['1', 'high', 'urgent'],
            'x-msmail-priority': ['high', 'urgent'],
            'x-mailer': ['outlook', 'thunderbird'],  # Can be spoofed
        }
        
        # Header validation rules
        self.header_rules = {
            'from': self._validate_from_header,
            'to': self._validate_to_header,
            'subject': self._validate_subject_header,
            'date': self._validate_date_header,
            'message-id': self._validate_message_id_header,
            'received': self._validate_received_header,
            'return-path': self._validate_return_path_header,
            'reply-to': self._validate_reply_to_header,
            'x-originating-ip': self._validate_originating_ip_header,
        }
    
    async def analyze_headers(self, headers: Dict[str, str]) -> EmailHeaderAnalysis:
        """
        Analyze email headers for security threats
        
        Args:
            headers: Dictionary of email headers
            
        Returns:
            EmailHeaderAnalysis with comprehensive results
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info("Analyzing email headers")
            
            # Analyze individual headers
            header_analyses = []
            for header_name, header_value in headers.items():
                analysis = await self._analyze_header(header_name, header_value, headers)
                header_analyses.append(analysis)
            
            # Check for missing required headers
            missing_headers = self.required_headers - set(headers.keys())
            if missing_headers:
                for missing_header in missing_headers:
                    header_analyses.append(HeaderAnalysis(
                        header_name=missing_header,
                        header_value="",
                        is_valid=False,
                        risk_level=HeaderRisk.HIGH,
                        anomalies=[HeaderAnomaly.MISSING_HEADERS],
                        indicators=[f"Missing required header: {missing_header}"],
                        metadata={}
                    ))
            
            # Analyze header relationships
            relationship_analysis = self._analyze_header_relationships(headers)
            
            # Calculate overall risk
            overall_risk, risk_score = self._calculate_overall_risk(header_analyses, relationship_analysis)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(header_analyses, relationship_analysis)
            
            # Collect all anomalies and indicators
            all_anomalies = []
            all_indicators = []
            for analysis in header_analyses:
                all_anomalies.extend(analysis.anomalies)
                all_indicators.extend(analysis.indicators)
            
            analysis_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = EmailHeaderAnalysis(
                overall_risk=overall_risk,
                risk_score=risk_score,
                header_analyses=header_analyses,
                anomalies=list(set(all_anomalies)),
                indicators=list(set(all_indicators)),
                recommendations=recommendations,
                analysis_time=analysis_time
            )
            
            logger.info(f"Header analysis complete: {overall_risk.value} (score: {risk_score:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing headers: {e}")
            return EmailHeaderAnalysis(
                overall_risk=HeaderRisk.CRITICAL,
                risk_score=1.0,
                header_analyses=[],
                anomalies=[HeaderAnomaly.INVALID_FORMAT],
                indicators=["Header analysis failed"],
                recommendations=["Manual review required"],
                analysis_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    async def _analyze_header(self, header_name: str, header_value: str, all_headers: Dict[str, str]) -> HeaderAnalysis:
        """Analyze a single header"""
        try:
            # Decode header value
            decoded_value = self._decode_header_value(header_value)
            
            # Check if we have a specific validator
            if header_name.lower() in self.header_rules:
                validator = self.header_rules[header_name.lower()]
                is_valid, risk_level, anomalies, indicators, metadata = validator(decoded_value, all_headers)
            else:
                # Generic header validation
                is_valid, risk_level, anomalies, indicators, metadata = self._validate_generic_header(
                    header_name, decoded_value, all_headers
                )
            
            return HeaderAnalysis(
                header_name=header_name,
                header_value=decoded_value,
                is_valid=is_valid,
                risk_level=risk_level,
                anomalies=anomalies,
                indicators=indicators,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error analyzing header {header_name}: {e}")
            return HeaderAnalysis(
                header_name=header_name,
                header_value=header_value,
                is_valid=False,
                risk_level=HeaderRisk.CRITICAL,
                anomalies=[HeaderAnomaly.INVALID_FORMAT],
                indicators=[f"Header analysis error: {str(e)}"],
                metadata={"error": str(e)}
            )
    
    def _decode_header_value(self, header_value: str) -> str:
        """Decode header value (handle encoding)"""
        try:
            # Handle quoted-printable encoding
            if '=?' in header_value and '?=' in header_value:
                decoded_parts = []
                for part in header_value.split():
                    if '=?' in part and '?=' in part:
                        try:
                            decoded_part = email.header.decode_header(part)[0][0]
                            if isinstance(decoded_part, bytes):
                                decoded_part = decoded_part.decode('utf-8', errors='ignore')
                            decoded_parts.append(decoded_part)
                        except:
                            decoded_parts.append(part)
                    else:
                        decoded_parts.append(part)
                return ' '.join(decoded_parts)
            
            # Handle base64 encoding
            if header_value.startswith('=?') and header_value.endswith('?='):
                try:
                    decoded = email.header.decode_header(header_value)[0][0]
                    if isinstance(decoded, bytes):
                        decoded = decoded.decode('utf-8', errors='ignore')
                    return decoded
                except:
                    pass
            
            return header_value
            
        except Exception:
            return header_value
    
    def _validate_from_header(self, value: str, all_headers: Dict[str, str]) -> Tuple[bool, HeaderRisk, List[HeaderAnomaly], List[str], Dict[str, Any]]:
        """Validate From header"""
        anomalies = []
        indicators = []
        metadata = {}
        risk_level = HeaderRisk.SAFE
        
        try:
            # Parse email address
            name, email_addr = email.utils.parseaddr(value)
            
            if not email_addr:
                return False, HeaderRisk.CRITICAL, [HeaderAnomaly.INVALID_FORMAT], ["Invalid From header format"], {}
            
            # Check for suspicious patterns
            if re.search(r'[a-z]{20,}@[a-z]{20,}', email_addr, re.IGNORECASE):
                anomalies.append(HeaderAnomaly.SUSPICIOUS_VALUES)
                indicators.append("Suspicious email pattern in From header")
                risk_level = HeaderRisk.HIGH
            
            # Check domain
            domain = email_addr.split('@')[1] if '@' in email_addr else ''
            if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', domain):
                anomalies.append(HeaderAnomaly.SUSPICIOUS_VALUES)
                indicators.append("IP address in From domain")
                risk_level = HeaderRisk.HIGH
            
            # Check for spoofing
            if 'return-path' in all_headers:
                return_path = all_headers['return-path']
                if email_addr.lower() not in return_path.lower():
                    anomalies.append(HeaderAnomaly.SPOOFING_ATTEMPT)
                    indicators.append("From header doesn't match Return-Path")
                    risk_level = HeaderRisk.MEDIUM
            
            metadata = {
                'parsed_name': name,
                'parsed_email': email_addr,
                'domain': domain
            }
            
            return True, risk_level, anomalies, indicators, metadata
            
        except Exception as e:
            return False, HeaderRisk.CRITICAL, [HeaderAnomaly.INVALID_FORMAT], [f"From header validation error: {str(e)}"], {}
    
    def _validate_to_header(self, value: str, all_headers: Dict[str, str]) -> Tuple[bool, HeaderRisk, List[HeaderAnomaly], List[str], Dict[str, Any]]:
        """Validate To header"""
        anomalies = []
        indicators = []
        metadata = {}
        risk_level = HeaderRisk.SAFE
        
        try:
            # Parse recipients
            recipients = email.utils.getaddresses([value])
            
            if not recipients:
                return False, HeaderRisk.CRITICAL, [HeaderAnomaly.INVALID_FORMAT], ["Invalid To header format"], {}
            
            # Check for suspicious patterns
            for name, email_addr in recipients:
                if re.search(r'[a-z]{20,}@[a-z]{20,}', email_addr, re.IGNORECASE):
                    anomalies.append(HeaderAnomaly.SUSPICIOUS_VALUES)
                    indicators.append("Suspicious email pattern in To header")
                    risk_level = HeaderRisk.MEDIUM
            
            metadata = {
                'recipient_count': len(recipients),
                'recipients': recipients
            }
            
            return True, risk_level, anomalies, indicators, metadata
            
        except Exception as e:
            return False, HeaderRisk.CRITICAL, [HeaderAnomaly.INVALID_FORMAT], [f"To header validation error: {str(e)}"], {}
    
    def _validate_subject_header(self, value: str, all_headers: Dict[str, str]) -> Tuple[bool, HeaderRisk, List[HeaderAnomaly], List[str], Dict[str, Any]]:
        """Validate Subject header"""
        anomalies = []
        indicators = []
        metadata = {}
        risk_level = HeaderRisk.SAFE
        
        try:
            # Check for suspicious patterns
            for pattern in self.suspicious_patterns['subject']:
                if re.search(pattern, value, re.IGNORECASE):
                    anomalies.append(HeaderAnomaly.SUSPICIOUS_VALUES)
                    indicators.append(f"Suspicious subject pattern: {pattern}")
                    risk_level = HeaderRisk.MEDIUM
            
            # Check for excessive urgency indicators
            urgency_words = ['urgent', 'immediate', 'asap', 'critical', 'emergency']
            urgency_count = sum(1 for word in urgency_words if word in value.lower())
            if urgency_count >= 2:
                anomalies.append(HeaderAnomaly.SUSPICIOUS_VALUES)
                indicators.append("Excessive urgency indicators in subject")
                risk_level = HeaderRisk.MEDIUM
            
            # Check for suspicious encoding
            if '=?' in value and '?=' in value:
                # Check for suspicious encoded content
                if len(value) > 200:  # Very long encoded subject
                    anomalies.append(HeaderAnomaly.ENCODING_ANOMALY)
                    indicators.append("Suspiciously long encoded subject")
                    risk_level = HeaderRisk.LOW
            
            metadata = {
                'length': len(value),
                'urgency_count': urgency_count,
                'is_encoded': '=?' in value
            }
            
            return True, risk_level, anomalies, indicators, metadata
            
        except Exception as e:
            return False, HeaderRisk.CRITICAL, [HeaderAnomaly.INVALID_FORMAT], [f"Subject header validation error: {str(e)}"], {}
    
    def _validate_date_header(self, value: str, all_headers: Dict[str, str]) -> Tuple[bool, HeaderRisk, List[HeaderAnomaly], List[str], Dict[str, Any]]:
        """Validate Date header"""
        anomalies = []
        indicators = []
        metadata = {}
        risk_level = HeaderRisk.SAFE
        
        try:
            # Parse date
            parsed_date = email.utils.parsedate_to_datetime(value)
            current_time = datetime.utcnow()
            
            # Check for future dates
            if parsed_date > current_time + timedelta(hours=1):
                anomalies.append(HeaderAnomaly.TIMING_ANOMALY)
                indicators.append("Date header is in the future")
                risk_level = HeaderRisk.MEDIUM
            
            # Check for very old dates
            if parsed_date < current_time - timedelta(days=365):
                anomalies.append(HeaderAnomaly.TIMING_ANOMALY)
                indicators.append("Date header is very old")
                risk_level = HeaderRisk.LOW
            
            metadata = {
                'parsed_date': parsed_date.isoformat(),
                'current_time': current_time.isoformat(),
                'time_diff_hours': (current_time - parsed_date).total_seconds() / 3600
            }
            
            return True, risk_level, anomalies, indicators, metadata
            
        except Exception as e:
            return False, HeaderRisk.CRITICAL, [HeaderAnomaly.INVALID_FORMAT], [f"Date header validation error: {str(e)}"], {}
    
    def _validate_message_id_header(self, value: str, all_headers: Dict[str, str]) -> Tuple[bool, HeaderRisk, List[HeaderAnomaly], List[str], Dict[str, Any]]:
        """Validate Message-ID header"""
        anomalies = []
        indicators = []
        metadata = {}
        risk_level = HeaderRisk.SAFE
        
        try:
            # Check format
            if not (value.startswith('<') and value.endswith('>')):
                anomalies.append(HeaderAnomaly.INVALID_FORMAT)
                indicators.append("Message-ID should be enclosed in angle brackets")
                risk_level = HeaderRisk.MEDIUM
            
            # Check for suspicious patterns
            if re.search(r'[a-z]{20,}', value, re.IGNORECASE):
                anomalies.append(HeaderAnomaly.SUSPICIOUS_VALUES)
                indicators.append("Suspicious pattern in Message-ID")
                risk_level = HeaderRisk.MEDIUM
            
            metadata = {
                'length': len(value),
                'has_angle_brackets': value.startswith('<') and value.endswith('>')
            }
            
            return True, risk_level, anomalies, indicators, metadata
            
        except Exception as e:
            return False, HeaderRisk.CRITICAL, [HeaderAnomaly.INVALID_FORMAT], [f"Message-ID header validation error: {str(e)}"], {}
    
    def _validate_received_header(self, value: str, all_headers: Dict[str, str]) -> Tuple[bool, HeaderRisk, List[HeaderAnomaly], List[str], Dict[str, Any]]:
        """Validate Received header"""
        anomalies = []
        indicators = []
        metadata = {}
        risk_level = HeaderRisk.SAFE
        
        try:
            # Check for suspicious IP addresses
            ip_pattern = r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
            ips = re.findall(ip_pattern, value)
            
            for ip in ips:
                try:
                    ip_obj = ipaddress.ip_address(ip)
                    if ip_obj.is_private:
                        anomalies.append(HeaderAnomaly.ROUTING_ANOMALY)
                        indicators.append("Private IP in Received header")
                        risk_level = HeaderRisk.MEDIUM
                except:
                    pass
            
            metadata = {
                'ip_addresses': ips,
                'length': len(value)
            }
            
            return True, risk_level, anomalies, indicators, metadata
            
        except Exception as e:
            return False, HeaderRisk.CRITICAL, [HeaderAnomaly.INVALID_FORMAT], [f"Received header validation error: {str(e)}"], {}
    
    def _validate_return_path_header(self, value: str, all_headers: Dict[str, str]) -> Tuple[bool, HeaderRisk, List[HeaderAnomaly], List[str], Dict[str, Any]]:
        """Validate Return-Path header"""
        anomalies = []
        indicators = []
        metadata = {}
        risk_level = HeaderRisk.SAFE
        
        try:
            # Check format
            if not (value.startswith('<') and value.endswith('>')):
                anomalies.append(HeaderAnomaly.INVALID_FORMAT)
                indicators.append("Return-Path should be enclosed in angle brackets")
                risk_level = HeaderRisk.MEDIUM
            
            # Extract email
            email_addr = value.strip('<>')
            
            # Check for suspicious patterns
            if re.search(r'[a-z]{20,}@[a-z]{20,}', email_addr, re.IGNORECASE):
                anomalies.append(HeaderAnomaly.SUSPICIOUS_VALUES)
                indicators.append("Suspicious email pattern in Return-Path")
                risk_level = HeaderRisk.HIGH
            
            metadata = {
                'email_address': email_addr,
                'has_angle_brackets': value.startswith('<') and value.endswith('>')
            }
            
            return True, risk_level, anomalies, indicators, metadata
            
        except Exception as e:
            return False, HeaderRisk.CRITICAL, [HeaderAnomaly.INVALID_FORMAT], [f"Return-Path header validation error: {str(e)}"], {}
    
    def _validate_reply_to_header(self, value: str, all_headers: Dict[str, str]) -> Tuple[bool, HeaderRisk, List[HeaderAnomaly], List[str], Dict[str, Any]]:
        """Validate Reply-To header"""
        anomalies = []
        indicators = []
        metadata = {}
        risk_level = HeaderRisk.SAFE
        
        try:
            # Parse email address
            name, email_addr = email.utils.parseaddr(value)
            
            if email_addr:
                # Check for suspicious patterns
                if re.search(r'[a-z]{20,}@[a-z]{20,}', email_addr, re.IGNORECASE):
                    anomalies.append(HeaderAnomaly.SUSPICIOUS_VALUES)
                    indicators.append("Suspicious email pattern in Reply-To header")
                    risk_level = HeaderRisk.MEDIUM
                
                # Check if Reply-To differs from From
                if 'from' in all_headers:
                    from_name, from_email = email.utils.parseaddr(all_headers['from'])
                    if email_addr.lower() != from_email.lower():
                        anomalies.append(HeaderAnomaly.SPOOFING_ATTEMPT)
                        indicators.append("Reply-To differs from From header")
                        risk_level = HeaderRisk.MEDIUM
            
            metadata = {
                'parsed_name': name,
                'parsed_email': email_addr
            }
            
            return True, risk_level, anomalies, indicators, metadata
            
        except Exception as e:
            return False, HeaderRisk.CRITICAL, [HeaderAnomaly.INVALID_FORMAT], [f"Reply-To header validation error: {str(e)}"], {}
    
    def _validate_originating_ip_header(self, value: str, all_headers: Dict[str, str]) -> Tuple[bool, HeaderRisk, List[HeaderAnomaly], List[str], Dict[str, Any]]:
        """Validate X-Originating-IP header"""
        anomalies = []
        indicators = []
        metadata = {}
        risk_level = HeaderRisk.SAFE
        
        try:
            # Check if it's a valid IP
            try:
                ip_obj = ipaddress.ip_address(value)
                if ip_obj.is_private:
                    anomalies.append(HeaderAnomaly.ROUTING_ANOMALY)
                    indicators.append("Private IP in X-Originating-IP header")
                    risk_level = HeaderRisk.MEDIUM
            except:
                anomalies.append(HeaderAnomaly.INVALID_FORMAT)
                indicators.append("Invalid IP address in X-Originating-IP header")
                risk_level = HeaderRisk.HIGH
            
            metadata = {
                'ip_address': value,
                'is_valid_ip': True
            }
            
            return True, risk_level, anomalies, indicators, metadata
            
        except Exception as e:
            return False, HeaderRisk.CRITICAL, [HeaderAnomaly.INVALID_FORMAT], [f"X-Originating-IP header validation error: {str(e)}"], {}
    
    def _validate_generic_header(self, header_name: str, value: str, all_headers: Dict[str, str]) -> Tuple[bool, HeaderRisk, List[HeaderAnomaly], List[str], Dict[str, Any]]:
        """Validate generic header"""
        anomalies = []
        indicators = []
        metadata = {}
        risk_level = HeaderRisk.SAFE
        
        try:
            # Check for suspicious patterns in header name
            if re.search(r'[^a-zA-Z0-9\-]', header_name):
                anomalies.append(HeaderAnomaly.INVALID_FORMAT)
                indicators.append("Invalid characters in header name")
                risk_level = HeaderRisk.MEDIUM
            
            # Check for suspicious patterns in value
            if re.search(r'[a-z]{30,}', value, re.IGNORECASE):
                anomalies.append(HeaderAnomaly.SUSPICIOUS_VALUES)
                indicators.append("Suspiciously long random string in header value")
                risk_level = HeaderRisk.MEDIUM
            
            metadata = {
                'header_name_length': len(header_name),
                'value_length': len(value)
            }
            
            return True, risk_level, anomalies, indicators, metadata
            
        except Exception as e:
            return False, HeaderRisk.CRITICAL, [HeaderAnomaly.INVALID_FORMAT], [f"Generic header validation error: {str(e)}"], {}
    
    def _analyze_header_relationships(self, headers: Dict[str, str]) -> Dict[str, Any]:
        """Analyze relationships between headers"""
        analysis = {
            'from_return_path_mismatch': False,
            'reply_to_from_mismatch': False,
            'multiple_received_headers': False,
            'suspicious_priority': False
        }
        
        try:
            # Check From vs Return-Path
            if 'from' in headers and 'return-path' in headers:
                from_email = email.utils.parseaddr(headers['from'])[1]
                return_path_email = headers['return-path'].strip('<>')
                if from_email.lower() != return_path_email.lower():
                    analysis['from_return_path_mismatch'] = True
            
            # Check Reply-To vs From
            if 'reply-to' in headers and 'from' in headers:
                reply_to_email = email.utils.parseaddr(headers['reply-to'])[1]
                from_email = email.utils.parseaddr(headers['from'])[1]
                if reply_to_email.lower() != from_email.lower():
                    analysis['reply_to_from_mismatch'] = True
            
            # Check for multiple Received headers
            received_headers = [h for h in headers.keys() if h.lower() == 'received']
            if len(received_headers) > 5:
                analysis['multiple_received_headers'] = True
            
            # Check for suspicious priority
            if 'x-priority' in headers and headers['x-priority'] in ['1', 'high', 'urgent']:
                analysis['suspicious_priority'] = True
            
        except Exception as e:
            logger.error(f"Error analyzing header relationships: {e}")
        
        return analysis
    
    def _calculate_overall_risk(self, header_analyses: List[HeaderAnalysis], relationship_analysis: Dict[str, Any]) -> Tuple[HeaderRisk, float]:
        """Calculate overall risk level and score"""
        if not header_analyses:
            return HeaderRisk.CRITICAL, 1.0
        
        # Calculate risk scores
        risk_scores = []
        for analysis in header_analyses:
            if analysis.risk_level == HeaderRisk.SAFE:
                risk_scores.append(0.0)
            elif analysis.risk_level == HeaderRisk.LOW:
                risk_scores.append(0.2)
            elif analysis.risk_level == HeaderRisk.MEDIUM:
                risk_scores.append(0.5)
            elif analysis.risk_level == HeaderRisk.HIGH:
                risk_scores.append(0.8)
            else:  # CRITICAL
                risk_scores.append(1.0)
        
        # Add relationship analysis penalties
        if relationship_analysis.get('from_return_path_mismatch'):
            risk_scores.append(0.6)
        if relationship_analysis.get('reply_to_from_mismatch'):
            risk_scores.append(0.4)
        if relationship_analysis.get('multiple_received_headers'):
            risk_scores.append(0.3)
        if relationship_analysis.get('suspicious_priority'):
            risk_scores.append(0.2)
        
        # Calculate average risk score
        if risk_scores:
            avg_score = sum(risk_scores) / len(risk_scores)
        else:
            avg_score = 0.0
        
        # Determine risk level
        if avg_score >= 0.8:
            risk_level = HeaderRisk.CRITICAL
        elif avg_score >= 0.6:
            risk_level = HeaderRisk.HIGH
        elif avg_score >= 0.4:
            risk_level = HeaderRisk.MEDIUM
        elif avg_score >= 0.2:
            risk_level = HeaderRisk.LOW
        else:
            risk_level = HeaderRisk.SAFE
        
        return risk_level, avg_score
    
    def _generate_recommendations(self, header_analyses: List[HeaderAnalysis], relationship_analysis: Dict[str, Any]) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        
        # Check for critical issues
        critical_issues = [a for a in header_analyses if a.risk_level == HeaderRisk.CRITICAL]
        if critical_issues:
            recommendations.append("Critical header validation failures detected - manual review required")
        
        # Check for high-risk issues
        high_risk_issues = [a for a in header_analyses if a.risk_level == HeaderRisk.HIGH]
        if high_risk_issues:
            recommendations.append("High-risk header anomalies detected - consider blocking")
        
        # Check for spoofing attempts
        spoofing_attempts = [a for a in header_analyses if HeaderAnomaly.SPOOFING_ATTEMPT in a.anomalies]
        if spoofing_attempts:
            recommendations.append("Potential email spoofing detected - verify sender authenticity")
        
        # Check for missing headers
        missing_headers = [a for a in header_analyses if HeaderAnomaly.MISSING_HEADERS in a.anomalies]
        if missing_headers:
            recommendations.append("Required headers missing - email may be malformed")
        
        # Check for relationship issues
        if relationship_analysis.get('from_return_path_mismatch'):
            recommendations.append("From and Return-Path headers don't match - potential spoofing")
        
        if relationship_analysis.get('reply_to_from_mismatch'):
            recommendations.append("Reply-To and From headers don't match - verify sender intent")
        
        return recommendations


# Global instance
email_header_analyzer = EmailHeaderAnalyzer()
