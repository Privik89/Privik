import re
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import structlog
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models.email import Email
from ..core.config import get_settings
from .domain_reputation import DomainReputationService

logger = structlog.get_logger()
settings = get_settings()


async def analyze_email_content(email_id: int, content: str, subject: str):
    """Analyze email content for phishing and BEC indicators."""
    
    logger.info("Starting email content analysis", email_id=email_id)
    
    db = SessionLocal()
    try:
        # Get the email record
        email = db.query(Email).filter(Email.id == email_id).first()
        if not email:
            logger.error("Email not found", email_id=email_id)
            return
        
        # Perform analysis
        analysis_result = await _perform_email_analysis(content, subject, email.sender)
        
        # Update email with analysis results
        email.threat_score = analysis_result.get("threat_score", 0.0)
        email.is_suspicious = analysis_result.get("is_suspicious", False)
        email.ai_verdict = analysis_result.get("ai_verdict", "safe")
        email.static_scan_result = analysis_result.get("static_scan_result", {})
        
        db.commit()
        
        logger.info("Email analysis completed", 
                   email_id=email_id,
                   threat_score=email.threat_score,
                   verdict=email.ai_verdict)
        
    except Exception as e:
        logger.error("Error during email analysis", 
                    email_id=email_id, 
                    error=str(e))
        db.rollback()
    finally:
        db.close()


async def _perform_email_analysis(content: str, subject: str, sender: str) -> Dict[str, Any]:
    """Perform comprehensive email analysis."""
    
    result = {
        "threat_score": 0.0,
        "is_suspicious": False,
        "ai_verdict": "safe",
        "static_scan_result": {}
    }
    
    try:
        # 1. Subject line analysis
        subject_analysis = _analyze_subject_line(subject)
        result["static_scan_result"]["subject"] = subject_analysis
        
        # 2. Content analysis
        content_analysis = _analyze_email_content(content)
        result["static_scan_result"]["content"] = content_analysis
        
        # 3. Sender analysis
        sender_analysis = _analyze_sender(sender)
        result["static_scan_result"]["sender"] = sender_analysis
        
        # 4. Domain reputation analysis
        domain_analysis = await _analyze_domain_reputation(content, sender)
        result["static_scan_result"]["domain_reputation"] = domain_analysis
        
        # 5. AI-powered analysis
        ai_analysis = await _perform_ai_email_analysis(content, subject, sender)
        result.update(ai_analysis)
        
        # 6. Calculate final threat score
        result["threat_score"] = _calculate_email_threat_score(result)
        result["is_suspicious"] = result["threat_score"] > 0.5
        result["ai_verdict"] = "malicious" if result["threat_score"] > 0.8 else \
                              "suspicious" if result["threat_score"] > 0.5 else "safe"
        
    except Exception as e:
        logger.error("Error in email analysis", error=str(e))
        result["ai_verdict"] = "error"
    
    return result


def _analyze_subject_line(subject: str) -> Dict[str, Any]:
    """Analyze subject line for suspicious patterns."""
    
    subject_lower = subject.lower()
    
    # Suspicious subject patterns
    suspicious_patterns = [
        "urgent", "action required", "account suspended", "security alert",
        "password expired", "login attempt", "unusual activity", "verify account",
        "invoice", "payment", "refund", "lottery", "inheritance", "prize"
    ]
    
    # BEC indicators
    bec_patterns = [
        "wire transfer", "bank transfer", "urgent payment", "vendor payment",
        "invoice payment", "account verification", "banking details"
    ]
    
    # Phishing indicators
    phishing_patterns = [
        "login", "signin", "password", "account", "verify", "confirm",
        "security", "suspended", "locked", "expired"
    ]
    
    # Count matches
    suspicious_count = sum(1 for pattern in suspicious_patterns if pattern in subject_lower)
    bec_count = sum(1 for pattern in bec_patterns if pattern in subject_lower)
    phishing_count = sum(1 for pattern in phishing_patterns if pattern in subject_lower)
    
    return {
        "suspicious_patterns": suspicious_count,
        "bec_indicators": bec_count,
        "phishing_indicators": phishing_count,
        "total_indicators": suspicious_count + bec_count + phishing_count,
        "is_suspicious": (suspicious_count + bec_count + phishing_count) > 2
    }


def _analyze_email_content(content: str) -> Dict[str, Any]:
    """Analyze email content for suspicious patterns."""
    
    content_lower = content.lower()
    
    # Extract URLs
    urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
    
    # Extract email addresses
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
    
    # Suspicious content patterns
    suspicious_patterns = [
        "click here", "login now", "verify your account", "confirm your details",
        "urgent action", "account suspended", "password expired", "unusual activity",
        "wire transfer", "bank transfer", "urgent payment", "vendor payment"
    ]
    
    # Count matches
    suspicious_count = sum(1 for pattern in suspicious_patterns if pattern in content_lower)
    
    # Check for urgency indicators
    urgency_words = ["urgent", "immediate", "asap", "now", "quickly", "hurry"]
    urgency_count = sum(1 for word in urgency_words if word in content_lower)
    
    # Check for authority indicators
    authority_words = ["ceo", "manager", "director", "president", "boss"]
    authority_count = sum(1 for word in authority_words if word in content_lower)
    
    return {
        "urls_found": len(urls),
        "emails_found": len(emails),
        "suspicious_patterns": suspicious_count,
        "urgency_indicators": urgency_count,
        "authority_indicators": authority_count,
        "is_suspicious": suspicious_count > 3 or urgency_count > 2
    }


def _analyze_sender(sender: str) -> Dict[str, Any]:
    """Analyze sender email for suspicious patterns."""
    
    sender_lower = sender.lower()
    
    # Check for suspicious domains
    suspicious_domains = [
        "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",  # Personal domains
        "free", "temp", "disposable"  # Disposable email indicators
    ]
    
    # Check for typosquatting
    typosquatting_indicators = [
        "microsoft", "google", "amazon", "paypal", "bank", "apple"
    ]
    
    # Check for random-looking domains
    random_patterns = [
        r'\d{3,}',  # Many numbers
        r'[a-z]{10,}',  # Very long random strings
    ]
    
    is_suspicious_domain = any(domain in sender_lower for domain in suspicious_domains)
    has_typosquatting = any(indicator in sender_lower for indicator in typosquatting_indicators)
    is_random_domain = any(re.search(pattern, sender_lower) for pattern in random_patterns)
    
    return {
        "is_suspicious_domain": is_suspicious_domain,
        "has_typosquatting": has_typosquatting,
        "is_random_domain": is_random_domain,
        "is_suspicious": is_suspicious_domain or has_typosquatting or is_random_domain
    }


async def _perform_ai_email_analysis(content: str, subject: str, sender: str) -> Dict[str, Any]:
    """Perform AI-powered analysis of email content."""
    
    # This is a placeholder for AI analysis
    # In production, this would integrate with:
    # - OpenAI GPT for content analysis
    # - Custom ML models for BEC detection
    # - NLP models for intent classification
    
    # Simple heuristic-based analysis for MVP
    content_lower = content.lower()
    subject_lower = subject.lower()
    
    # BEC detection
    bec_indicators = [
        "wire transfer", "bank transfer", "urgent payment", "vendor payment",
        "invoice payment", "account verification", "banking details", "ceo",
        "manager", "director", "president", "boss"
    ]
    
    bec_score = sum(1 for indicator in bec_indicators 
                   if indicator in content_lower or indicator in subject_lower)
    
    # Phishing detection
    phishing_indicators = [
        "login", "signin", "password", "account", "verify", "confirm",
        "security", "suspended", "locked", "expired", "click here"
    ]
    
    phishing_score = sum(1 for indicator in phishing_indicators 
                        if indicator in content_lower or indicator in subject_lower)
    
    # Calculate AI confidence and intent
    total_indicators = bec_score + phishing_score
    ai_confidence = min(total_indicators / 10.0, 1.0)  # Normalize to 0-1
    
    if bec_score > phishing_score and bec_score > 3:
        ai_intent = "bec_attack"
    elif phishing_score > 3:
        ai_intent = "phishing_attack"
    else:
        ai_intent = "legitimate"
    
    return {
        "ai_intent": ai_intent,
        "ai_confidence": ai_confidence,
        "ai_details": {
            "bec_indicators": bec_score,
            "phishing_indicators": phishing_score,
            "analysis_method": "heuristic"
        }
    }


async def _analyze_domain_reputation(content: str, sender: str) -> Dict[str, Any]:
    """Analyze domain reputation for sender and links in email content."""
    
    result = {
        "sender_domain_score": 0.5,  # Default neutral score
        "link_domain_scores": [],
        "overall_domain_threat": 0.0,
        "threat_indicators": [],
        "analysis_method": "domain_reputation"
    }
    
    try:
        async with DomainReputationService() as reputation_service:
            # Extract sender domain
            sender_domain = _extract_domain_from_email(sender)
            
            # Extract link domains from content
            link_domains = _extract_link_domains(content)
            
            # Collect all domains to score
            domains_to_score = []
            if sender_domain:
                domains_to_score.append(sender_domain)
            domains_to_score.extend(link_domains)
            
            if not domains_to_score:
                return result
            
            # Score all domains in parallel
            domain_scores = await reputation_service.bulk_score_domains(domains_to_score)
            
            # Process sender domain score
            if sender_domain:
                sender_score = next((ds for ds in domain_scores if ds.domain == sender_domain), None)
                if sender_score:
                    result["sender_domain_score"] = sender_score.reputation_score
                    result["threat_indicators"].extend(sender_score.threat_indicators)
            
            # Process link domain scores
            link_scores = []
            for domain_score in domain_scores:
                if domain_score.domain in link_domains:
                    link_scores.append({
                        "domain": domain_score.domain,
                        "score": domain_score.reputation_score,
                        "risk_level": domain_score.risk_level,
                        "threat_indicators": domain_score.threat_indicators
                    })
                    result["threat_indicators"].extend(domain_score.threat_indicators)
            
            result["link_domain_scores"] = link_scores
            
            # Calculate overall domain threat score
            all_scores = [result["sender_domain_score"]] + [ls["score"] for ls in link_scores]
            if all_scores:
                # Use lowest score (most malicious) as overall threat
                result["overall_domain_threat"] = 1.0 - min(all_scores)
            
            # Remove duplicate threat indicators
            result["threat_indicators"] = list(set(result["threat_indicators"]))
            
    except Exception as e:
        logger.error("Error in domain reputation analysis", error=str(e))
        result["analysis_method"] = "error"
    
    return result


def _extract_domain_from_email(email: str) -> Optional[str]:
    """Extract domain from email address."""
    try:
        if '@' in email:
            return email.split('@')[1].lower()
        return None
    except:
        return None


def _extract_link_domains(content: str) -> List[str]:
    """Extract domains from URLs in email content."""
    domains = []
    
    try:
        # URL pattern matching
        url_pattern = r'https?://([^/\s]+)'
        urls = re.findall(url_pattern, content, re.IGNORECASE)
        
        for url_domain in urls:
            # Clean domain (remove port, path fragments)
            domain = url_domain.split(':')[0].split('/')[0].lower()
            if domain and domain not in domains:
                domains.append(domain)
        
        # Also check for domains without protocol
        domain_pattern = r'([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}'
        found_domains = re.findall(domain_pattern, content, re.IGNORECASE)
        
        for domain in found_domains:
            domain = domain.lower()
            if domain not in domains and len(domain) > 3:  # Filter out very short matches
                domains.append(domain)
                
    except Exception as e:
        logger.error("Error extracting link domains", error=str(e))
    
    return domains


def _calculate_email_threat_score(analysis: Dict[str, Any]) -> float:
    """Calculate threat score based on email analysis results."""
    
    score = 0.0
    
    # Subject analysis
    subject_analysis = analysis.get("static_scan_result", {}).get("subject", {})
    if subject_analysis.get("is_suspicious"):
        score += 0.2
    score += subject_analysis.get("total_indicators", 0) * 0.05
    
    # Content analysis
    content_analysis = analysis.get("static_scan_result", {}).get("content", {})
    if content_analysis.get("is_suspicious"):
        score += 0.3
    score += content_analysis.get("suspicious_patterns", 0) * 0.05
    score += content_analysis.get("urgency_indicators", 0) * 0.03
    
    # Sender analysis
    sender_analysis = analysis.get("static_scan_result", {}).get("sender", {})
    if sender_analysis.get("is_suspicious"):
        score += 0.2
    
    # Domain reputation analysis
    domain_analysis = analysis.get("static_scan_result", {}).get("domain_reputation", {})
    if domain_analysis.get("overall_domain_threat", 0) > 0.7:
        score += 0.4  # High domain threat
    elif domain_analysis.get("overall_domain_threat", 0) > 0.4:
        score += 0.2  # Medium domain threat
    
    # Add domain threat indicators
    threat_indicators = domain_analysis.get("threat_indicators", [])
    for indicator in threat_indicators:
        if "malicious" in indicator:
            score += 0.15
        elif "suspicious" in indicator:
            score += 0.1
        elif "phishing" in indicator:
            score += 0.2
    
    # AI analysis
    ai_confidence = analysis.get("ai_confidence", 0.0)
    ai_intent = analysis.get("ai_intent", "legitimate")
    
    if ai_intent == "bec_attack":
        score += 0.4 * ai_confidence
    elif ai_intent == "phishing_attack":
        score += 0.3 * ai_confidence
    
    return min(score, 1.0)
