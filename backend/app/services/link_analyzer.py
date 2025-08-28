import asyncio
import aiohttp
import hashlib
from typing import Dict, Any, Optional
from urllib.parse import urlparse
import structlog
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models.click import ClickEvent, LinkAnalysis
from ..core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


async def analyze_link_safety(click_event_id: int, original_url: str, user_id: str):
    """Analyze a clicked link for safety using multiple detection methods."""
    
    logger.info("Starting link analysis", click_event_id=click_event_id, url=original_url)
    
    db = SessionLocal()
    try:
        # Get the click event
        click_event = db.query(ClickEvent).filter(ClickEvent.id == click_event_id).first()
        if not click_event:
            logger.error("Click event not found", click_event_id=click_event_id)
            return
        
        # Perform analysis
        analysis_result = await _perform_link_analysis(original_url)
        
        # Create link analysis record
        link_analysis = LinkAnalysis(
            click_event_id=click_event_id,
            page_title=analysis_result.get("page_title"),
            page_content=analysis_result.get("page_content"),
            page_screenshot=analysis_result.get("screenshot_path"),
            is_login_page=analysis_result.get("is_login_page", False),
            is_phishing_page=analysis_result.get("is_phishing_page", False),
            has_suspicious_forms=analysis_result.get("has_suspicious_forms", False),
            redirect_chain=analysis_result.get("redirect_chain"),
            ai_intent=analysis_result.get("ai_intent"),
            ai_confidence=analysis_result.get("ai_confidence", 0.0),
            ai_details=analysis_result.get("ai_details"),
            http_status=analysis_result.get("http_status"),
            response_headers=analysis_result.get("response_headers"),
            load_time=analysis_result.get("load_time")
        )
        
        db.add(link_analysis)
        
        # Update click event with analysis results
        click_event.threat_score = analysis_result.get("threat_score", 0.0)
        click_event.is_suspicious = analysis_result.get("is_suspicious", False)
        click_event.ai_verdict = analysis_result.get("ai_verdict", "safe")
        
        db.commit()
        
        logger.info("Link analysis completed", 
                   click_event_id=click_event_id, 
                   threat_score=click_event.threat_score,
                   verdict=click_event.ai_verdict)
        
    except Exception as e:
        logger.error("Error during link analysis", 
                    click_event_id=click_event_id, 
                    error=str(e))
        db.rollback()
    finally:
        db.close()


async def _perform_link_analysis(url: str) -> Dict[str, Any]:
    """Perform comprehensive link analysis."""
    
    result = {
        "threat_score": 0.0,
        "is_suspicious": False,
        "ai_verdict": "safe",
        "ai_confidence": 0.0,
        "ai_intent": None,
        "ai_details": {}
    }
    
    try:
        # 1. Basic URL analysis
        url_analysis = _analyze_url_structure(url)
        result.update(url_analysis)
        
        # 2. Fetch and analyze page content
        page_analysis = await _fetch_and_analyze_page(url)
        result.update(page_analysis)
        
        # 3. AI-powered analysis
        ai_analysis = await _perform_ai_analysis(url, page_analysis)
        result.update(ai_analysis)
        
        # 4. Calculate final threat score
        result["threat_score"] = _calculate_threat_score(result)
        result["is_suspicious"] = result["threat_score"] > 0.5
        result["ai_verdict"] = "malicious" if result["threat_score"] > 0.8 else \
                              "suspicious" if result["threat_score"] > 0.5 else "safe"
        
    except Exception as e:
        logger.error("Error in link analysis", url=url, error=str(e))
        result["ai_verdict"] = "error"
    
    return result


def _analyze_url_structure(url: str) -> Dict[str, Any]:
    """Analyze URL structure for suspicious patterns."""
    
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    
    # Suspicious patterns
    suspicious_patterns = [
        "bit.ly", "tinyurl", "goo.gl", "t.co",  # URL shorteners
        "login", "signin", "auth", "secure",    # Login-related
        "bank", "paypal", "amazon", "microsoft" # Brand impersonation
    ]
    
    # Check for suspicious patterns
    is_suspicious_domain = any(pattern in domain for pattern in suspicious_patterns)
    
    # Check for IP addresses (often suspicious)
    is_ip_address = _is_ip_address(domain)
    
    # Check for typosquatting indicators
    has_typosquatting = _check_typosquatting(domain)
    
    return {
        "is_suspicious_domain": is_suspicious_domain,
        "is_ip_address": is_ip_address,
        "has_typosquatting": has_typosquatting,
        "domain": domain
    }


async def _fetch_and_analyze_page(url: str) -> Dict[str, Any]:
    """Fetch and analyze page content."""
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                content = await response.text()
                
                return {
                    "http_status": response.status,
                    "response_headers": dict(response.headers),
                    "page_content": content[:10000],  # Limit content size
                    "page_title": _extract_title(content),
                    "is_login_page": _detect_login_page(content),
                    "has_suspicious_forms": _detect_suspicious_forms(content),
                    "load_time": 0.0  # Placeholder
                }
    except Exception as e:
        logger.error("Error fetching page", url=url, error=str(e))
        return {
            "http_status": None,
            "page_content": "",
            "is_login_page": False,
            "has_suspicious_forms": False
        }


async def _perform_ai_analysis(url: str, page_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Perform AI-powered analysis of the link and page content."""
    
    # This is a placeholder for AI analysis
    # In production, this would integrate with:
    # - OpenAI GPT for intent classification
    # - Custom ML models for phishing detection
    # - Computer vision for login page detection
    
    ai_confidence = 0.7
    ai_intent = "unknown"
    
    # Simple heuristic-based analysis for MVP
    if page_analysis.get("is_login_page"):
        ai_intent = "login_harvesting"
        ai_confidence = 0.8
    elif page_analysis.get("has_suspicious_forms"):
        ai_intent = "data_harvesting"
        ai_confidence = 0.6
    
    return {
        "ai_intent": ai_intent,
        "ai_confidence": ai_confidence,
        "ai_details": {
            "analysis_method": "heuristic",
            "confidence_factors": ["page_content", "form_detection"]
        }
    }


def _calculate_threat_score(analysis: Dict[str, Any]) -> float:
    """Calculate threat score based on analysis results."""
    
    score = 0.0
    
    # URL structure analysis
    if analysis.get("is_suspicious_domain"):
        score += 0.2
    if analysis.get("is_ip_address"):
        score += 0.3
    if analysis.get("has_typosquatting"):
        score += 0.4
    
    # Page content analysis
    if analysis.get("is_login_page"):
        score += 0.3
    if analysis.get("has_suspicious_forms"):
        score += 0.2
    
    # AI analysis
    ai_confidence = analysis.get("ai_confidence", 0.0)
    if analysis.get("ai_intent") in ["login_harvesting", "data_harvesting"]:
        score += 0.4 * ai_confidence
    
    return min(score, 1.0)


def _is_ip_address(domain: str) -> bool:
    """Check if domain is an IP address."""
    import re
    ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    return bool(re.match(ip_pattern, domain))


def _check_typosquatting(domain: str) -> bool:
    """Check for typosquatting indicators."""
    # This is a simplified check
    # In production, this would use more sophisticated algorithms
    suspicious_indicators = ["microsoft", "google", "amazon", "paypal", "bank"]
    return any(indicator in domain for indicator in suspicious_indicators)


def _extract_title(content: str) -> str:
    """Extract page title from HTML content."""
    import re
    title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
    return title_match.group(1) if title_match else ""


def _detect_login_page(content: str) -> bool:
    """Detect if page is a login page."""
    login_indicators = [
        "login", "signin", "password", "username", "email",
        "form", "submit", "authentication"
    ]
    content_lower = content.lower()
    return any(indicator in content_lower for indicator in login_indicators)


def _detect_suspicious_forms(content: str) -> bool:
    """Detect suspicious forms on the page."""
    suspicious_patterns = [
        "password", "credit", "card", "ssn", "social",
        "bank", "account", "routing"
    ]
    content_lower = content.lower()
    return any(pattern in content_lower for pattern in suspicious_patterns)
