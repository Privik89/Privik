import asyncio
import hashlib
import os
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog
from sqlalchemy.orm import Session

from ..database import SessionLocal
from ..models.sandbox import SandboxAnalysis, SandboxVerdict
from ..models.email import EmailAttachment
from ..core.config import get_settings

logger = structlog.get_logger()
settings = get_settings()


@dataclass
class SandboxVerdict:
    verdict: str
    score: float
    details: Dict[str, Any]


async def enqueue_file_for_detonation(attachment_id: int, file_path: str) -> SandboxVerdict:
    """Enqueue a file for sandbox detonation and analysis."""
    
    logger.info("Enqueueing file for detonation", attachment_id=attachment_id, file_path=file_path)
    
    db = SessionLocal()
    try:
        # Get attachment details
        attachment = db.query(EmailAttachment).filter(EmailAttachment.id == attachment_id).first()
        if not attachment:
            raise ValueError(f"Attachment {attachment_id} not found")
        
        # Create sandbox analysis record
        sandbox_analysis = SandboxAnalysis(
            attachment_id=attachment_id,
            sandbox_id=f"sb_{attachment_id}_{int(datetime.utcnow().timestamp())}",
            analysis_started=datetime.utcnow(),
            file_hash=_calculate_file_hash(file_path),
            file_type=_detect_file_type(file_path),
            file_size=os.path.getsize(file_path)
        )
        
        db.add(sandbox_analysis)
        db.commit()
        db.refresh(sandbox_analysis)
        
        # Start background analysis
        asyncio.create_task(_perform_sandbox_analysis(sandbox_analysis.id, file_path))
        
        return SandboxVerdict(
            verdict="queued",
            score=0.0,
            details={"sandbox_id": sandbox_analysis.sandbox_id, "status": "queued"}
        )
        
    except Exception as e:
        logger.error("Error enqueueing file for detonation", 
                    attachment_id=attachment_id, 
                    error=str(e))
        db.rollback()
        return SandboxVerdict(verdict="error", score=0.0, details={"error": str(e)})
    finally:
        db.close()


async def _perform_sandbox_analysis(analysis_id: int, file_path: str):
    """Perform sandbox analysis of the file."""
    
    logger.info("Starting sandbox analysis", analysis_id=analysis_id)
    
    db = SessionLocal()
    try:
        # Get the analysis record
        analysis = db.query(SandboxAnalysis).filter(SandboxAnalysis.id == analysis_id).first()
        if not analysis:
            logger.error("Sandbox analysis not found", analysis_id=analysis_id)
            return
        
        # Perform different types of analysis
        static_verdict = await _perform_static_analysis(file_path)
        behavioral_verdict = await _perform_behavioral_analysis(file_path)
        ai_verdict = await _perform_ai_analysis(file_path, static_verdict, behavioral_verdict)
        
        # Calculate final verdict
        final_verdict = _calculate_final_verdict(static_verdict, behavioral_verdict, ai_verdict)
        
        # Update analysis record
        analysis.analysis_completed = datetime.utcnow()
        analysis.analysis_duration = (analysis.analysis_completed - analysis.analysis_started).total_seconds()
        analysis.threat_score = final_verdict.score
        analysis.verdict = final_verdict.verdict
        analysis.confidence = final_verdict.details.get("confidence", 0.0)
        analysis.ai_verdict = ai_verdict.verdict
        analysis.ai_confidence = ai_verdict.details.get("confidence", 0.0)
        analysis.ai_details = ai_verdict.details
        
        # Store behavioral analysis results
        analysis.process_created = behavioral_verdict.details.get("processes", [])
        analysis.files_created = behavioral_verdict.details.get("files", [])
        analysis.registry_changes = behavioral_verdict.details.get("registry", [])
        analysis.network_connections = behavioral_verdict.details.get("network", [])
        analysis.api_calls = behavioral_verdict.details.get("api_calls", [])
        
        # Create verdict records
        for verdict_type, verdict in [
            ("static", static_verdict),
            ("behavioral", behavioral_verdict),
            ("ai", ai_verdict),
            ("final", final_verdict)
        ]:
            verdict_record = SandboxVerdict(
                analysis_id=analysis_id,
                verdict_type=verdict_type,
                verdict=verdict.verdict,
                confidence=verdict.details.get("confidence", 0.0),
                details=verdict.details
            )
            db.add(verdict_record)
        
        db.commit()
        
        logger.info("Sandbox analysis completed", 
                   analysis_id=analysis_id,
                   verdict=final_verdict.verdict,
                   threat_score=final_verdict.score)
        
    except Exception as e:
        logger.error("Error during sandbox analysis", 
                    analysis_id=analysis_id, 
                    error=str(e))
        db.rollback()
    finally:
        db.close()


async def _perform_static_analysis(file_path: str) -> SandboxVerdict:
    """Perform static analysis of the file."""
    
    try:
        # Basic file analysis
        file_size = os.path.getsize(file_path)
        file_hash = _calculate_file_hash(file_path)
        file_type = _detect_file_type(file_path)
        
        # Check file size (suspicious if too small or too large)
        size_suspicious = file_size < 100 or file_size > 50 * 1024 * 1024  # 50MB
        
        # Check file type
        suspicious_extensions = [".exe", ".bat", ".cmd", ".ps1", ".vbs", ".js"]
        is_suspicious_type = any(file_path.lower().endswith(ext) for ext in suspicious_extensions)
        
        # Calculate static threat score
        static_score = 0.0
        if size_suspicious:
            static_score += 0.2
        if is_suspicious_type:
            static_score += 0.3
        
        return SandboxVerdict(
            verdict="suspicious" if static_score > 0.3 else "allow",
            score=static_score,
            details={
                "file_size": file_size,
                "file_hash": file_hash,
                "file_type": file_type,
                "size_suspicious": size_suspicious,
                "suspicious_type": is_suspicious_type,
                "confidence": 0.6
            }
        )
        
    except Exception as e:
        logger.error("Error in static analysis", file_path=file_path, error=str(e))
        return SandboxVerdict(verdict="error", score=0.0, details={"error": str(e)})


async def _perform_behavioral_analysis(file_path: str) -> SandboxVerdict:
    """Perform behavioral analysis (simulated for MVP)."""
    
    # This is a placeholder for behavioral analysis
    # In production, this would integrate with:
    # - Cuckoo Sandbox
    # - CAPEv2
    # - Custom sandbox environment
    
    # Simulate some behavioral analysis results
    simulated_behaviors = {
        "processes": [],
        "files": [],
        "registry": [],
        "network": [],
        "api_calls": []
    }
    
    # For MVP, we'll simulate based on file type
    file_type = _detect_file_type(file_path)
    if file_type in [".exe", ".bat", ".cmd"]:
        simulated_behaviors["processes"] = ["cmd.exe", "powershell.exe"]
        simulated_behaviors["api_calls"] = ["CreateProcess", "WriteFile"]
    
    behavioral_score = 0.1  # Low score for MVP simulation
    
    return SandboxVerdict(
        verdict="allow",
        score=behavioral_score,
        details={
            **simulated_behaviors,
            "confidence": 0.4,
            "analysis_method": "simulated"
        }
    )


async def _perform_ai_analysis(file_path: str, static_verdict: SandboxVerdict, behavioral_verdict: SandboxVerdict) -> SandboxVerdict:
    """Perform AI-powered analysis of the file."""
    
    # This is a placeholder for AI analysis
    # In production, this would integrate with:
    # - OpenAI GPT for file analysis
    # - Custom ML models for malware detection
    # - Computer vision for document analysis
    
    # Combine static and behavioral analysis for AI decision
    combined_score = (static_verdict.score + behavioral_verdict.score) / 2
    
    ai_confidence = 0.7
    ai_verdict = "allow"
    
    if combined_score > 0.5:
        ai_verdict = "suspicious"
    elif combined_score > 0.8:
        ai_verdict = "malicious"
    
    return SandboxVerdict(
        verdict=ai_verdict,
        score=combined_score,
        details={
            "confidence": ai_confidence,
            "analysis_method": "ai_heuristic",
            "static_score": static_verdict.score,
            "behavioral_score": behavioral_verdict.score
        }
    )


def _calculate_final_verdict(static_verdict: SandboxVerdict, behavioral_verdict: SandboxVerdict, ai_verdict: SandboxVerdict) -> SandboxVerdict:
    """Calculate final verdict based on all analysis results."""
    
    # Weight the different analysis types
    static_weight = 0.3
    behavioral_weight = 0.4
    ai_weight = 0.3
    
    final_score = (
        static_verdict.score * static_weight +
        behavioral_verdict.score * behavioral_weight +
        ai_verdict.score * ai_weight
    )
    
    # Determine final verdict
    if final_score > 0.8:
        final_verdict = "malicious"
    elif final_score > 0.5:
        final_verdict = "suspicious"
    else:
        final_verdict = "allow"
    
    # Calculate confidence
    confidence = (
        static_verdict.details.get("confidence", 0.0) * static_weight +
        behavioral_verdict.details.get("confidence", 0.0) * behavioral_weight +
        ai_verdict.details.get("confidence", 0.0) * ai_weight
    )
    
    return SandboxVerdict(
        verdict=final_verdict,
        score=final_score,
        details={
            "confidence": confidence,
            "static_verdict": static_verdict.verdict,
            "behavioral_verdict": behavioral_verdict.verdict,
            "ai_verdict": ai_verdict.verdict
        }
    )


def _calculate_file_hash(file_path: str) -> str:
    """Calculate SHA256 hash of the file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def _detect_file_type(file_path: str) -> str:
    """Detect file type based on extension."""
    _, ext = os.path.splitext(file_path)
    return ext.lower() if ext else ""


