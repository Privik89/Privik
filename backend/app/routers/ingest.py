from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime
import json

from ..database import get_db
from ..models.email import Email, EmailAttachment
from ..services.sandbox import enqueue_file_for_detonation
from ..services.email_analyzer import analyze_email_content
from ..core.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/ingest", tags=["ingest"])


class EmailIngestRequest(BaseModel):
    message_id: str
    subject: str
    sender: EmailStr
    recipients: List[EmailStr]
    content_type: str = "text/plain"
    body_text: Optional[str] = None
    body_html: Optional[str] = None


class EmailIngestResponse(BaseModel):
    email_id: int
    message_id: str
    threat_score: float
    is_suspicious: bool
    ai_verdict: str
    attachments_count: int
    status: str


@router.post("/email", response_model=EmailIngestResponse)
async def ingest_email(
    email_data: EmailIngestRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Ingest and analyze an email."""
    
    # Check if email already exists
    existing_email = db.query(Email).filter(Email.message_id == email_data.message_id).first()
    if existing_email:
        raise HTTPException(status_code=409, detail="Email already exists")
    
    # Create email record
    email = Email(
        message_id=email_data.message_id,
        subject=email_data.subject,
        sender=email_data.sender,
        recipients=email_data.recipients,
        content_type=email_data.content_type,
        body_text=email_data.body_text,
        body_html=email_data.body_html,
        received_at=datetime.utcnow()
    )
    
    db.add(email)
    db.commit()
    db.refresh(email)
    
    # Queue background analysis
    background_tasks.add_task(
        analyze_email_content,
        email.id,
        email_data.body_text or email_data.body_html or "",
        email_data.subject
    )
    
    return EmailIngestResponse(
        email_id=email.id,
        message_id=email.message_id,
        threat_score=email.threat_score,
        is_suspicious=email.is_suspicious,
        ai_verdict=email.ai_verdict or "pending",
        attachments_count=len(email.attachments),
        status="ingested"
    )


@router.post("/attachment/{email_id}")
async def upload_attachment(
    email_id: int,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """Upload and analyze an email attachment."""
    
    # Verify email exists
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    # Validate file type
    allowed_types = settings.allowed_file_types.split(",")
    file_extension = f".{file.filename.split('.')[-1].lower()}" if '.' in file.filename else ""
    
    if file_extension not in allowed_types:
        raise HTTPException(
            status_code=400, 
            detail=f"File type {file_extension} not allowed. Allowed types: {allowed_types}"
        )
    
    # Save file to temporary location (in production, save to S3/MinIO)
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    try:
        # Create attachment record
        attachment = EmailAttachment(
            email_id=email_id,
            filename=file.filename,
            content_type=file.content_type,
            file_size=len(content),
            s3_key=f"attachments/{email_id}/{file.filename}"  # Placeholder
        )
        
        db.add(attachment)
        db.commit()
        db.refresh(attachment)
        
        # Queue sandbox analysis
        if background_tasks:
            background_tasks.add_task(
                enqueue_file_for_detonation,
                attachment.id,
                temp_file_path
            )
        
        return {
            "attachment_id": attachment.id,
            "filename": attachment.filename,
            "file_size": attachment.file_size,
            "status": "uploaded"
        }
        
    except Exception as e:
        # Clean up temp file
        os.unlink(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Error processing attachment: {str(e)}")


@router.get("/email/{email_id}")
async def get_email(email_id: int, db: Session = Depends(get_db)):
    """Get email details and analysis results."""
    
    email = db.query(Email).filter(Email.id == email_id).first()
    if not email:
        raise HTTPException(status_code=404, detail="Email not found")
    
    return {
        "id": email.id,
        "message_id": email.message_id,
        "subject": email.subject,
        "sender": email.sender,
        "recipients": email.recipients,
        "received_at": email.received_at,
        "threat_score": email.threat_score,
        "is_suspicious": email.is_suspicious,
        "ai_verdict": email.ai_verdict,
        "attachments": [
            {
                "id": att.id,
                "filename": att.filename,
                "file_size": att.file_size,
                "threat_score": att.threat_score,
                "sandbox_verdict": att.sandbox_verdict
            }
            for att in email.attachments
        ],
        "click_events": [
            {
                "id": click.id,
                "original_url": click.original_url,
                "threat_score": click.threat_score,
                "ai_verdict": click.ai_verdict,
                "clicked_at": click.clicked_at
            }
            for click in email.click_events
        ]
    }


@router.get("/ping")
def ping():
    return {"message": "ingest up", "status": "healthy"}


