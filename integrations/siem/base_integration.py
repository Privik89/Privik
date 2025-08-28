"""
Privik Base SIEM Integration
Common interface for all SIEM integrations
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import structlog

logger = structlog.get_logger()

class BaseSIEMIntegration(ABC):
    """Base class for all SIEM integrations."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize base SIEM integration."""
        self.config = config
        self.connected = False
        self.siem_type = config.get('siem_type', 'unknown')
        self.enabled = config.get('enabled', True)
        
        # Common configuration
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', 0)
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        self.api_key = config.get('api_key', '')
        self.ssl_verify = config.get('ssl_verify', True)
        
        # Threat intelligence settings
        self.enable_threat_intel = config.get('enable_threat_intel', True)
        self.enable_alerting = config.get('enable_alerting', True)
        self.enable_dashboards = config.get('enable_dashboards', True)
        
        # Data format settings
        self.data_format = config.get('data_format', 'json')  # json, xml, csv
        self.compression = config.get('compression', False)
        self.batch_size = config.get('batch_size', 100)
        self.batch_timeout = config.get('batch_timeout', 30)
    
    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize SIEM connection."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test SIEM connection."""
        pass
    
    @abstractmethod
    async def send_threat_data(self, threat_data: Dict[str, Any]) -> bool:
        """Send threat data to SIEM."""
        pass
    
    @abstractmethod
    async def send_status_data(self, status_data: Dict[str, Any]) -> bool:
        """Send status data to SIEM."""
        pass
    
    @abstractmethod
    async def get_threat_intelligence(self, indicators: List[str]) -> Dict[str, Any]:
        """Get threat intelligence from SIEM."""
        pass
    
    @abstractmethod
    async def create_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Create SIEM alert."""
        pass
    
    @abstractmethod
    async def get_dashboard_data(self, dashboard_name: str) -> Dict[str, Any]:
        """Get dashboard data from SIEM."""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Cleanup SIEM integration."""
        pass
    
    def get_siem_info(self) -> Dict[str, Any]:
        """Get SIEM information."""
        return {
            'siem_type': self.siem_type,
            'host': self.host,
            'port': self.port,
            'connected': self.connected,
            'enabled': self.enabled,
            'features': {
                'threat_intelligence': self.enable_threat_intel,
                'alerting': self.enable_alerting,
                'dashboards': self.enable_dashboards
            }
        }
    
    def format_threat_data(self, threat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format threat data for SIEM."""
        try:
            # Standard threat data format
            formatted_data = {
                'timestamp': threat_data.get('timestamp', int(time.time())),
                'threat_id': threat_data.get('threat_id'),
                'threat_type': threat_data.get('threat_type'),
                'threat_score': threat_data.get('threat_score', 0),
                'threat_indicators': threat_data.get('threat_indicators', []),
                'source': threat_data.get('source', 'privik'),
                'agent_id': threat_data.get('agent_id'),
                'ai_confidence': threat_data.get('ai_confidence', 0),
                'model_predictions': threat_data.get('model_predictions', {}),
                'raw_data': threat_data.get('raw_data', {}),
                'metadata': {
                    'siem_type': self.siem_type,
                    'data_format': self.data_format,
                    'compression': self.compression
                }
            }
            
            return formatted_data
            
        except Exception as e:
            logger.error("Error formatting threat data", error=str(e))
            return threat_data
    
    def format_status_data(self, status_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format status data for SIEM."""
        try:
            # Standard status data format
            formatted_data = {
                'timestamp': status_data.get('timestamp', int(time.time())),
                'agent_id': status_data.get('agent_id'),
                'status': status_data.get('status'),
                'monitors': status_data.get('monitors', {}),
                'performance': status_data.get('performance', {}),
                'errors': status_data.get('errors', []),
                'metadata': {
                    'siem_type': self.siem_type,
                    'data_format': self.data_format,
                    'compression': self.compression
                }
            }
            
            return formatted_data
            
        except Exception as e:
            logger.error("Error formatting status data", error=str(e))
            return status_data
    
    async def validate_config(self) -> bool:
        """Validate SIEM configuration."""
        try:
            required_fields = ['host', 'siem_type']
            
            for field in required_fields:
                if not self.config.get(field):
                    logger.error(f"Missing required field: {field}")
                    return False
            
            # Validate SIEM type
            valid_siem_types = [
                'splunk', 'elk', 'qradar', 'servicenow', 'solarwinds',
                'logrhythm', 'exabeam', 'sumologic', 'datadog', 'custom'
            ]
            
            if self.siem_type not in valid_siem_types:
                logger.error(f"Invalid SIEM type: {self.siem_type}")
                return False
            
            logger.info(f"SIEM configuration validated: {self.siem_type}")
            return True
            
        except Exception as e:
            logger.error("Error validating SIEM configuration", error=str(e))
            return False
