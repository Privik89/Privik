"""
Privik SIEM Manager
Manages multiple SIEM integrations and auto-detection
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Type
import structlog

from .base_integration import BaseSIEMIntegration
from .splunk_integration import SplunkIntegration
from .elk_integration import ELKIntegration

logger = structlog.get_logger()

class SIEMManager:
    """Manages multiple SIEM integrations."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize SIEM manager."""
        self.config = config
        self.integrations: Dict[str, BaseSIEMIntegration] = {}
        self.active_integrations: List[str] = []
        
        # Available SIEM integrations
        self.siem_integrations = {
            'splunk': SplunkIntegration,
            'elk': ELKIntegration,
            # Add more SIEM integrations here
        }
        
        # Auto-detection settings
        self.auto_detect = config.get('auto_detect', True)
        self.detection_timeout = config.get('detection_timeout', 30)
    
    async def initialize(self) -> bool:
        """Initialize SIEM manager."""
        try:
            logger.info("Initializing SIEM manager")
            
            # Load SIEM configurations
            siem_configs = self.config.get('siem_configs', [])
            
            # Initialize each SIEM integration
            for siem_config in siem_configs:
                await self._add_siem_integration(siem_config)
            
            # Auto-detect SIEM if enabled
            if self.auto_detect and not self.integrations:
                await self._auto_detect_siem()
            
            # Activate integrations
            await self._activate_integrations()
            
            logger.info(f"SIEM manager initialized with {len(self.active_integrations)} active integrations")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize SIEM manager", error=str(e))
            return False
    
    async def _add_siem_integration(self, siem_config: Dict[str, Any]) -> bool:
        """Add a SIEM integration."""
        try:
            siem_type = siem_config.get('siem_type')
            if not siem_type:
                logger.error("SIEM type not specified in configuration")
                return False
            
            if siem_type not in self.siem_integrations:
                logger.error(f"Unsupported SIEM type: {siem_type}")
                return False
            
            # Create SIEM integration instance
            siem_class = self.siem_integrations[siem_type]
            integration = siem_class(siem_config)
            
            # Validate configuration
            if not await integration.validate_config():
                logger.error(f"Invalid configuration for {siem_type}")
                return False
            
            # Initialize integration
            if await integration.initialize():
                self.integrations[siem_type] = integration
                logger.info(f"Added SIEM integration: {siem_type}")
                return True
            else:
                logger.error(f"Failed to initialize {siem_type} integration")
                return False
                
        except Exception as e:
            logger.error(f"Error adding SIEM integration", error=str(e))
            return False
    
    async def _auto_detect_siem(self):
        """Auto-detect SIEM systems."""
        try:
            logger.info("Auto-detecting SIEM systems...")
            
            # Common SIEM detection patterns
            detection_configs = [
                # Splunk
                {
                    'siem_type': 'splunk',
                    'host': 'localhost',
                    'port': 8089,
                    'username': 'admin',
                    'password': '',
                    'siem_app': 'search'
                },
                # ELK Stack
                {
                    'siem_type': 'elk',
                    'host': 'localhost',
                    'port': 9200,
                    'username': '',
                    'password': '',
                    'elasticsearch_ssl': False
                },
                # QRadar
                {
                    'siem_type': 'qradar',
                    'host': 'localhost',
                    'port': 443,
                    'username': 'admin',
                    'password': '',
                    'qradar_ssl': True
                }
            ]
            
            # Test each configuration
            for config in detection_configs:
                try:
                    if await self._test_siem_connection(config):
                        logger.info(f"Auto-detected SIEM: {config['siem_type']}")
                        await self._add_siem_integration(config)
                        break
                except Exception as e:
                    logger.debug(f"SIEM detection failed for {config['siem_type']}: {str(e)}")
                    continue
                    
        except Exception as e:
            logger.error("Error during SIEM auto-detection", error=str(e))
    
    async def _test_siem_connection(self, config: Dict[str, Any]) -> bool:
        """Test SIEM connection."""
        try:
            siem_type = config.get('siem_type')
            if siem_type not in self.siem_integrations:
                return False
            
            # Create temporary integration for testing
            siem_class = self.siem_integrations[siem_type]
            temp_integration = siem_class(config)
            
            # Test connection with timeout
            try:
                await asyncio.wait_for(temp_integration.test_connection(), timeout=self.detection_timeout)
                return True
            except asyncio.TimeoutError:
                logger.debug(f"SIEM connection timeout for {siem_type}")
                return False
            except Exception:
                return False
                
        except Exception as e:
            logger.debug(f"Error testing SIEM connection: {str(e)}")
            return False
    
    async def _activate_integrations(self):
        """Activate SIEM integrations."""
        try:
            for siem_type, integration in self.integrations.items():
                if integration.connected and integration.enabled:
                    self.active_integrations.append(siem_type)
                    logger.info(f"Activated SIEM integration: {siem_type}")
                    
        except Exception as e:
            logger.error("Error activating SIEM integrations", error=str(e))
    
    async def send_threat_data(self, threat_data: Dict[str, Any]) -> Dict[str, bool]:
        """Send threat data to all active SIEM integrations."""
        try:
            results = {}
            
            for siem_type in self.active_integrations:
                integration = self.integrations[siem_type]
                try:
                    success = await integration.send_threat_data(threat_data)
                    results[siem_type] = success
                except Exception as e:
                    logger.error(f"Error sending threat data to {siem_type}", error=str(e))
                    results[siem_type] = False
            
            return results
            
        except Exception as e:
            logger.error("Error sending threat data to SIEMs", error=str(e))
            return {}
    
    async def send_status_data(self, status_data: Dict[str, Any]) -> Dict[str, bool]:
        """Send status data to all active SIEM integrations."""
        try:
            results = {}
            
            for siem_type in self.active_integrations:
                integration = self.integrations[siem_type]
                try:
                    success = await integration.send_status_data(status_data)
                    results[siem_type] = success
                except Exception as e:
                    logger.error(f"Error sending status data to {siem_type}", error=str(e))
                    results[siem_type] = False
            
            return results
            
        except Exception as e:
            logger.error("Error sending status data to SIEMs", error=str(e))
            return {}
    
    async def get_threat_intelligence(self, indicators: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get threat intelligence from all active SIEM integrations."""
        try:
            intelligence = {}
            
            for siem_type in self.active_integrations:
                integration = self.integrations[siem_type]
                try:
                    siem_intel = await integration.get_threat_intelligence(indicators)
                    intelligence[siem_type] = siem_intel
                except Exception as e:
                    logger.error(f"Error getting threat intelligence from {siem_type}", error=str(e))
                    intelligence[siem_type] = {}
            
            return intelligence
            
        except Exception as e:
            logger.error("Error getting threat intelligence from SIEMs", error=str(e))
            return {}
    
    async def create_alert(self, alert_data: Dict[str, Any]) -> Dict[str, bool]:
        """Create alerts in all active SIEM integrations."""
        try:
            results = {}
            
            for siem_type in self.active_integrations:
                integration = self.integrations[siem_type]
                try:
                    success = await integration.create_alert(alert_data)
                    results[siem_type] = success
                except Exception as e:
                    logger.error(f"Error creating alert in {siem_type}", error=str(e))
                    results[siem_type] = False
            
            return results
            
        except Exception as e:
            logger.error("Error creating alerts in SIEMs", error=str(e))
            return {}
    
    async def get_dashboard_data(self, dashboard_name: str) -> Dict[str, Dict[str, Any]]:
        """Get dashboard data from all active SIEM integrations."""
        try:
            dashboard_data = {}
            
            for siem_type in self.active_integrations:
                integration = self.integrations[siem_type]
                try:
                    siem_data = await integration.get_dashboard_data(dashboard_name)
                    dashboard_data[siem_type] = siem_data
                except Exception as e:
                    logger.error(f"Error getting dashboard data from {siem_type}", error=str(e))
                    dashboard_data[siem_type] = {}
            
            return dashboard_data
            
        except Exception as e:
            logger.error("Error getting dashboard data from SIEMs", error=str(e))
            return {}
    
    async def add_custom_siem(self, siem_config: Dict[str, Any]) -> bool:
        """Add a custom SIEM integration."""
        try:
            # Validate custom SIEM configuration
            if not siem_config.get('siem_type'):
                logger.error("Custom SIEM type not specified")
                return False
            
            # Add custom SIEM integration
            return await self._add_siem_integration(siem_config)
            
        except Exception as e:
            logger.error("Error adding custom SIEM", error=str(e))
            return False
    
    def get_siem_status(self) -> Dict[str, Any]:
        """Get status of all SIEM integrations."""
        try:
            status = {
                'total_integrations': len(self.integrations),
                'active_integrations': len(self.active_integrations),
                'integrations': {}
            }
            
            for siem_type, integration in self.integrations.items():
                status['integrations'][siem_type] = integration.get_siem_info()
            
            return status
            
        except Exception as e:
            logger.error("Error getting SIEM status", error=str(e))
            return {}
    
    async def test_all_connections(self) -> Dict[str, bool]:
        """Test connections to all SIEM integrations."""
        try:
            results = {}
            
            for siem_type, integration in self.integrations.items():
                try:
                    success = await integration.test_connection()
                    results[siem_type] = success
                except Exception as e:
                    logger.error(f"Error testing connection to {siem_type}", error=str(e))
                    results[siem_type] = False
            
            return results
            
        except Exception as e:
            logger.error("Error testing SIEM connections", error=str(e))
            return {}
    
    async def cleanup(self):
        """Cleanup all SIEM integrations."""
        try:
            for siem_type, integration in self.integrations.items():
                try:
                    await integration.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up {siem_type} integration", error=str(e))
            
            logger.info("SIEM manager cleaned up")
            
        except Exception as e:
            logger.error("Error cleaning up SIEM manager", error=str(e))
