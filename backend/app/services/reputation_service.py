"""
Reputation Service
Implements domain and IP reputation checking for email security
"""

import asyncio
import aiohttp
import structlog
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import ipaddress
import re
from datetime import datetime, timedelta
import json

logger = structlog.get_logger()


class ReputationLevel(Enum):
    """Reputation levels"""
    TRUSTED = "trusted"
    GOOD = "good"
    NEUTRAL = "neutral"
    SUSPICIOUS = "suspicious"
    MALICIOUS = "malicious"
    UNKNOWN = "unknown"


@dataclass
class ReputationResult:
    """Reputation check result"""
    level: ReputationLevel
    score: float
    confidence: float
    sources: List[str]
    details: Dict[str, Any]
    last_updated: datetime
    recommendations: List[str]


@dataclass
class DomainReputationResult(ReputationResult):
    """Domain reputation result"""
    domain: str
    registration_date: Optional[datetime] = None
    registrar: Optional[str] = None
    country: Optional[str] = None
    is_disposable: bool = False
    is_typosquat: bool = False


@dataclass
class IPReputationResult(ReputationResult):
    """IP reputation result"""
    ip_address: str
    country: Optional[str] = None
    isp: Optional[str] = None
    is_proxy: bool = False
    is_tor: bool = False
    is_vpn: bool = False


class ReputationService:
    """Service for checking domain and IP reputation"""
    
    def __init__(self):
        self.session_timeout = 10
        self.cache_ttl = 3600  # 1 hour
        self.reputation_cache = {}
        
        # Known malicious patterns
        self.malicious_patterns = [
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',  # IP in domain
            r'[a-z]{20,}',  # Very long random strings
            r'\d{10,}',  # Many numbers
            r'[a-z]+\d+[a-z]+',  # Mixed random pattern
        ]
        
        # Disposable email domains (sample)
        self.disposable_domains = {
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'throwaway.email', 'temp-mail.org'
        }
        
        # Known typosquatting patterns
        self.typosquat_patterns = [
            'microsoft', 'google', 'amazon', 'paypal', 'apple',
            'facebook', 'twitter', 'linkedin', 'github', 'dropbox'
        ]
    
    async def check_domain_reputation(self, domain: str) -> DomainReputationResult:
        """Check domain reputation"""
        try:
            # Check cache first
            cache_key = f"domain:{domain}"
            if cache_key in self.reputation_cache:
                cached_result, timestamp = self.reputation_cache[cache_key]
                if datetime.utcnow() - timestamp < timedelta(seconds=self.cache_ttl):
                    return cached_result
            
            logger.info(f"Checking domain reputation for {domain}")
            
            # Run multiple reputation checks in parallel
            tasks = [
                self._check_domain_age(domain),
                self._check_disposable_domain(domain),
                self._check_typosquatting(domain),
                self._check_domain_patterns(domain),
                self._check_external_reputation(domain)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            age_result = results[0] if not isinstance(results[0], Exception) else {}
            is_disposable = results[1] if not isinstance(results[1], Exception) else False
            is_typosquat = results[2] if not isinstance(results[2], Exception) else False
            pattern_result = results[3] if not isinstance(results[3], Exception) else {}
            external_result = results[4] if not isinstance(results[4], Exception) else {}
            
            # Calculate reputation score
            score, level, confidence = self._calculate_domain_reputation(
                age_result, is_disposable, is_typosquat, pattern_result, external_result
            )
            
            # Generate recommendations
            recommendations = self._generate_domain_recommendations(
                domain, is_disposable, is_typosquat, pattern_result, external_result
            )
            
            result = DomainReputationResult(
                level=level,
                score=score,
                confidence=confidence,
                sources=["domain_age", "disposable_check", "typosquat_check", "pattern_analysis", "external_feeds"],
                details={
                    "age": age_result,
                    "is_disposable": is_disposable,
                    "is_typosquat": is_typosquat,
                    "patterns": pattern_result,
                    "external": external_result
                },
                last_updated=datetime.utcnow(),
                recommendations=recommendations,
                domain=domain,
                registration_date=age_result.get("registration_date"),
                registrar=age_result.get("registrar"),
                country=age_result.get("country"),
                is_disposable=is_disposable,
                is_typosquat=is_typosquat
            )
            
            # Cache result
            self.reputation_cache[cache_key] = (result, datetime.utcnow())
            
            logger.info(f"Domain reputation for {domain}: {level.value} (score: {score:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error checking domain reputation for {domain}: {e}")
            return DomainReputationResult(
                level=ReputationLevel.UNKNOWN,
                score=0.5,
                confidence=0.0,
                sources=[],
                details={"error": str(e)},
                last_updated=datetime.utcnow(),
                recommendations=["Domain reputation check failed"],
                domain=domain
            )
    
    async def check_ip_reputation(self, ip_address: str) -> IPReputationResult:
        """Check IP reputation"""
        try:
            # Check cache first
            cache_key = f"ip:{ip_address}"
            if cache_key in self.reputation_cache:
                cached_result, timestamp = self.reputation_cache[cache_key]
                if datetime.utcnow() - timestamp < timedelta(seconds=self.cache_ttl):
                    return cached_result
            
            logger.info(f"Checking IP reputation for {ip_address}")
            
            # Run multiple reputation checks in parallel
            tasks = [
                self._check_ip_geolocation(ip_address),
                self._check_proxy_vpn(ip_address),
                self._check_tor_exit(ip_address),
                self._check_external_ip_reputation(ip_address)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            geo_result = results[0] if not isinstance(results[0], Exception) else {}
            proxy_result = results[1] if not isinstance(results[1], Exception) else {}
            tor_result = results[2] if not isinstance(results[2], Exception) else False
            external_result = results[3] if not isinstance(results[3], Exception) else {}
            
            # Calculate reputation score
            score, level, confidence = self._calculate_ip_reputation(
                geo_result, proxy_result, tor_result, external_result
            )
            
            # Generate recommendations
            recommendations = self._generate_ip_recommendations(
                ip_address, geo_result, proxy_result, tor_result, external_result
            )
            
            result = IPReputationResult(
                level=level,
                score=score,
                confidence=confidence,
                sources=["geolocation", "proxy_check", "tor_check", "external_feeds"],
                details={
                    "geolocation": geo_result,
                    "proxy": proxy_result,
                    "is_tor": tor_result,
                    "external": external_result
                },
                last_updated=datetime.utcnow(),
                recommendations=recommendations,
                ip_address=ip_address,
                country=geo_result.get("country"),
                isp=geo_result.get("isp"),
                is_proxy=proxy_result.get("is_proxy", False),
                is_tor=tor_result,
                is_vpn=proxy_result.get("is_vpn", False)
            )
            
            # Cache result
            self.reputation_cache[cache_key] = (result, datetime.utcnow())
            
            logger.info(f"IP reputation for {ip_address}: {level.value} (score: {score:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error checking IP reputation for {ip_address}: {e}")
            return IPReputationResult(
                level=ReputationLevel.UNKNOWN,
                score=0.5,
                confidence=0.0,
                sources=[],
                details={"error": str(e)},
                last_updated=datetime.utcnow(),
                recommendations=["IP reputation check failed"],
                ip_address=ip_address
            )
    
    async def _check_domain_age(self, domain: str) -> Dict[str, Any]:
        """Check domain age and registration details"""
        try:
            # Simulate domain age check (in production, use WHOIS API)
            # For MVP, return mock data
            return {
                "registration_date": datetime.utcnow() - timedelta(days=365),
                "age_days": 365,
                "registrar": "Example Registrar",
                "country": "US",
                "is_new": False
            }
        except Exception as e:
            logger.error(f"Error checking domain age: {e}")
            return {}
    
    async def _check_disposable_domain(self, domain: str) -> bool:
        """Check if domain is a disposable email service"""
        try:
            domain_lower = domain.lower()
            return domain_lower in self.disposable_domains
        except Exception:
            return False
    
    async def _check_typosquatting(self, domain: str) -> bool:
        """Check for typosquatting patterns"""
        try:
            domain_lower = domain.lower()
            for pattern in self.typosquat_patterns:
                if pattern in domain_lower:
                    # Check if it's a close variation
                    if self._is_typosquat_variation(domain_lower, pattern):
                        return True
            return False
        except Exception:
            return False
    
    async def _check_domain_patterns(self, domain: str) -> Dict[str, Any]:
        """Check domain for suspicious patterns"""
        try:
            patterns_found = []
            is_suspicious = False
            
            for pattern in self.malicious_patterns:
                if re.search(pattern, domain):
                    patterns_found.append(pattern)
                    is_suspicious = True
            
            return {
                "patterns_found": patterns_found,
                "is_suspicious": is_suspicious,
                "length": len(domain),
                "has_numbers": bool(re.search(r'\d', domain)),
                "has_hyphens": '-' in domain
            }
        except Exception:
            return {}
    
    async def _check_external_reputation(self, domain: str) -> Dict[str, Any]:
        """Check external reputation feeds"""
        try:
            # Simulate external reputation check
            # In production, integrate with real threat intelligence feeds
            return {
                "malware_detections": 0,
                "phishing_detections": 0,
                "spam_detections": 0,
                "reputation_score": 0.8
            }
        except Exception:
            return {}
    
    async def _check_ip_geolocation(self, ip_address: str) -> Dict[str, Any]:
        """Check IP geolocation"""
        try:
            # Simulate geolocation check
            # In production, use real geolocation API
            return {
                "country": "US",
                "region": "California",
                "city": "San Francisco",
                "isp": "Example ISP",
                "organization": "Example Corp"
            }
        except Exception:
            return {}
    
    async def _check_proxy_vpn(self, ip_address: str) -> Dict[str, Any]:
        """Check if IP is a proxy or VPN"""
        try:
            # Simulate proxy/VPN check
            # In production, use real proxy detection API
            return {
                "is_proxy": False,
                "is_vpn": False,
                "proxy_type": None
            }
        except Exception:
            return {}
    
    async def _check_tor_exit(self, ip_address: str) -> bool:
        """Check if IP is a Tor exit node"""
        try:
            # Simulate Tor exit node check
            # In production, use real Tor exit node list
            return False
        except Exception:
            return False
    
    async def _check_external_ip_reputation(self, ip_address: str) -> Dict[str, Any]:
        """Check external IP reputation feeds"""
        try:
            # Simulate external IP reputation check
            return {
                "malware_detections": 0,
                "spam_detections": 0,
                "reputation_score": 0.8
            }
        except Exception:
            return {}
    
    def _is_typosquat_variation(self, domain: str, brand: str) -> bool:
        """Check if domain is a typosquatting variation of a brand"""
        try:
            # Simple typosquatting detection
            # In production, use more sophisticated algorithms
            if brand in domain:
                # Check for common typosquatting patterns
                variations = [
                    brand + "s",  # plurals
                    brand + "-" + "official",  # fake official
                    brand + "-" + "secure",  # fake secure
                    "my-" + brand,  # my-brand
                    brand + "-" + "login"  # fake login
                ]
                return any(var in domain for var in variations)
            return False
        except Exception:
            return False
    
    def _calculate_domain_reputation(
        self, 
        age_result: Dict[str, Any],
        is_disposable: bool,
        is_typosquat: bool,
        pattern_result: Dict[str, Any],
        external_result: Dict[str, Any]
    ) -> Tuple[float, ReputationLevel, float]:
        """Calculate domain reputation score and level"""
        score = 0.5  # Start neutral
        confidence = 0.8
        
        # Age factor
        if age_result.get("age_days", 0) > 365:
            score += 0.2
        elif age_result.get("age_days", 0) < 30:
            score -= 0.3
        
        # Disposable domain
        if is_disposable:
            score -= 0.4
        
        # Typosquatting
        if is_typosquat:
            score -= 0.5
        
        # Pattern analysis
        if pattern_result.get("is_suspicious", False):
            score -= 0.3
        
        # External reputation
        external_score = external_result.get("reputation_score", 0.5)
        score = (score + external_score) / 2
        
        # Determine level
        if score >= 0.8:
            level = ReputationLevel.TRUSTED
        elif score >= 0.6:
            level = ReputationLevel.GOOD
        elif score >= 0.4:
            level = ReputationLevel.NEUTRAL
        elif score >= 0.2:
            level = ReputationLevel.SUSPICIOUS
        else:
            level = ReputationLevel.MALICIOUS
        
        return max(0.0, min(1.0, score)), level, confidence
    
    def _calculate_ip_reputation(
        self,
        geo_result: Dict[str, Any],
        proxy_result: Dict[str, Any],
        is_tor: bool,
        external_result: Dict[str, Any]
    ) -> Tuple[float, ReputationLevel, float]:
        """Calculate IP reputation score and level"""
        score = 0.5  # Start neutral
        confidence = 0.8
        
        # Proxy/VPN detection
        if proxy_result.get("is_proxy", False):
            score -= 0.3
        if proxy_result.get("is_vpn", False):
            score -= 0.2
        
        # Tor exit node
        if is_tor:
            score -= 0.5
        
        # External reputation
        external_score = external_result.get("reputation_score", 0.5)
        score = (score + external_score) / 2
        
        # Determine level
        if score >= 0.8:
            level = ReputationLevel.TRUSTED
        elif score >= 0.6:
            level = ReputationLevel.GOOD
        elif score >= 0.4:
            level = ReputationLevel.NEUTRAL
        elif score >= 0.2:
            level = ReputationLevel.SUSPICIOUS
        else:
            level = ReputationLevel.MALICIOUS
        
        return max(0.0, min(1.0, score)), level, confidence
    
    def _generate_domain_recommendations(
        self,
        domain: str,
        is_disposable: bool,
        is_typosquat: bool,
        pattern_result: Dict[str, Any],
        external_result: Dict[str, Any]
    ) -> List[str]:
        """Generate domain reputation recommendations"""
        recommendations = []
        
        if is_disposable:
            recommendations.append("Domain appears to be a disposable email service")
        
        if is_typosquat:
            recommendations.append("Domain may be typosquatting a known brand")
        
        if pattern_result.get("is_suspicious", False):
            recommendations.append("Domain has suspicious patterns")
        
        if external_result.get("malware_detections", 0) > 0:
            recommendations.append("Domain has been associated with malware")
        
        if external_result.get("phishing_detections", 0) > 0:
            recommendations.append("Domain has been used for phishing")
        
        return recommendations
    
    def _generate_ip_recommendations(
        self,
        ip_address: str,
        geo_result: Dict[str, Any],
        proxy_result: Dict[str, Any],
        is_tor: bool,
        external_result: Dict[str, Any]
    ) -> List[str]:
        """Generate IP reputation recommendations"""
        recommendations = []
        
        if proxy_result.get("is_proxy", False):
            recommendations.append("IP address appears to be a proxy server")
        
        if proxy_result.get("is_vpn", False):
            recommendations.append("IP address appears to be a VPN")
        
        if is_tor:
            recommendations.append("IP address is a Tor exit node")
        
        if external_result.get("malware_detections", 0) > 0:
            recommendations.append("IP address has been associated with malware")
        
        if external_result.get("spam_detections", 0) > 0:
            recommendations.append("IP address has been used for spam")
        
        return recommendations


# Global instance
reputation_service = ReputationService()
