"""
UI SOC Proxy: CSV export of incidents list with JWT/UI guard.
"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
import io
import csv
from typing import List

from ..security.ui_guard import ui_guard
from ..security.jwt_auth import verify_jwt_admin
from ..database import SessionLocal
from ..models.sandbox import SandboxAnalysis
from ..models.email import Email, EmailAttachment


router = APIRouter(prefix="/api/ui/soc", tags=["ui-soc"], dependencies=[Depends(ui_guard), Depends(verify_jwt_admin)])


@router.get("/incidents/export.csv")
async def export_incidents_csv(limit: int = 100):
    db = SessionLocal()
    try:
        analyses: List[SandboxAnalysis] = db.query(SandboxAnalysis).order_by(SandboxAnalysis.created_at.desc()).limit(limit).all()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "created_at", "verdict", "confidence", "threat_score", "email_subject", "filename"])
        for a in analyses:
            att = db.query(EmailAttachment).filter(EmailAttachment.id == a.attachment_id).first() if a.attachment_id else None
            eml = db.query(Email).filter(Email.id == att.email_id).first() if att else None
            writer.writerow([
                a.id,
                a.created_at.isoformat() if a.created_at else "",
                a.verdict or "",
                f"{a.confidence:.2f}" if a.confidence is not None else "",
                f"{a.threat_score:.2f}" if a.threat_score is not None else "",
                eml.subject if eml else "",
                att.filename if att else "",
            ])
        output.seek(0)
        return StreamingResponse(iter([output.getvalue()]), media_type="text/csv")
    finally:
        db.close()


@router.get("/incidents/{incident_id}/export.json")
async def export_incident_json(incident_id: int):
    db = SessionLocal()
    try:
        a = db.query(SandboxAnalysis).filter(SandboxAnalysis.id == incident_id).first()
        if not a:
            return StreamingResponse(iter(["{}"]), media_type="application/json")
        att = db.query(EmailAttachment).filter(EmailAttachment.id == a.attachment_id).first() if a.attachment_id else None
        eml = db.query(Email).filter(Email.id == att.email_id).first() if att else None
        payload = {
            'id': a.id,
            'created_at': a.created_at.isoformat() if a.created_at else None,
            'verdict': a.verdict,
            'confidence': a.confidence,
            'threat_score': a.threat_score,
            'artifacts': {
                'report_key': a.artifacts_report_key,
                'screenshots': a.artifacts_screenshots or []
            },
            'behavior': {
                'process_created': a.process_created,
                'network_connections': a.network_connections,
                'registry_changes': a.registry_changes,
                'api_calls': a.api_calls,
            },
            'ai_details': a.ai_details,
            'email': {
                'subject': eml.subject if eml else None,
                'sender': eml.sender if eml else None,
                'recipients': eml.recipients if eml else None,
                'message_id': eml.message_id if eml else None,
            },
            'attachment': {
                'filename': att.filename if att else None,
                'content_type': att.content_type if att else None,
                'file_size': att.file_size if att else None,
            }
        }
        data = io.StringIO()
        import json
        data.write(json.dumps(payload, default=str))
        data.seek(0)
        return StreamingResponse(iter([data.getvalue()]), media_type="application/json")
    finally:
        db.close()


