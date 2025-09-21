"""
Logging Service
Structured logging and audit trail management
"""

import json
import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union
import structlog
from pathlib import Path
import aiofiles
from ..core.config import get_settings

logger = structlog.get_logger()

class AuditEvent:
    """Audit event data structure"""
    
    def __init__(
        self,
        event_type: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        severity: str = "info"
    ):
        self.event_id = f"audit_{datetime.now(timezone.utc).timestamp()}_{id(self)}"
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.event_type = event_type
        self.user_id = user_id
        self.session_id = session_id
        self.resource = resource
        self.action = action
        self.details = details or {}
        self.ip_address = ip_address
        self.user_agent = user_agent
        self.severity = severity
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "resource": self.resource,
            "action": self.action,
            "details": self.details,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "severity": self.severity
        }

class LoggingService:
    """Centralized logging and audit service"""
    
    def __init__(self):
        self.log_directory = Path(getattr(get_settings(), 'LOG_DIRECTORY', 'logs'))
        self.audit_directory = self.log_directory / "audit"
        self.application_directory = self.log_directory / "application"
        self.error_directory = self.log_directory / "error"
        
        # Create directories
        self.log_directory.mkdir(exist_ok=True)
        self.audit_directory.mkdir(exist_ok=True)
        self.application_directory.mkdir(exist_ok=True)
        self.error_directory.mkdir(exist_ok=True)
        
        # Configure structured logging
        self._configure_structlog()
    
    def _configure_structlog(self):
        """Configure structured logging"""
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    async def log_audit_event(self, event: AuditEvent) -> bool:
        """Log audit event to file"""
        try:
            # Get current date for file naming
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            audit_file = self.audit_directory / f"audit_{date_str}.jsonl"
            
            # Write to file
            async with aiofiles.open(audit_file, "a", encoding="utf-8") as f:
                await f.write(json.dumps(event.to_dict()) + "\n")
            
            # Also log to structured logger
            logger.info(
                "Audit event logged",
                event_type=event.event_type,
                user_id=event.user_id,
                resource=event.resource,
                action=event.action,
                severity=event.severity
            )
            
            return True
            
        except Exception as e:
            logger.error("Failed to log audit event", error=str(e))
            return False
    
    async def log_application_event(
        self,
        level: str,
        message: str,
        **kwargs
    ) -> bool:
        """Log application event"""
        try:
            # Get current date for file naming
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            app_file = self.application_directory / f"application_{date_str}.jsonl"
            
            # Create log entry
            log_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "level": level,
                "message": message,
                **kwargs
            }
            
            # Write to file
            async with aiofiles.open(app_file, "a", encoding="utf-8") as f:
                await f.write(json.dumps(log_entry) + "\n")
            
            # Log to structured logger
            getattr(logger, level)(message, **kwargs)
            
            return True
            
        except Exception as e:
            logger.error("Failed to log application event", error=str(e))
            return False
    
    async def log_error_event(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Log error event"""
        try:
            # Get current date for file naming
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            error_file = self.error_directory / f"errors_{date_str}.jsonl"
            
            # Create error entry
            error_entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error_type": type(error).__name__,
                "error_message": str(error),
                "context": context or {},
                "traceback": None  # Could add traceback if needed
            }
            
            # Write to file
            async with aiofiles.open(error_file, "a", encoding="utf-8") as f:
                await f.write(json.dumps(error_entry) + "\n")
            
            # Log to structured logger
            logger.error(
                "Error occurred",
                error_type=error_entry["error_type"],
                error_message=error_entry["error_message"],
                context=context
            )
            
            return True
            
        except Exception as e:
            logger.error("Failed to log error event", error=str(e))
            return False
    
    async def get_audit_logs(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """Retrieve audit logs with filtering"""
        try:
            logs = []
            
            # Get date range
            if not start_date:
                start_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            if not end_date:
                end_date = datetime.now(timezone.utc)
            
            # Iterate through date range
            current_date = start_date.date()
            end_date_only = end_date.date()
            
            while current_date <= end_date_only:
                date_str = current_date.strftime("%Y-%m-%d")
                audit_file = self.audit_directory / f"audit_{date_str}.jsonl"
                
                if audit_file.exists():
                    async with aiofiles.open(audit_file, "r", encoding="utf-8") as f:
                        async for line in f:
                            try:
                                log_entry = json.loads(line.strip())
                                
                                # Apply filters
                                if event_type and log_entry.get("event_type") != event_type:
                                    continue
                                if user_id and log_entry.get("user_id") != user_id:
                                    continue
                                
                                # Check timestamp range
                                log_timestamp = datetime.fromisoformat(log_entry["timestamp"])
                                if start_date <= log_timestamp <= end_date:
                                    logs.append(log_entry)
                                
                                # Limit results
                                if len(logs) >= limit:
                                    break
                                    
                            except (json.JSONDecodeError, KeyError, ValueError):
                                continue
                
                current_date = datetime.fromordinal(current_date.toordinal() + 1).date()
            
            return logs[:limit]
            
        except Exception as e:
            logger.error("Failed to retrieve audit logs", error=str(e))
            return []
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """Get system logging metrics"""
        try:
            metrics = {
                "log_files": {
                    "audit": len(list(self.audit_directory.glob("*.jsonl"))),
                    "application": len(list(self.application_directory.glob("*.jsonl"))),
                    "error": len(list(self.error_directory.glob("*.jsonl")))
                },
                "total_size": {
                    "audit": sum(f.stat().st_size for f in self.audit_directory.glob("*.jsonl")),
                    "application": sum(f.stat().st_size for f in self.application_directory.glob("*.jsonl")),
                    "error": sum(f.stat().st_size for f in self.error_directory.glob("*.jsonl"))
                },
                "recent_activity": await self._get_recent_activity()
            }
            
            return metrics
            
        except Exception as e:
            logger.error("Failed to get system metrics", error=str(e))
            return {}
    
    async def _get_recent_activity(self) -> Dict[str, int]:
        """Get recent logging activity"""
        try:
            today = datetime.now(timezone.utc).date()
            activity = {"audit": 0, "application": 0, "error": 0}
            
            # Count today's entries
            for log_type in activity.keys():
                log_file = getattr(self, f"{log_type}_directory") / f"{log_type}_{today.strftime('%Y-%m-%d')}.jsonl"
                if log_file.exists():
                    async with aiofiles.open(log_file, "r", encoding="utf-8") as f:
                        activity[log_type] = sum(1 async for _ in f)
            
            return activity
            
        except Exception as e:
            logger.error("Failed to get recent activity", error=str(e))
            return {}

# Audit event types
class AuditEventTypes:
    """Common audit event types"""
    
    # Authentication events
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILURE = "auth.login.failure"
    LOGOUT = "auth.logout"
    TOKEN_REFRESH = "auth.token.refresh"
    
    # Email events
    EMAIL_RECEIVED = "email.received"
    EMAIL_ANALYZED = "email.analyzed"
    EMAIL_QUARANTINED = "email.quarantined"
    EMAIL_RELEASED = "email.released"
    
    # Sandbox events
    SANDBOX_ANALYSIS_STARTED = "sandbox.analysis.started"
    SANDBOX_ANALYSIS_COMPLETED = "sandbox.analysis.completed"
    SANDBOX_ANALYSIS_FAILED = "sandbox.analysis.failed"
    
    # Incident events
    INCIDENT_CREATED = "incident.created"
    INCIDENT_ASSIGNED = "incident.assigned"
    INCIDENT_RESOLVED = "incident.resolved"
    
    # Configuration events
    CONFIG_UPDATED = "config.updated"
    POLICY_UPDATED = "policy.updated"
    DOMAIN_LIST_UPDATED = "domain.list.updated"
    
    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    BACKUP_CREATED = "system.backup.created"
    MAINTENANCE_MODE = "system.maintenance.mode"

# Global logging service instance
logging_service = LoggingService()
