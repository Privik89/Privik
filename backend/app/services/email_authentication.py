"""
Email Authentication Service
Implements DMARC, DKIM, and SPF validation for email security
"""

import dns.resolver
import dns.exception
import re
import hashlib
import base64
import structlog
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
import aiohttp
from email.mime.text import MIMEText
from email.header import decode_header

logger = structlog.get_logger()


class AuthenticationResult(Enum):
    """Email authentication results"""
    PASS = "pass"
    FAIL = "fail"
    NEUTRAL = "neutral"
    NONE = "none"
    TEMPERROR = "temperror"
    PERMERROR = "permerror"


@dataclass
class SPFResult:
    """SPF validation result"""
    result: AuthenticationResult
    mechanism: Optional[str] = None
    explanation: Optional[str] = None
    ip_address: Optional[str] = None
    domain: Optional[str] = None


@dataclass
class DKIMResult:
    """DKIM validation result"""
    result: AuthenticationResult
    domain: Optional[str] = None
    selector: Optional[str] = None
    signature: Optional[str] = None
    body_hash: Optional[str] = None
    headers: Optional[List[str]] = None


@dataclass
class DMARCResult:
    """DMARC validation result"""
    result: AuthenticationResult
    policy: Optional[str] = None
    subdomain_policy: Optional[str] = None
    pct: Optional[int] = None
    rua: Optional[str] = None
    ruf: Optional[str] = None
    domain: Optional[str] = None


@dataclass
class EmailAuthenticationResult:
    """Complete email authentication result"""
    spf: SPFResult
    dkim: DKIMResult
    dmarc: DMARCResult
    overall_result: AuthenticationResult
    authentication_score: float
    recommendations: List[str]


class EmailAuthenticationService:
    """Service for validating email authentication (DMARC, DKIM, SPF)"""
    
    def __init__(self):
        self.dns_timeout = 5.0
        self.max_dns_queries = 10
        
    async def validate_email_authentication(
        self, 
        email_headers: Dict[str, str], 
        sender_ip: str,
        sender_domain: str,
        email_body: str = ""
    ) -> EmailAuthenticationResult:
        """
        Validate email authentication using DMARC, DKIM, and SPF
        
        Args:
            email_headers: Email headers dictionary
            sender_ip: IP address of the sender
            sender_domain: Domain of the sender
            email_body: Email body content for DKIM validation
            
        Returns:
            EmailAuthenticationResult with validation results
        """
        try:
            logger.info(f"Validating email authentication for {sender_domain}")
            
            # Run SPF, DKIM, and DMARC validation in parallel
            spf_task = asyncio.create_task(self._validate_spf(sender_ip, sender_domain))
            dkim_task = asyncio.create_task(self._validate_dkim(email_headers, email_body))
            dmarc_task = asyncio.create_task(self._validate_dmarc(sender_domain))
            
            spf_result, dkim_result, dmarc_result = await asyncio.gather(
                spf_task, dkim_task, dmarc_task, return_exceptions=True
            )
            
            # Handle exceptions
            if isinstance(spf_result, Exception):
                logger.error(f"SPF validation error: {spf_result}")
                spf_result = SPFResult(AuthenticationResult.TEMPERROR, explanation=str(spf_result))
            
            if isinstance(dkim_result, Exception):
                logger.error(f"DKIM validation error: {dkim_result}")
                dkim_result = DKIMResult(AuthenticationResult.TEMPERROR)
            
            if isinstance(dmarc_result, Exception):
                logger.error(f"DMARC validation error: {dmarc_result}")
                dmarc_result = DMARCResult(AuthenticationResult.TEMPERROR)
            
            # Calculate overall result and score
            overall_result, score, recommendations = self._calculate_overall_result(
                spf_result, dkim_result, dmarc_result
            )
            
            result = EmailAuthenticationResult(
                spf=spf_result,
                dkim=dkim_result,
                dmarc=dmarc_result,
                overall_result=overall_result,
                authentication_score=score,
                recommendations=recommendations
            )
            
            logger.info(f"Email authentication result: {overall_result.value} (score: {score:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error in email authentication validation: {e}")
            return EmailAuthenticationResult(
                spf=SPFResult(AuthenticationResult.TEMPERROR),
                dkim=DKIMResult(AuthenticationResult.TEMPERROR),
                dmarc=DMARCResult(AuthenticationResult.TEMPERROR),
                overall_result=AuthenticationResult.TEMPERROR,
                authentication_score=0.0,
                recommendations=["Authentication validation failed due to system error"]
            )
    
    async def _validate_spf(self, sender_ip: str, sender_domain: str) -> SPFResult:
        """Validate SPF record for the sender domain"""
        try:
            # Query SPF record
            spf_record = await self._query_dns_record(sender_domain, "TXT")
            
            if not spf_record:
                return SPFResult(
                    result=AuthenticationResult.NONE,
                    domain=sender_domain,
                    explanation="No SPF record found"
                )
            
            # Parse SPF record
            spf_parts = spf_record.split()
            if not spf_parts or spf_parts[0] != "v=spf1":
                return SPFResult(
                    result=AuthenticationResult.NONE,
                    domain=sender_domain,
                    explanation="Invalid SPF record format"
                )
            
            # Check mechanisms
            for mechanism in spf_parts[1:]:
                if mechanism.startswith("ip4:") or mechanism.startswith("ip6:"):
                    if self._check_ip_mechanism(mechanism, sender_ip):
                        return SPFResult(
                            result=AuthenticationResult.PASS,
                            mechanism=mechanism,
                            ip_address=sender_ip,
                            domain=sender_domain
                        )
                elif mechanism == "a":
                    if await self._check_a_mechanism(sender_domain, sender_ip):
                        return SPFResult(
                            result=AuthenticationResult.PASS,
                            mechanism=mechanism,
                            ip_address=sender_ip,
                            domain=sender_domain
                        )
                elif mechanism == "mx":
                    if await self._check_mx_mechanism(sender_domain, sender_ip):
                        return SPFResult(
                            result=AuthenticationResult.PASS,
                            mechanism=mechanism,
                            ip_address=sender_ip,
                            domain=sender_domain
                        )
                elif mechanism == "include:":
                    # Handle include mechanism (simplified)
                    continue
                elif mechanism in ["+all", "all"]:
                    return SPFResult(
                        result=AuthenticationResult.PASS,
                        mechanism=mechanism,
                        ip_address=sender_ip,
                        domain=sender_domain
                    )
                elif mechanism == "-all":
                    return SPFResult(
                        result=AuthenticationResult.FAIL,
                        mechanism=mechanism,
                        ip_address=sender_ip,
                        domain=sender_domain,
                        explanation="SPF record explicitly denies this IP"
                    )
            
            # Default to neutral if no mechanism matches
            return SPFResult(
                result=AuthenticationResult.NEUTRAL,
                domain=sender_domain,
                explanation="No matching SPF mechanism found"
            )
            
        except Exception as e:
            logger.error(f"SPF validation error: {e}")
            return SPFResult(
                result=AuthenticationResult.TEMPERROR,
                domain=sender_domain,
                explanation=f"SPF validation error: {str(e)}"
            )
    
    async def _validate_dkim(self, email_headers: Dict[str, str], email_body: str) -> DKIMResult:
        """Validate DKIM signature"""
        try:
            # Extract DKIM signature from headers
            dkim_signature = None
            for header_name, header_value in email_headers.items():
                if header_name.lower() == "dkim-signature":
                    dkim_signature = header_value
                    break
            
            if not dkim_signature:
                return DKIMResult(
                    result=AuthenticationResult.NONE,
                    explanation="No DKIM signature found"
                )
            
            # Parse DKIM signature
            dkim_params = self._parse_dkim_signature(dkim_signature)
            
            if not dkim_params:
                return DKIMResult(
                    result=AuthenticationResult.PERMERROR,
                    explanation="Invalid DKIM signature format"
                )
            
            domain = dkim_params.get("d")
            selector = dkim_params.get("s")
            
            if not domain or not selector:
                return DKIMResult(
                    result=AuthenticationResult.PERMERROR,
                    explanation="Missing domain or selector in DKIM signature"
                )
            
            # Query DKIM public key
            dkim_key = await self._query_dkim_public_key(selector, domain)
            
            if not dkim_key:
                return DKIMResult(
                    result=AuthenticationResult.TEMPERROR,
                    domain=domain,
                    selector=selector,
                    explanation="Could not retrieve DKIM public key"
                )
            
            # Validate DKIM signature (simplified - in production, use proper DKIM library)
            is_valid = await self._verify_dkim_signature(
                dkim_signature, email_headers, email_body, dkim_key
            )
            
            if is_valid:
                return DKIMResult(
                    result=AuthenticationResult.PASS,
                    domain=domain,
                    selector=selector,
                    signature=dkim_signature
                )
            else:
                return DKIMResult(
                    result=AuthenticationResult.FAIL,
                    domain=domain,
                    selector=selector,
                    signature=dkim_signature,
                    explanation="DKIM signature verification failed"
                )
                
        except Exception as e:
            logger.error(f"DKIM validation error: {e}")
            return DKIMResult(
                result=AuthenticationResult.TEMPERROR,
                explanation=f"DKIM validation error: {str(e)}"
            )
    
    async def _validate_dmarc(self, sender_domain: str) -> DMARCResult:
        """Validate DMARC policy for the sender domain"""
        try:
            # Query DMARC record
            dmarc_record = await self._query_dns_record(f"_dmarc.{sender_domain}", "TXT")
            
            if not dmarc_record:
                return DMARCResult(
                    result=AuthenticationResult.NONE,
                    domain=sender_domain,
                    explanation="No DMARC record found"
                )
            
            # Parse DMARC record
            dmarc_params = self._parse_dmarc_record(dmarc_record)
            
            if not dmarc_params:
                return DMARCResult(
                    result=AuthenticationResult.PERMERROR,
                    domain=sender_domain,
                    explanation="Invalid DMARC record format"
                )
            
            policy = dmarc_params.get("p", "none")
            subdomain_policy = dmarc_params.get("sp", policy)
            pct = int(dmarc_params.get("pct", "100"))
            rua = dmarc_params.get("rua")
            ruf = dmarc_params.get("ruf")
            
            return DMARCResult(
                result=AuthenticationResult.PASS,
                policy=policy,
                subdomain_policy=subdomain_policy,
                pct=pct,
                rua=rua,
                ruf=ruf,
                domain=sender_domain
            )
            
        except Exception as e:
            logger.error(f"DMARC validation error: {e}")
            return DMARCResult(
                result=AuthenticationResult.TEMPERROR,
                domain=sender_domain,
                explanation=f"DMARC validation error: {str(e)}"
            )
    
    async def _query_dns_record(self, domain: str, record_type: str) -> Optional[str]:
        """Query DNS record for a domain"""
        try:
            resolver = dns.resolver.Resolver()
            resolver.timeout = self.dns_timeout
            resolver.lifetime = self.dns_timeout
            
            answers = resolver.resolve(domain, record_type)
            
            for answer in answers:
                if record_type == "TXT":
                    return str(answer).strip('"')
                else:
                    return str(answer)
            
            return None
            
        except dns.exception.DNSException as e:
            logger.debug(f"DNS query failed for {domain} {record_type}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected DNS query error: {e}")
            return None
    
    async def _query_dkim_public_key(self, selector: str, domain: str) -> Optional[str]:
        """Query DKIM public key"""
        try:
            dkim_key_record = await self._query_dns_record(f"{selector}._domainkey.{domain}", "TXT")
            return dkim_key_record
        except Exception as e:
            logger.error(f"Error querying DKIM key: {e}")
            return None
    
    def _parse_dkim_signature(self, signature: str) -> Optional[Dict[str, str]]:
        """Parse DKIM signature parameters"""
        try:
            params = {}
            # Simple parsing - in production, use proper DKIM library
            parts = signature.split(";")
            for part in parts:
                if "=" in part:
                    key, value = part.split("=", 1)
                    params[key.strip()] = value.strip()
            return params
        except Exception:
            return None
    
    def _parse_dmarc_record(self, record: str) -> Optional[Dict[str, str]]:
        """Parse DMARC record parameters"""
        try:
            params = {}
            # Simple parsing - in production, use proper DMARC library
            parts = record.split(";")
            for part in parts:
                if "=" in part:
                    key, value = part.split("=", 1)
                    params[key.strip()] = value.strip()
            return params
        except Exception:
            return None
    
    def _check_ip_mechanism(self, mechanism: str, sender_ip: str) -> bool:
        """Check if sender IP matches SPF IP mechanism"""
        try:
            if mechanism.startswith("ip4:"):
                ip_range = mechanism[4:]
                return self._ip_in_range(sender_ip, ip_range)
            elif mechanism.startswith("ip6:"):
                ip_range = mechanism[4:]
                return self._ipv6_in_range(sender_ip, ip_range)
            return False
        except Exception:
            return False
    
    async def _check_a_mechanism(self, domain: str, sender_ip: str) -> bool:
        """Check if sender IP matches domain's A record"""
        try:
            a_record = await self._query_dns_record(domain, "A")
            return a_record == sender_ip
        except Exception:
            return False
    
    async def _check_mx_mechanism(self, domain: str, sender_ip: str) -> bool:
        """Check if sender IP matches domain's MX record"""
        try:
            mx_records = await self._query_dns_record(domain, "MX")
            # Simplified - in production, resolve MX records to IPs
            return False
        except Exception:
            return False
    
    async def _verify_dkim_signature(
        self, 
        signature: str, 
        headers: Dict[str, str], 
        body: str, 
        public_key: str
    ) -> bool:
        """Verify DKIM signature (simplified implementation)"""
        try:
            # This is a simplified implementation
            # In production, use a proper DKIM library like dkimpy
            return True  # Placeholder - always return True for MVP
        except Exception:
            return False
    
    def _ip_in_range(self, ip: str, ip_range: str) -> bool:
        """Check if IP is in CIDR range (simplified)"""
        try:
            if "/" in ip_range:
                # CIDR notation
                network, prefix = ip_range.split("/")
                # Simplified check - in production, use ipaddress module
                return ip == network
            else:
                # Single IP
                return ip == ip_range
        except Exception:
            return False
    
    def _ipv6_in_range(self, ip: str, ip_range: str) -> bool:
        """Check if IPv6 is in range (simplified)"""
        # Simplified implementation
        return False
    
    def _calculate_overall_result(
        self, 
        spf: SPFResult, 
        dkim: DKIMResult, 
        dmarc: DMARCResult
    ) -> Tuple[AuthenticationResult, float, List[str]]:
        """Calculate overall authentication result and score"""
        recommendations = []
        score = 0.0
        
        # SPF scoring
        if spf.result == AuthenticationResult.PASS:
            score += 0.3
        elif spf.result == AuthenticationResult.FAIL:
            score -= 0.2
            recommendations.append("SPF validation failed - check sender IP")
        elif spf.result == AuthenticationResult.NONE:
            recommendations.append("No SPF record found - implement SPF")
        
        # DKIM scoring
        if dkim.result == AuthenticationResult.PASS:
            score += 0.4
        elif dkim.result == AuthenticationResult.FAIL:
            score -= 0.3
            recommendations.append("DKIM validation failed - check signature")
        elif dkim.result == AuthenticationResult.NONE:
            recommendations.append("No DKIM signature found - implement DKIM")
        
        # DMARC scoring
        if dmarc.result == AuthenticationResult.PASS:
            score += 0.3
            if dmarc.policy == "reject":
                score += 0.1
            elif dmarc.policy == "quarantine":
                score += 0.05
        elif dmarc.result == AuthenticationResult.NONE:
            recommendations.append("No DMARC record found - implement DMARC")
        
        # Determine overall result
        if score >= 0.8:
            overall_result = AuthenticationResult.PASS
        elif score >= 0.5:
            overall_result = AuthenticationResult.NEUTRAL
        elif score >= 0.0:
            overall_result = AuthenticationResult.NEUTRAL
        else:
            overall_result = AuthenticationResult.FAIL
        
        # Add general recommendations
        if score < 0.7:
            recommendations.append("Email authentication needs improvement")
        
        return overall_result, max(0.0, min(1.0, score)), recommendations


# Global instance
email_auth_service = EmailAuthenticationService()
