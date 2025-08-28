"""
Privik IBM QRadar SIEM Integration
QRadar integration for enterprise threat intelligence sharing
"""

import asyncio
import json
import time
import base64
from typing import Dict, Any, List, Optional
import structlog

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

from .base_integration import BaseSIEMIntegration

logger = structlog.get_logger()

class QRadarIntegration(BaseSIEMIntegration):
    """IBM QRadar SIEM integration for Privik."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize QRadar integration."""
        super().__init__(config)
        self.session = None
        self.auth_token = None
        
        # QRadar configuration
        self.qradar_host = config.get('qradar_host', 'localhost')
        self.qradar_port = config.get('qradar_port', 443)
        self.qradar_username = config.get('qradar_username', 'admin')
        self.qradar_password = config.get('qradar_password', '')
        self.qradar_ssl = config.get('qradar_ssl', True)
        
        # QRadar specific settings
        self.offense_source = config.get('offense_source', 'Privik Email Security')
        self.log_source_id = config.get('log_source_id', 0)
        self.low_level_category_id = config.get('low_level_category_id', 0)
        
        # API endpoints
        self.base_url = f"{'https' if self.qradar_ssl else 'http'}://{self.qradar_host}:{self.qradar_port}"
        self.auth_url = f"{self.base_url}/api/auth"
        self.events_url = f"{self.base_url}/api/events"
        self.offenses_url = f"{self.base_url}/api/siem/offenses"
        self.reference_data_url = f"{self.base_url}/api/reference_data"
    
    async def initialize(self) -> bool:
        """Initialize QRadar connection."""
        try:
            if not AIOHTTP_AVAILABLE:
                logger.error("aiohttp library not available")
                return False
            
            logger.info("Initializing QRadar integration")
            
            # Create HTTP session
            connector = aiohttp.TCPConnector(verify_ssl=self.ssl_verify)
            self.session = aiohttp.ClientSession(connector=connector)
            
            # Authenticate with QRadar
            await self._authenticate()
            
            # Test connection
            await self.test_connection()
            
            # Setup reference data
            if self.enable_threat_intel:
                await self._setup_reference_data()
            
            self.connected = True
            logger.info("QRadar integration initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize QRadar integration", error=str(e))
            return False
    
    async def _authenticate(self):
        """Authenticate with QRadar."""
        try:
            # Create basic auth header
            auth_string = f"{self.qradar_username}:{self.qradar_password}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                'Authorization': f'Basic {auth_b64}',
                'Content-Type': 'application/json',
                'Version': '12.0'
            }
            
            # Authenticate
            async with self.session.get(self.auth_url, headers=headers) as response:
                if response.status == 200:
                    auth_data = await response.json()
                    self.auth_token = auth_data.get('session_id')
                    logger.info("QRadar authentication successful")
                else:
                    raise Exception(f"QRadar authentication failed: {response.status}")
                    
        except Exception as e:
            logger.error("Error authenticating with QRadar", error=str(e))
            raise
    
    async def test_connection(self) -> bool:
        """Test QRadar connection."""
        try:
            headers = self._get_auth_headers()
            
            # Test API connectivity
            async with self.session.get(f"{self.base_url}/api/version", headers=headers) as response:
                if response.status == 200:
                    version_data = await response.json()
                    logger.info(f"Connected to QRadar version: {version_data.get('version')}")
                    return True
                else:
                    logger.error(f"QRadar connection test failed: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error("QRadar connection test failed", error=str(e))
            return False
    
    async def _setup_reference_data(self):
        """Setup QRadar reference data."""
        try:
            # Create threat intelligence reference set
            threat_intel_set = {
                "name": "Privik_Threat_Intelligence",
                "element_type": "ALN",
                "time_to_live": "0",
                "timeout_type": "FIRST_SEEN"
            }
            
            headers = self._get_auth_headers()
            
            # Create reference set
            async with self.session.post(
                f"{self.reference_data_url}/sets",
                headers=headers,
                json=threat_intel_set
            ) as response:
                if response.status in [200, 201]:
                    logger.info("Created QRadar threat intelligence reference set")
                else:
                    logger.warning("Threat intelligence reference set may already exist")
            
        except Exception as e:
            logger.error("Error setting up QRadar reference data", error=str(e))
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        return {
            'SEC': self.auth_token,
            'Content-Type': 'application/json',
            'Version': '12.0'
        }
    
    async def send_threat_data(self, threat_data: Dict[str, Any]) -> bool:
        """Send threat data to QRadar."""
        try:
            # Format threat data
            formatted_data = self.format_threat_data(threat_data)
            
            # Create QRadar event
            qradar_event = {
                "qid": self._get_qid_for_threat(formatted_data['threat_type']),
                "sourceip": formatted_data.get('source_ip', '0.0.0.0'),
                "magnitude": self._calculate_magnitude(formatted_data['threat_score']),
                "credibility": int(formatted_data.get('ai_confidence', 0) * 10),
                "relevance": 10,
                "source": self.offense_source,
                "starttime": formatted_data['timestamp'],
                "endtime": formatted_data['timestamp'],
                "username": formatted_data.get('agent_id', 'unknown'),
                "eventcount": 1,
                "event_description": f"Privik detected {formatted_data['threat_type']} threat",
                "custom_data": {
                    "threat_id": formatted_data['threat_id'],
                    "threat_score": formatted_data['threat_score'],
                    "threat_indicators": formatted_data['threat_indicators'],
                    "ai_confidence": formatted_data['ai_confidence'],
                    "model_predictions": formatted_data['model_predictions']
                }
            }
            
            headers = self._get_auth_headers()
            
            # Send event to QRadar
            async with self.session.post(
                self.events_url,
                headers=headers,
                json=qradar_event
            ) as response:
                if response.status in [200, 201]:
                    logger.info(f"Sent threat data to QRadar: {threat_data.get('threat_id')}")
                    return True
                else:
                    logger.error(f"Failed to send threat data to QRadar: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error("Error sending threat data to QRadar", error=str(e))
            return False
    
    async def send_status_data(self, status_data: Dict[str, Any]) -> bool:
        """Send status data to QRadar."""
        try:
            # Format status data
            formatted_data = self.format_status_data(status_data)
            
            # Create QRadar event for status
            qradar_event = {
                "qid": 1000001,  # Generic log event
                "sourceip": "0.0.0.0",
                "magnitude": 1,
                "credibility": 5,
                "relevance": 5,
                "source": self.offense_source,
                "starttime": formatted_data['timestamp'],
                "endtime": formatted_data['timestamp'],
                "username": formatted_data.get('agent_id', 'unknown'),
                "eventcount": 1,
                "event_description": f"Privik agent status: {formatted_data['status']}",
                "custom_data": {
                    "agent_id": formatted_data['agent_id'],
                    "status": formatted_data['status'],
                    "monitors": formatted_data['monitors'],
                    "performance": formatted_data['performance'],
                    "errors": formatted_data['errors']
                }
            }
            
            headers = self._get_auth_headers()
            
            # Send event to QRadar
            async with self.session.post(
                self.events_url,
                headers=headers,
                json=qradar_event
            ) as response:
                if response.status in [200, 201]:
                    logger.debug(f"Sent status data to QRadar: {status_data.get('agent_id')}")
                    return True
                else:
                    logger.error(f"Failed to send status data to QRadar: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error("Error sending status data to QRadar", error=str(e))
            return False
    
    async def get_threat_intelligence(self, indicators: List[str]) -> Dict[str, Any]:
        """Get threat intelligence from QRadar."""
        try:
            intelligence = {}
            
            for indicator in indicators:
                # Search for indicator in reference data
                headers = self._get_auth_headers()
                
                async with self.session.get(
                    f"{self.reference_data_url}/sets/Privik_Threat_Intelligence",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        ref_data = await response.json()
                        
                        # Check if indicator exists
                        for item in ref_data.get('data', []):
                            if item.get('value') == indicator:
                                intelligence[indicator] = {
                                    'exists': True,
                                    'first_seen': item.get('first_seen'),
                                    'last_seen': item.get('last_seen'),
                                    'source': 'qradar'
                                }
                                break
                        else:
                            intelligence[indicator] = {
                                'exists': False,
                                'source': 'qradar'
                            }
                    else:
                        logger.warning(f"Could not retrieve reference data for {indicator}")
            
            logger.info(f"Retrieved threat intelligence for {len(indicators)} indicators")
            return intelligence
            
        except Exception as e:
            logger.error("Error getting threat intelligence from QRadar", error=str(e))
            return {}
    
    async def create_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Create QRadar offense."""
        try:
            # Create QRadar offense
            offense_data = {
                "description": alert_data.get('description', 'Privik Security Alert'),
                "assigned_to": "",
                "closing_reason_id": 0,
                "credibility": int(alert_data.get('credibility', 5)),
                "magnitude": int(alert_data.get('magnitude', 5)),
                "relevance": int(alert_data.get('relevance', 5)),
                "severity": int(alert_data.get('severity', 5)),
                "status": "OPEN",
                "source_network": "0.0.0.0/0",
                "source": self.offense_source,
                "custom_data": alert_data.get('threat_data', {})
            }
            
            headers = self._get_auth_headers()
            
            # Create offense
            async with self.session.post(
                self.offenses_url,
                headers=headers,
                json=offense_data
            ) as response:
                if response.status in [200, 201]:
                    offense_info = await response.json()
                    logger.info(f"Created QRadar offense: {offense_info.get('id')}")
                    return True
                else:
                    logger.error(f"Failed to create QRadar offense: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error("Error creating QRadar offense", error=str(e))
            return False
    
    async def get_dashboard_data(self, dashboard_name: str) -> Dict[str, Any]:
        """Get dashboard data from QRadar."""
        try:
            # Get offense statistics
            headers = self._get_auth_headers()
            
            # Get recent offenses
            params = {
                "filter": f"source='{self.offense_source}'",
                "fields": "id,description,severity,magnitude,credibility,relevance,status,start_time",
                "limit": 100
            }
            
            async with self.session.get(
                self.offenses_url,
                headers=headers,
                params=params
            ) as response:
                if response.status == 200:
                    offenses_data = await response.json()
                    
                    dashboard_data = {
                        'total_offenses': len(offenses_data),
                        'open_offenses': len([o for o in offenses_data if o.get('status') == 'OPEN']),
                        'avg_severity': sum(o.get('severity', 0) for o in offenses_data) / len(offenses_data) if offenses_data else 0,
                        'recent_offenses': offenses_data[:10]
                    }
                    
                    return dashboard_data
                else:
                    logger.error(f"Failed to get QRadar dashboard data: {response.status}")
                    return {}
                    
        except Exception as e:
            logger.error("Error getting dashboard data from QRadar", error=str(e))
            return {}
    
    def _get_qid_for_threat(self, threat_type: str) -> int:
        """Get QRadar QID for threat type."""
        qid_mapping = {
            'phishing': 1000001,
            'malware': 1000002,
            'suspicious_behavior': 1000003,
            'data_exfiltration': 1000004,
            'credential_theft': 1000005
        }
        return qid_mapping.get(threat_type, 1000000)  # Default QID
    
    def _calculate_magnitude(self, threat_score: float) -> int:
        """Calculate QRadar magnitude from threat score."""
        if threat_score >= 80:
            return 10
        elif threat_score >= 60:
            return 7
        elif threat_score >= 40:
            return 5
        elif threat_score >= 20:
            return 3
        else:
            return 1
    
    async def cleanup(self):
        """Cleanup QRadar integration."""
        try:
            if self.session:
                await self.session.close()
                logger.info("QRadar integration cleaned up")
        except Exception as e:
            logger.error("Error cleaning up QRadar integration", error=str(e))
