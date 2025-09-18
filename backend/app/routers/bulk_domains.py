"""
Bulk Domain Operations API Router
Handles bulk import/export operations for domain lists
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..security.hmac_auth import verify_request
from ..services.bulk_domain_manager import BulkDomainManager
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.post("/domains/bulk/import/csv")
async def import_domains_csv(
    file: UploadFile = File(...),
    list_type: str = Form(...),
    created_by: str = Form("bulk_import"),
    validate_domains: bool = Form(True),
    score_domains: bool = Form(True),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Import domains from CSV file"""
    try:
        if not file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="File must be a CSV")
        
        if list_type not in ['whitelist', 'blacklist']:
            raise HTTPException(status_code=400, detail="list_type must be 'whitelist' or 'blacklist'")
        
        # Read file content
        content = await file.read()
        csv_content = content.decode('utf-8')
        
        # Import domains
        manager = BulkDomainManager()
        result = await manager.import_domains_from_csv(
            csv_content=csv_content,
            list_type=list_type,
            created_by=created_by,
            validate_domains=validate_domains,
            score_domains=score_domains
        )
        
        logger.info("CSV import completed", 
                   list_type=list_type,
                   successful=result["successful_imports"])
        
        return result
        
    except Exception as e:
        logger.error("CSV import failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@router.post("/domains/bulk/import/json")
async def import_domains_json(
    file: UploadFile = File(...),
    list_type: str = Form(...),
    created_by: str = Form("bulk_import"),
    validate_domains: bool = Form(True),
    score_domains: bool = Form(True),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Import domains from JSON file"""
    try:
        if not file.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="File must be a JSON")
        
        if list_type not in ['whitelist', 'blacklist']:
            raise HTTPException(status_code=400, detail="list_type must be 'whitelist' or 'blacklist'")
        
        # Read file content
        content = await file.read()
        json_content = content.decode('utf-8')
        
        # Import domains
        manager = BulkDomainManager()
        result = await manager.import_domains_from_json(
            json_content=json_content,
            list_type=list_type,
            created_by=created_by,
            validate_domains=validate_domains,
            score_domains=score_domains
        )
        
        logger.info("JSON import completed", 
                   list_type=list_type,
                   successful=result["successful_imports"])
        
        return result
        
    except Exception as e:
        logger.error("JSON import failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@router.get("/domains/bulk/export/csv")
async def export_domains_csv(
    list_type: Optional[str] = Query(None, description="Filter by list type"),
    active_only: bool = Query(True, description="Export only active domains"),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Export domains to CSV format"""
    try:
        manager = BulkDomainManager()
        csv_content = await manager.export_domains_to_csv(
            list_type=list_type,
            active_only=active_only
        )
        
        from fastapi.responses import Response
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=domains_export.csv"}
        )
        
    except Exception as e:
        logger.error("CSV export failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.get("/domains/bulk/export/json")
async def export_domains_json(
    list_type: Optional[str] = Query(None, description="Filter by list type"),
    active_only: bool = Query(True, description="Export only active domains"),
    include_metadata: bool = Query(True, description="Include export metadata"),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Export domains to JSON format"""
    try:
        manager = BulkDomainManager()
        json_content = await manager.export_domains_to_json(
            list_type=list_type,
            active_only=active_only,
            include_metadata=include_metadata
        )
        
        from fastapi.responses import Response
        return Response(
            content=json_content,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=domains_export.json"}
        )
        
    except Exception as e:
        logger.error("JSON export failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")

@router.post("/domains/bulk/update")
async def bulk_update_domains(
    updates: List[dict],
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Bulk update domain properties"""
    try:
        if len(updates) > 1000:
            raise HTTPException(status_code=400, detail="Maximum 1000 domains per update")
        
        manager = BulkDomainManager()
        result = await manager.bulk_update_domains(updates)
        
        logger.info("Bulk update completed", 
                   successful=result["successful_updates"])
        
        return result
        
    except Exception as e:
        logger.error("Bulk update failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

@router.post("/domains/bulk/delete")
async def bulk_delete_domains(
    domain_identifiers: List[str],
    soft_delete: bool = Query(True, description="Soft delete (mark inactive) or hard delete"),
    db: Session = Depends(get_db),
    _: dict = Depends(verify_request)
):
    """Bulk delete domains"""
    try:
        if len(domain_identifiers) > 1000:
            raise HTTPException(status_code=400, detail="Maximum 1000 domains per delete")
        
        manager = BulkDomainManager()
        result = await manager.bulk_delete_domains(
            domain_identifiers=domain_identifiers,
            soft_delete=soft_delete
        )
        
        logger.info("Bulk delete completed", 
                   successful=result["successful_deletes"],
                   soft_delete=soft_delete)
        
        return result
        
    except Exception as e:
        logger.error("Bulk delete failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
