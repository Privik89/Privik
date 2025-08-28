"""
Privik Endpoint Agent Main Class
Orchestrates all security monitoring and communication
"""

import asyncio
import time
import signal
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path
import structlog

from .config import config_manager, AgentConfig
from .security import SecurityManager
from .monitors.email_monitor import EmailMonitor
from .monitors.file_monitor import FileMonitor
from .monitors.link_monitor import LinkMonitor
from .communication import ServerCommunicator

logger = structlog.get_logger()

class PrivikAgent:
    """Main Privik endpoint agent class."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the agent."""
        self.config_path = config_path
        self.config: Optional[AgentConfig] = None
        self.security_manager: Optional[SecurityManager] = None
        self.server_communicator: Optional[ServerCommunicator] = None
        
        # Monitoring components
        self.email_monitor: Optional[EmailMonitor] = None
        self.file_monitor: Optional[FileMonitor] = None
        self.link_monitor: Optional[LinkMonitor] = None
        
        # Agent state
        self.running = False
        self.tasks: List[asyncio.Task] = []
        
        # Setup signal handlers
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info("Received shutdown signal", signal=signum)
            self.stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    async def initialize(self) -> bool:
        """Initialize the agent and all components."""
        try:
            logger.info("Initializing Privik endpoint agent...")
            
            # Load configuration
            self.config = config_manager.load_config()
            if not config_manager.validate_config():
                logger.error("Configuration validation failed")
                return False
            
            # Initialize security manager
            self.security_manager = SecurityManager(self.config)
            
            # Initialize server communicator
            self.server_communicator = ServerCommunicator(
                self.config, 
                self.security_manager
            )
            
            # Test server connection
            if not await self.server_communicator.test_connection():
                logger.error("Failed to connect to server")
                return False
            
            # Initialize monitoring components
            await self._initialize_monitors()
            
            logger.info("Agent initialized successfully", 
                       agent_id=self.config.agent_id,
                       agent_name=self.config.agent_name)
            
            return True
            
        except Exception as e:
            logger.error("Failed to initialize agent", error=str(e))
            return False
    
    async def _initialize_monitors(self):
        """Initialize all monitoring components."""
        try:
            # Initialize email monitor
            if self.config.email_clients:
                self.email_monitor = EmailMonitor(
                    self.config, 
                    self.security_manager,
                    self.server_communicator
                )
                await self.email_monitor.initialize()
                logger.info("Email monitor initialized")
            
            # Initialize file monitor
            if self.config.file_scan_enabled:
                self.file_monitor = FileMonitor(
                    self.config,
                    self.security_manager,
                    self.server_communicator
                )
                await self.file_monitor.initialize()
                logger.info("File monitor initialized")
            
            # Initialize link monitor
            if self.config.browser_monitoring:
                self.link_monitor = LinkMonitor(
                    self.config,
                    self.security_manager,
                    self.server_communicator
                )
                await self.link_monitor.initialize()
                logger.info("Link monitor initialized")
            
        except Exception as e:
            logger.error("Failed to initialize monitors", error=str(e))
            raise
    
    async def start(self) -> bool:
        """Start the agent and all monitoring."""
        try:
            if not await self.initialize():
                return False
            
            logger.info("Starting Privik endpoint agent...")
            self.running = True
            
            # Start monitoring tasks
            await self._start_monitoring_tasks()
            
            # Start heartbeat task
            heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            self.tasks.append(heartbeat_task)
            
            # Start status reporting task
            status_task = asyncio.create_task(self._status_reporting_loop())
            self.tasks.append(status_task)
            
            logger.info("Agent started successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to start agent", error=str(e))
            return False
    
    async def _start_monitoring_tasks(self):
        """Start all monitoring tasks."""
        try:
            # Start email monitoring
            if self.email_monitor:
                email_task = asyncio.create_task(self.email_monitor.start_monitoring())
                self.tasks.append(email_task)
                logger.info("Email monitoring started")
            
            # Start file monitoring
            if self.file_monitor:
                file_task = asyncio.create_task(self.file_monitor.start_monitoring())
                self.tasks.append(file_task)
                logger.info("File monitoring started")
            
            # Start link monitoring
            if self.link_monitor:
                link_task = asyncio.create_task(self.link_monitor.start_monitoring())
                self.tasks.append(link_task)
                logger.info("Link monitoring started")
            
        except Exception as e:
            logger.error("Failed to start monitoring tasks", error=str(e))
            raise
    
    async def _heartbeat_loop(self):
        """Send periodic heartbeat to server."""
        while self.running:
            try:
                await self.server_communicator.send_heartbeat()
                await asyncio.sleep(60)  # Send heartbeat every minute
            except Exception as e:
                logger.error("Failed to send heartbeat", error=str(e))
                await asyncio.sleep(30)  # Retry sooner on error
    
    async def _status_reporting_loop(self):
        """Send periodic status reports to server."""
        while self.running:
            try:
                status = await self._collect_status()
                await self.server_communicator.send_status_report(status)
                await asyncio.sleep(300)  # Send status every 5 minutes
            except Exception as e:
                logger.error("Failed to send status report", error=str(e))
                await asyncio.sleep(60)  # Retry sooner on error
    
    async def _collect_status(self) -> Dict[str, Any]:
        """Collect current agent status."""
        try:
            status = {
                'agent_id': self.config.agent_id,
                'agent_name': self.config.agent_name,
                'version': self.config.version,
                'timestamp': int(time.time()),
                'running': self.running,
                'monitors': {}
            }
            
            # Add monitor status
            if self.email_monitor:
                status['monitors']['email'] = await self.email_monitor.get_status()
            
            if self.file_monitor:
                status['monitors']['file'] = await self.file_monitor.get_status()
            
            if self.link_monitor:
                status['monitors']['link'] = await self.link_monitor.get_status()
            
            return status
            
        except Exception as e:
            logger.error("Failed to collect status", error=str(e))
            return {'error': str(e)}
    
    def stop(self):
        """Stop the agent and cleanup."""
        try:
            logger.info("Stopping Privik endpoint agent...")
            self.running = False
            
            # Cancel all tasks
            for task in self.tasks:
                if not task.done():
                    task.cancel()
            
            # Stop monitors
            if self.email_monitor:
                asyncio.create_task(self.email_monitor.stop())
            
            if self.file_monitor:
                asyncio.create_task(self.file_monitor.stop())
            
            if self.link_monitor:
                asyncio.create_task(self.link_monitor.stop())
            
            # Cleanup security manager
            if self.security_manager:
                self.security_manager.cleanup()
            
            logger.info("Agent stopped successfully")
            
        except Exception as e:
            logger.error("Error during agent shutdown", error=str(e))
    
    async def run(self):
        """Main run loop for the agent."""
        try:
            if not await self.start():
                logger.error("Failed to start agent")
                return False
            
            logger.info("Agent running. Press Ctrl+C to stop.")
            
            # Keep the agent running
            while self.running:
                await asyncio.sleep(1)
            
            return True
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt")
            self.stop()
            return True
        except Exception as e:
            logger.error("Agent run error", error=str(e))
            self.stop()
            return False
    
    async def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information."""
        return {
            'agent_id': self.config.agent_id,
            'agent_name': self.config.agent_name,
            'version': self.config.version,
            'server_url': self.config.server_url,
            'running': self.running,
            'monitors_active': {
                'email': self.email_monitor is not None,
                'file': self.file_monitor is not None,
                'link': self.link_monitor is not None,
            }
        }
    
    async def update_config(self, updates: Dict[str, Any]) -> bool:
        """Update agent configuration."""
        try:
            config_manager.update_config(updates)
            
            # Reload configuration
            self.config = config_manager.load_config()
            
            # Update components with new config
            if self.server_communicator:
                self.server_communicator.update_config(self.config)
            
            logger.info("Configuration updated successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to update configuration", error=str(e))
            return False

async def main():
    """Main entry point for the agent."""
    # Setup logging
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Create and run agent
    agent = PrivikAgent()
    
    try:
        success = await agent.run()
        return 0 if success else 1
    except Exception as e:
        logger.error("Fatal error in main", error=str(e))
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
