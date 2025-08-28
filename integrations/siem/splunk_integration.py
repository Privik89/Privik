"""
Privik Splunk SIEM Integration
Real-time threat intelligence sharing with Splunk Enterprise Security
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional
import structlog

try:
    import splunklib.client as client
    import splunklib.results as results
    SPLUNK_AVAILABLE = True
except ImportError:
    SPLUNK_AVAILABLE = False

from .base_integration import BaseSIEMIntegration

logger = structlog.get_logger()

class SplunkIntegration(BaseSIEMIntegration):
    """Splunk Enterprise Security integration for Privik."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize Splunk integration."""
        super().__init__(config)
        self.service = None
        self.index = None
        self.sourcetype = "privik:threats"
        self.source = "privik_email_security"
        
        # Splunk configuration
        self.host = config.get('splunk_host', 'localhost')
        self.port = config.get('splunk_port', 8089)
        self.username = config.get('splunk_username', 'admin')
        self.password = config.get('splunk_password', '')
        self.index_name = config.get('splunk_index', 'main')
        self.app = config.get('splunk_app', 'search')
        
        # Threat intelligence settings
        self.enable_threat_intel = config.get('enable_threat_intel', True)
        self.enable_alerting = config.get('enable_alerting', True)
        self.enable_dashboards = config.get('enable_dashboards', True)
    
    async def initialize(self) -> bool:
        """Initialize Splunk connection."""
        try:
            if not SPLUNK_AVAILABLE:
                logger.error("Splunk library not available")
                return False
            
            logger.info("Initializing Splunk integration")
            
            # Connect to Splunk
            self.service = client.connect(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                app=self.app
            )
            
            # Get index
            self.index = self.service.indexes[self.index_name]
            
            # Test connection
            await self._test_connection()
            
            # Setup threat intelligence
            if self.enable_threat_intel:
                await self._setup_threat_intelligence()
            
            # Setup alerting
            if self.enable_alerting:
                await self._setup_alerting()
            
            # Setup dashboards
            if self.enable_dashboards:
                await self._setup_dashboards()
            
            logger.info("Splunk integration initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize Splunk integration", error=str(e))
            return False
    
    async def _test_connection(self) -> bool:
        """Test Splunk connection."""
        try:
            # Test basic connectivity
            info = self.service.info()
            logger.info(f"Connected to Splunk version: {info['version']}")
            
            # Test index access
            index_info = self.index.refresh()
            logger.info(f"Index '{self.index_name}' accessible")
            
            return True
            
        except Exception as e:
            logger.error("Splunk connection test failed", error=str(e))
            return False
    
    async def _setup_threat_intelligence(self):
        """Setup threat intelligence sharing."""
        try:
            # Create threat intelligence lookup
            lookup_name = "privik_threat_intel"
            
            # Define lookup fields
            fields = [
                "threat_id",
                "threat_type",
                "threat_score",
                "indicators",
                "first_seen",
                "last_seen",
                "status"
            ]
            
            # Create lookup if it doesn't exist
            try:
                lookup = self.service.kvstore_collections.create(
                    lookup_name,
                    fields=fields
                )
                logger.info(f"Created threat intelligence lookup: {lookup_name}")
            except Exception:
                logger.info(f"Threat intelligence lookup already exists: {lookup_name}")
            
        except Exception as e:
            logger.error("Error setting up threat intelligence", error=str(e))
    
    async def _setup_alerting(self):
        """Setup Splunk alerting."""
        try:
            # Create saved search for high-threat alerts
            search_query = f"""
            index="{self.index_name}" sourcetype="{self.sourcetype}" threat_score>80
            | stats count by threat_type, threat_id
            | where count > 0
            """
            
            saved_search_name = "privik_high_threat_alert"
            
            # Create saved search
            saved_search = self.service.saved_searches.create(
                saved_search_name,
                search_query,
                dispatch.earliest_time="-15m",
                dispatch.latest_time="now",
                dispatch.auto_cancel="10m",
                dispatch.auto_pause="0",
                actions="email",
                action.email.to="security@company.com",
                action.email.subject="Privik High Threat Alert",
                action.email.message="High threat detected: $threat_type$"
            )
            
            logger.info(f"Created high threat alert: {saved_search_name}")
            
        except Exception as e:
            logger.error("Error setting up alerting", error=str(e))
    
    async def _setup_dashboards(self):
        """Setup Splunk dashboards."""
        try:
            # Create dashboard for Privik threats
            dashboard_name = "privik_threat_dashboard"
            
            dashboard_xml = f"""
            <dashboard version="1" script="privik_dashboard.js">
                <label>Privik Email Security Dashboard</label>
                <description>Real-time threat monitoring and analysis</description>
                
                <row>
                    <panel>
                        <title>Threat Activity (Last 24 Hours)</title>
                        <chart>
                            <search>
                                <query>
                                    index="{self.index_name}" sourcetype="{self.sourcetype}"
                                    | timechart count by threat_type
                                </query>
                                <earliest>-24h</earliest>
                                <latest>now</latest>
                            </search>
                            <option name="charting.chart">line</option>
                        </chart>
                    </panel>
                </row>
                
                <row>
                    <panel>
                        <title>Top Threat Types</title>
                        <table>
                            <search>
                                <query>
                                    index="{self.index_name}" sourcetype="{self.sourcetype}"
                                    | stats count by threat_type
                                    | sort -count
                                    | head 10
                                </query>
                                <earliest>-24h</earliest>
                                <latest>now</latest>
                            </search>
                        </table>
                    </panel>
                    
                    <panel>
                        <title>Threat Score Distribution</title>
                        <chart>
                            <search>
                                <query>
                                    index="{self.index_name}" sourcetype="{self.sourcetype}"
                                    | bucket threat_score span=10
                                    | stats count by threat_score
                                </query>
                                <earliest>-24h</earliest>
                                <latest>now</latest>
                            </search>
                            <option name="charting.chart">column</option>
                        </chart>
                    </panel>
                </row>
            </dashboard>
            """
            
            # Create dashboard
            self.service.confs['savedsearches'].create(
                dashboard_name,
                dashboard_xml
            )
            
            logger.info(f"Created dashboard: {dashboard_name}")
            
        except Exception as e:
            logger.error("Error setting up dashboards", error=str(e))
    
    async def send_threat_data(self, threat_data: Dict[str, Any]) -> bool:
        """Send threat data to Splunk."""
        try:
            # Prepare event data
            event_data = {
                'time': int(time.time()),
                'host': threat_data.get('host', 'unknown'),
                'source': self.source,
                'sourcetype': self.sourcetype,
                'index': self.index_name,
                'event': {
                    'threat_id': threat_data.get('threat_id'),
                    'threat_type': threat_data.get('threat_type'),
                    'threat_score': threat_data.get('threat_score', 0),
                    'indicators': threat_data.get('threat_indicators', []),
                    'source': threat_data.get('source', 'unknown'),
                    'agent_id': threat_data.get('agent_id'),
                    'timestamp': threat_data.get('timestamp', int(time.time())),
                    'ai_confidence': threat_data.get('ai_confidence', 0),
                    'model_predictions': threat_data.get('model_predictions', {}),
                    'raw_data': threat_data.get('raw_data', {})
                }
            }
            
            # Send to Splunk
            self.service.indexes[self.index_name].submit(
                json.dumps(event_data['event']),
                sourcetype=self.sourcetype,
                source=self.source,
                host=event_data['host']
            )
            
            logger.info(f"Sent threat data to Splunk: {threat_data.get('threat_id')}")
            return True
            
        except Exception as e:
            logger.error("Error sending threat data to Splunk", error=str(e))
            return False
    
    async def send_status_data(self, status_data: Dict[str, Any]) -> bool:
        """Send status data to Splunk."""
        try:
            # Prepare status event
            event_data = {
                'time': int(time.time()),
                'host': status_data.get('host', 'unknown'),
                'source': self.source,
                'sourcetype': f"{self.sourcetype}:status",
                'index': self.index_name,
                'event': {
                    'agent_id': status_data.get('agent_id'),
                    'status': status_data.get('status'),
                    'timestamp': status_data.get('timestamp', int(time.time())),
                    'monitors': status_data.get('monitors', {}),
                    'performance': status_data.get('performance', {}),
                    'errors': status_data.get('errors', [])
                }
            }
            
            # Send to Splunk
            self.service.indexes[self.index_name].submit(
                json.dumps(event_data['event']),
                sourcetype=event_data['sourcetype'],
                source=self.source,
                host=event_data['host']
            )
            
            logger.debug(f"Sent status data to Splunk: {status_data.get('agent_id')}")
            return True
            
        except Exception as e:
            logger.error("Error sending status data to Splunk", error=str(e))
            return False
    
    async def get_threat_intelligence(self, indicators: List[str]) -> Dict[str, Any]:
        """Get threat intelligence from Splunk."""
        try:
            # Search for threat intelligence
            search_query = f"""
            index="{self.index_name}" sourcetype="{self.sourcetype}"
            | search {" OR ".join([f'indicators="{indicator}"' for indicator in indicators])}
            | stats latest(threat_score) as max_score, 
                     latest(threat_type) as threat_type,
                     count as occurrences,
                     latest(timestamp) as last_seen
            | where max_score > 0
            """
            
            # Execute search
            search_results = self.service.jobs.oneshot(search_query)
            
            # Parse results
            intelligence = {}
            for result in results.ResultsReader(search_results):
                if result.get('max_score'):
                    intelligence[result.get('threat_type', 'unknown')] = {
                        'max_score': float(result['max_score']),
                        'occurrences': int(result['occurrences']),
                        'last_seen': result['last_seen']
                    }
            
            logger.info(f"Retrieved threat intelligence for {len(indicators)} indicators")
            return intelligence
            
        except Exception as e:
            logger.error("Error getting threat intelligence from Splunk", error=str(e))
            return {}
    
    async def create_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Create Splunk alert."""
        try:
            # Create alert search
            alert_name = f"privik_alert_{int(time.time())}"
            
            # Build search query
            search_query = f"""
            index="{self.index_name}" sourcetype="{self.sourcetype}"
            threat_score >= {alert_data.get('threshold', 80)}
            | stats count by threat_type, threat_id
            | where count > 0
            """
            
            # Create saved search for alert
            saved_search = self.service.saved_searches.create(
                alert_name,
                search_query,
                dispatch.earliest_time="-5m",
                dispatch.latest_time="now",
                dispatch.auto_cancel="5m",
                actions="email",
                action.email.to=alert_data.get('recipients', 'security@company.com'),
                action.email.subject=f"Privik Alert: {alert_data.get('title', 'Threat Detected')}",
                action.email.message=alert_data.get('message', 'Threat detected by Privik')
            )
            
            logger.info(f"Created Splunk alert: {alert_name}")
            return True
            
        except Exception as e:
            logger.error("Error creating Splunk alert", error=str(e))
            return False
    
    async def get_dashboard_data(self, dashboard_name: str) -> Dict[str, Any]:
        """Get dashboard data from Splunk."""
        try:
            # Execute dashboard search
            search_query = f"""
            index="{self.index_name}" sourcetype="{self.sourcetype}"
            | stats count by threat_type
            | sort -count
            """
            
            search_results = self.service.jobs.oneshot(search_query)
            
            # Parse results
            dashboard_data = {
                'threat_types': [],
                'total_threats': 0
            }
            
            for result in results.ResultsReader(search_results):
                threat_type = result.get('threat_type', 'unknown')
                count = int(result.get('count', 0))
                
                dashboard_data['threat_types'].append({
                    'type': threat_type,
                    'count': count
                })
                dashboard_data['total_threats'] += count
            
            return dashboard_data
            
        except Exception as e:
            logger.error("Error getting dashboard data from Splunk", error=str(e))
            return {}
    
    async def cleanup(self):
        """Cleanup Splunk integration."""
        try:
            if self.service:
                self.service.logout()
                logger.info("Splunk integration cleaned up")
        except Exception as e:
            logger.error("Error cleaning up Splunk integration", error=str(e))
