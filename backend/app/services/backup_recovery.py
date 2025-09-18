"""
Backup and Disaster Recovery Service
Automated backup and disaster recovery capabilities
"""

import asyncio
import json
import os
import shutil
import gzip
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import structlog
import aiofiles
from pathlib import Path
from ..services.cache_manager import cache_manager
from ..services.logging_service import logging_service

logger = structlog.get_logger()

class BackupType(Enum):
    FULL = "full"
    INCREMENTAL = "incremental"
    DIFFERENTIAL = "differential"

class BackupStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BackupDestination(Enum):
    LOCAL = "local"
    S3 = "s3"
    AZURE_BLOB = "azure_blob"
    GOOGLE_CLOUD = "google_cloud"
    FTP = "ftp"
    SFTP = "sftp"

class BackupRecoveryService:
    """Automated backup and disaster recovery service"""
    
    def __init__(self):
        self.backup_jobs = {}
        self.restore_jobs = {}
        self.backup_schedules = {}
        self.backup_configs = {
            BackupDestination.LOCAL: {
                "name": "Local Storage",
                "supported_types": [BackupType.FULL, BackupType.INCREMENTAL, BackupType.DIFFERENTIAL],
                "compression": True,
                "encryption": True
            },
            BackupDestination.S3: {
                "name": "Amazon S3",
                "supported_types": [BackupType.FULL, BackupType.INCREMENTAL, BackupType.DIFFERENTIAL],
                "compression": True,
                "encryption": True
            },
            BackupDestination.AZURE_BLOB: {
                "name": "Azure Blob Storage",
                "supported_types": [BackupType.FULL, BackupType.INCREMENTAL, BackupType.DIFFERENTIAL],
                "compression": True,
                "encryption": True
            }
        }
        
        # Default backup settings
        self.default_settings = {
            "backup_directory": "backups",
            "retention_days": 30,
            "compression": True,
            "encryption": True,
            "verify_backup": True,
            "parallel_jobs": 3
        }
        
        # Initialize backup directories
        self._initialize_backup_directories()
    
    def _initialize_backup_directories(self):
        """Initialize backup directories"""
        try:
            backup_dir = Path(self.default_settings["backup_directory"])
            backup_dir.mkdir(exist_ok=True)
            
            # Create subdirectories
            (backup_dir / "database").mkdir(exist_ok=True)
            (backup_dir / "files").mkdir(exist_ok=True)
            (backup_dir / "configurations").mkdir(exist_ok=True)
            (backup_dir / "logs").mkdir(exist_ok=True)
            
            logger.info("Initialized backup directories")
            
        except Exception as e:
            logger.error("Error initializing backup directories", error=str(e))
    
    async def create_backup_job(
        self,
        backup_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new backup job"""
        try:
            logger.info("Creating backup job", name=backup_config.get("name"))
            
            # Validate backup configuration
            validation_result = await self._validate_backup_config(backup_config)
            if not validation_result.get("valid"):
                return {"success": False, "error": validation_result.get("error")}
            
            # Generate backup job ID
            job_id = self._generate_backup_job_id(backup_config.get("name"))
            
            # Create backup job
            backup_job = {
                "job_id": job_id,
                "name": backup_config["name"],
                "description": backup_config.get("description", ""),
                "backup_type": backup_config["backup_type"],
                "destination": backup_config["destination"],
                "destination_config": backup_config["destination_config"],
                "sources": backup_config["sources"],
                "schedule": backup_config.get("schedule"),
                "retention_days": backup_config.get("retention_days", 30),
                "compression": backup_config.get("compression", True),
                "encryption": backup_config.get("encryption", True),
                "verify_backup": backup_config.get("verify_backup", True),
                "status": BackupStatus.PENDING.value,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "last_run": None,
                "next_run": None,
                "success_count": 0,
                "failure_count": 0
            }
            
            # Store backup job
            self.backup_jobs[job_id] = backup_job
            
            # Schedule job if schedule is provided
            if backup_config.get("schedule"):
                await self._schedule_backup_job(job_id, backup_config["schedule"])
            
            # Cache backup job
            await cache_manager.set(
                f"backup_job_{job_id}",
                backup_job,
                ttl=86400 * 365,  # 1 year
                namespace="backup_jobs"
            )
            
            # Log backup job creation
            await logging_service.log_audit_event(
                logging_service.AuditEvent(
                    event_type='backup_job_created',
                    details={
                        'job_id': job_id,
                        'name': backup_config["name"],
                        'backup_type': backup_config["backup_type"],
                        'destination': backup_config["destination"]
                    },
                    severity='low'
                )
            )
            
            logger.info("Backup job created successfully", job_id=job_id)
            
            return {
                "success": True,
                "job_id": job_id,
                "created_at": backup_job["created_at"].isoformat()
            }
            
        except Exception as e:
            logger.error("Error creating backup job", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _validate_backup_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate backup configuration"""
        try:
            required_fields = ["name", "backup_type", "destination", "destination_config", "sources"]
            missing_fields = [field for field in required_fields if field not in config]
            
            if missing_fields:
                return {
                    "valid": False,
                    "error": f"Missing required fields: {', '.join(missing_fields)}"
                }
            
            # Validate backup type
            backup_type = config["backup_type"]
            if backup_type not in [t.value for t in BackupType]:
                return {
                    "valid": False,
                    "error": f"Invalid backup type: {backup_type}"
                }
            
            # Validate destination
            destination = config["destination"]
            if destination not in [d.value for d in BackupDestination]:
                return {
                    "valid": False,
                    "error": f"Invalid destination: {destination}"
                }
            
            # Validate sources
            sources = config["sources"]
            if not isinstance(sources, list) or not sources:
                return {
                    "valid": False,
                    "error": "Sources must be a non-empty list"
                }
            
            # Validate destination configuration
            destination_config = config["destination_config"]
            if destination == BackupDestination.S3.value:
                required_s3_fields = ["bucket", "access_key", "secret_key"]
                missing_s3_fields = [field for field in required_s3_fields if field not in destination_config]
                if missing_s3_fields:
                    return {
                        "valid": False,
                        "error": f"Missing S3 configuration fields: {', '.join(missing_s3_fields)}"
                    }
            
            return {"valid": True}
            
        except Exception as e:
            logger.error("Error validating backup config", error=str(e))
            return {"valid": False, "error": str(e)}
    
    async def execute_backup_job(
        self,
        job_id: str,
        manual: bool = False
    ) -> Dict[str, Any]:
        """Execute a backup job"""
        try:
            if job_id not in self.backup_jobs:
                return {"success": False, "error": "Backup job not found"}
            
            backup_job = self.backup_jobs[job_id]
            
            # Update job status
            backup_job["status"] = BackupStatus.IN_PROGRESS.value
            backup_job["updated_at"] = datetime.now()
            
            logger.info("Starting backup job", job_id=job_id, backup_type=backup_job["backup_type"])
            
            # Create backup session
            backup_session = {
                "session_id": f"{job_id}_{int(datetime.now().timestamp())}",
                "job_id": job_id,
                "started_at": datetime.now(),
                "backup_type": backup_job["backup_type"],
                "destination": backup_job["destination"],
                "sources": backup_job["sources"],
                "status": BackupStatus.IN_PROGRESS.value,
                "files_backed_up": 0,
                "bytes_backed_up": 0,
                "errors": []
            }
            
            # Execute backup based on type
            if backup_job["backup_type"] == BackupType.FULL.value:
                result = await self._execute_full_backup(backup_job, backup_session)
            elif backup_job["backup_type"] == BackupType.INCREMENTAL.value:
                result = await self._execute_incremental_backup(backup_job, backup_session)
            elif backup_job["backup_type"] == BackupType.DIFFERENTIAL.value:
                result = await self._execute_differential_backup(backup_job, backup_session)
            else:
                result = {"success": False, "error": "Unsupported backup type"}
            
            # Update job status
            if result.get("success"):
                backup_job["status"] = BackupStatus.COMPLETED.value
                backup_job["success_count"] += 1
                backup_job["last_run"] = datetime.now()
            else:
                backup_job["status"] = BackupStatus.FAILED.value
                backup_job["failure_count"] += 1
            
            backup_job["updated_at"] = datetime.now()
            
            # Update cache
            await cache_manager.set(
                f"backup_job_{job_id}",
                backup_job,
                ttl=86400 * 365,
                namespace="backup_jobs"
            )
            
            # Log backup completion
            await logging_service.log_audit_event(
                logging_service.AuditEvent(
                    event_type='backup_job_completed',
                    details={
                        'job_id': job_id,
                        'success': result.get("success"),
                        'files_backed_up': backup_session.get("files_backed_up", 0),
                        'bytes_backed_up': backup_session.get("bytes_backed_up", 0),
                        'errors': backup_session.get("errors", [])
                    },
                    severity='medium' if result.get("success") else 'high'
                )
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error executing backup job {job_id}", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _execute_full_backup(
        self,
        backup_job: Dict[str, Any],
        backup_session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute full backup"""
        try:
            logger.info("Executing full backup", job_id=backup_job["job_id"])
            
            total_files = 0
            total_bytes = 0
            errors = []
            
            # Backup each source
            for source in backup_job["sources"]:
                try:
                    source_result = await self._backup_source(source, backup_job, backup_session)
                    if source_result.get("success"):
                        total_files += source_result.get("files_count", 0)
                        total_bytes += source_result.get("bytes_count", 0)
                    else:
                        errors.append({
                            "source": source,
                            "error": source_result.get("error")
                        })
                except Exception as e:
                    logger.error(f"Error backing up source {source}", error=str(e))
                    errors.append({
                        "source": source,
                        "error": str(e)
                    })
            
            # Update session
            backup_session.update({
                "files_backed_up": total_files,
                "bytes_backed_up": total_bytes,
                "errors": errors,
                "status": BackupStatus.COMPLETED.value if not errors else BackupStatus.FAILED.value,
                "completed_at": datetime.now()
            })
            
            success = len(errors) == 0
            
            return {
                "success": success,
                "files_backed_up": total_files,
                "bytes_backed_up": total_bytes,
                "errors": errors,
                "session_id": backup_session["session_id"]
            }
            
        except Exception as e:
            logger.error("Error executing full backup", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _execute_incremental_backup(
        self,
        backup_job: Dict[str, Any],
        backup_session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute incremental backup"""
        try:
            logger.info("Executing incremental backup", job_id=backup_job["job_id"])
            
            # Get last backup timestamp
            last_backup = await self._get_last_backup_timestamp(backup_job["job_id"])
            
            total_files = 0
            total_bytes = 0
            errors = []
            
            # Backup only changed files since last backup
            for source in backup_job["sources"]:
                try:
                    source_result = await self._backup_source_incremental(
                        source, backup_job, backup_session, last_backup
                    )
                    if source_result.get("success"):
                        total_files += source_result.get("files_count", 0)
                        total_bytes += source_result.get("bytes_count", 0)
                    else:
                        errors.append({
                            "source": source,
                            "error": source_result.get("error")
                        })
                except Exception as e:
                    logger.error(f"Error backing up source {source}", error=str(e))
                    errors.append({
                        "source": source,
                        "error": str(e)
                    })
            
            # Update session
            backup_session.update({
                "files_backed_up": total_files,
                "bytes_backed_up": total_bytes,
                "errors": errors,
                "status": BackupStatus.COMPLETED.value if not errors else BackupStatus.FAILED.value,
                "completed_at": datetime.now()
            })
            
            success = len(errors) == 0
            
            return {
                "success": success,
                "files_backed_up": total_files,
                "bytes_backed_up": total_bytes,
                "errors": errors,
                "session_id": backup_session["session_id"]
            }
            
        except Exception as e:
            logger.error("Error executing incremental backup", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _execute_differential_backup(
        self,
        backup_job: Dict[str, Any],
        backup_session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute differential backup"""
        try:
            logger.info("Executing differential backup", job_id=backup_job["job_id"])
            
            # Get last full backup timestamp
            last_full_backup = await self._get_last_full_backup_timestamp(backup_job["job_id"])
            
            total_files = 0
            total_bytes = 0
            errors = []
            
            # Backup files changed since last full backup
            for source in backup_job["sources"]:
                try:
                    source_result = await self._backup_source_incremental(
                        source, backup_job, backup_session, last_full_backup
                    )
                    if source_result.get("success"):
                        total_files += source_result.get("files_count", 0)
                        total_bytes += source_result.get("bytes_count", 0)
                    else:
                        errors.append({
                            "source": source,
                            "error": source_result.get("error")
                        })
                except Exception as e:
                    logger.error(f"Error backing up source {source}", error=str(e))
                    errors.append({
                        "source": source,
                        "error": str(e)
                    })
            
            # Update session
            backup_session.update({
                "files_backed_up": total_files,
                "bytes_backed_up": total_bytes,
                "errors": errors,
                "status": BackupStatus.COMPLETED.value if not errors else BackupStatus.FAILED.value,
                "completed_at": datetime.now()
            })
            
            success = len(errors) == 0
            
            return {
                "success": success,
                "files_backed_up": total_files,
                "bytes_backed_up": total_bytes,
                "errors": errors,
                "session_id": backup_session["session_id"]
            }
            
        except Exception as e:
            logger.error("Error executing differential backup", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _backup_source(
        self,
        source: str,
        backup_job: Dict[str, Any],
        backup_session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Backup a single source"""
        try:
            # Mock backup implementation
            # In real implementation, would copy files based on source type
            
            if source == "database":
                return await self._backup_database(backup_job, backup_session)
            elif source == "files":
                return await self._backup_files(backup_job, backup_session)
            elif source == "configurations":
                return await self._backup_configurations(backup_job, backup_session)
            elif source == "logs":
                return await self._backup_logs(backup_job, backup_session)
            else:
                return {"success": False, "error": f"Unknown source type: {source}"}
                
        except Exception as e:
            logger.error(f"Error backing up source {source}", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _backup_database(
        self,
        backup_job: Dict[str, Any],
        backup_session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Backup database"""
        try:
            # Mock database backup
            # In real implementation, would use database-specific tools
            
            backup_filename = f"database_backup_{backup_session['session_id']}.sql"
            backup_path = Path(self.default_settings["backup_directory"]) / "database" / backup_filename
            
            # Create mock backup file
            async with aiofiles.open(backup_path, 'w') as f:
                await f.write("-- Database backup content\n")
            
            # Compress if enabled
            if backup_job.get("compression", True):
                compressed_path = f"{backup_path}.gz"
                with open(backup_path, 'rb') as f_in:
                    with gzip.open(compressed_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(backup_path)
                backup_path = Path(compressed_path)
            
            return {
                "success": True,
                "files_count": 1,
                "bytes_count": backup_path.stat().st_size,
                "backup_path": str(backup_path)
            }
            
        except Exception as e:
            logger.error("Error backing up database", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _backup_files(
        self,
        backup_job: Dict[str, Any],
        backup_session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Backup files"""
        try:
            # Mock file backup
            # In real implementation, would copy actual files
            
            files_backed_up = 0
            bytes_backed_up = 0
            
            # Create mock backup
            backup_filename = f"files_backup_{backup_session['session_id']}.tar.gz"
            backup_path = Path(self.default_settings["backup_directory"]) / "files" / backup_filename
            
            # Create mock backup file
            async with aiofiles.open(backup_path, 'w') as f:
                await f.write("Mock files backup content\n")
            
            files_backed_up = 1
            bytes_backed_up = backup_path.stat().st_size
            
            return {
                "success": True,
                "files_count": files_backed_up,
                "bytes_count": bytes_backed_up,
                "backup_path": str(backup_path)
            }
            
        except Exception as e:
            logger.error("Error backing up files", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _backup_configurations(
        self,
        backup_job: Dict[str, Any],
        backup_session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Backup configurations"""
        try:
            # Mock configuration backup
            backup_filename = f"config_backup_{backup_session['session_id']}.json"
            backup_path = Path(self.default_settings["backup_directory"]) / "configurations" / backup_filename
            
            # Create mock configuration backup
            config_data = {
                "backup_session": backup_session["session_id"],
                "timestamp": datetime.now().isoformat(),
                "settings": self.default_settings
            }
            
            async with aiofiles.open(backup_path, 'w') as f:
                await f.write(json.dumps(config_data, indent=2))
            
            return {
                "success": True,
                "files_count": 1,
                "bytes_count": backup_path.stat().st_size,
                "backup_path": str(backup_path)
            }
            
        except Exception as e:
            logger.error("Error backing up configurations", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _backup_logs(
        self,
        backup_job: Dict[str, Any],
        backup_session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Backup logs"""
        try:
            # Mock log backup
            backup_filename = f"logs_backup_{backup_session['session_id']}.log"
            backup_path = Path(self.default_settings["backup_directory"]) / "logs" / backup_filename
            
            # Create mock log backup
            async with aiofiles.open(backup_path, 'w') as f:
                await f.write(f"Log backup for session {backup_session['session_id']}\n")
                await f.write(f"Generated at {datetime.now().isoformat()}\n")
            
            return {
                "success": True,
                "files_count": 1,
                "bytes_count": backup_path.stat().st_size,
                "backup_path": str(backup_path)
            }
            
        except Exception as e:
            logger.error("Error backing up logs", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _backup_source_incremental(
        self,
        source: str,
        backup_job: Dict[str, Any],
        backup_session: Dict[str, Any],
        since_timestamp: Optional[datetime]
    ) -> Dict[str, Any]:
        """Backup source incrementally"""
        try:
            # Mock incremental backup
            # In real implementation, would check file modification times
            
            return await self._backup_source(source, backup_job, backup_session)
            
        except Exception as e:
            logger.error(f"Error backing up source incrementally {source}", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _get_last_backup_timestamp(self, job_id: str) -> Optional[datetime]:
        """Get last backup timestamp for incremental backup"""
        try:
            # Mock implementation
            # In real implementation, would check backup metadata
            return datetime.now() - timedelta(hours=24)
            
        except Exception as e:
            logger.error(f"Error getting last backup timestamp for {job_id}", error=str(e))
            return None
    
    async def _get_last_full_backup_timestamp(self, job_id: str) -> Optional[datetime]:
        """Get last full backup timestamp for differential backup"""
        try:
            # Mock implementation
            # In real implementation, would check backup metadata
            return datetime.now() - timedelta(days=7)
            
        except Exception as e:
            logger.error(f"Error getting last full backup timestamp for {job_id}", error=str(e))
            return None
    
    async def _schedule_backup_job(self, job_id: str, schedule: str):
        """Schedule backup job"""
        try:
            # Mock scheduling implementation
            # In real implementation, would use a proper scheduler
            
            self.backup_schedules[job_id] = {
                "job_id": job_id,
                "schedule": schedule,
                "next_run": datetime.now() + timedelta(hours=1),
                "enabled": True
            }
            
            logger.info(f"Scheduled backup job {job_id}", schedule=schedule)
            
        except Exception as e:
            logger.error(f"Error scheduling backup job {job_id}", error=str(e))
    
    async def get_backup_jobs(self) -> List[Dict[str, Any]]:
        """Get all backup jobs"""
        try:
            jobs = []
            for job_id, job in self.backup_jobs.items():
                job_info = {
                    "job_id": job_id,
                    "name": job["name"],
                    "description": job["description"],
                    "backup_type": job["backup_type"],
                    "destination": job["destination"],
                    "status": job["status"],
                    "created_at": job["created_at"].isoformat(),
                    "last_run": job["last_run"].isoformat() if job["last_run"] else None,
                    "next_run": job["next_run"].isoformat() if job["next_run"] else None,
                    "success_count": job["success_count"],
                    "failure_count": job["failure_count"]
                }
                jobs.append(job_info)
            
            return jobs
            
        except Exception as e:
            logger.error("Error getting backup jobs", error=str(e))
            return []
    
    async def restore_from_backup(
        self,
        backup_session_id: str,
        restore_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Restore from backup"""
        try:
            logger.info("Starting restore operation", backup_session_id=backup_session_id)
            
            # Create restore job
            restore_job_id = f"restore_{int(datetime.now().timestamp())}"
            restore_job = {
                "restore_job_id": restore_job_id,
                "backup_session_id": backup_session_id,
                "restore_config": restore_config,
                "status": BackupStatus.IN_PROGRESS.value,
                "started_at": datetime.now(),
                "files_restored": 0,
                "bytes_restored": 0,
                "errors": []
            }
            
            self.restore_jobs[restore_job_id] = restore_job
            
            # Mock restore implementation
            # In real implementation, would restore actual files
            
            restore_job.update({
                "files_restored": 10,
                "bytes_restored": 1024000,
                "status": BackupStatus.COMPLETED.value,
                "completed_at": datetime.now()
            })
            
            # Log restore completion
            await logging_service.log_audit_event(
                logging_service.AuditEvent(
                    event_type='backup_restore_completed',
                    details={
                        'restore_job_id': restore_job_id,
                        'backup_session_id': backup_session_id,
                        'files_restored': restore_job["files_restored"],
                        'bytes_restored': restore_job["bytes_restored"]
                    },
                    severity='high'
                )
            )
            
            return {
                "success": True,
                "restore_job_id": restore_job_id,
                "files_restored": restore_job["files_restored"],
                "bytes_restored": restore_job["bytes_restored"]
            }
            
        except Exception as e:
            logger.error("Error restoring from backup", error=str(e))
            return {"success": False, "error": str(e)}
    
    def _generate_backup_job_id(self, name: str) -> str:
        """Generate unique backup job ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"backup_{name.lower().replace(' ', '_')}_{timestamp}"

# Global backup and recovery service instance
backup_recovery_service = BackupRecoveryService()
