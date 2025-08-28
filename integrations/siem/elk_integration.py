"""
Privik ELK Stack SIEM Integration
Elasticsearch, Logstash, Kibana integration for threat intelligence sharing
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional
import structlog

try:
    from elasticsearch import AsyncElasticsearch
    from elasticsearch.helpers import async_bulk
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False

from .base_integration import BaseSIEMIntegration

logger = structlog.get_logger()

class ELKIntegration(BaseSIEMIntegration):
    """ELK Stack (Elasticsearch, Logstash, Kibana) integration for Privik."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize ELK integration."""
        super().__init__(config)
        self.client = None
        self.index_prefix = config.get('index_prefix', 'privik')
        
        # ELK configuration
        self.elasticsearch_host = config.get('elasticsearch_host', 'localhost')
        self.elasticsearch_port = config.get('elasticsearch_port', 9200)
        self.elasticsearch_username = config.get('elasticsearch_username', '')
        self.elasticsearch_password = config.get('elasticsearch_password', '')
        self.elasticsearch_ssl = config.get('elasticsearch_ssl', False)
        
        # Index configuration
        self.threats_index = f"{self.index_prefix}-threats"
        self.status_index = f"{self.index_prefix}-status"
        self.alerts_index = f"{self.index_prefix}-alerts"
        
        # Mapping templates
        self.threat_mapping = {
            "mappings": {
                "properties": {
                    "timestamp": {"type": "date"},
                    "threat_id": {"type": "keyword"},
                    "threat_type": {"type": "keyword"},
                    "threat_score": {"type": "float"},
                    "threat_indicators": {"type": "keyword"},
                    "source": {"type": "keyword"},
                    "agent_id": {"type": "keyword"},
                    "ai_confidence": {"type": "float"},
                    "model_predictions": {"type": "object"},
                    "raw_data": {"type": "object"}
                }
            }
        }
    
    async def initialize(self) -> bool:
        """Initialize ELK connection."""
        try:
            if not ELASTICSEARCH_AVAILABLE:
                logger.error("Elasticsearch library not available")
                return False
            
            logger.info("Initializing ELK integration")
            
            # Create Elasticsearch client
            self.client = AsyncElasticsearch(
                hosts=[{
                    'host': self.elasticsearch_host,
                    'port': self.elasticsearch_port
                }],
                http_auth=(self.elasticsearch_username, self.elasticsearch_password) if self.elasticsearch_username else None,
                use_ssl=self.elasticsearch_ssl,
                verify_certs=self.ssl_verify,
                timeout=30,
                max_retries=3,
                retry_on_timeout=True
            )
            
            # Test connection
            await self.test_connection()
            
            # Setup indices
            await self._setup_indices()
            
            # Setup Kibana dashboards
            if self.enable_dashboards:
                await self._setup_kibana_dashboards()
            
            self.connected = True
            logger.info("ELK integration initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize ELK integration", error=str(e))
            return False
    
    async def test_connection(self) -> bool:
        """Test ELK connection."""
        try:
            # Test Elasticsearch connectivity
            info = await self.client.info()
            logger.info(f"Connected to Elasticsearch version: {info['version']['number']}")
            
            # Test cluster health
            health = await self.client.cluster.health()
            logger.info(f"Cluster status: {health['status']}")
            
            return True
            
        except Exception as e:
            logger.error("ELK connection test failed", error=str(e))
            return False
    
    async def _setup_indices(self):
        """Setup Elasticsearch indices."""
        try:
            # Create threats index
            if not await self.client.indices.exists(index=self.threats_index):
                await self.client.indices.create(
                    index=self.threats_index,
                    body=self.threat_mapping
                )
                logger.info(f"Created threats index: {self.threats_index}")
            
            # Create status index
            if not await self.client.indices.exists(index=self.status_index):
                await self.client.indices.create(
                    index=self.status_index,
                    body={
                        "mappings": {
                            "properties": {
                                "timestamp": {"type": "date"},
                                "agent_id": {"type": "keyword"},
                                "status": {"type": "keyword"},
                                "monitors": {"type": "object"},
                                "performance": {"type": "object"},
                                "errors": {"type": "keyword"}
                            }
                        }
                    }
                )
                logger.info(f"Created status index: {self.status_index}")
            
            # Create alerts index
            if not await self.client.indices.exists(index=self.alerts_index):
                await self.client.indices.create(
                    index=self.alerts_index,
                    body={
                        "mappings": {
                            "properties": {
                                "timestamp": {"type": "date"},
                                "alert_id": {"type": "keyword"},
                                "alert_type": {"type": "keyword"},
                                "severity": {"type": "keyword"},
                                "threat_data": {"type": "object"},
                                "status": {"type": "keyword"}
                            }
                        }
                    }
                )
                logger.info(f"Created alerts index: {self.alerts_index}")
            
        except Exception as e:
            logger.error("Error setting up indices", error=str(e))
    
    async def _setup_kibana_dashboards(self):
        """Setup Kibana dashboards."""
        try:
            # Create dashboard configuration
            dashboard_config = {
                "dashboard": {
                    "title": "Privik Email Security Dashboard",
                    "description": "Real-time threat monitoring and analysis",
                    "panels": [
                        {
                            "title": "Threat Activity (Last 24 Hours)",
                            "type": "visualization",
                            "visualization": {
                                "type": "line",
                                "index": self.threats_index,
                                "query": {
                                    "bool": {
                                        "filter": [
                                            {"range": {"timestamp": {"gte": "now-24h"}}}
                                        ]
                                    }
                                },
                                "aggs": {
                                    "threats_over_time": {
                                        "date_histogram": {
                                            "field": "timestamp",
                                            "interval": "1h"
                                        }
                                    }
                                }
                            }
                        },
                        {
                            "title": "Top Threat Types",
                            "type": "visualization",
                            "visualization": {
                                "type": "table",
                                "index": self.threats_index,
                                "query": {
                                    "bool": {
                                        "filter": [
                                            {"range": {"timestamp": {"gte": "now-24h"}}}
                                        ]
                                    }
                                },
                                "aggs": {
                                    "threat_types": {
                                        "terms": {
                                            "field": "threat_type",
                                            "size": 10
                                        }
                                    }
                                }
                            }
                        }
                    ]
                }
            }
            
            # Note: In a real implementation, you would use the Kibana API
            # to create the dashboard. This is a simplified example.
            logger.info("Kibana dashboard configuration prepared")
            
        except Exception as e:
            logger.error("Error setting up Kibana dashboards", error=str(e))
    
    async def send_threat_data(self, threat_data: Dict[str, Any]) -> bool:
        """Send threat data to Elasticsearch."""
        try:
            # Format threat data
            formatted_data = self.format_threat_data(threat_data)
            
            # Add index-specific fields
            formatted_data['@timestamp'] = formatted_data['timestamp']
            
            # Send to Elasticsearch
            response = await self.client.index(
                index=self.threats_index,
                body=formatted_data
            )
            
            logger.info(f"Sent threat data to ELK: {threat_data.get('threat_id')}")
            return True
            
        except Exception as e:
            logger.error("Error sending threat data to ELK", error=str(e))
            return False
    
    async def send_status_data(self, status_data: Dict[str, Any]) -> bool:
        """Send status data to Elasticsearch."""
        try:
            # Format status data
            formatted_data = self.format_status_data(status_data)
            
            # Add index-specific fields
            formatted_data['@timestamp'] = formatted_data['timestamp']
            
            # Send to Elasticsearch
            response = await self.client.index(
                index=self.status_index,
                body=formatted_data
            )
            
            logger.debug(f"Sent status data to ELK: {status_data.get('agent_id')}")
            return True
            
        except Exception as e:
            logger.error("Error sending status data to ELK", error=str(e))
            return False
    
    async def get_threat_intelligence(self, indicators: List[str]) -> Dict[str, Any]:
        """Get threat intelligence from Elasticsearch."""
        try:
            # Build search query
            should_clauses = []
            for indicator in indicators:
                should_clauses.append({
                    "term": {"threat_indicators": indicator}
                })
            
            query = {
                "bool": {
                    "should": should_clauses,
                    "minimum_should_match": 1
                }
            }
            
            # Search Elasticsearch
            response = await self.client.search(
                index=self.threats_index,
                body={
                    "query": query,
                    "aggs": {
                        "threat_types": {
                            "terms": {"field": "threat_type"},
                            "aggs": {
                                "max_score": {"max": {"field": "threat_score"}},
                                "count": {"value_count": {"field": "threat_id"}},
                                "latest": {"max": {"field": "timestamp"}}
                            }
                        }
                    },
                    "size": 0
                }
            )
            
            # Parse results
            intelligence = {}
            for bucket in response['aggregations']['threat_types']['buckets']:
                threat_type = bucket['key']
                intelligence[threat_type] = {
                    'max_score': bucket['max_score']['value'],
                    'occurrences': bucket['count']['value'],
                    'last_seen': bucket['latest']['value_as_string']
                }
            
            logger.info(f"Retrieved threat intelligence for {len(indicators)} indicators")
            return intelligence
            
        except Exception as e:
            logger.error("Error getting threat intelligence from ELK", error=str(e))
            return {}
    
    async def create_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Create ELK alert."""
        try:
            # Create alert document
            alert_doc = {
                'timestamp': int(time.time()),
                'alert_id': f"privik_alert_{int(time.time())}",
                'alert_type': alert_data.get('alert_type', 'threat'),
                'severity': alert_data.get('severity', 'medium'),
                'threat_data': alert_data.get('threat_data', {}),
                'status': 'active',
                'source': 'privik',
                'description': alert_data.get('description', 'Threat detected by Privik')
            }
            
            # Send to Elasticsearch
            response = await self.client.index(
                index=self.alerts_index,
                body=alert_doc
            )
            
            logger.info(f"Created ELK alert: {alert_doc['alert_id']}")
            return True
            
        except Exception as e:
            logger.error("Error creating ELK alert", error=str(e))
            return False
    
    async def get_dashboard_data(self, dashboard_name: str) -> Dict[str, Any]:
        """Get dashboard data from Elasticsearch."""
        try:
            # Get threat statistics
            threat_stats = await self.client.search(
                index=self.threats_index,
                body={
                    "query": {
                        "bool": {
                            "filter": [
                                {"range": {"timestamp": {"gte": "now-24h"}}}
                            ]
                        }
                    },
                    "aggs": {
                        "threat_types": {
                            "terms": {"field": "threat_type"},
                            "aggs": {
                                "count": {"value_count": {"field": "threat_id"}}
                            }
                        },
                        "total_threats": {"value_count": {"field": "threat_id"}},
                        "avg_score": {"avg": {"field": "threat_score"}}
                    },
                    "size": 0
                }
            )
            
            # Parse results
            dashboard_data = {
                'threat_types': [],
                'total_threats': threat_stats['aggregations']['total_threats']['value'],
                'avg_threat_score': threat_stats['aggregations']['avg_score']['value']
            }
            
            for bucket in threat_stats['aggregations']['threat_types']['buckets']:
                dashboard_data['threat_types'].append({
                    'type': bucket['key'],
                    'count': bucket['count']['value']
                })
            
            return dashboard_data
            
        except Exception as e:
            logger.error("Error getting dashboard data from ELK", error=str(e))
            return {}
    
    async def bulk_send_data(self, data_list: List[Dict[str, Any]], data_type: str = 'threat') -> bool:
        """Send multiple documents in bulk."""
        try:
            # Prepare bulk actions
            actions = []
            index_name = self.threats_index if data_type == 'threat' else self.status_index
            
            for data in data_list:
                formatted_data = self.format_threat_data(data) if data_type == 'threat' else self.format_status_data(data)
                formatted_data['@timestamp'] = formatted_data['timestamp']
                
                actions.append({
                    '_index': index_name,
                    '_source': formatted_data
                })
            
            # Send bulk data
            success, failed = await async_bulk(self.client, actions)
            
            logger.info(f"Bulk sent {success} documents to ELK, {len(failed)} failed")
            return len(failed) == 0
            
        except Exception as e:
            logger.error("Error bulk sending data to ELK", error=str(e))
            return False
    
    async def cleanup(self):
        """Cleanup ELK integration."""
        try:
            if self.client:
                await self.client.close()
                logger.info("ELK integration cleaned up")
        except Exception as e:
            logger.error("Error cleaning up ELK integration", error=str(e))
