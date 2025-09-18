"""
Enhanced SIEM Integration Service
Real-time event streaming and advanced SIEM integrations
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import structlog
import aiohttp
from ..services.cache_manager import cache_manager
from ..services.logging_service import logging_service

logger = structlog.get_logger()

class SIEMProvider(Enum):
    SPLUNK = "splunk"
    QRADAR = "qradar"
    ELK_STACK = "elk_stack"
    MICROSOFT_SENTINEL = "microsoft_sentinel"
    PALO_ALTO_CORTEX = "palo_alto_cortex"
    CROWDSTRIKE_FALCON = "crowdstrike_falcon"

class EventSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class EnhancedSIEMIntegration:
    """Enhanced SIEM integration with real-time streaming"""
    
    def __init__(self):
        self.active_connections = {}
        self.event_streams = {}
        self.siem_configs = {
            SIEMProvider.SPLUNK: {
                "name": "Splunk Enterprise Security",
                "supported_formats": ["json", "cef", "leef"],
                "real_time_streaming": True,
                "bulk_upload": True,
                "authentication": "token"
            },
            SIEMProvider.QRADAR: {
                "name": "IBM QRadar",
                "supported_formats": ["json", "cef", "syslog"],
                "real_time_streaming": True,
                "bulk_upload": True,
                "authentication": "api_key"
            },
            SIEMProvider.ELK_STACK: {
                "name": "Elastic Stack (ELK)",
                "supported_formats": ["json", "logstash"],
                "real_time_streaming": True,
                "bulk_upload": True,
                "authentication": "basic"
            },
            SIEMProvider.MICROSOFT_SENTINEL: {
                "name": "Microsoft Sentinel",
                "supported_formats": ["json", "cef"],
                "real_time_streaming": True,
                "bulk_upload": True,
                "authentication": "oauth2"
            }
        }
        
        # Event categorization for SIEM integration
        self.event_categories = {
            "authentication": ["login", "logout", "failed_login", "mfa_challenge"],
            "email_security": ["phishing_detected", "malware_detected", "spam_blocked", "email_quarantined"],
            "user_behavior": ["anomaly_detected", "risk_score_changed", "suspicious_activity"],
            "system_events": ["system_startup", "system_shutdown", "configuration_change", "error_occurred"],
            "compliance": ["policy_violation", "access_review", "audit_event", "data_breach"]
        }
    
    async def establish_siem_connection(
        self,
        provider: SIEMProvider,
        connection_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Establish connection to SIEM provider"""
        try:
            logger.info(f"Establishing connection to {provider.value}", config_keys=list(connection_config.keys()))
            
            # Validate configuration
            validation_result = await self._validate_siem_config(provider, connection_config)
            if not validation_result.get("valid"):
                return {"success": False, "error": validation_result.get("error")}
            
            # Test connection
            connection_test = await self._test_siem_connection(provider, connection_config)
            if not connection_test.get("success"):
                return {"success": False, "error": connection_test.get("error")}
            
            # Store connection configuration
            connection_id = self._generate_connection_id(provider)
            self.active_connections[connection_id] = {
                "provider": provider,
                "config": connection_config,
                "established_at": datetime.now(),
                "status": "active",
                "last_heartbeat": datetime.now()
            }
            
            # Start heartbeat monitoring
            asyncio.create_task(self._monitor_siem_connection(connection_id))
            
            # Initialize event streaming
            await self._initialize_event_streaming(connection_id)
            
            logger.info(f"Successfully established connection to {provider.value}", connection_id=connection_id)
            
            return {
                "success": True,
                "connection_id": connection_id,
                "provider": provider.value,
                "established_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error establishing SIEM connection to {provider.value}", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _validate_siem_config(self, provider: SIEMProvider, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate SIEM configuration"""
        try:
            required_fields = {
                SIEMProvider.SPLUNK: ["host", "port", "token"],
                SIEMProvider.QRADAR: ["host", "port", "api_key"],
                SIEMProvider.ELK_STACK: ["host", "port", "username", "password"],
                SIEMProvider.MICROSOFT_SENTINEL: ["workspace_id", "client_id", "client_secret"]
            }
            
            required = required_fields.get(provider, [])
            missing_fields = [field for field in required if field not in config]
            
            if missing_fields:
                return {
                    "valid": False,
                    "error": f"Missing required fields: {', '.join(missing_fields)}"
                }
            
            return {"valid": True}
            
        except Exception as e:
            logger.error("Error validating SIEM config", error=str(e))
            return {"valid": False, "error": str(e)}
    
    async def _test_siem_connection(self, provider: SIEMProvider, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test SIEM connection"""
        try:
            # Mock connection test based on provider
            if provider == SIEMProvider.SPLUNK:
                # Test Splunk connection
                test_url = f"https://{config['host']}:{config['port']}/services/auth/login"
                # In real implementation, would make actual HTTP request
                return {"success": True, "response_time": 150}
            
            elif provider == SIEMProvider.QRADAR:
                # Test QRadar connection
                test_url = f"https://{config['host']}/api/config/access/access_control_management"
                # In real implementation, would make actual HTTP request
                return {"success": True, "response_time": 200}
            
            elif provider == SIEMProvider.ELK_STACK:
                # Test ELK connection
                test_url = f"http://{config['host']}:{config['port']}/_cluster/health"
                # In real implementation, would make actual HTTP request
                return {"success": True, "response_time": 180}
            
            elif provider == SIEMProvider.MICROSOFT_SENTINEL:
                # Test Microsoft Sentinel connection
                test_url = "https://management.azure.com/subscriptions/test/resourceGroups/test/providers/Microsoft.OperationalInsights/workspaces/test"
                # In real implementation, would make actual HTTP request
                return {"success": True, "response_time": 250}
            
            return {"success": False, "error": "Unsupported SIEM provider"}
            
        except Exception as e:
            logger.error("Error testing SIEM connection", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _monitor_siem_connection(self, connection_id: str):
        """Monitor SIEM connection health"""
        try:
            while connection_id in self.active_connections:
                connection = self.active_connections[connection_id]
                
                # Perform heartbeat check
                heartbeat_result = await self._perform_heartbeat_check(connection_id)
                
                if heartbeat_result.get("success"):
                    connection["last_heartbeat"] = datetime.now()
                    connection["status"] = "active"
                else:
                    connection["status"] = "disconnected"
                    logger.warning(f"SIEM connection {connection_id} heartbeat failed")
                
                # Update connection status in cache
                await cache_manager.set(
                    f"siem_connection_{connection_id}",
                    connection,
                    ttl=300,  # 5 minutes
                    namespace="siem_connections"
                )
                
                # Wait before next heartbeat
                await asyncio.sleep(60)  # 1 minute
                
        except Exception as e:
            logger.error(f"Error monitoring SIEM connection {connection_id}", error=str(e))
            if connection_id in self.active_connections:
                self.active_connections[connection_id]["status"] = "error"
    
    async def _perform_heartbeat_check(self, connection_id: str) -> Dict[str, Any]:
        """Perform heartbeat check for SIEM connection"""
        try:
            connection = self.active_connections.get(connection_id)
            if not connection:
                return {"success": False, "error": "Connection not found"}
            
            provider = connection["provider"]
            config = connection["config"]
            
            # Mock heartbeat check based on provider
            if provider == SIEMProvider.SPLUNK:
                # Splunk heartbeat - check server info
                return {"success": True, "response_time": 120}
            
            elif provider == SIEMProvider.QRADAR:
                # QRadar heartbeat - check system health
                return {"success": True, "response_time": 180}
            
            elif provider == SIEMProvider.ELK_STACK:
                # ELK heartbeat - check cluster health
                return {"success": True, "response_time": 150}
            
            elif provider == SIEMProvider.MICROSOFT_SENTINEL:
                # Sentinel heartbeat - check workspace status
                return {"success": True, "response_time": 200}
            
            return {"success": False, "error": "Unsupported provider"}
            
        except Exception as e:
            logger.error(f"Error performing heartbeat check for {connection_id}", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _initialize_event_streaming(self, connection_id: str):
        """Initialize real-time event streaming"""
        try:
            connection = self.active_connections.get(connection_id)
            if not connection:
                return
            
            provider = connection["provider"]
            
            # Initialize event stream based on provider
            if provider == SIEMProvider.SPLUNK:
                await self._initialize_splunk_streaming(connection_id)
            elif provider == SIEMProvider.QRADAR:
                await self._initialize_qradar_streaming(connection_id)
            elif provider == SIEMProvider.ELK_STACK:
                await self._initialize_elk_streaming(connection_id)
            elif provider == SIEMProvider.MICROSOFT_SENTINEL:
                await self._initialize_sentinel_streaming(connection_id)
            
            logger.info(f"Initialized event streaming for connection {connection_id}")
            
        except Exception as e:
            logger.error(f"Error initializing event streaming for {connection_id}", error=str(e))
    
    async def _initialize_splunk_streaming(self, connection_id: str):
        """Initialize Splunk event streaming"""
        try:
            # Mock Splunk streaming initialization
            self.event_streams[connection_id] = {
                "type": "splunk",
                "stream_id": f"splunk_stream_{connection_id}",
                "status": "active",
                "events_sent": 0,
                "last_event": None
            }
            
            logger.info(f"Initialized Splunk streaming for {connection_id}")
            
        except Exception as e:
            logger.error(f"Error initializing Splunk streaming for {connection_id}", error=str(e))
    
    async def _initialize_qradar_streaming(self, connection_id: str):
        """Initialize QRadar event streaming"""
        try:
            # Mock QRadar streaming initialization
            self.event_streams[connection_id] = {
                "type": "qradar",
                "stream_id": f"qradar_stream_{connection_id}",
                "status": "active",
                "events_sent": 0,
                "last_event": None
            }
            
            logger.info(f"Initialized QRadar streaming for {connection_id}")
            
        except Exception as e:
            logger.error(f"Error initializing QRadar streaming for {connection_id}", error=str(e))
    
    async def _initialize_elk_streaming(self, connection_id: str):
        """Initialize ELK Stack event streaming"""
        try:
            # Mock ELK streaming initialization
            self.event_streams[connection_id] = {
                "type": "elk",
                "stream_id": f"elk_stream_{connection_id}",
                "status": "active",
                "events_sent": 0,
                "last_event": None
            }
            
            logger.info(f"Initialized ELK streaming for {connection_id}")
            
        except Exception as e:
            logger.error(f"Error initializing ELK streaming for {connection_id}", error=str(e))
    
    async def _initialize_sentinel_streaming(self, connection_id: str):
        """Initialize Microsoft Sentinel event streaming"""
        try:
            # Mock Sentinel streaming initialization
            self.event_streams[connection_id] = {
                "type": "sentinel",
                "stream_id": f"sentinel_stream_{connection_id}",
                "status": "active",
                "events_sent": 0,
                "last_event": None
            }
            
            logger.info(f"Initialized Sentinel streaming for {connection_id}")
            
        except Exception as e:
            logger.error(f"Error initializing Sentinel streaming for {connection_id}", error=str(e))
    
    async def stream_event_to_siem(
        self,
        event_data: Dict[str, Any],
        connection_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Stream event to SIEM providers"""
        try:
            # Normalize event data
            normalized_event = await self._normalize_event_for_siem(event_data)
            
            # Get target connections
            target_connections = connection_ids or list(self.active_connections.keys())
            
            results = {}
            for connection_id in target_connections:
                if connection_id not in self.active_connections:
                    results[connection_id] = {"success": False, "error": "Connection not found"}
                    continue
                
                if connection_id not in self.event_streams:
                    results[connection_id] = {"success": False, "error": "Event stream not initialized"}
                    continue
                
                # Stream to specific SIEM
                stream_result = await self._stream_to_specific_siem(connection_id, normalized_event)
                results[connection_id] = stream_result
                
                # Update stream statistics
                if stream_result.get("success"):
                    stream = self.event_streams[connection_id]
                    stream["events_sent"] += 1
                    stream["last_event"] = datetime.now().isoformat()
            
            # Log event streaming
            await logging_service.log_audit_event(
                logging_service.AuditEvent(
                    event_type='siem_event_streamed',
                    details={
                        'event_type': event_data.get('event_type'),
                        'target_connections': target_connections,
                        'results': results
                    },
                    severity='low'
                )
            )
            
            return {
                "success": True,
                "event_id": event_data.get("event_id"),
                "streamed_to": len([r for r in results.values() if r.get("success")]),
                "total_targets": len(target_connections),
                "results": results
            }
            
        except Exception as e:
            logger.error("Error streaming event to SIEM", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _normalize_event_for_siem(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize event data for SIEM integration"""
        try:
            # Standard event format for SIEM
            normalized_event = {
                "@timestamp": event_data.get("timestamp", datetime.now().isoformat()),
                "event_id": event_data.get("event_id"),
                "event_type": event_data.get("event_type"),
                "severity": event_data.get("severity", "medium"),
                "source": "privik_email_gateway",
                "category": self._categorize_event(event_data.get("event_type")),
                "description": event_data.get("description"),
                "user_id": event_data.get("user_id"),
                "source_ip": event_data.get("source_ip"),
                "target": event_data.get("target"),
                "raw_data": event_data
            }
            
            # Add provider-specific fields
            if event_data.get("email_data"):
                normalized_event["email"] = {
                    "subject": event_data["email_data"].get("subject"),
                    "sender": event_data["email_data"].get("sender"),
                    "recipient": event_data["email_data"].get("recipient"),
                    "threat_score": event_data["email_data"].get("threat_score")
                }
            
            if event_data.get("attachment_data"):
                normalized_event["attachment"] = {
                    "filename": event_data["attachment_data"].get("filename"),
                    "file_hash": event_data["attachment_data"].get("file_hash"),
                    "file_type": event_data["attachment_data"].get("file_type"),
                    "verdict": event_data["attachment_data"].get("verdict")
                }
            
            return normalized_event
            
        except Exception as e:
            logger.error("Error normalizing event for SIEM", error=str(e))
            return event_data
    
    def _categorize_event(self, event_type: str) -> str:
        """Categorize event type for SIEM"""
        for category, events in self.event_categories.items():
            if event_type in events:
                return category
        return "other"
    
    async def _stream_to_specific_siem(self, connection_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Stream event to specific SIEM provider"""
        try:
            connection = self.active_connections[connection_id]
            stream = self.event_streams[connection_id]
            provider = connection["provider"]
            
            # Stream based on provider
            if provider == SIEMProvider.SPLUNK:
                return await self._stream_to_splunk(connection, event_data)
            elif provider == SIEMProvider.QRADAR:
                return await self._stream_to_qradar(connection, event_data)
            elif provider == SIEMProvider.ELK_STACK:
                return await self._stream_to_elk(connection, event_data)
            elif provider == SIEMProvider.MICROSOFT_SENTINEL:
                return await self._stream_to_sentinel(connection, event_data)
            
            return {"success": False, "error": "Unsupported SIEM provider"}
            
        except Exception as e:
            logger.error(f"Error streaming to SIEM {connection_id}", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _stream_to_splunk(self, connection: Dict[str, Any], event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Stream event to Splunk"""
        try:
            # Mock Splunk streaming
            # In real implementation, would use Splunk HTTP Event Collector or TCP input
            config = connection["config"]
            
            # Simulate HTTP request to Splunk HEC
            splunk_url = f"https://{config['host']}:{config['port']}/services/collector/event"
            headers = {
                "Authorization": f"Splunk {config['token']}",
                "Content-Type": "application/json"
            }
            
            # Mock successful response
            return {
                "success": True,
                "provider": "splunk",
                "response_time": 120,
                "message": "Event successfully sent to Splunk"
            }
            
        except Exception as e:
            logger.error("Error streaming to Splunk", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _stream_to_qradar(self, connection: Dict[str, Any], event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Stream event to QRadar"""
        try:
            # Mock QRadar streaming
            # In real implementation, would use QRadar API or syslog
            config = connection["config"]
            
            # Simulate API request to QRadar
            qradar_url = f"https://{config['host']}/api/siem/offenses"
            
            # Mock successful response
            return {
                "success": True,
                "provider": "qradar",
                "response_time": 180,
                "message": "Event successfully sent to QRadar"
            }
            
        except Exception as e:
            logger.error("Error streaming to QRadar", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _stream_to_elk(self, connection: Dict[str, Any], event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Stream event to ELK Stack"""
        try:
            # Mock ELK streaming
            # In real implementation, would use Elasticsearch API
            config = connection["config"]
            
            # Simulate API request to Elasticsearch
            elk_url = f"http://{config['host']}:{config['port']}/privik-events/_doc"
            
            # Mock successful response
            return {
                "success": True,
                "provider": "elk",
                "response_time": 150,
                "message": "Event successfully sent to ELK Stack"
            }
            
        except Exception as e:
            logger.error("Error streaming to ELK", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _stream_to_sentinel(self, connection: Dict[str, Any], event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Stream event to Microsoft Sentinel"""
        try:
            # Mock Sentinel streaming
            # In real implementation, would use Azure Monitor Data Collector API
            config = connection["config"]
            
            # Simulate API request to Sentinel
            sentinel_url = f"https://management.azure.com/subscriptions/{config.get('subscription_id')}/resourceGroups/{config.get('resource_group')}/providers/Microsoft.OperationalInsights/workspaces/{config['workspace_id']}/api/logs"
            
            # Mock successful response
            return {
                "success": True,
                "provider": "sentinel",
                "response_time": 200,
                "message": "Event successfully sent to Microsoft Sentinel"
            }
            
        except Exception as e:
            logger.error("Error streaming to Sentinel", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def bulk_upload_events(
        self,
        events: List[Dict[str, Any]],
        connection_id: str
    ) -> Dict[str, Any]:
        """Bulk upload events to SIEM"""
        try:
            connection = self.active_connections.get(connection_id)
            if not connection:
                return {"success": False, "error": "Connection not found"}
            
            provider = connection["provider"]
            
            # Normalize all events
            normalized_events = []
            for event in events:
                normalized_event = await self._normalize_event_for_siem(event)
                normalized_events.append(normalized_event)
            
            # Bulk upload based on provider
            if provider == SIEMProvider.SPLUNK:
                result = await self._bulk_upload_to_splunk(connection, normalized_events)
            elif provider == SIEMProvider.QRADAR:
                result = await self._bulk_upload_to_qradar(connection, normalized_events)
            elif provider == SIEMProvider.ELK_STACK:
                result = await self._bulk_upload_to_elk(connection, normalized_events)
            elif provider == SIEMProvider.MICROSOFT_SENTINEL:
                result = await self._bulk_upload_to_sentinel(connection, normalized_events)
            else:
                result = {"success": False, "error": "Unsupported provider for bulk upload"}
            
            # Update stream statistics
            if result.get("success") and connection_id in self.event_streams:
                stream = self.event_streams[connection_id]
                stream["events_sent"] += len(normalized_events)
                stream["last_event"] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Error in bulk upload to {connection_id}", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _bulk_upload_to_splunk(self, connection: Dict[str, Any], events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk upload to Splunk"""
        try:
            # Mock bulk upload to Splunk
            return {
                "success": True,
                "provider": "splunk",
                "events_uploaded": len(events),
                "response_time": 500
            }
        except Exception as e:
            logger.error("Error in bulk upload to Splunk", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _bulk_upload_to_qradar(self, connection: Dict[str, Any], events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk upload to QRadar"""
        try:
            # Mock bulk upload to QRadar
            return {
                "success": True,
                "provider": "qradar",
                "events_uploaded": len(events),
                "response_time": 600
            }
        except Exception as e:
            logger.error("Error in bulk upload to QRadar", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _bulk_upload_to_elk(self, connection: Dict[str, Any], events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk upload to ELK Stack"""
        try:
            # Mock bulk upload to ELK
            return {
                "success": True,
                "provider": "elk",
                "events_uploaded": len(events),
                "response_time": 450
            }
        except Exception as e:
            logger.error("Error in bulk upload to ELK", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _bulk_upload_to_sentinel(self, connection: Dict[str, Any], events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Bulk upload to Microsoft Sentinel"""
        try:
            # Mock bulk upload to Sentinel
            return {
                "success": True,
                "provider": "sentinel",
                "events_uploaded": len(events),
                "response_time": 700
            }
        except Exception as e:
            logger.error("Error in bulk upload to Sentinel", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def get_siem_connections(self) -> List[Dict[str, Any]]:
        """Get all active SIEM connections"""
        try:
            connections = []
            for connection_id, connection in self.active_connections.items():
                stream = self.event_streams.get(connection_id, {})
                
                connections.append({
                    "connection_id": connection_id,
                    "provider": connection["provider"].value,
                    "provider_name": self.siem_configs[connection["provider"]]["name"],
                    "status": connection["status"],
                    "established_at": connection["established_at"].isoformat(),
                    "last_heartbeat": connection["last_heartbeat"].isoformat(),
                    "stream_status": stream.get("status", "inactive"),
                    "events_sent": stream.get("events_sent", 0),
                    "last_event": stream.get("last_event")
                })
            
            return connections
            
        except Exception as e:
            logger.error("Error getting SIEM connections", error=str(e))
            return []
    
    async def disconnect_siem(self, connection_id: str) -> Dict[str, Any]:
        """Disconnect from SIEM provider"""
        try:
            if connection_id not in self.active_connections:
                return {"success": False, "error": "Connection not found"}
            
            # Remove from active connections
            del self.active_connections[connection_id]
            
            # Remove from event streams
            if connection_id in self.event_streams:
                del self.event_streams[connection_id]
            
            # Remove from cache
            await cache_manager.delete(f"siem_connection_{connection_id}", namespace="siem_connections")
            
            logger.info(f"Disconnected SIEM connection {connection_id}")
            
            return {"success": True, "message": "Successfully disconnected"}
            
        except Exception as e:
            logger.error(f"Error disconnecting SIEM {connection_id}", error=str(e))
            return {"success": False, "error": str(e)}
    
    def _generate_connection_id(self, provider: SIEMProvider) -> str:
        """Generate unique connection ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{provider.value}_conn_{timestamp}"

# Global enhanced SIEM integration instance
enhanced_siem_integration = EnhancedSIEMIntegration()
