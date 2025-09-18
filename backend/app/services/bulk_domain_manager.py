"""
Bulk Domain Manager Service
Handles bulk import/export operations for domain lists
"""

import csv
import json
import asyncio
from io import StringIO, BytesIO
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import structlog
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models.domain_list import DomainList
from .domain_reputation import DomainReputationService
import re

logger = structlog.get_logger()

class BulkDomainManager:
    """Manages bulk domain import/export operations"""
    
    def __init__(self):
        self.db = SessionLocal()
        
    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()
    
    async def import_domains_from_csv(
        self, 
        csv_content: str, 
        list_type: str,
        created_by: str = "bulk_import",
        validate_domains: bool = True,
        score_domains: bool = True
    ) -> Dict[str, Any]:
        """Import domains from CSV content"""
        
        result = {
            "total_processed": 0,
            "successful_imports": 0,
            "validation_errors": 0,
            "duplicate_domains": 0,
            "errors": [],
            "imported_domains": [],
            "failed_domains": []
        }
        
        try:
            # Parse CSV content
            csv_reader = csv.DictReader(StringIO(csv_content))
            
            # Validate required columns
            required_columns = ['domain']
            if not all(col in csv_reader.fieldnames for col in required_columns):
                raise ValueError(f"CSV must contain columns: {', '.join(required_columns)}")
            
            # Process each row
            domains_to_import = []
            for row_num, row in enumerate(csv_reader, start=2):  # Start at 2 (header is row 1)
                try:
                    domain = row['domain'].strip().lower()
                    reason = row.get('reason', '').strip()
                    
                    if not domain:
                        result["errors"].append(f"Row {row_num}: Empty domain")
                        result["validation_errors"] += 1
                        continue
                    
                    # Validate domain format
                    if validate_domains and not self._validate_domain_format(domain):
                        result["errors"].append(f"Row {row_num}: Invalid domain format '{domain}'")
                        result["validation_errors"] += 1
                        result["failed_domains"].append(domain)
                        continue
                    
                    # Check for duplicates
                    existing = self.db.query(DomainList).filter(
                        DomainList.domain == domain,
                        DomainList.list_type == list_type
                    ).first()
                    
                    if existing:
                        if existing.is_active:
                            result["duplicate_domains"] += 1
                            result["errors"].append(f"Row {row_num}: Domain '{domain}' already exists")
                            continue
                        else:
                            # Reactivate existing domain
                            existing.is_active = True
                            existing.reason = reason
                            existing.created_by = created_by
                            existing.created_at = datetime.utcnow()
                            self.db.commit()
                            result["successful_imports"] += 1
                            result["imported_domains"].append(domain)
                            continue
                    
                    domains_to_import.append({
                        'domain': domain,
                        'reason': reason,
                        'created_by': created_by
                    })
                    
                except Exception as e:
                    result["errors"].append(f"Row {row_num}: {str(e)}")
                    result["validation_errors"] += 1
            
            # Bulk insert new domains
            if domains_to_import:
                domain_objects = [
                    DomainList(
                        domain=d['domain'],
                        list_type=list_type,
                        reason=d['reason'],
                        created_by=d['created_by']
                    )
                    for d in domains_to_import
                ]
                
                self.db.add_all(domain_objects)
                self.db.commit()
                
                result["successful_imports"] += len(domain_objects)
                result["imported_domains"].extend([d['domain'] for d in domains_to_import])
            
            # Score imported domains if requested
            if score_domains and result["imported_domains"]:
                await self._score_imported_domains(result["imported_domains"])
            
            result["total_processed"] = len(csv_reader.fieldnames) + len(domains_to_import) + result["validation_errors"]
            
            logger.info("CSV import completed", 
                       list_type=list_type,
                       successful=result["successful_imports"],
                       errors=result["validation_errors"])
            
        except Exception as e:
            logger.error("CSV import failed", error=str(e))
            result["errors"].append(f"Import failed: {str(e)}")
        
        return result
    
    async def import_domains_from_json(
        self,
        json_content: str,
        list_type: str,
        created_by: str = "bulk_import",
        validate_domains: bool = True,
        score_domains: bool = True
    ) -> Dict[str, Any]:
        """Import domains from JSON content"""
        
        result = {
            "total_processed": 0,
            "successful_imports": 0,
            "validation_errors": 0,
            "duplicate_domains": 0,
            "errors": [],
            "imported_domains": [],
            "failed_domains": []
        }
        
        try:
            # Parse JSON content
            data = json.loads(json_content)
            
            # Handle different JSON formats
            domains_data = []
            if isinstance(data, list):
                domains_data = data
            elif isinstance(data, dict):
                if 'domains' in data:
                    domains_data = data['domains']
                else:
                    # Treat as single domain entry
                    domains_data = [data]
            
            # Process each domain entry
            domains_to_import = []
            for idx, entry in enumerate(domains_data):
                try:
                    if isinstance(entry, str):
                        # Simple string format
                        domain = entry.strip().lower()
                        reason = ""
                    elif isinstance(entry, dict):
                        # Object format
                        domain = entry.get('domain', '').strip().lower()
                        reason = entry.get('reason', '').strip()
                    else:
                        result["errors"].append(f"Entry {idx + 1}: Invalid format")
                        result["validation_errors"] += 1
                        continue
                    
                    if not domain:
                        result["errors"].append(f"Entry {idx + 1}: Empty domain")
                        result["validation_errors"] += 1
                        continue
                    
                    # Validate domain format
                    if validate_domains and not self._validate_domain_format(domain):
                        result["errors"].append(f"Entry {idx + 1}: Invalid domain format '{domain}'")
                        result["validation_errors"] += 1
                        result["failed_domains"].append(domain)
                        continue
                    
                    # Check for duplicates
                    existing = self.db.query(DomainList).filter(
                        DomainList.domain == domain,
                        DomainList.list_type == list_type
                    ).first()
                    
                    if existing:
                        if existing.is_active:
                            result["duplicate_domains"] += 1
                            result["errors"].append(f"Entry {idx + 1}: Domain '{domain}' already exists")
                            continue
                        else:
                            # Reactivate existing domain
                            existing.is_active = True
                            existing.reason = reason
                            existing.created_by = created_by
                            existing.created_at = datetime.utcnow()
                            self.db.commit()
                            result["successful_imports"] += 1
                            result["imported_domains"].append(domain)
                            continue
                    
                    domains_to_import.append({
                        'domain': domain,
                        'reason': reason,
                        'created_by': created_by
                    })
                    
                except Exception as e:
                    result["errors"].append(f"Entry {idx + 1}: {str(e)}")
                    result["validation_errors"] += 1
            
            # Bulk insert new domains
            if domains_to_import:
                domain_objects = [
                    DomainList(
                        domain=d['domain'],
                        list_type=list_type,
                        reason=d['reason'],
                        created_by=d['created_by']
                    )
                    for d in domains_to_import
                ]
                
                self.db.add_all(domain_objects)
                self.db.commit()
                
                result["successful_imports"] += len(domain_objects)
                result["imported_domains"].extend([d['domain'] for d in domains_to_import])
            
            # Score imported domains if requested
            if score_domains and result["imported_domains"]:
                await self._score_imported_domains(result["imported_domains"])
            
            result["total_processed"] = len(domains_data)
            
            logger.info("JSON import completed", 
                       list_type=list_type,
                       successful=result["successful_imports"],
                       errors=result["validation_errors"])
            
        except json.JSONDecodeError as e:
            logger.error("JSON import failed - invalid JSON", error=str(e))
            result["errors"].append(f"Invalid JSON: {str(e)}")
        except Exception as e:
            logger.error("JSON import failed", error=str(e))
            result["errors"].append(f"Import failed: {str(e)}")
        
        return result
    
    async def export_domains_to_csv(
        self,
        list_type: Optional[str] = None,
        active_only: bool = True
    ) -> str:
        """Export domains to CSV format"""
        
        try:
            # Query domains
            query = self.db.query(DomainList)
            if list_type:
                query = query.filter(DomainList.list_type == list_type)
            if active_only:
                query = query.filter(DomainList.is_active == True)
            
            domains = query.order_by(DomainList.created_at.desc()).all()
            
            # Create CSV content
            output = StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['domain', 'list_type', 'reason', 'created_at', 'created_by', 'is_active'])
            
            # Write data
            for domain in domains:
                writer.writerow([
                    domain.domain,
                    domain.list_type,
                    domain.reason or '',
                    domain.created_at.isoformat() if domain.created_at else '',
                    domain.created_by or '',
                    domain.is_active
                ])
            
            csv_content = output.getvalue()
            output.close()
            
            logger.info("CSV export completed", 
                       domains_exported=len(domains),
                       list_type=list_type)
            
            return csv_content
            
        except Exception as e:
            logger.error("CSV export failed", error=str(e))
            raise
    
    async def export_domains_to_json(
        self,
        list_type: Optional[str] = None,
        active_only: bool = True,
        include_metadata: bool = True
    ) -> str:
        """Export domains to JSON format"""
        
        try:
            # Query domains
            query = self.db.query(DomainList)
            if list_type:
                query = query.filter(DomainList.list_type == list_type)
            if active_only:
                query = query.filter(DomainList.is_active == True)
            
            domains = query.order_by(DomainList.created_at.desc()).all()
            
            # Create JSON structure
            if include_metadata:
                result = {
                    "export_info": {
                        "exported_at": datetime.utcnow().isoformat(),
                        "total_domains": len(domains),
                        "list_type": list_type,
                        "active_only": active_only
                    },
                    "domains": []
                }
            else:
                result = []
            
            # Add domain data
            for domain in domains:
                domain_data = {
                    "domain": domain.domain,
                    "list_type": domain.list_type,
                    "reason": domain.reason,
                    "created_at": domain.created_at.isoformat() if domain.created_at else None,
                    "created_by": domain.created_by,
                    "is_active": domain.is_active
                }
                
                if include_metadata:
                    result["domains"].append(domain_data)
                else:
                    result.append(domain_data)
            
            json_content = json.dumps(result, indent=2)
            
            logger.info("JSON export completed", 
                       domains_exported=len(domains),
                       list_type=list_type)
            
            return json_content
            
        except Exception as e:
            logger.error("JSON export failed", error=str(e))
            raise
    
    async def bulk_update_domains(
        self,
        domain_updates: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Bulk update domain properties"""
        
        result = {
            "total_processed": len(domain_updates),
            "successful_updates": 0,
            "not_found": 0,
            "errors": []
        }
        
        try:
            for update in domain_updates:
                try:
                    domain_id = update.get('id')
                    domain_name = update.get('domain')
                    
                    if not domain_id and not domain_name:
                        result["errors"].append("Missing domain identifier")
                        continue
                    
                    # Find domain
                    query = self.db.query(DomainList)
                    if domain_id:
                        query = query.filter(DomainList.id == domain_id)
                    else:
                        query = query.filter(DomainList.domain == domain_name)
                    
                    domain = query.first()
                    
                    if not domain:
                        result["not_found"] += 1
                        result["errors"].append(f"Domain not found: {domain_name or domain_id}")
                        continue
                    
                    # Update properties
                    if 'reason' in update:
                        domain.reason = update['reason']
                    if 'is_active' in update:
                        domain.is_active = update['is_active']
                    if 'list_type' in update:
                        domain.list_type = update['list_type']
                    
                    self.db.commit()
                    result["successful_updates"] += 1
                    
                except Exception as e:
                    result["errors"].append(f"Update failed: {str(e)}")
            
            logger.info("Bulk update completed", 
                       successful=result["successful_updates"],
                       errors=len(result["errors"]))
            
        except Exception as e:
            logger.error("Bulk update failed", error=str(e))
            result["errors"].append(f"Bulk update failed: {str(e)}")
        
        return result
    
    async def bulk_delete_domains(
        self,
        domain_identifiers: List[str],
        soft_delete: bool = True
    ) -> Dict[str, Any]:
        """Bulk delete domains (soft or hard delete)"""
        
        result = {
            "total_processed": len(domain_identifiers),
            "successful_deletes": 0,
            "not_found": 0,
            "errors": []
        }
        
        try:
            for identifier in domain_identifiers:
                try:
                    # Try to find by ID first, then by domain name
                    query = self.db.query(DomainList)
                    if identifier.isdigit():
                        query = query.filter(DomainList.id == int(identifier))
                    else:
                        query = query.filter(DomainList.domain == identifier)
                    
                    domain = query.first()
                    
                    if not domain:
                        result["not_found"] += 1
                        result["errors"].append(f"Domain not found: {identifier}")
                        continue
                    
                    if soft_delete:
                        domain.is_active = False
                        self.db.commit()
                    else:
                        self.db.delete(domain)
                        self.db.commit()
                    
                    result["successful_deletes"] += 1
                    
                except Exception as e:
                    result["errors"].append(f"Delete failed for {identifier}: {str(e)}")
            
            logger.info("Bulk delete completed", 
                       successful=result["successful_deletes"],
                       soft_delete=soft_delete)
            
        except Exception as e:
            logger.error("Bulk delete failed", error=str(e))
            result["errors"].append(f"Bulk delete failed: {str(e)}")
        
        return result
    
    def _validate_domain_format(self, domain: str) -> bool:
        """Validate domain format"""
        try:
            # Basic domain validation regex
            domain_pattern = r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
            return bool(re.match(domain_pattern, domain))
        except:
            return False
    
    async def _score_imported_domains(self, domains: List[str]):
        """Score imported domains using reputation service"""
        try:
            async with DomainReputationService() as reputation_service:
                await reputation_service.bulk_score_domains(domains)
            logger.info("Scored imported domains", count=len(domains))
        except Exception as e:
            logger.error("Failed to score imported domains", error=str(e))
