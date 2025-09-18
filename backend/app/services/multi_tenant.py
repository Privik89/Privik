"""
Multi-Tenant Service
Support for multi-tenant deployments and MSP scenarios
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import structlog
from ..services.cache_manager import cache_manager
from ..services.logging_service import logging_service

logger = structlog.get_logger()

class TenantType(Enum):
    ENTERPRISE = "enterprise"
    SMB = "smb"
    MSP = "msp"
    RESELLER = "reseller"

class TenantStatus(Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"
    TRIAL = "trial"

class TenantPlan(Enum):
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"

class MultiTenantService:
    """Multi-tenant service for MSP and enterprise deployments"""
    
    def __init__(self):
        self.tenants = {}
        self.tenant_users = {}
        self.tenant_resources = {}
        self.tenant_quotas = {}
        self.tenant_billing = {}
        
        # Default tenant plans
        self.tenant_plans = {
            TenantPlan.BASIC: {
                "name": "Basic",
                "max_users": 25,
                "max_emails_per_month": 10000,
                "storage_gb": 10,
                "features": [
                    "email_security",
                    "basic_reporting",
                    "email_support"
                ],
                "price_per_month": 99.00
            },
            TenantPlan.PROFESSIONAL: {
                "name": "Professional",
                "max_users": 100,
                "max_emails_per_month": 50000,
                "storage_gb": 50,
                "features": [
                    "email_security",
                    "advanced_reporting",
                    "api_access",
                    "priority_support",
                    "custom_policies"
                ],
                "price_per_month": 299.00
            },
            TenantPlan.ENTERPRISE: {
                "name": "Enterprise",
                "max_users": 500,
                "max_emails_per_month": 250000,
                "storage_gb": 200,
                "features": [
                    "email_security",
                    "advanced_reporting",
                    "api_access",
                    "priority_support",
                    "custom_policies",
                    "siem_integration",
                    "ldap_integration",
                    "custom_deployment",
                    "dedicated_support"
                ],
                "price_per_month": 999.00
            }
        }
    
    async def create_tenant(
        self,
        tenant_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create a new tenant"""
        try:
            logger.info("Creating tenant", name=tenant_config.get("name"))
            
            # Validate tenant configuration
            validation_result = await self._validate_tenant_config(tenant_config)
            if not validation_result.get("valid"):
                return {"success": False, "error": validation_result.get("error")}
            
            # Generate tenant ID
            tenant_id = self._generate_tenant_id(tenant_config.get("name"))
            
            # Create tenant object
            tenant = {
                "tenant_id": tenant_id,
                "name": tenant_config["name"],
                "domain": tenant_config.get("domain"),
                "tenant_type": tenant_config.get("tenant_type", TenantType.ENTERPRISE.value),
                "status": TenantStatus.TRIAL.value,
                "plan": tenant_config.get("plan", TenantPlan.BASIC.value),
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
                "trial_ends_at": datetime.now() + timedelta(days=30),
                "admin_contact": tenant_config.get("admin_contact", {}),
                "billing_contact": tenant_config.get("billing_contact", {}),
                "settings": tenant_config.get("settings", {}),
                "custom_domain": tenant_config.get("custom_domain"),
                "ssl_enabled": tenant_config.get("ssl_enabled", False)
            }
            
            # Initialize tenant resources
            await self._initialize_tenant_resources(tenant_id, tenant["plan"])
            
            # Initialize tenant quotas
            await self._initialize_tenant_quotas(tenant_id, tenant["plan"])
            
            # Initialize tenant billing
            await self._initialize_tenant_billing(tenant_id, tenant["plan"])
            
            # Store tenant
            self.tenants[tenant_id] = tenant
            
            # Cache tenant
            await cache_manager.set(
                f"tenant_{tenant_id}",
                tenant,
                ttl=86400,  # 24 hours
                namespace="tenants"
            )
            
            # Log tenant creation
            await logging_service.log_audit_event(
                logging_service.AuditEvent(
                    event_type='tenant_created',
                    details={
                        'tenant_id': tenant_id,
                        'tenant_name': tenant_config["name"],
                        'tenant_type': tenant["tenant_type"],
                        'plan': tenant["plan"]
                    },
                    severity='medium'
                )
            )
            
            logger.info("Tenant created successfully", tenant_id=tenant_id)
            
            return {
                "success": True,
                "tenant_id": tenant_id,
                "created_at": tenant["created_at"].isoformat(),
                "trial_ends_at": tenant["trial_ends_at"].isoformat()
            }
            
        except Exception as e:
            logger.error("Error creating tenant", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _validate_tenant_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate tenant configuration"""
        try:
            required_fields = ["name"]
            missing_fields = [field for field in required_fields if field not in config]
            
            if missing_fields:
                return {
                    "valid": False,
                    "error": f"Missing required fields: {', '.join(missing_fields)}"
                }
            
            # Validate tenant type
            tenant_type = config.get("tenant_type", TenantType.ENTERPRISE.value)
            if tenant_type not in [t.value for t in TenantType]:
                return {
                    "valid": False,
                    "error": f"Invalid tenant type: {tenant_type}"
                }
            
            # Validate plan
            plan = config.get("plan", TenantPlan.BASIC.value)
            if plan not in [p.value for p in TenantPlan]:
                return {
                    "valid": False,
                    "error": f"Invalid plan: {plan}"
                }
            
            # Validate domain uniqueness
            domain = config.get("domain")
            if domain:
                existing_tenant = await self._find_tenant_by_domain(domain)
                if existing_tenant:
                    return {
                        "valid": False,
                        "error": f"Domain {domain} is already in use"
                    }
            
            return {"valid": True}
            
        except Exception as e:
            logger.error("Error validating tenant config", error=str(e))
            return {"valid": False, "error": str(e)}
    
    async def _initialize_tenant_resources(self, tenant_id: str, plan: str):
        """Initialize tenant resources"""
        try:
            plan_config = self.tenant_plans.get(TenantPlan(plan), self.tenant_plans[TenantPlan.BASIC])
            
            resources = {
                "tenant_id": tenant_id,
                "plan": plan,
                "max_users": plan_config["max_users"],
                "max_emails_per_month": plan_config["max_emails_per_month"],
                "storage_gb": plan_config["storage_gb"],
                "features": plan_config["features"],
                "current_users": 0,
                "current_emails_this_month": 0,
                "current_storage_gb": 0,
                "created_at": datetime.now()
            }
            
            self.tenant_resources[tenant_id] = resources
            
            # Cache resources
            await cache_manager.set(
                f"tenant_resources_{tenant_id}",
                resources,
                ttl=3600,  # 1 hour
                namespace="tenant_resources"
            )
            
        except Exception as e:
            logger.error(f"Error initializing tenant resources for {tenant_id}", error=str(e))
    
    async def _initialize_tenant_quotas(self, tenant_id: str, plan: str):
        """Initialize tenant quotas"""
        try:
            plan_config = self.tenant_plans.get(TenantPlan(plan), self.tenant_plans[TenantPlan.BASIC])
            
            quotas = {
                "tenant_id": tenant_id,
                "plan": plan,
                "user_quota": plan_config["max_users"],
                "email_quota": plan_config["max_emails_per_month"],
                "storage_quota_gb": plan_config["storage_gb"],
                "api_calls_per_hour": plan_config.get("api_calls_per_hour", 1000),
                "webhook_deliveries_per_day": plan_config.get("webhook_deliveries_per_day", 1000),
                "created_at": datetime.now()
            }
            
            self.tenant_quotas[tenant_id] = quotas
            
            # Cache quotas
            await cache_manager.set(
                f"tenant_quotas_{tenant_id}",
                quotas,
                ttl=3600,  # 1 hour
                namespace="tenant_quotas"
            )
            
        except Exception as e:
            logger.error(f"Error initializing tenant quotas for {tenant_id}", error=str(e))
    
    async def _initialize_tenant_billing(self, tenant_id: str, plan: str):
        """Initialize tenant billing"""
        try:
            plan_config = self.tenant_plans.get(TenantPlan(plan), self.tenant_plans[TenantPlan.BASIC])
            
            billing = {
                "tenant_id": tenant_id,
                "plan": plan,
                "price_per_month": plan_config["price_per_month"],
                "billing_cycle": "monthly",
                "currency": "USD",
                "payment_method": None,
                "last_payment": None,
                "next_billing_date": datetime.now() + timedelta(days=30),
                "total_paid": 0.00,
                "outstanding_balance": 0.00,
                "created_at": datetime.now()
            }
            
            self.tenant_billing[tenant_id] = billing
            
            # Cache billing
            await cache_manager.set(
                f"tenant_billing_{tenant_id}",
                billing,
                ttl=3600,  # 1 hour
                namespace="tenant_billing"
            )
            
        except Exception as e:
            logger.error(f"Error initializing tenant billing for {tenant_id}", error=str(e))
    
    async def add_user_to_tenant(
        self,
        tenant_id: str,
        user_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Add user to tenant"""
        try:
            # Check tenant exists
            if tenant_id not in self.tenants:
                return {"success": False, "error": "Tenant not found"}
            
            # Check user quota
            quota_check = await self._check_user_quota(tenant_id)
            if not quota_check.get("allowed"):
                return {"success": False, "error": quota_check.get("error")}
            
            # Initialize tenant users if not exists
            if tenant_id not in self.tenant_users:
                self.tenant_users[tenant_id] = {}
            
            user_id = user_data.get("user_id") or self._generate_user_id(user_data.get("email"))
            
            # Create user object
            user = {
                "user_id": user_id,
                "tenant_id": tenant_id,
                "email": user_data["email"],
                "name": user_data.get("name", ""),
                "role": user_data.get("role", "user"),
                "status": "active",
                "created_at": datetime.now(),
                "last_login": None,
                "permissions": user_data.get("permissions", []),
                "settings": user_data.get("settings", {})
            }
            
            # Add user to tenant
            self.tenant_users[tenant_id][user_id] = user
            
            # Update tenant resource count
            if tenant_id in self.tenant_resources:
                self.tenant_resources[tenant_id]["current_users"] += 1
            
            # Cache user
            await cache_manager.set(
                f"tenant_user_{tenant_id}_{user_id}",
                user,
                ttl=3600,  # 1 hour
                namespace="tenant_users"
            )
            
            # Log user addition
            await logging_service.log_audit_event(
                logging_service.AuditEvent(
                    event_type='tenant_user_added',
                    user_id=user_id,
                    details={
                        'tenant_id': tenant_id,
                        'user_email': user_data["email"],
                        'user_role': user.get("role")
                    },
                    severity='low'
                )
            )
            
            logger.info(f"Added user to tenant", tenant_id=tenant_id, user_id=user_id)
            
            return {
                "success": True,
                "user_id": user_id,
                "tenant_id": tenant_id
            }
            
        except Exception as e:
            logger.error(f"Error adding user to tenant {tenant_id}", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _check_user_quota(self, tenant_id: str) -> Dict[str, Any]:
        """Check if tenant can add more users"""
        try:
            if tenant_id not in self.tenant_resources:
                return {"allowed": False, "error": "Tenant resources not found"}
            
            resources = self.tenant_resources[tenant_id]
            current_users = resources["current_users"]
            max_users = resources["max_users"]
            
            if current_users >= max_users:
                return {
                    "allowed": False,
                    "error": f"User quota exceeded ({current_users}/{max_users})"
                }
            
            return {"allowed": True}
            
        except Exception as e:
            logger.error(f"Error checking user quota for {tenant_id}", error=str(e))
            return {"allowed": False, "error": str(e)}
    
    async def check_email_quota(self, tenant_id: str, email_count: int = 1) -> Dict[str, Any]:
        """Check if tenant can process more emails"""
        try:
            if tenant_id not in self.tenant_resources:
                return {"allowed": False, "error": "Tenant resources not found"}
            
            resources = self.tenant_resources[tenant_id]
            current_emails = resources["current_emails_this_month"]
            max_emails = resources["max_emails_per_month"]
            
            if current_emails + email_count > max_emails:
                return {
                    "allowed": False,
                    "error": f"Email quota would be exceeded ({current_emails + email_count}/{max_emails})"
                }
            
            return {"allowed": True}
            
        except Exception as e:
            logger.error(f"Error checking email quota for {tenant_id}", error=str(e))
            return {"allowed": False, "error": str(e)}
    
    async def record_email_processing(self, tenant_id: str, email_count: int = 1):
        """Record email processing for quota tracking"""
        try:
            if tenant_id in self.tenant_resources:
                self.tenant_resources[tenant_id]["current_emails_this_month"] += email_count
                
                # Update cache
                await cache_manager.set(
                    f"tenant_resources_{tenant_id}",
                    self.tenant_resources[tenant_id],
                    ttl=3600,
                    namespace="tenant_resources"
                )
                
        except Exception as e:
            logger.error(f"Error recording email processing for {tenant_id}", error=str(e))
    
    async def get_tenant_info(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant information"""
        try:
            if tenant_id not in self.tenants:
                return {"error": "Tenant not found"}
            
            tenant = self.tenants[tenant_id]
            resources = self.tenant_resources.get(tenant_id, {})
            quotas = self.tenant_quotas.get(tenant_id, {})
            billing = self.tenant_billing.get(tenant_id, {})
            
            # Get user count
            user_count = len(self.tenant_users.get(tenant_id, {}))
            
            return {
                "tenant_id": tenant_id,
                "name": tenant["name"],
                "domain": tenant["domain"],
                "tenant_type": tenant["tenant_type"],
                "status": tenant["status"],
                "plan": tenant["plan"],
                "created_at": tenant["created_at"].isoformat(),
                "trial_ends_at": tenant["trial_ends_at"].isoformat(),
                "user_count": user_count,
                "resources": resources,
                "quotas": quotas,
                "billing": billing
            }
            
        except Exception as e:
            logger.error(f"Error getting tenant info for {tenant_id}", error=str(e))
            return {"error": str(e)}
    
    async def get_tenant_users(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Get all users for a tenant"""
        try:
            if tenant_id not in self.tenant_users:
                return []
            
            users = []
            for user_id, user in self.tenant_users[tenant_id].items():
                user_info = {
                    "user_id": user_id,
                    "email": user["email"],
                    "name": user["name"],
                    "role": user["role"],
                    "status": user["status"],
                    "created_at": user["created_at"].isoformat(),
                    "last_login": user["last_login"].isoformat() if user["last_login"] else None
                }
                users.append(user_info)
            
            return users
            
        except Exception as e:
            logger.error(f"Error getting tenant users for {tenant_id}", error=str(e))
            return []
    
    async def update_tenant_plan(
        self,
        tenant_id: str,
        new_plan: str
    ) -> Dict[str, Any]:
        """Update tenant plan"""
        try:
            if tenant_id not in self.tenants:
                return {"success": False, "error": "Tenant not found"}
            
            if new_plan not in [p.value for p in TenantPlan]:
                return {"success": False, "error": f"Invalid plan: {new_plan}"}
            
            # Update tenant plan
            self.tenants[tenant_id]["plan"] = new_plan
            self.tenants[tenant_id]["updated_at"] = datetime.now()
            
            # Update resources and quotas
            await self._initialize_tenant_resources(tenant_id, new_plan)
            await self._initialize_tenant_quotas(tenant_id, new_plan)
            
            # Update billing
            plan_config = self.tenant_plans.get(TenantPlan(new_plan), self.tenant_plans[TenantPlan.BASIC])
            if tenant_id in self.tenant_billing:
                self.tenant_billing[tenant_id]["plan"] = new_plan
                self.tenant_billing[tenant_id]["price_per_month"] = plan_config["price_per_month"]
            
            # Update cache
            await cache_manager.set(
                f"tenant_{tenant_id}",
                self.tenants[tenant_id],
                ttl=86400,
                namespace="tenants"
            )
            
            logger.info(f"Updated tenant plan", tenant_id=tenant_id, new_plan=new_plan)
            
            return {"success": True, "message": "Plan updated successfully"}
            
        except Exception as e:
            logger.error(f"Error updating tenant plan for {tenant_id}", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def get_all_tenants(self) -> List[Dict[str, Any]]:
        """Get all tenants"""
        try:
            tenants = []
            for tenant_id, tenant in self.tenants.items():
                resources = self.tenant_resources.get(tenant_id, {})
                user_count = len(self.tenant_users.get(tenant_id, {}))
                
                tenant_info = {
                    "tenant_id": tenant_id,
                    "name": tenant["name"],
                    "domain": tenant["domain"],
                    "tenant_type": tenant["tenant_type"],
                    "status": tenant["status"],
                    "plan": tenant["plan"],
                    "user_count": user_count,
                    "created_at": tenant["created_at"].isoformat(),
                    "trial_ends_at": tenant["trial_ends_at"].isoformat()
                }
                tenants.append(tenant_info)
            
            return tenants
            
        except Exception as e:
            logger.error("Error getting all tenants", error=str(e))
            return []
    
    async def _find_tenant_by_domain(self, domain: str) -> Optional[str]:
        """Find tenant by domain"""
        try:
            for tenant_id, tenant in self.tenants.items():
                if tenant.get("domain") == domain:
                    return tenant_id
            return None
            
        except Exception as e:
            logger.error(f"Error finding tenant by domain {domain}", error=str(e))
            return None
    
    def _generate_tenant_id(self, name: str) -> str:
        """Generate unique tenant ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"tenant_{name.lower().replace(' ', '_')}_{timestamp}"
    
    def _generate_user_id(self, email: str) -> str:
        """Generate unique user ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        email_hash = hash(email) % 10000
        return f"user_{email_hash}_{timestamp}"
    
    async def get_tenant_plans(self) -> Dict[str, Any]:
        """Get available tenant plans"""
        try:
            return {
                "plans": {
                    plan.value: {
                        "name": config["name"],
                        "max_users": config["max_users"],
                        "max_emails_per_month": config["max_emails_per_month"],
                        "storage_gb": config["storage_gb"],
                        "features": config["features"],
                        "price_per_month": config["price_per_month"]
                    }
                    for plan, config in self.tenant_plans.items()
                }
            }
            
        except Exception as e:
            logger.error("Error getting tenant plans", error=str(e))
            return {"error": str(e)}

# Global multi-tenant service instance
multi_tenant_service = MultiTenantService()
