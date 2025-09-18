"""
Privik Endpoint Agent Communication Module
Handles all communication with the Privik server
"""

import asyncio
import time
import json
import base64
from typing import Dict, Any, Optional, List
import aiohttp
import httpx
import structlog
import os

from .config import AgentConfig
from .security import SecurityManager

logger = structlog.get_logger()

class ServerCommunicator:
    """Handles all communication with the Privik server."""
    
    def __init__(self, config: AgentConfig, security_manager: SecurityManager):
        """Initialize the server communicator."""
        self.config = config
        self.security_manager = security_manager
        self.session: Optional[aiohttp.ClientSession] = None
        self.last_heartbeat = 0
        self.connection_retries = 0
        self.max_retries = 5
    
    async def initialize(self) -> bool:
        """Initialize the communication session."""
        try:
            # Create aiohttp session with custom settings
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                ttl_dns_cache=300,
                use_dns_cache=True,
            )
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={
                    'User-Agent': f'PrivikAgent/{self.config.version}',
                }
            )
            
            logger.info("Server communicator initialized")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize server communicator", error=str(e))
            return False
    
    async def test_connection(self) -> bool:
        """Test connection to the server."""
        try:
            # Prefer an authenticated endpoint for smoke: email-gateway status
            url = f"{self.config.server_url}/api/email-gateway/status"
            headers = self.security_manager.create_secure_headers("/api/email-gateway/status", method="GET", body="")
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("Server connection test successful", 
                               server_url=self.config.server_url,
                               details=data)
                    return True
                else:
                    logger.error("Server connection test failed", 
                                status=response.status,
                                response=await response.text())
                    return False
                    
        except Exception as e:
            logger.error("Server connection test error", error=str(e))
            return False
    
    async def send_heartbeat(self) -> bool:
        """Send heartbeat to server."""
        try:
            url = f"{self.config.server_url}/api/agent/heartbeat"
            payload = {
                'agent_id': self.config.agent_id,
                'agent_name': self.config.agent_name,
                'timestamp': int(time.time()),
                'version': self.config.version,
            }
            headers = self.security_manager.create_secure_headers("/api/agent/heartbeat", method="POST", body=json.dumps(payload))
            
            async with self.session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    self.last_heartbeat = time.time()
                    self.connection_retries = 0
                    logger.debug("Heartbeat sent successfully")
                    return True
                else:
                    logger.warning("Heartbeat failed", status=response.status)
                    return False
                    
        except Exception as e:
            logger.error("Heartbeat error", error=str(e))
            self.connection_retries += 1
            return False
    
    async def send_status_report(self, status: Dict[str, Any]) -> bool:
        """Send status report to server."""
        try:
            url = f"{self.config.server_url}/api/agent/status"
            headers = self.security_manager.create_secure_headers("/api/agent/status", method="POST", body=json.dumps(status))
            
            async with self.session.post(url, headers=headers, json=status) as response:
                if response.status == 200:
                    logger.debug("Status report sent successfully")
                    return True
                else:
                    logger.warning("Status report failed", status=response.status)
                    return False
                    
        except Exception as e:
            logger.error("Status report error", error=str(e))
            return False
    
    async def send_email_analysis(self, email_data: Dict[str, Any]) -> bool:
        """Send email analysis to server."""
        try:
            url = f"{self.config.server_url}/api/ingest/email"
            headers = self.security_manager.create_secure_headers("/api/ingest/email", method="POST", body=json.dumps(email_data))
            
            # Add agent information
            email_data['agent_id'] = self.config.agent_id
            email_data['agent_name'] = self.config.agent_name
            email_data['timestamp'] = int(time.time())
            
            async with self.session.post(url, headers=headers, json=email_data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info("Email analysis sent successfully", 
                               email_id=result.get('email_id'))
                    return True
                else:
                    logger.warning("Email analysis failed", status=response.status)
                    return False
                    
        except Exception as e:
            logger.error("Email analysis error", error=str(e))
            return False
    
    async def send_file_analysis(self, file_data: Dict[str, Any]) -> bool:
        """Send file analysis to server."""
        try:
            url = f"{self.config.server_url}/api/ingest/attachment"
            headers = self.security_manager.create_secure_headers("/api/ingest/attachment", method="POST", body=json.dumps(file_data))
            
            # Add agent information
            file_data['agent_id'] = self.config.agent_id
            file_data['agent_name'] = self.config.agent_name
            file_data['timestamp'] = int(time.time())
            
            async with self.session.post(url, headers=headers, json=file_data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info("File analysis sent successfully", 
                               file_id=result.get('file_id'))
                    return True
                else:
                    logger.warning("File analysis failed", status=response.status)
                    return False
                    
        except Exception as e:
            logger.error("File analysis error", error=str(e))
            return False
    
    async def send_link_analysis(self, link_data: Dict[str, Any]) -> bool:
        """Send link analysis to server."""
        try:
            url = f"{self.config.server_url}/api/click/analyze"
            headers = self.security_manager.create_secure_headers("/api/click/analyze", method="POST", body=json.dumps(link_data))
            
            # Add agent information
            link_data['agent_id'] = self.config.agent_id
            link_data['agent_name'] = self.config.agent_name
            link_data['timestamp'] = int(time.time())
            
            async with self.session.post(url, headers=headers, json=link_data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info("Link analysis sent successfully", 
                               analysis_id=result.get('analysis_id'))
                    return True
                else:
                    logger.warning("Link analysis failed", status=response.status)
                    return False
                    
        except Exception as e:
            logger.error("Link analysis error", error=str(e))
            return False
    
    async def get_threat_intelligence(self, indicators: List[str]) -> Optional[Dict[str, Any]]:
        """Get threat intelligence from server."""
        try:
            url = f"{self.config.server_url}/api/threat/intel"
            headers = self.security_manager.create_secure_headers("/api/threat/intel", method="POST", body=json.dumps(payload))
            
            payload = {
                'indicators': indicators,
                'agent_id': self.config.agent_id,
            }
            
            async with self.session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.debug("Threat intelligence retrieved", 
                                indicators_count=len(indicators))
                    return data
                else:
                    logger.warning("Threat intelligence request failed", status=response.status)
                    return None
                    
        except Exception as e:
            logger.error("Threat intelligence error", error=str(e))
            return None
    
    async def get_agent_config(self) -> Optional[Dict[str, Any]]:
        """Get updated configuration from server."""
        try:
            url = f"{self.config.server_url}/api/agent/config"
            headers = self.security_manager.create_secure_headers("/api/agent/config", method="GET", body="")
            
            params = {
                'agent_id': self.config.agent_id,
            }
            
            async with self.session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("Agent configuration retrieved from server")
                    return data
                else:
                    logger.warning("Configuration request failed", status=response.status)
                    return None
                    
        except Exception as e:
            logger.error("Configuration request error", error=str(e))
            return None
    
    async def upload_file(self, file_path: str, file_type: str) -> Optional[str]:
        """Upload file to server for analysis."""
        try:
            url = f"{self.config.server_url}/api/upload/file"
            headers = self.security_manager.create_secure_headers("/api/upload/file", method="POST", body="")
            
            # Remove content-type header for multipart upload
            headers.pop('Content-Type', None)
            
            # Prepare multipart data
            data = aiohttp.FormData()
            data.add_field('file',
                          open(file_path, 'rb'),
                          filename=os.path.basename(file_path),
                          content_type='application/octet-stream')
            data.add_field('file_type', file_type)
            data.add_field('agent_id', self.config.agent_id)
            data.add_field('agent_name', self.config.agent_name)
            
            async with self.session.post(url, headers=headers, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    file_id = result.get('file_id')
                    logger.info("File uploaded successfully", file_id=file_id)
                    return file_id
                else:
                    logger.warning("File upload failed", status=response.status)
                    return None
                    
        except Exception as e:
            logger.error("File upload error", error=str(e))
            return None
    
    async def get_rewritten_url(self, original_url: str) -> Optional[str]:
        """Get rewritten URL from server."""
        try:
            url = f"{self.config.server_url}/api/click/rewrite"
            headers = self.security_manager.create_secure_headers("/api/click/rewrite", method="POST", body=json.dumps(payload))
            
            payload = {
                'original_url': original_url,
                'agent_id': self.config.agent_id,
                'user_agent': 'PrivikAgent',
            }
            
            async with self.session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    rewritten_url = result.get('rewritten_url')
                    logger.debug("URL rewritten successfully", 
                                original=original_url,
                                rewritten=rewritten_url)
                    return rewritten_url
                else:
                    logger.warning("URL rewrite failed", status=response.status)
                    return None
                    
        except Exception as e:
            logger.error("URL rewrite error", error=str(e))
            return None
    
    async def report_threat(self, threat_data: Dict[str, Any]) -> bool:
        """Report threat to server."""
        try:
            url = f"{self.config.server_url}/api/threat/report"
            headers = self.security_manager.create_secure_headers("/api/threat/report", method="POST", body=json.dumps(threat_data))
            
            # Add agent information
            threat_data['agent_id'] = self.config.agent_id
            threat_data['agent_name'] = self.config.agent_name
            threat_data['timestamp'] = int(time.time())
            
            async with self.session.post(url, headers=headers, json=threat_data) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info("Threat reported successfully", 
                               threat_id=result.get('threat_id'))
                    return True
                else:
                    logger.warning("Threat report failed", status=response.status)
                    return False
                    
        except Exception as e:
            logger.error("Threat report error", error=str(e))
            return False
    
    def update_config(self, config: AgentConfig):
        """Update configuration."""
        self.config = config
    
    async def cleanup(self):
        """Cleanup resources."""
        try:
            if self.session:
                await self.session.close()
                logger.info("Server communicator cleaned up")
        except Exception as e:
            logger.error("Error during communicator cleanup", error=str(e))
