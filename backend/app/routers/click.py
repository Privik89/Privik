from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, AnyHttpUrl
from typing import Optional
from datetime import datetime

from ..database import get_db
from ..models.click import ClickEvent, LinkAnalysis
from ..models.email import Email
from ..services.click_proxy import build_proxy_url
from ..services.link_analyzer import analyze_link_safety


class ClickRequest(BaseModel):
    original_url: AnyHttpUrl
    user_id: str
    message_id: str
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None


class ClickResponse(BaseModel):
    proxy_url: str
    analysis_id: str
    estimated_analysis_time: int
    status: str


router = APIRouter(prefix="/click", tags=["click"])


@router.post("/redirect", response_model=ClickResponse)
async def redirect_click(
    payload: ClickRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Handle click redirection and queue for analysis."""
    
    # Find the email by message_id
    email = db.query(Email).filter(Email.message_id == payload.message_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # Create click event record
    click_event = ClickEvent(
        email_id=email.id,
        user_id=payload.user_id,
        original_url=str(payload.original_url),
        proxy_url=build_proxy_url(str(payload.original_url)),
        clicked_at=datetime.utcnow()
    )
    
    db.add(click_event)
    db.commit()
    db.refresh(click_event)
    
    # Queue background analysis
    background_tasks.add_task(
        analyze_link_safety,
        click_event.id,
        str(payload.original_url),
        payload.user_id
    )
    
    return ClickResponse(
        proxy_url=click_event.proxy_url,
        analysis_id=str(click_event.id),
        estimated_analysis_time=5,  # seconds
        status="queued"
    )


@router.get("/analysis/{analysis_id}")
async def get_analysis_status(analysis_id: int, db: Session = Depends(get_db)):
    """Get the status of a link analysis."""
    
    click_event = db.query(ClickEvent).filter(ClickEvent.id == analysis_id).first()
    if not click_event:
        raise HTTPException(status_code=404, detail="Analysis not found")
    
    link_analysis = db.query(LinkAnalysis).filter(
        LinkAnalysis.click_event_id == analysis_id
    ).first()
    
    return {
        "analysis_id": analysis_id,
        "status": "completed" if link_analysis else "in_progress",
        "threat_score": click_event.threat_score,
        "verdict": click_event.ai_verdict,
        "is_suspicious": click_event.is_suspicious,
        "analysis_details": link_analysis.ai_details if link_analysis else None
    }


