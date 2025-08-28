"""
Privik Endpoint Agent Link Monitor
Monitors and analyzes URLs for threats before access
"""

import asyncio
import time
import re
import urllib.parse
from typing import Dict, Any, List, Optional, Set
import structlog

from ..config import AgentConfig
from ..security import SecurityManager
from ..communication import ServerCommunicator

logger = structlog.get_logger()

class LinkMonitor:
    """Monitors and analyzes URLs for threats."""
    
    def __init__(self, config: AgentConfig, security_manager: SecurityManager, 
                 communicator: ServerCommunicator):
        """Initialize the link monitor."""
        self.config = config
        self.security_manager = security_manager
        self.communicator = communicator
        self.running = False
        self.analyzed_urls: Set[str] = set()
        
        # URL patterns to monitor
        self.suspicious_domains = [
            'bit.ly', 'tinyurl.com', 'goo.gl', 't.co', 'is.gd', 'v.gd',
            'ow.ly', 'su.pr', 'twurl.nl', 'snipurl.com', 'short.to',
            'BudURL.com', 'ping.fm', 'tr.im', 'snipr.com', 'short.ie',
            'kl.am', 'wp.me', 'rubyurl.com', 'om.ly', 'to.ly', 'bit.do',
            't.co', 'lnkd.in', 'db.tt', 'qr.ae', 'adf.ly', 'goo.gl',
            'bitly.com', 'cur.lv', 'tiny.cc', 'url4.eu', 'tr.im',
            'twitthis.com', 'u.to', 'j.mp', 'buzurl.com', 'cutt.us',
            'u.bb', 'yourls.org', 'x.co', 'prettylinkpro.com', 'scrnch.me',
            'filoops.info', 'vzturl.com', 'qr.net', '1url.com', 'tweez.me',
            'v.gd', 'tr.im', 'link.zip.net'
        ]
        
        # Suspicious TLDs
        self.suspicious_tlds = [
            '.tk', '.ml', '.ga', '.cf', '.gq', '.pw', '.cc', '.co',
            '.xyz', '.top', '.club', '.online', '.site', '.website'
        ]
        
        # URL patterns that indicate threats
        self.threat_patterns = [
            r'login.*bank',
            r'verify.*account',
            r'secure.*login',
            r'update.*password',
            r'confirm.*details',
            r'account.*suspended',
            r'security.*alert',
            r'payment.*failed',
            r'invoice.*payment',
            r'document.*view',
            r'file.*download',
            r'update.*software',
            r'install.*update',
            r'flash.*player',
            r'java.*update',
            r'adobe.*reader',
            r'microsoft.*update',
            r'windows.*update',
            r'antivirus.*scan',
            r'security.*scan'
        ]
    
    async def initialize(self) -> bool:
        """Initialize the link monitor."""
        try:
            logger.info("Initializing link monitor")
            
            # Initialize URL rewriting if enabled
            if self.config.link_rewrite_enabled:
                logger.info("URL rewriting enabled")
            
            # Initialize safe browsing if enabled
            if self.config.safe_browsing_enabled:
                logger.info("Safe browsing enabled")
            
            logger.info("Link monitor initialized")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize link monitor", error=str(e))
            return False
    
    async def start_monitoring(self):
        """Start link monitoring."""
        try:
            self.running = True
            logger.info("Starting link monitoring")
            
            # For now, this is a placeholder for future browser integration
            # In a real implementation, this would hook into browser events
            while self.running:
                await asyncio.sleep(1)
            
        except Exception as e:
            logger.error("Link monitoring error", error=str(e))
        finally:
            self.running = False
            logger.info("Link monitoring stopped")
    
    async def analyze_url(self, url: str, context: str = "unknown") -> Dict[str, Any]:
        """Analyze a URL for threats."""
        try:
            # Check if we've already analyzed this URL
            url_hash = self.security_manager.hash_file(url.encode())
            if url_hash in self.analyzed_urls:
                return {'threat_score': 0, 'already_analyzed': True}
            
            # Parse URL
            parsed_url = urllib.parse.urlparse(url)
            
            # Perform analysis
            analysis_result = await self._perform_url_analysis(parsed_url, url, context)
            
            # Mark as analyzed
            self.analyzed_urls.add(url_hash)
            
            # Send analysis to server if threat detected
            if analysis_result['threat_score'] > 0:
                await self.communicator.send_link_analysis(analysis_result)
                logger.info("Threat detected in URL", 
                           url=url,
                           threat_score=analysis_result['threat_score'])
            
            return analysis_result
            
        except Exception as e:
            logger.error("Error analyzing URL", url=url, error=str(e))
            return {'threat_score': 0, 'error': str(e)}
    
    async def _perform_url_analysis(self, parsed_url, original_url: str, context: str) -> Dict[str, Any]:
        """Perform comprehensive URL analysis."""
        try:
            analysis = {
                'original_url': original_url,
                'parsed_url': {
                    'scheme': parsed_url.scheme,
                    'netloc': parsed_url.netloc,
                    'path': parsed_url.path,
                    'query': parsed_url.query,
                    'fragment': parsed_url.fragment,
                },
                'context': context,
                'threat_score': 0,
                'threat_indicators': [],
                'rewritten_url': None,
                'analysis_type': 'link_monitor',
                'timestamp': int(time.time()),
            }
            
            # Analyze domain
            domain_score, domain_indicators = self._analyze_domain(parsed_url.netloc)
            analysis['threat_score'] += domain_score
            analysis['threat_indicators'].extend(domain_indicators)
            
            # Analyze path
            path_score, path_indicators = self._analyze_path(parsed_url.path)
            analysis['threat_score'] += path_score
            analysis['threat_indicators'].extend(path_indicators)
            
            # Analyze query parameters
            query_score, query_indicators = self._analyze_query(parsed_url.query)
            analysis['threat_score'] += query_score
            analysis['threat_indicators'].extend(query_indicators)
            
            # Analyze full URL
            url_score, url_indicators = self._analyze_full_url(original_url)
            analysis['threat_score'] += url_score
            analysis['threat_indicators'].extend(url_indicators)
            
            # Get rewritten URL if enabled and threat detected
            if self.config.link_rewrite_enabled and analysis['threat_score'] > 0:
                rewritten_url = await self.communicator.get_rewritten_url(original_url)
                if rewritten_url:
                    analysis['rewritten_url'] = rewritten_url
            
            return analysis
            
        except Exception as e:
            logger.error("Error performing URL analysis", error=str(e))
            return {'threat_score': 0, 'error': str(e)}
    
    def _analyze_domain(self, domain: str) -> tuple:
        """Analyze domain for threats."""
        score = 0
        indicators = []
        
        try:
            domain_lower = domain.lower()
            
            # Check for suspicious domains
            for suspicious_domain in self.suspicious_domains:
                if suspicious_domain in domain_lower:
                    score += 15
                    indicators.append(f"suspicious_domain_{suspicious_domain}")
            
            # Check for suspicious TLDs
            for suspicious_tld in self.suspicious_tlds:
                if domain_lower.endswith(suspicious_tld):
                    score += 10
                    indicators.append(f"suspicious_tld_{suspicious_tld}")
            
            # Check for IP addresses
            ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
            if re.search(ip_pattern, domain):
                score += 20
                indicators.append("ip_address_domain")
            
            # Check for random-looking domains
            if len(domain) > 20 and not any(char.isalpha() for char in domain):
                score += 10
                indicators.append("random_domain")
            
            # Check for subdomain abuse
            subdomain_count = domain.count('.')
            if subdomain_count > 3:
                score += 5
                indicators.append("excessive_subdomains")
            
            return score, indicators
            
        except Exception as e:
            logger.error("Error analyzing domain", error=str(e))
            return 0, []
    
    def _analyze_path(self, path: str) -> tuple:
        """Analyze URL path for threats."""
        score = 0
        indicators = []
        
        try:
            path_lower = path.lower()
            
            # Check for threat patterns in path
            for pattern in self.threat_patterns:
                if re.search(pattern, path_lower):
                    score += 10
                    indicators.append(f"threat_pattern_path_{pattern}")
            
            # Check for suspicious path components
            suspicious_paths = [
                'login', 'signin', 'auth', 'verify', 'confirm', 'update',
                'download', 'install', 'setup', 'update', 'flash', 'java',
                'adobe', 'microsoft', 'windows', 'antivirus', 'security'
            ]
            
            for suspicious_path in suspicious_paths:
                if suspicious_path in path_lower:
                    score += 5
                    indicators.append(f"suspicious_path_{suspicious_path}")
            
            # Check for executable files in path
            executable_extensions = ['.exe', '.bat', '.cmd', '.com', '.pif', '.scr']
            for ext in executable_extensions:
                if ext in path_lower:
                    score += 20
                    indicators.append(f"executable_in_path_{ext}")
            
            # Check for encoded content
            if '%' in path and len(path) > 50:
                score += 5
                indicators.append("encoded_path")
            
            return score, indicators
            
        except Exception as e:
            logger.error("Error analyzing path", error=str(e))
            return 0, []
    
    def _analyze_query(self, query: str) -> tuple:
        """Analyze URL query parameters for threats."""
        score = 0
        indicators = []
        
        try:
            if not query:
                return 0, []
            
            query_lower = query.lower()
            
            # Check for suspicious query parameters
            suspicious_params = [
                'redirect', 'url', 'link', 'goto', 'target', 'dest',
                'next', 'return', 'continue', 'callback', 'ref'
            ]
            
            for param in suspicious_params:
                if param in query_lower:
                    score += 5
                    indicators.append(f"suspicious_param_{param}")
            
            # Check for encoded content in query
            if '%' in query and len(query) > 100:
                score += 10
                indicators.append("encoded_query")
            
            # Check for JavaScript in query
            if 'javascript:' in query_lower or 'data:' in query_lower:
                score += 25
                indicators.append("javascript_in_query")
            
            # Check for file extensions in query
            file_extensions = ['.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js']
            for ext in file_extensions:
                if ext in query_lower:
                    score += 15
                    indicators.append(f"file_extension_in_query_{ext}")
            
            return score, indicators
            
        except Exception as e:
            logger.error("Error analyzing query", error=str(e))
            return 0, []
    
    def _analyze_full_url(self, url: str) -> tuple:
        """Analyze full URL for threats."""
        score = 0
        indicators = []
        
        try:
            url_lower = url.lower()
            
            # Check for threat patterns in full URL
            for pattern in self.threat_patterns:
                if re.search(pattern, url_lower):
                    score += 10
                    indicators.append(f"threat_pattern_url_{pattern}")
            
            # Check for phishing indicators
            phishing_indicators = [
                'secure', 'login', 'signin', 'verify', 'confirm',
                'update', 'account', 'bank', 'paypal', 'ebay',
                'amazon', 'google', 'microsoft', 'apple'
            ]
            
            phishing_count = sum(1 for indicator in phishing_indicators if indicator in url_lower)
            if phishing_count > 2:
                score += 15
                indicators.append("multiple_phishing_indicators")
            
            # Check for excessive length
            if len(url) > 200:
                score += 5
                indicators.append("excessively_long_url")
            
            # Check for mixed case (potential homograph attack)
            if any(c.isupper() for c in url) and any(c.islower() for c in url):
                score += 5
                indicators.append("mixed_case_url")
            
            return score, indicators
            
        except Exception as e:
            logger.error("Error analyzing full URL", error=str(e))
            return 0, []
    
    async def get_rewritten_url(self, original_url: str) -> Optional[str]:
        """Get a rewritten URL from the server."""
        try:
            if not self.config.link_rewrite_enabled:
                return None
            
            rewritten_url = await self.communicator.get_rewritten_url(original_url)
            return rewritten_url
            
        except Exception as e:
            logger.error("Error getting rewritten URL", error=str(e))
            return None
    
    async def check_safe_browsing(self, url: str) -> Dict[str, Any]:
        """Check URL against safe browsing databases."""
        try:
            if not self.config.safe_browsing_enabled:
                return {'safe': True, 'reason': 'safe_browsing_disabled'}
            
            # This would integrate with Google Safe Browsing API or similar
            # For now, return a placeholder
            return {'safe': True, 'reason': 'not_implemented'}
            
        except Exception as e:
            logger.error("Error checking safe browsing", error=str(e))
            return {'safe': False, 'error': str(e)}
    
    async def get_status(self) -> Dict[str, Any]:
        """Get link monitor status."""
        return {
            'running': self.running,
            'analyzed_urls_count': len(self.analyzed_urls),
            'link_rewrite_enabled': self.config.link_rewrite_enabled,
            'safe_browsing_enabled': self.config.safe_browsing_enabled,
        }
    
    async def stop(self):
        """Stop the link monitor."""
        self.running = False
        logger.info("Link monitor stopped")
