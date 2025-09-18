"""
Domain Reputation API Router
Provides endpoints for domain reputation scoring and management
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..security.hmac_auth import verify_request
from ..services.domain_reputation import DomainReputationService
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.get("/domains/{domain}/score")
async def get_domain_score(
    domain: str,
    force_refresh: bool = Query(False, description="Force refresh from threat intelligence sources"),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Get domain reputation score"""
    try:
        async with DomainReputationService() as reputation_service:
            score = await reputation_service.get_domain_score(domain, force_refresh=force_refresh)
            
            if not score:
                raise HTTPException(status_code=404, detail="Domain score not available")
            
            return {
                "domain": score.domain,
                "reputation_score": score.reputation_score,
                "confidence": score.confidence,
                "risk_level": score.risk_level,
                "threat_indicators": score.threat_indicators,
                "last_updated": score.last_updated.isoformat(),
                "expires_at": score.expires_at.isoformat(),
                "sources": [
                    {
                        "source": source.source,
                        "score": source.score,
                        "confidence": source.confidence,
                        "threat_indicators": source.threat_indicators,
                        "last_checked": source.last_checked.isoformat()
                    }
                    for source in score.sources
                ]
            }
            
    except Exception as e:
        logger.error("Error getting domain score", domain=domain, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/domains/bulk-score")
async def bulk_score_domains(
    domains: List[str],
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Score multiple domains in parallel"""
    try:
        if len(domains) > 100:
            raise HTTPException(status_code=400, detail="Maximum 100 domains per request")
        
        async with DomainReputationService() as reputation_service:
            scores = await reputation_service.bulk_score_domains(domains)
            
            return {
                "domains_scored": len(scores),
                "total_requested": len(domains),
                "scores": [
                    {
                        "domain": score.domain,
                        "reputation_score": score.reputation_score,
                        "confidence": score.confidence,
                        "risk_level": score.risk_level,
                        "threat_indicators": score.threat_indicators,
                        "last_updated": score.last_updated.isoformat()
                    }
                    for score in scores
                ]
            }
            
    except Exception as e:
        logger.error("Error in bulk domain scoring", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/domains/{domain}/history")
async def get_domain_history(
    domain: str,
    days: int = Query(7, description="Number of days of history to retrieve"),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Get historical domain scores"""
    try:
        async with DomainReputationService() as reputation_service:
            history = await reputation_service.get_domain_history(domain, days)
            
            return {
                "domain": domain,
                "history_days": days,
                "scores": [
                    {
                        "reputation_score": score.reputation_score,
                        "confidence": score.confidence,
                        "risk_level": score.risk_level,
                        "threat_indicators": score.threat_indicators,
                        "last_updated": score.last_updated.isoformat()
                    }
                    for score in history
                ]
            }
            
    except Exception as e:
        logger.error("Error getting domain history", domain=domain, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/domains/{domain}/refresh")
async def refresh_domain_score(
    domain: str,
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Force refresh domain score from threat intelligence sources"""
    try:
        async with DomainReputationService() as reputation_service:
            score = await reputation_service.get_domain_score(domain, force_refresh=True)
            
            if not score:
                raise HTTPException(status_code=404, detail="Domain score not available")
            
            return {
                "message": "Domain score refreshed successfully",
                "domain": score.domain,
                "reputation_score": score.reputation_score,
                "confidence": score.confidence,
                "risk_level": score.risk_level,
                "last_updated": score.last_updated.isoformat()
            }
            
    except Exception as e:
        logger.error("Error refreshing domain score", domain=domain, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
