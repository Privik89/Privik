"""
Webhook System Service
Manages webhooks for external integrations and real-time notifications
"""

import asyncio
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import structlog
import aiohttp
from ..services.cache_manager import cache_manager
from ..services.logging_service import logging_service

logger = structlog.get_logger()

class WebhookEventType(Enum):
    EMAIL_THREAT_DETECTED = "email_threat_detected"
    USER_BEHAVIOR_ANOMALY = "user_behavior_anomaly"
    SANDBOX_ANALYSIS_COMPLETE = "sandbox_analysis_complete"
    COMPLIANCE_VIOLATION = "compliance_violation"
    SYSTEM_ALERT = "system_alert"
    INCIDENT_CREATED = "incident_created"
    INCIDENT_RESOLVED = "incident_resolved"
    POLICY_UPDATED = "policy_updated"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"

class WebhookStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    SUSPENDED = "suspended"

class WebhookSystem:
    """Webhook system for external integrations"""
    
    def __init__(self):
        self.webhooks = {}
        self.webhook_queues = {}
        self.delivery_attempts = {}
        self.webhook_events = {
            WebhookEventType.EMAIL_THREAT_DETECTED: {
                "name": "Email Threat Detected",
                "description": "Triggered when a malicious email is detected",
                "schema": {
                    "event_type": "string",
                    "timestamp": "datetime",
                    "email_id": "string",
                    "threat_type": "string",
                    "threat_score": "float",
                    "sender": "string",
                    "subject": "string"
                }
            },
            WebhookEventType.USER_BEHAVIOR_ANOMALY: {
                "name": "User Behavior Anomaly",
                "description": "Triggered when user behavior anomaly is detected",
                "schema": {
                    "event_type": "string",
                    "timestamp": "datetime",
                    "user_id": "string",
                    "anomaly_type": "string",
                    "risk_score": "float",
                    "details": "object"
                }
            },
            WebhookEventType.SANDBOX_ANALYSIS_COMPLETE: {
                "name": "Sandbox Analysis Complete",
                "description": "Triggered when sandbox analysis is completed",
                "schema": {
                    "event_type": "string",
                    "timestamp": "datetime",
                    "analysis_id": "string",
                    "verdict": "string",
                    "threat_score": "float",
                    "file_hash": "string"
                }
            },
            WebhookEventType.COMPLIANCE_VIOLATION: {
                "name": "Compliance Violation",
                "description": "Triggered when compliance violation is detected",
                "schema": {
                    "event_type": "string",
                    "timestamp": "datetime",
                    "violation_type": "string",
                    "severity": "string",
                    "user_id": "string",
                    "details": "object"
                }
            },
            WebhookEventType.SYSTEM_ALERT: {
                "name": "System Alert",
                "description": "Triggered for system-level alerts",
                "schema": {
                    "event_type": "string",
                    "timestamp": "datetime",
                    "alert_type": "string",
                    "severity": "string",
                    "message": "string",
                    "system_component": "string"
                }
            },
            WebhookEventType.INCIDENT_CREATED: {
                "name": "Incident Created",
                "description": "Triggered when security incident is created",
                "schema": {
                    "event_type": "string",
                    "timestamp": "datetime",
                    "incident_id": "string",
                    "incident_type": "string",
                    "severity": "string",
                    "description": "string"
                }
            },
            WebhookEventType.INCIDENT_RESOLVED: {
                "name": "Incident Resolved",
                "description": "Triggered when security incident is resolved",
                "schema": {
                    "event_type": "string",
                    "timestamp": "datetime",
                    "incident_id": "string",
                    "resolution_time": "integer",
                    "resolution_notes": "string"
                }
            },
            WebhookEventType.POLICY_UPDATED: {
                "name": "Policy Updated",
                "description": "Triggered when security policy is updated",
                "schema": {
                    "event_type": "string",
                    "timestamp": "datetime",
                    "policy_id": "string",
                    "policy_name": "string",
                    "updated_by": "string",
                    "changes": "object"
                }
            },
            WebhookEventType.USER_LOGIN: {
                "name": "User Login",
                "description": "Triggered when user logs in",
                "schema": {
                    "event_type": "string",
                    "timestamp": "datetime",
                    "user_id": "string",
                    "ip_address": "string",
                    "user_agent": "string"
                }
            },
            WebhookEventType.USER_LOGOUT: {
                "name": "User Logout",
                "description": "Triggered when user logs out",
                "schema": {
                    "event_type": "string",
                    "timestamp": "datetime",
                    "user_id": "string",
                    "session_duration": "integer"
                }
            }
        }
    
    async def create_webhook(
        self,
        webhook_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new webhook"""
        try:
            logger.info("Creating webhook", name=webhook_config.get("name"))
            
            # Validate webhook configuration
            validation_result = await self._validate_webhook_config(webhook_config)
            if not validation_result.get("valid"):
                return {"success": False, "error": validation_result.get("error")}
            
            # Test webhook endpoint
            test_result = await self._test_webhook_endpoint(webhook_config)
            if not test_result.get("success"):
                return {"success": False, "error": test_result.get("error")}
            
            # Generate webhook ID and secret
            webhook_id = self._generate_webhook_id(webhook_config.get("name"))
            webhook_secret = self._generate_webhook_secret()
            
            # Create webhook object
            webhook = {
                "webhook_id": webhook_id,
                "name": webhook_config["name"],
                "description": webhook_config.get("description", ""),
                "url": webhook_config["url"],
                "events": webhook_config["events"],
                "secret": webhook_secret,
                "headers": webhook_config.get("headers", {}),
                "status": WebhookStatus.ACTIVE.value,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "last_delivery": None,
                "delivery_count": 0,
                "failure_count": 0,
                "timeout": webhook_config.get("timeout", 30),
                "retry_count": webhook_config.get("retry_count", 3),
                "retry_delay": webhook_config.get("retry_delay", 60)
            }
            
            # Store webhook
            self.webhooks[webhook_id] = webhook
            
            # Initialize delivery queue
            self.webhook_queues[webhook_id] = asyncio.Queue()
            self.delivery_attempts[webhook_id] = {}
            
            # Cache webhook
            await cache_manager.set(
                f"webhook_{webhook_id}",
                webhook,
                ttl=86400 * 365,  # 1 year
                namespace="webhooks"
            )
            
            # Start delivery worker
            asyncio.create_task(self._webhook_delivery_worker(webhook_id))
            
            # Log webhook creation
            await logging_service.log_audit_event(
                logging_service.AuditEvent(
                    event_type='webhook_created',
                    details={
                        'webhook_id': webhook_id,
                        'name': webhook_config["name"],
                        'url': webhook_config["url"],
                        'events': webhook_config["events"]
                    },
                    severity='low'
                )
            )
            
            logger.info("Webhook created successfully", webhook_id=webhook_id)
            
            return {
                "success": True,
                "webhook_id": webhook_id,
                "webhook_secret": webhook_secret,
                "created_at": webhook["created_at"].isoformat()
            }
            
        except Exception as e:
            logger.error("Error creating webhook", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _validate_webhook_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate webhook configuration"""
        try:
            required_fields = ["name", "url", "events"]
            missing_fields = [field for field in required_fields if field not in config]
            
            if missing_fields:
                return {
                    "valid": False,
                    "error": f"Missing required fields: {', '.join(missing_fields)}"
                }
            
            # Validate URL
            url = config["url"]
            if not url.startswith(("http://", "https://")):
                return {
                    "valid": False,
                    "error": "Invalid URL format"
                }
            
            # Validate events
            events = config["events"]
            if not isinstance(events, list) or not events:
                return {
                    "valid": False,
                    "error": "Events must be a non-empty list"
                }
            
            valid_events = [event.value for event in WebhookEventType]
            invalid_events = [event for event in events if event not in valid_events]
            if invalid_events:
                return {
                    "valid": False,
                    "error": f"Invalid event types: {', '.join(invalid_events)}"
                }
            
            # Validate timeout
            timeout = config.get("timeout", 30)
            if not isinstance(timeout, int) or timeout < 1 or timeout > 300:
                return {
                    "valid": False,
                    "error": "Timeout must be between 1 and 300 seconds"
                }
            
            return {"valid": True}
            
        except Exception as e:
            logger.error("Error validating webhook config", error=str(e))
            return {"valid": False, "error": str(e)}
    
    async def _test_webhook_endpoint(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test webhook endpoint"""
        try:
            url = config["url"]
            timeout = config.get("timeout", 30)
            headers = config.get("headers", {})
            
            # Create test payload
            test_payload = {
                "event_type": "webhook_test",
                "timestamp": datetime.now().isoformat(),
                "message": "This is a test webhook delivery"
            }
            
            # Add webhook signature
            if config.get("secret"):
                signature = self._generate_webhook_signature(test_payload, config["secret"])
                headers["X-Webhook-Signature"] = f"sha256={signature}"
            
            # Send test request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=test_payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    if response.status in [200, 201, 202, 204]:
                        return {"success": True, "status_code": response.status}
                    else:
                        return {
                            "success": False,
                            "error": f"HTTP {response.status}: {await response.text()}"
                        }
                        
        except asyncio.TimeoutError:
            return {"success": False, "error": "Request timeout"}
        except aiohttp.ClientError as e:
            return {"success": False, "error": f"Connection error: {str(e)}"}
        except Exception as e:
            logger.error("Error testing webhook endpoint", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def trigger_webhook(
        self,
        event_type: WebhookEventType,
        event_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Trigger webhook for specific event"""
        try:
            logger.info("Triggering webhook", event_type=event_type.value)
            
            # Find webhooks subscribed to this event
            subscribed_webhooks = []
            for webhook_id, webhook in self.webhooks.items():
                if (event_type.value in webhook["events"] and 
                    webhook["status"] == WebhookStatus.ACTIVE.value):
                    subscribed_webhooks.append(webhook_id)
            
            if not subscribed_webhooks:
                logger.info("No webhooks subscribed to event", event_type=event_type.value)
                return {"success": True, "delivered_to": 0, "message": "No subscribers"}
            
            # Prepare event payload
            payload = {
                "event_type": event_type.value,
                "timestamp": datetime.now().isoformat(),
                "data": event_data
            }
            
            # Queue delivery for each webhook
            delivery_results = {}
            for webhook_id in subscribed_webhooks:
                try:
                    await self.webhook_queues[webhook_id].put(payload)
                    delivery_results[webhook_id] = {"queued": True}
                except Exception as e:
                    logger.error(f"Error queuing webhook {webhook_id}", error=str(e))
                    delivery_results[webhook_id] = {"queued": False, "error": str(e)}
            
            # Log webhook trigger
            await logging_service.log_audit_event(
                logging_service.AuditEvent(
                    event_type='webhook_triggered',
                    details={
                        'event_type': event_type.value,
                        'subscribed_webhooks': subscribed_webhooks,
                        'delivery_results': delivery_results
                    },
                    severity='low'
                )
            )
            
            return {
                "success": True,
                "event_type": event_type.value,
                "subscribed_webhooks": len(subscribed_webhooks),
                "delivery_results": delivery_results
            }
            
        except Exception as e:
            logger.error("Error triggering webhook", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _webhook_delivery_worker(self, webhook_id: str):
        """Webhook delivery worker"""
        try:
            webhook = self.webhooks.get(webhook_id)
            if not webhook:
                return
            
            queue = self.webhook_queues.get(webhook_id)
            if not queue:
                return
            
            logger.info(f"Started webhook delivery worker for {webhook_id}")
            
            while webhook_id in self.webhooks:
                try:
                    # Get payload from queue
                    payload = await asyncio.wait_for(queue.get(), timeout=1.0)
                    
                    # Deliver webhook
                    delivery_result = await self._deliver_webhook(webhook_id, payload)
                    
                    # Update webhook statistics
                    if delivery_result.get("success"):
                        webhook["delivery_count"] += 1
                        webhook["last_delivery"] = datetime.now()
                    else:
                        webhook["failure_count"] += 1
                    
                    # Update cached webhook
                    await cache_manager.set(
                        f"webhook_{webhook_id}",
                        webhook,
                        ttl=86400 * 365,
                        namespace="webhooks"
                    )
                    
                except asyncio.TimeoutError:
                    # No payload in queue, continue
                    continue
                except Exception as e:
                    logger.error(f"Error in webhook delivery worker {webhook_id}", error=str(e))
                    await asyncio.sleep(5)  # Wait before retrying
            
            logger.info(f"Stopped webhook delivery worker for {webhook_id}")
            
        except Exception as e:
            logger.error(f"Error in webhook delivery worker {webhook_id}", error=str(e))
    
    async def _deliver_webhook(self, webhook_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Deliver webhook payload"""
        try:
            webhook = self.webhooks.get(webhook_id)
            if not webhook:
                return {"success": False, "error": "Webhook not found"}
            
            url = webhook["url"]
            headers = webhook["headers"].copy()
            timeout = webhook["timeout"]
            secret = webhook["secret"]
            
            # Add webhook signature
            signature = self._generate_webhook_signature(payload, secret)
            headers["X-Webhook-Signature"] = f"sha256={signature}"
            headers["X-Webhook-ID"] = webhook_id
            headers["X-Webhook-Event"] = payload["event_type"]
            headers["Content-Type"] = "application/json"
            
            # Track delivery attempt
            attempt_id = f"{webhook_id}_{int(datetime.now().timestamp())}"
            self.delivery_attempts[webhook_id][attempt_id] = {
                "started_at": datetime.now(),
                "payload": payload,
                "status": "delivering"
            }
            
            # Send webhook
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    response_text = await response.text()
                    
                    # Update delivery attempt
                    self.delivery_attempts[webhook_id][attempt_id].update({
                        "completed_at": datetime.now(),
                        "status": "completed" if response.status in [200, 201, 202, 204] else "failed",
                        "status_code": response.status,
                        "response": response_text
                    })
                    
                    if response.status in [200, 201, 202, 204]:
                        logger.info(f"Webhook delivered successfully", webhook_id=webhook_id, attempt_id=attempt_id)
                        return {"success": True, "status_code": response.status}
                    else:
                        logger.warning(f"Webhook delivery failed", webhook_id=webhook_id, status_code=response.status)
                        return {
                            "success": False,
                            "status_code": response.status,
                            "error": response_text
                        }
                        
        except asyncio.TimeoutError:
            logger.error(f"Webhook delivery timeout", webhook_id=webhook_id)
            return {"success": False, "error": "Delivery timeout"}
        except aiohttp.ClientError as e:
            logger.error(f"Webhook delivery error", webhook_id=webhook_id, error=str(e))
            return {"success": False, "error": str(e)}
        except Exception as e:
            logger.error(f"Unexpected error delivering webhook {webhook_id}", error=str(e))
            return {"success": False, "error": str(e)}
    
    def _generate_webhook_signature(self, payload: Dict[str, Any], secret: str) -> str:
        """Generate webhook signature"""
        try:
            payload_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
            signature = hmac.new(
                secret.encode('utf-8'),
                payload_json.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            return signature
            
        except Exception as e:
            logger.error("Error generating webhook signature", error=str(e))
            return ""
    
    async def get_webhooks(self) -> List[Dict[str, Any]]:
        """Get all webhooks"""
        try:
            webhooks = []
            for webhook_id, webhook in self.webhooks.items():
                webhook_info = {
                    "webhook_id": webhook_id,
                    "name": webhook["name"],
                    "description": webhook["description"],
                    "url": webhook["url"],
                    "events": webhook["events"],
                    "status": webhook["status"],
                    "created_at": webhook["created_at"].isoformat(),
                    "updated_at": webhook["updated_at"].isoformat(),
                    "last_delivery": webhook["last_delivery"].isoformat() if webhook["last_delivery"] else None,
                    "delivery_count": webhook["delivery_count"],
                    "failure_count": webhook["failure_count"]
                }
                webhooks.append(webhook_info)
            
            return webhooks
            
        except Exception as e:
            logger.error("Error getting webhooks", error=str(e))
            return []
    
    async def update_webhook(
        self,
        webhook_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update webhook configuration"""
        try:
            if webhook_id not in self.webhooks:
                return {"success": False, "error": "Webhook not found"}
            
            webhook = self.webhooks[webhook_id]
            
            # Validate updates
            if "events" in updates:
                valid_events = [event.value for event in WebhookEventType]
                invalid_events = [event for event in updates["events"] if event not in valid_events]
                if invalid_events:
                    return {"success": False, "error": f"Invalid event types: {', '.join(invalid_events)}"}
            
            # Update webhook
            for key, value in updates.items():
                if key in ["name", "description", "url", "events", "headers", "timeout", "retry_count", "retry_delay"]:
                    webhook[key] = value
            
            webhook["updated_at"] = datetime.now()
            
            # Test endpoint if URL was updated
            if "url" in updates:
                test_result = await self._test_webhook_endpoint(webhook)
                if not test_result.get("success"):
                    return {"success": False, "error": f"Endpoint test failed: {test_result.get('error')}"}
            
            # Update cached webhook
            await cache_manager.set(
                f"webhook_{webhook_id}",
                webhook,
                ttl=86400 * 365,
                namespace="webhooks"
            )
            
            logger.info(f"Updated webhook {webhook_id}")
            
            return {"success": True, "message": "Webhook updated successfully"}
            
        except Exception as e:
            logger.error(f"Error updating webhook {webhook_id}", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def delete_webhook(self, webhook_id: str) -> Dict[str, Any]:
        """Delete webhook"""
        try:
            if webhook_id not in self.webhooks:
                return {"success": False, "error": "Webhook not found"}
            
            # Remove webhook
            del self.webhooks[webhook_id]
            
            # Remove queue
            if webhook_id in self.webhook_queues:
                del self.webhook_queues[webhook_id]
            
            # Remove delivery attempts
            if webhook_id in self.delivery_attempts:
                del self.delivery_attempts[webhook_id]
            
            # Remove from cache
            await cache_manager.delete(f"webhook_{webhook_id}", namespace="webhooks")
            
            logger.info(f"Deleted webhook {webhook_id}")
            
            return {"success": True, "message": "Webhook deleted successfully"}
            
        except Exception as e:
            logger.error(f"Error deleting webhook {webhook_id}", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def get_webhook_events(self) -> Dict[str, Any]:
        """Get available webhook events"""
        try:
            return {
                "events": {
                    event.value: {
                        "name": info["name"],
                        "description": info["description"],
                        "schema": info["schema"]
                    }
                    for event, info in self.webhook_events.items()
                }
            }
            
        except Exception as e:
            logger.error("Error getting webhook events", error=str(e))
            return {"error": str(e)}
    
    async def get_webhook_delivery_logs(
        self,
        webhook_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get webhook delivery logs"""
        try:
            if webhook_id not in self.delivery_attempts:
                return []
            
            attempts = self.delivery_attempts[webhook_id]
            
            # Sort by timestamp (newest first)
            sorted_attempts = sorted(
                attempts.items(),
                key=lambda x: x[1]["started_at"],
                reverse=True
            )
            
            # Format logs
            logs = []
            for attempt_id, attempt_data in sorted_attempts[:limit]:
                log_entry = {
                    "attempt_id": attempt_id,
                    "started_at": attempt_data["started_at"].isoformat(),
                    "completed_at": attempt_data.get("completed_at", "").isoformat() if attempt_data.get("completed_at") else None,
                    "status": attempt_data["status"],
                    "status_code": attempt_data.get("status_code"),
                    "event_type": attempt_data["payload"]["event_type"],
                    "response": attempt_data.get("response", "")[:500]  # Truncate response
                }
                logs.append(log_entry)
            
            return logs
            
        except Exception as e:
            logger.error(f"Error getting webhook delivery logs for {webhook_id}", error=str(e))
            return []
    
    def _generate_webhook_id(self, name: str) -> str:
        """Generate unique webhook ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"wh_{name.lower().replace(' ', '_')}_{timestamp}"
    
    def _generate_webhook_secret(self) -> str:
        """Generate webhook secret"""
        import secrets
        return secrets.token_urlsafe(32)

# Global webhook system instance
webhook_system = WebhookSystem()
