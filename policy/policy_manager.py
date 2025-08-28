"""
Privik Policy Manager
Centralized security policy management and enforcement
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
import structlog

from .policy_engine import PolicyEngine
from .policy_validator import PolicyValidator
from .policy_enforcer import PolicyEnforcer

logger = structlog.get_logger()

class PolicyManager:
    """Manages security policies across the Privik platform."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the policy manager."""
        self.config = config
        self.policies: Dict[str, Dict[str, Any]] = {}
        self.active_policies: Set[str] = set()
        self.policy_engine = PolicyEngine()
        self.policy_validator = PolicyValidator()
        self.policy_enforcer = PolicyEnforcer()
        
        # Policy storage
        self.policy_dir = Path(config.get('policy_dir', './policies'))
        self.policy_dir.mkdir(exist_ok=True)
        
        # Policy categories
        self.policy_categories = {
            'email': 'Email security policies',
            'file': 'File security policies', 
            'link': 'Link security policies',
            'user': 'User behavior policies',
            'system': 'System security policies',
            'compliance': 'Compliance policies'
        }
    
    async def initialize(self) -> bool:
        """Initialize the policy manager."""
        try:
            logger.info("Initializing policy manager")
            
            # Load existing policies
            await self._load_policies()
            
            # Initialize policy engine
            await self.policy_engine.initialize()
            
            # Initialize policy validator
            await self.policy_validator.initialize()
            
            # Initialize policy enforcer
            await self.policy_enforcer.initialize()
            
            # Activate default policies
            await self._activate_default_policies()
            
            logger.info("Policy manager initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize policy manager", error=str(e))
            return False
    
    async def _load_policies(self):
        """Load policies from storage."""
        try:
            # Load from policy directory
            for policy_file in self.policy_dir.glob("*.json"):
                try:
                    with open(policy_file, 'r') as f:
                        policy_data = json.load(f)
                    
                    policy_id = policy_data.get('id')
                    if policy_id:
                        self.policies[policy_id] = policy_data
                        logger.info(f"Loaded policy: {policy_id}")
                        
                except Exception as e:
                    logger.error(f"Error loading policy file {policy_file}", error=str(e))
            
            # Load built-in policies
            await self._load_builtin_policies()
            
            logger.info(f"Loaded {len(self.policies)} policies")
            
        except Exception as e:
            logger.error("Error loading policies", error=str(e))
    
    async def _load_builtin_policies(self):
        """Load built-in default policies."""
        try:
            builtin_policies = {
                'email_phishing': {
                    'id': 'email_phishing',
                    'name': 'Email Phishing Protection',
                    'category': 'email',
                    'description': 'Detect and block phishing emails',
                    'enabled': True,
                    'priority': 'high',
                    'rules': [
                        {
                            'condition': 'threat_score > 70',
                            'action': 'block',
                            'notification': True
                        },
                        {
                            'condition': 'threat_score > 50',
                            'action': 'quarantine',
                            'notification': True
                        }
                    ],
                    'ai_enabled': True,
                    'thresholds': {
                        'block': 70,
                        'quarantine': 50,
                        'alert': 30
                    }
                },
                'file_malware': {
                    'id': 'file_malware',
                    'name': 'File Malware Protection',
                    'category': 'file',
                    'description': 'Detect and block malicious files',
                    'enabled': True,
                    'priority': 'high',
                    'rules': [
                        {
                            'condition': 'file_type in ["exe", "bat", "cmd", "vbs"]',
                            'action': 'block',
                            'notification': True
                        },
                        {
                            'condition': 'threat_score > 80',
                            'action': 'block',
                            'notification': True
                        }
                    ],
                    'ai_enabled': True,
                    'thresholds': {
                        'block': 80,
                        'quarantine': 60,
                        'alert': 40
                    }
                },
                'link_suspicious': {
                    'id': 'link_suspicious',
                    'name': 'Suspicious Link Protection',
                    'category': 'link',
                    'description': 'Detect and block suspicious links',
                    'enabled': True,
                    'priority': 'medium',
                    'rules': [
                        {
                            'condition': 'domain in suspicious_domains',
                            'action': 'rewrite',
                            'notification': True
                        },
                        {
                            'condition': 'threat_score > 60',
                            'action': 'block',
                            'notification': True
                        }
                    ],
                    'ai_enabled': True,
                    'thresholds': {
                        'block': 60,
                        'rewrite': 40,
                        'alert': 20
                    }
                },
                'user_behavior': {
                    'id': 'user_behavior',
                    'name': 'User Behavior Monitoring',
                    'category': 'user',
                    'description': 'Monitor and alert on suspicious user behavior',
                    'enabled': True,
                    'priority': 'medium',
                    'rules': [
                        {
                            'condition': 'click_rate > 0.8',
                            'action': 'alert',
                            'notification': True
                        },
                        {
                            'condition': 'download_rate > 0.6',
                            'action': 'alert',
                            'notification': True
                        }
                    ],
                    'ai_enabled': True,
                    'thresholds': {
                        'high_risk': 0.8,
                        'medium_risk': 0.6,
                        'low_risk': 0.4
                    }
                },
                'compliance_gdpr': {
                    'id': 'compliance_gdpr',
                    'name': 'GDPR Compliance',
                    'category': 'compliance',
                    'description': 'Ensure GDPR compliance for data handling',
                    'enabled': True,
                    'priority': 'high',
                    'rules': [
                        {
                            'condition': 'contains_pii',
                            'action': 'encrypt',
                            'notification': False
                        },
                        {
                            'condition': 'data_retention > 30_days',
                            'action': 'delete',
                            'notification': True
                        }
                    ],
                    'ai_enabled': False,
                    'thresholds': {
                        'retention_days': 30,
                        'encryption_required': True
                    }
                }
            }
            
            # Add built-in policies
            for policy_id, policy_data in builtin_policies.items():
                if policy_id not in self.policies:
                    self.policies[policy_id] = policy_data
                    logger.info(f"Added built-in policy: {policy_id}")
            
        except Exception as e:
            logger.error("Error loading built-in policies", error=str(e))
    
    async def _activate_default_policies(self):
        """Activate default policies."""
        try:
            default_policies = [
                'email_phishing',
                'file_malware', 
                'link_suspicious',
                'user_behavior',
                'compliance_gdpr'
            ]
            
            for policy_id in default_policies:
                if policy_id in self.policies:
                    await self.activate_policy(policy_id)
            
            logger.info(f"Activated {len(self.active_policies)} default policies")
            
        except Exception as e:
            logger.error("Error activating default policies", error=str(e))
    
    async def create_policy(self, policy_data: Dict[str, Any]) -> str:
        """Create a new policy."""
        try:
            # Validate policy data
            if not await self.policy_validator.validate_policy(policy_data):
                raise ValueError("Invalid policy data")
            
            # Generate policy ID
            policy_id = policy_data.get('id') or f"policy_{int(time.time())}"
            policy_data['id'] = policy_id
            policy_data['created_at'] = int(time.time())
            policy_data['updated_at'] = int(time.time())
            
            # Add policy
            self.policies[policy_id] = policy_data
            
            # Save to file
            await self._save_policy(policy_id, policy_data)
            
            logger.info(f"Created policy: {policy_id}")
            return policy_id
            
        except Exception as e:
            logger.error("Error creating policy", error=str(e))
            raise
    
    async def update_policy(self, policy_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing policy."""
        try:
            if policy_id not in self.policies:
                raise ValueError(f"Policy not found: {policy_id}")
            
            # Update policy data
            policy_data = self.policies[policy_id].copy()
            policy_data.update(updates)
            policy_data['updated_at'] = int(time.time())
            
            # Validate updated policy
            if not await self.policy_validator.validate_policy(policy_data):
                raise ValueError("Invalid policy data")
            
            # Update policy
            self.policies[policy_id] = policy_data
            
            # Save to file
            await self._save_policy(policy_id, policy_data)
            
            logger.info(f"Updated policy: {policy_id}")
            return True
            
        except Exception as e:
            logger.error("Error updating policy", error=str(e))
            return False
    
    async def delete_policy(self, policy_id: str) -> bool:
        """Delete a policy."""
        try:
            if policy_id not in self.policies:
                return False
            
            # Deactivate if active
            if policy_id in self.active_policies:
                await self.deactivate_policy(policy_id)
            
            # Remove policy
            del self.policies[policy_id]
            
            # Delete file
            policy_file = self.policy_dir / f"{policy_id}.json"
            if policy_file.exists():
                policy_file.unlink()
            
            logger.info(f"Deleted policy: {policy_id}")
            return True
            
        except Exception as e:
            logger.error("Error deleting policy", error=str(e))
            return False
    
    async def activate_policy(self, policy_id: str) -> bool:
        """Activate a policy."""
        try:
            if policy_id not in self.policies:
                return False
            
            policy_data = self.policies[policy_id]
            if not policy_data.get('enabled', True):
                return False
            
            # Add to active policies
            self.active_policies.add(policy_id)
            
            # Register with policy engine
            await self.policy_engine.register_policy(policy_id, policy_data)
            
            logger.info(f"Activated policy: {policy_id}")
            return True
            
        except Exception as e:
            logger.error("Error activating policy", error=str(e))
            return False
    
    async def deactivate_policy(self, policy_id: str) -> bool:
        """Deactivate a policy."""
        try:
            if policy_id not in self.active_policies:
                return False
            
            # Remove from active policies
            self.active_policies.remove(policy_id)
            
            # Unregister from policy engine
            await self.policy_engine.unregister_policy(policy_id)
            
            logger.info(f"Deactivated policy: {policy_id}")
            return True
            
        except Exception as e:
            logger.error("Error deactivating policy", error=str(e))
            return False
    
    async def evaluate_policy(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate policies against an event."""
        try:
            # Get relevant policies
            relevant_policies = await self._get_relevant_policies(event_data)
            
            # Evaluate each policy
            results = {}
            for policy_id in relevant_policies:
                if policy_id in self.active_policies:
                    result = await self.policy_engine.evaluate_policy(
                        policy_id, 
                        event_data
                    )
                    results[policy_id] = result
            
            # Apply enforcement actions
            enforcement_result = await self.policy_enforcer.apply_actions(results, event_data)
            
            return {
                'policy_results': results,
                'enforcement_result': enforcement_result,
                'evaluated_policies': list(results.keys())
            }
            
        except Exception as e:
            logger.error("Error evaluating policies", error=str(e))
            return {'error': str(e)}
    
    async def _get_relevant_policies(self, event_data: Dict[str, Any]) -> List[str]:
        """Get policies relevant to the event."""
        try:
            relevant_policies = []
            event_type = event_data.get('event_type', 'unknown')
            
            for policy_id, policy_data in self.policies.items():
                category = policy_data.get('category', 'unknown')
                
                # Match by event type and category
                if (event_type == 'email' and category == 'email') or \
                   (event_type == 'file' and category == 'file') or \
                   (event_type == 'link' and category == 'link') or \
                   (event_type == 'user' and category == 'user') or \
                   category == 'system' or category == 'compliance':
                    relevant_policies.append(policy_id)
            
            return relevant_policies
            
        except Exception as e:
            logger.error("Error getting relevant policies", error=str(e))
            return []
    
    async def _save_policy(self, policy_id: str, policy_data: Dict[str, Any]):
        """Save policy to file."""
        try:
            policy_file = self.policy_dir / f"{policy_id}.json"
            with open(policy_file, 'w') as f:
                json.dump(policy_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving policy {policy_id}", error=str(e))
    
    async def get_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific policy."""
        return self.policies.get(policy_id)
    
    async def list_policies(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all policies, optionally filtered by category."""
        try:
            policies = []
            for policy_id, policy_data in self.policies.items():
                if category is None or policy_data.get('category') == category:
                    policy_info = {
                        'id': policy_id,
                        'name': policy_data.get('name'),
                        'category': policy_data.get('category'),
                        'description': policy_data.get('description'),
                        'enabled': policy_data.get('enabled', True),
                        'active': policy_id in self.active_policies,
                        'priority': policy_data.get('priority'),
                        'created_at': policy_data.get('created_at'),
                        'updated_at': policy_data.get('updated_at')
                    }
                    policies.append(policy_info)
            
            return policies
            
        except Exception as e:
            logger.error("Error listing policies", error=str(e))
            return []
    
    async def get_policy_statistics(self) -> Dict[str, Any]:
        """Get policy statistics."""
        try:
            stats = {
                'total_policies': len(self.policies),
                'active_policies': len(self.active_policies),
                'categories': {},
                'priorities': {}
            }
            
            # Count by category
            for policy_data in self.policies.values():
                category = policy_data.get('category', 'unknown')
                stats['categories'][category] = stats['categories'].get(category, 0) + 1
                
                priority = policy_data.get('priority', 'medium')
                stats['priorities'][priority] = stats['priorities'].get(priority, 0) + 1
            
            return stats
            
        except Exception as e:
            logger.error("Error getting policy statistics", error=str(e))
            return {}
    
    async def cleanup(self):
        """Cleanup policy manager."""
        try:
            await self.policy_engine.cleanup()
            await self.policy_validator.cleanup()
            await self.policy_enforcer.cleanup()
            logger.info("Policy manager cleaned up")
        except Exception as e:
            logger.error("Error cleaning up policy manager", error=str(e))
