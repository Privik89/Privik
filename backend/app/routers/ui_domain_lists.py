"""
UI Domain Lists API Router
UI-safe proxy endpoints for domain list management
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..models.domain_list import DomainList
from ..security.jwt_auth import verify_jwt_token
from ..security.ui_guard import ui_guard
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.get("/domains")
async def list_domains(
    list_type: Optional[str] = Query(None, description="Filter by list type: whitelist or blacklist"),
    active_only: bool = Query(True, description="Show only active domains"),
    db: Session = Depends(get_db),
    _: bool = Depends(ui_guard),
    ___: dict = Depends(verify_jwt_token)
):
    """List domains in whitelist/blacklist"""
    query = db.query(DomainList)
    
    if list_type:
        query = query.filter(DomainList.list_type == list_type)
    
    if active_only:
        query = query.filter(DomainList.is_active == True)
    
    domains = query.order_by(DomainList.created_at.desc()).all()
    
    return {
        "domains": [
            {
                "id": d.id,
                "domain": d.domain,
                "list_type": d.list_type,
                "reason": d.reason,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "created_by": d.created_by,
                "is_active": d.is_active
            }
            for d in domains
        ]
    }

@router.post("/domains")
async def add_domain(
    domain: str,
    list_type: str,
    reason: Optional[str] = None,
    created_by: Optional[str] = None,
    db: Session = Depends(get_db),
    _: bool = Depends(ui_guard),
    ___: dict = Depends(verify_jwt_token)
):
    """Add domain to whitelist or blacklist"""
    if list_type not in ['whitelist', 'blacklist']:
        raise HTTPException(status_code=400, detail="list_type must be 'whitelist' or 'blacklist'")
    
    # Check if domain already exists
    existing = db.query(DomainList).filter(
        DomainList.domain == domain,
        DomainList.list_type == list_type
    ).first()
    
    if existing:
        if existing.is_active:
            raise HTTPException(status_code=409, detail="Domain already exists in this list")
        else:
            # Reactivate existing domain
            existing.is_active = True
            existing.reason = reason
            existing.created_by = created_by
            existing.created_at = datetime.utcnow()
            db.commit()
            return {"message": "Domain reactivated", "id": existing.id}
    
    # Create new domain entry
    domain_entry = DomainList(
        domain=domain,
        list_type=list_type,
        reason=reason,
        created_by=created_by
    )
    
    db.add(domain_entry)
    db.commit()
    db.refresh(domain_entry)
    
    logger.info("Domain added to list", domain=domain, list_type=list_type, created_by=created_by)
    
    return {"message": "Domain added successfully", "id": domain_entry.id}

@router.delete("/domains/{domain_id}")
async def remove_domain(
    domain_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(ui_guard),
    ___: dict = Depends(verify_jwt_token)
):
    """Remove domain from list (soft delete)"""
    domain = db.query(DomainList).filter(DomainList.id == domain_id).first()
    
    if not domain:
        raise HTTPException(status_code=404, detail="Domain not found")
    
    domain.is_active = False
    db.commit()
    
    logger.info("Domain removed from list", domain=domain.domain, list_type=domain.list_type)
    
    return {"message": "Domain removed successfully"}

@router.get("/domains/check/{domain}")
async def check_domain(
    domain: str,
    db: Session = Depends(get_db),
    _: bool = Depends(ui_guard),
    ___: dict = Depends(verify_jwt_token)
):
    """Check if domain is in whitelist or blacklist"""
    domain_entry = db.query(DomainList).filter(
        DomainList.domain == domain,
        DomainList.is_active == True
    ).first()
    
    if not domain_entry:
        return {"status": "neutral", "list_type": None}
    
    return {
        "status": "listed",
        "list_type": domain_entry.list_type,
        "reason": domain_entry.reason,
        "created_at": domain_entry.created_at.isoformat() if domain_entry.created_at else None
    }
