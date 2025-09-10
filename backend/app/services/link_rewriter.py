"""
Link Rewriter Service
Implements link rewriting for click-time analysis and security
"""

import re
import hashlib
import base64
import urllib.parse
import structlog
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio
import aiohttp
from datetime import datetime, timedelta
import json
import uuid

logger = structlog.get_logger()


class LinkType(Enum):
    """Link types for analysis"""
    HTTP = "http"
    HTTPS = "https"
    EMAIL = "email"
    PHONE = "phone"
    FILE = "file"
    UNKNOWN = "unknown"


class LinkRisk(Enum):
    """Link risk levels"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class LinkAnalysis:
    """Link analysis result"""
    original_url: str
    rewritten_url: str
    link_type: LinkType
    risk_level: LinkRisk
    domain: str
    is_suspicious: bool
    indicators: List[str]
    analysis_time: float
    metadata: Dict[str, Any]


@dataclass
class RewriteResult:
    """Link rewrite result"""
    original_content: str
    rewritten_content: str
    links_found: int
    links_rewritten: int
    analysis_results: List[LinkAnalysis]
    processing_time: float


class LinkRewriter:
    """Service for rewriting links in email content for security analysis"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config.get('base_url', 'https://privik.example.com')
        self.rewrite_endpoint = config.get('rewrite_endpoint', '/api/click/analyze')
        self.max_links_per_email = config.get('max_links_per_email', 50)
        self.timeout = config.get('timeout', 10)
        
        # Link patterns
        self.link_patterns = {
            'url': re.compile(r'https?://[^\s<>"\']+', re.IGNORECASE),
            'email': re.compile(r'mailto:([^\s<>"\']+)', re.IGNORECASE),
            'phone': re.compile(r'tel:([^\s<>"\']+)', re.IGNORECASE),
            'file': re.compile(r'file://[^\s<>"\']+', re.IGNORECASE),
        }
        
        # Suspicious patterns
        self.suspicious_patterns = [
            r'bit\.ly', r'tinyurl\.com', r'short\.link',  # URL shorteners
            r'goo\.gl', r'ow\.ly', r't\.co',  # More shorteners
            r'[a-z0-9]{8,}\.tk', r'[a-z0-9]{8,}\.ml',  # Suspicious TLDs
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',  # IP addresses
            r'[a-z]{20,}',  # Very long random strings
        ]
        
        # Safe domains (whitelist)
        self.safe_domains = {
            'google.com', 'microsoft.com', 'apple.com', 'amazon.com',
            'github.com', 'stackoverflow.com', 'wikipedia.org'
        }
        
        # Link cache
        self.link_cache = {}
        self.cache_ttl = 3600  # 1 hour
    
    async def rewrite_email_links(self, email_content: str, email_id: str) -> RewriteResult:
        """
        Rewrite all links in email content for security analysis
        
        Args:
            email_content: Original email content (HTML or text)
            email_id: Unique email identifier
            
        Returns:
            RewriteResult with rewritten content and analysis
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Rewriting links for email {email_id}")
            
            # Extract all links
            links = self._extract_links(email_content)
            
            if not links:
                return RewriteResult(
                    original_content=email_content,
                    rewritten_content=email_content,
                    links_found=0,
                    links_rewritten=0,
                    analysis_results=[],
                    processing_time=(datetime.utcnow() - start_time).total_seconds()
                )
            
            # Limit number of links
            if len(links) > self.max_links_per_email:
                links = links[:self.max_links_per_email]
                logger.warning(f"Limited links to {self.max_links_per_email} for email {email_id}")
            
            # Analyze links in parallel
            analysis_tasks = [
                self._analyze_link(link, email_id) for link in links
            ]
            
            analysis_results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Filter out exceptions
            valid_results = []
            for result in analysis_results:
                if not isinstance(result, Exception):
                    valid_results.append(result)
                else:
                    logger.error(f"Link analysis error: {result}")
            
            # Rewrite content
            rewritten_content = self._rewrite_content(email_content, valid_results)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = RewriteResult(
                original_content=email_content,
                rewritten_content=rewritten_content,
                links_found=len(links),
                links_rewritten=len(valid_results),
                analysis_results=valid_results,
                processing_time=processing_time
            )
            
            logger.info(f"Rewrote {len(valid_results)} links for email {email_id} in {processing_time:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error rewriting links for email {email_id}: {e}")
            return RewriteResult(
                original_content=email_content,
                rewritten_content=email_content,
                links_found=0,
                links_rewritten=0,
                analysis_results=[],
                processing_time=(datetime.utcnow() - start_time).total_seconds()
            )
    
    def _extract_links(self, content: str) -> List[str]:
        """Extract all links from content"""
        links = []
        
        for pattern_name, pattern in self.link_patterns.items():
            matches = pattern.findall(content)
            if pattern_name == 'url':
                links.extend(matches)
            else:
                # For email, phone, file - extract the actual value
                links.extend([f"{pattern_name}:{match}" for match in matches])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_links = []
        for link in links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)
        
        return unique_links
    
    async def _analyze_link(self, link: str, email_id: str) -> LinkAnalysis:
        """Analyze a single link"""
        start_time = datetime.utcnow()
        
        try:
            # Check cache first
            cache_key = hashlib.md5(link.encode()).hexdigest()
            if cache_key in self.link_cache:
                cached_result, timestamp = self.link_cache[cache_key]
                if datetime.utcnow() - timestamp < timedelta(seconds=self.cache_ttl):
                    return cached_result
            
            # Determine link type
            link_type = self._determine_link_type(link)
            
            # Extract domain
            domain = self._extract_domain(link)
            
            # Analyze for suspicious patterns
            is_suspicious, indicators = self._analyze_suspicious_patterns(link, domain)
            
            # Determine risk level
            risk_level = self._determine_risk_level(link, domain, is_suspicious, indicators)
            
            # Generate rewritten URL
            rewritten_url = self._generate_rewritten_url(link, email_id, cache_key)
            
            analysis_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = LinkAnalysis(
                original_url=link,
                rewritten_url=rewritten_url,
                link_type=link_type,
                risk_level=risk_level,
                domain=domain,
                is_suspicious=is_suspicious,
                indicators=indicators,
                analysis_time=analysis_time,
                metadata={
                    'email_id': email_id,
                    'cache_key': cache_key,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            
            # Cache result
            self.link_cache[cache_key] = (result, datetime.utcnow())
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing link {link}: {e}")
            return LinkAnalysis(
                original_url=link,
                rewritten_url=link,
                link_type=LinkType.UNKNOWN,
                risk_level=LinkRisk.MEDIUM,
                domain="unknown",
                is_suspicious=True,
                indicators=["analysis_error"],
                analysis_time=(datetime.utcnow() - start_time).total_seconds(),
                metadata={'error': str(e)}
            )
    
    def _determine_link_type(self, link: str) -> LinkType:
        """Determine the type of link"""
        link_lower = link.lower()
        
        if link_lower.startswith('mailto:'):
            return LinkType.EMAIL
        elif link_lower.startswith('tel:'):
            return LinkType.PHONE
        elif link_lower.startswith('file://'):
            return LinkType.FILE
        elif link_lower.startswith('https://'):
            return LinkType.HTTPS
        elif link_lower.startswith('http://'):
            return LinkType.HTTP
        else:
            return LinkType.UNKNOWN
    
    def _extract_domain(self, link: str) -> str:
        """Extract domain from link"""
        try:
            if link.startswith(('http://', 'https://')):
                parsed = urllib.parse.urlparse(link)
                return parsed.netloc.lower()
            elif link.startswith('mailto:'):
                email = link[7:]  # Remove 'mailto:'
                if '@' in email:
                    return email.split('@')[1].lower()
            return "unknown"
        except Exception:
            return "unknown"
    
    def _analyze_suspicious_patterns(self, link: str, domain: str) -> Tuple[bool, List[str]]:
        """Analyze link for suspicious patterns"""
        indicators = []
        is_suspicious = False
        
        # Check suspicious patterns
        for pattern in self.suspicious_patterns:
            if re.search(pattern, link, re.IGNORECASE):
                indicators.append(f"suspicious_pattern: {pattern}")
                is_suspicious = True
        
        # Check for URL shorteners
        if any(shortener in domain for shortener in ['bit.ly', 'tinyurl.com', 'short.link', 'goo.gl']):
            indicators.append("url_shortener")
            is_suspicious = True
        
        # Check for suspicious TLDs
        suspicious_tlds = ['.tk', '.ml', '.ga', '.cf']
        if any(domain.endswith(tld) for tld in suspicious_tlds):
            indicators.append("suspicious_tld")
            is_suspicious = True
        
        # Check for IP addresses in domain
        if re.search(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', domain):
            indicators.append("ip_address_domain")
            is_suspicious = True
        
        # Check for very long domains
        if len(domain) > 50:
            indicators.append("long_domain")
            is_suspicious = True
        
        # Check for random-looking domains
        if re.search(r'[a-z]{15,}', domain):
            indicators.append("random_domain")
            is_suspicious = True
        
        return is_suspicious, indicators
    
    def _determine_risk_level(self, link: str, domain: str, is_suspicious: bool, indicators: List[str]) -> LinkRisk:
        """Determine risk level for the link"""
        if domain in self.safe_domains:
            return LinkRisk.SAFE
        
        if not is_suspicious:
            return LinkRisk.LOW
        
        # Count high-risk indicators
        high_risk_indicators = ['url_shortener', 'suspicious_tld', 'ip_address_domain', 'random_domain']
        high_risk_count = sum(1 for indicator in indicators if any(hr in indicator for hr in high_risk_indicators))
        
        if high_risk_count >= 3:
            return LinkRisk.CRITICAL
        elif high_risk_count >= 2:
            return LinkRisk.HIGH
        elif high_risk_count >= 1:
            return LinkRisk.MEDIUM
        else:
            return LinkRisk.LOW
    
    def _generate_rewritten_url(self, original_url: str, email_id: str, cache_key: str) -> str:
        """Generate rewritten URL for click tracking"""
        try:
            # Encode original URL
            encoded_url = base64.urlsafe_b64encode(original_url.encode()).decode()
            
            # Create tracking parameters
            params = {
                'url': encoded_url,
                'email_id': email_id,
                'link_id': cache_key,
                'timestamp': int(datetime.utcnow().timestamp())
            }
            
            # Build rewritten URL
            query_string = urllib.parse.urlencode(params)
            rewritten_url = f"{self.base_url}{self.rewrite_endpoint}?{query_string}"
            
            return rewritten_url
            
        except Exception as e:
            logger.error(f"Error generating rewritten URL: {e}")
            return original_url
    
    def _rewrite_content(self, content: str, analysis_results: List[LinkAnalysis]) -> str:
        """Rewrite content with new URLs"""
        try:
            rewritten_content = content
            
            for analysis in analysis_results:
                # Replace original URL with rewritten URL
                # Use word boundaries to avoid partial replacements
                pattern = re.escape(analysis.original_url)
                rewritten_content = re.sub(
                    f'\\b{pattern}\\b',
                    analysis.rewritten_url,
                    rewritten_content,
                    flags=re.IGNORECASE
                )
            
            return rewritten_content
            
        except Exception as e:
            logger.error(f"Error rewriting content: {e}")
            return content
    
    async def get_original_url(self, link_id: str) -> Optional[str]:
        """Get original URL from link ID (for click tracking)"""
        try:
            if link_id in self.link_cache:
                cached_result, timestamp = self.link_cache[link_id]
                if datetime.utcnow() - timestamp < timedelta(seconds=self.cache_ttl):
                    return cached_result.original_url
            return None
        except Exception as e:
            logger.error(f"Error getting original URL: {e}")
            return None
    
    async def analyze_click(self, link_id: str, user_id: str = None) -> Optional[LinkAnalysis]:
        """Analyze a click on a rewritten link"""
        try:
            if link_id in self.link_cache:
                cached_result, timestamp = self.link_cache[link_id]
                if datetime.utcnow() - timestamp < timedelta(seconds=self.cache_ttl):
                    # Log the click
                    logger.info(f"Link clicked: {link_id} by user {user_id}")
                    
                    # Update metadata
                    cached_result.metadata['clicked_by'] = user_id
                    cached_result.metadata['clicked_at'] = datetime.utcnow().isoformat()
                    
                    return cached_result
            return None
        except Exception as e:
            logger.error(f"Error analyzing click: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get link rewriter statistics"""
        try:
            total_links = len(self.link_cache)
            suspicious_links = sum(1 for result, _ in self.link_cache.values() if result.is_suspicious)
            
            risk_distribution = {}
            for risk in LinkRisk:
                risk_distribution[risk.value] = sum(
                    1 for result, _ in self.link_cache.values() 
                    if result.risk_level == risk
                )
            
            return {
                'total_links_analyzed': total_links,
                'suspicious_links': suspicious_links,
                'risk_distribution': risk_distribution,
                'cache_size': total_links,
                'cache_ttl': self.cache_ttl
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}


# Global instance
link_rewriter = None


def get_link_rewriter(config: Dict[str, Any] = None) -> LinkRewriter:
    """Get the global link rewriter instance"""
    global link_rewriter
    if link_rewriter is None:
        default_config = {
            'base_url': 'https://privik.example.com',
            'rewrite_endpoint': '/api/click/analyze',
            'max_links_per_email': 50,
            'timeout': 10
        }
        config = config or default_config
        link_rewriter = LinkRewriter(config)
    return link_rewriter
