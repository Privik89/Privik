"""
Domain Reputation Service
Centralized domain scoring using multiple threat intelligence sources
"""

import asyncio
import aiohttp
import redis
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import structlog
from .virustotal import VirusTotalService

logger = structlog.get_logger()

@dataclass
class SourceScore:
    """Score from a single threat intelligence source"""
    source: str
    score: float  # 0.0 (malicious) to 1.0 (trusted)
    confidence: float  # 0.0 to 1.0 (data reliability)
    last_checked: datetime
    raw_data: Dict[str, Any]
    threat_indicators: List[str]

@dataclass
class DomainScore:
    """Aggregated domain reputation score"""
    domain: str
    reputation_score: float  # 0.0 (malicious) to 1.0 (trusted)
    confidence: float  # 0.0 to 1.0 (overall reliability)
    sources: List[SourceScore]
    last_updated: datetime
    expires_at: datetime
    risk_level: str  # "low", "medium", "high", "critical"
    threat_indicators: List[str]

class DomainReputationService:
    """Centralized domain reputation scoring service"""
    
    def __init__(self, redis_client: redis.Redis = None):
        self.redis_client = redis_client or redis.Redis(host='localhost', port=6379, db=1)
        self.virustotal = VirusTotalService()
        self.session = None
        
        # Source weights for final score calculation
        self.source_weights = {
            'virustotal': 0.4,
            'google_safe_browsing': 0.3,
            'urlvoid': 0.2,
            'phishtank': 0.1
        }
        
        # Cache TTL (1 hour)
        self.cache_ttl = 3600
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_domain_score(self, domain: str, force_refresh: bool = False) -> Optional[DomainScore]:
        """Get domain reputation score with caching"""
        try:
            # Check cache first (unless force refresh)
            if not force_refresh:
                cached_score = await self._get_cached_score(domain)
                if cached_score:
                    logger.debug("Returning cached domain score", domain=domain)
                    return cached_score
            
            # Fetch fresh score from all sources
            logger.info("Fetching fresh domain score", domain=domain)
            sources = await self._fetch_all_source_scores(domain)
            
            if not sources:
                logger.warning("No source scores available", domain=domain)
                return None
            
            # Calculate aggregated score
            domain_score = self._calculate_aggregated_score(domain, sources)
            
            # Cache the result
            await self._cache_score(domain_score)
            
            return domain_score
            
        except Exception as e:
            logger.error("Error getting domain score", domain=domain, error=str(e))
            return None
    
    async def bulk_score_domains(self, domains: List[str]) -> List[DomainScore]:
        """Score multiple domains in parallel"""
        try:
            # Check cache for existing scores
            cached_scores = {}
            uncached_domains = []
            
            for domain in domains:
                cached_score = await self._get_cached_score(domain)
                if cached_score:
                    cached_scores[domain] = cached_score
                else:
                    uncached_domains.append(domain)
            
            # Fetch scores for uncached domains in parallel
            if uncached_domains:
                tasks = [self.get_domain_score(domain, force_refresh=True) for domain in uncached_domains]
                fresh_scores = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Combine cached and fresh scores
                all_scores = list(cached_scores.values())
                for score in fresh_scores:
                    if isinstance(score, DomainScore):
                        all_scores.append(score)
            else:
                all_scores = list(cached_scores.values())
            
            logger.info("Bulk domain scoring completed", 
                       total=len(domains), 
                       cached=len(cached_scores), 
                       fresh=len(uncached_domains))
            
            return all_scores
            
        except Exception as e:
            logger.error("Error in bulk domain scoring", error=str(e))
            return []
    
    async def get_domain_history(self, domain: str, days: int = 7) -> List[DomainScore]:
        """Get historical domain scores (placeholder for future implementation)"""
        # TODO: Implement historical tracking in database
        current_score = await self.get_domain_score(domain)
        return [current_score] if current_score else []
    
    async def _fetch_all_source_scores(self, domain: str) -> List[SourceScore]:
        """Fetch scores from all threat intelligence sources"""
        sources = []
        
        # Fetch from all sources in parallel
        tasks = [
            self._fetch_virustotal_score(domain),
            self._fetch_google_safe_browsing_score(domain),
            self._fetch_urlvoid_score(domain),
            self._fetch_phishtank_score(domain)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, SourceScore):
                sources.append(result)
            elif isinstance(result, Exception):
                logger.warning("Source scoring failed", error=str(result))
        
        return sources
    
    async def _fetch_virustotal_score(self, domain: str) -> Optional[SourceScore]:
        """Fetch VirusTotal domain reputation score"""
        try:
            # Use existing VirusTotal service
            report = await self.virustotal.get_domain_report(domain)
            
            if not report:
                return None
            
            # Convert VirusTotal response to standardized score
            score = self._parse_virustotal_score(report)
            confidence = 0.9  # VirusTotal is highly reliable
            
            threat_indicators = []
            if report.get('last_analysis_stats', {}).get('malicious', 0) > 0:
                threat_indicators.append('malicious_detections')
            if report.get('last_analysis_stats', {}).get('suspicious', 0) > 0:
                threat_indicators.append('suspicious_detections')
            
            return SourceScore(
                source='virustotal',
                score=score,
                confidence=confidence,
                last_checked=datetime.utcnow(),
                raw_data=report,
                threat_indicators=threat_indicators
            )
            
        except Exception as e:
            logger.error("VirusTotal scoring failed", domain=domain, error=str(e))
            return None
    
    async def _fetch_google_safe_browsing_score(self, domain: str) -> Optional[SourceScore]:
        """Fetch Google Safe Browsing score"""
        try:
            # Google Safe Browsing API (simplified implementation)
            # Note: Requires API key for production use
            url = f"https://safebrowsing.googleapis.com/v4/threatMatches:find"
            
            payload = {
                "client": {
                    "clientId": "privik-email-security",
                    "clientVersion": "1.0.0"
                },
                "threatInfo": {
                    "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
                    "platformTypes": ["ANY_PLATFORM"],
                    "threatEntryTypes": ["URL"],
                    "threatEntries": [{"url": f"http://{domain}"}]
                }
            }
            
            # For now, return neutral score (implement API key integration later)
            return SourceScore(
                source='google_safe_browsing',
                score=0.5,  # Neutral score
                confidence=0.7,
                last_checked=datetime.utcnow(),
                raw_data={"status": "not_implemented"},
                threat_indicators=[]
            )
            
        except Exception as e:
            logger.error("Google Safe Browsing scoring failed", domain=domain, error=str(e))
            return None
    
    async def _fetch_urlvoid_score(self, domain: str) -> Optional[SourceScore]:
        """Fetch URLVoid domain reputation score"""
        try:
            # URLVoid API (simplified implementation)
            # Note: Requires API key for production use
            url = f"https://api.urlvoid.com/v1/pay-as-you-go/{domain}"
            
            # For now, return neutral score (implement API key integration later)
            return SourceScore(
                source='urlvoid',
                score=0.5,  # Neutral score
                confidence=0.6,
                last_checked=datetime.utcnow(),
                raw_data={"status": "not_implemented"},
                threat_indicators=[]
            )
            
        except Exception as e:
            logger.error("URLVoid scoring failed", domain=domain, error=str(e))
            return None
    
    async def _fetch_phishtank_score(self, domain: str) -> Optional[SourceScore]:
        """Fetch PhishTank phishing score"""
        try:
            # PhishTank API (free, no key required)
            url = f"https://checkurl.phishtank.com/checkurl/"
            
            payload = {
                "url": f"http://{domain}",
                "format": "json"
            }
            
            if self.session:
                async with self.session.post(url, data=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # PhishTank returns 1 if phishing, 0 if clean
                        is_phishing = data.get('results', {}).get('in_database', False)
                        score = 0.0 if is_phishing else 1.0
                        
                        threat_indicators = []
                        if is_phishing:
                            threat_indicators.append('phishing_detection')
                        
                        return SourceScore(
                            source='phishtank',
                            score=score,
                            confidence=0.8,
                            last_checked=datetime.utcnow(),
                            raw_data=data,
                            threat_indicators=threat_indicators
                        )
            
            return None
            
        except Exception as e:
            logger.error("PhishTank scoring failed", domain=domain, error=str(e))
            return None
    
    def _parse_virustotal_score(self, report: Dict[str, Any]) -> float:
        """Parse VirusTotal report into standardized score"""
        try:
            stats = report.get('last_analysis_stats', {})
            malicious = stats.get('malicious', 0)
            suspicious = stats.get('suspicious', 0)
            total = sum(stats.values())
            
            if total == 0:
                return 0.5  # Neutral if no data
            
            # Calculate score: 1.0 = clean, 0.0 = malicious
            malicious_ratio = malicious / total
            suspicious_ratio = suspicious / total
            
            # Weight malicious more heavily than suspicious
            score = 1.0 - (malicious_ratio * 0.8 + suspicious_ratio * 0.2)
            
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            logger.error("Error parsing VirusTotal score", error=str(e))
            return 0.5
    
    def _calculate_aggregated_score(self, domain: str, sources: List[SourceScore]) -> DomainScore:
        """Calculate weighted aggregate score from all sources"""
        try:
            if not sources:
                return None
            
            # Calculate weighted score
            total_weight = 0.0
            weighted_score = 0.0
            total_confidence = 0.0
            all_threat_indicators = []
            
            for source in sources:
                weight = self.source_weights.get(source.source, 0.1)
                total_weight += weight
                weighted_score += source.score * weight * source.confidence
                total_confidence += source.confidence
                all_threat_indicators.extend(source.threat_indicators)
            
            # Normalize scores
            final_score = weighted_score / total_weight if total_weight > 0 else 0.5
            final_confidence = total_confidence / len(sources) if sources else 0.0
            
            # Determine risk level
            risk_level = self._determine_risk_level(final_score, all_threat_indicators)
            
            return DomainScore(
                domain=domain,
                reputation_score=final_score,
                confidence=final_confidence,
                sources=sources,
                last_updated=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(seconds=self.cache_ttl),
                risk_level=risk_level,
                threat_indicators=list(set(all_threat_indicators))
            )
            
        except Exception as e:
            logger.error("Error calculating aggregated score", error=str(e))
            return None
    
    def _determine_risk_level(self, score: float, threat_indicators: List[str]) -> str:
        """Determine risk level based on score and threat indicators"""
        if score <= 0.2 or 'malicious_detections' in threat_indicators:
            return 'critical'
        elif score <= 0.4 or 'suspicious_detections' in threat_indicators:
            return 'high'
        elif score <= 0.6 or 'phishing_detection' in threat_indicators:
            return 'medium'
        else:
            return 'low'
    
    async def _get_cached_score(self, domain: str) -> Optional[DomainScore]:
        """Get cached domain score from Redis"""
        try:
            cache_key = f"domain_score:{domain}"
            cached_data = self.redis_client.get(cache_key)
            
            if cached_data:
                data = json.loads(cached_data)
                
                # Convert datetime strings back to datetime objects
                data['last_updated'] = datetime.fromisoformat(data['last_updated'])
                data['expires_at'] = datetime.fromisoformat(data['expires_at'])
                
                for source in data['sources']:
                    source['last_checked'] = datetime.fromisoformat(source['last_checked'])
                
                return DomainScore(**data)
            
            return None
            
        except Exception as e:
            logger.error("Error getting cached score", domain=domain, error=str(e))
            return None
    
    async def _cache_score(self, domain_score: DomainScore):
        """Cache domain score in Redis"""
        try:
            cache_key = f"domain_score:{domain_score.domain}"
            
            # Convert to JSON-serializable format
            data = asdict(domain_score)
            data['last_updated'] = data['last_updated'].isoformat()
            data['expires_at'] = data['expires_at'].isoformat()
            
            for source in data['sources']:
                source['last_checked'] = source['last_checked'].isoformat()
            
            # Store with TTL
            self.redis_client.setex(
                cache_key, 
                self.cache_ttl, 
                json.dumps(data)
            )
            
            logger.debug("Cached domain score", domain=domain_score.domain)
            
        except Exception as e:
            logger.error("Error caching score", domain=domain_score.domain, error=str(e))
