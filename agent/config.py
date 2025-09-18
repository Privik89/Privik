"""
Privik Endpoint Agent Configuration
Handles all agent settings, security, and cross-platform compatibility
"""

import os
import platform
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()

@dataclass
class AgentConfig:
    """Central configuration for the Privik endpoint agent."""
    
    # Agent identity
    agent_id: str
    agent_name: str
    version: str = "1.0.0"
    
    # Server connection
    server_url: str = "http://localhost:8000"
    server_api_key: Optional[str] = None
    server_cert_path: Optional[str] = None
    # HMAC auth
    hmac_api_key_id: Optional[str] = None
    hmac_api_secret: Optional[str] = None
    
    # Security settings
    encryption_enabled: bool = True
    certificate_verification: bool = True
    jwt_secret: Optional[str] = None
    
    # Email monitoring
    email_clients: list = None
    email_scan_interval: int = 30  # seconds
    attachment_scan_enabled: bool = True
    
    # Link monitoring
    browser_monitoring: bool = True
    link_rewrite_enabled: bool = True
    safe_browsing_enabled: bool = True
    
    # File monitoring
    file_watch_directories: list = None
    file_scan_enabled: bool = True
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    # Performance
    max_concurrent_scans: int = 5
    cache_size: int = 1000
    cache_ttl: int = 3600  # 1 hour
    
    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.email_clients is None:
            self.email_clients = self._get_default_email_clients()
        
        if self.file_watch_directories is None:
            self.file_watch_directories = self._get_default_watch_directories()
    
    def _get_default_email_clients(self) -> list:
        """Get default email client paths based on platform."""
        system = platform.system().lower()
        
        if system == "windows":
            return [
                os.path.expanduser("~/AppData/Local/Microsoft/Outlook"),
                os.path.expanduser("~/AppData/Roaming/Thunderbird"),
                os.path.expanduser("~/AppData/Local/Google/Chrome/User Data/Default"),
            ]
        elif system == "darwin":  # macOS
            return [
                os.path.expanduser("~/Library/Mail"),
                os.path.expanduser("~/Library/Thunderbird"),
                os.path.expanduser("~/Library/Application Support/Google/Chrome/Default"),
            ]
        else:  # Linux
            return [
                os.path.expanduser("~/.thunderbird"),
                os.path.expanduser("~/.mozilla"),
                os.path.expanduser("~/.config/google-chrome/Default"),
            ]
    
    def _get_default_watch_directories(self) -> list:
        """Get default file watch directories based on platform."""
        system = platform.system().lower()
        
        if system == "windows":
            return [
                os.path.expanduser("~/Downloads"),
                os.path.expanduser("~/Desktop"),
                os.path.expanduser("~/Documents"),
            ]
        elif system == "darwin":  # macOS
            return [
                os.path.expanduser("~/Downloads"),
                os.path.expanduser("~/Desktop"),
                os.path.expanduser("~/Documents"),
            ]
        else:  # Linux
            return [
                os.path.expanduser("~/Downloads"),
                os.path.expanduser("~/Desktop"),
                os.path.expanduser("~/Documents"),
            ]

class ConfigManager:
    """Manages agent configuration loading, saving, and validation."""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._get_default_config_path()
        self.config: Optional[AgentConfig] = None
    
    def _get_default_config_path(self) -> str:
        """Get default configuration file path based on platform."""
        system = platform.system().lower()
        
        if system == "windows":
            config_dir = os.path.expanduser("~/AppData/Local/Privik")
        elif system == "darwin":  # macOS
            config_dir = os.path.expanduser("~/Library/Application Support/Privik")
        else:  # Linux
            config_dir = os.path.expanduser("~/.config/privik")
        
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "agent_config.json")
    
    def load_config(self) -> AgentConfig:
        """Load configuration from file or create default."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                
                # Create config object from loaded data
                self.config = AgentConfig(**config_data)
                logger.info("Configuration loaded from file", path=self.config_path)
                
            except Exception as e:
                logger.warning("Failed to load config, using defaults", error=str(e))
                self.config = self._create_default_config()
        else:
            logger.info("No config file found, creating default")
            self.config = self._create_default_config()
            self.save_config()
        
        return self.config
    
    def _create_default_config(self) -> AgentConfig:
        """Create default configuration."""
        import uuid
        
        return AgentConfig(
            agent_id=str(uuid.uuid4()),
            agent_name=f"privik-agent-{platform.node()}",
            server_url=os.getenv("PRIVIK_SERVER_URL", "http://localhost:8000"),
            server_api_key=os.getenv("PRIVIK_API_KEY"),
            hmac_api_key_id=os.getenv("PRIVIK_HMAC_API_KEY_ID", "privik-agent"),
            hmac_api_secret=os.getenv("PRIVIK_HMAC_API_SECRET"),
            jwt_secret=os.getenv("PRIVIK_JWT_SECRET"),
            log_level=os.getenv("PRIVIK_LOG_LEVEL", "INFO"),
        )
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        if self.config is None:
            raise ValueError("No configuration loaded")
        
        try:
            config_data = {
                'agent_id': self.config.agent_id,
                'agent_name': self.config.agent_name,
                'version': self.config.version,
                'server_url': self.config.server_url,
                'server_api_key': self.config.server_api_key,
                'server_cert_path': self.config.server_cert_path,
                'hmac_api_key_id': self.config.hmac_api_key_id,
                'hmac_api_secret': self.config.hmac_api_secret,
                'encryption_enabled': self.config.encryption_enabled,
                'certificate_verification': self.config.certificate_verification,
                'jwt_secret': self.config.jwt_secret,
                'email_clients': self.config.email_clients,
                'email_scan_interval': self.config.email_scan_interval,
                'attachment_scan_enabled': self.config.attachment_scan_enabled,
                'browser_monitoring': self.config.browser_monitoring,
                'link_rewrite_enabled': self.config.link_rewrite_enabled,
                'safe_browsing_enabled': self.config.safe_browsing_enabled,
                'file_watch_directories': self.config.file_watch_directories,
                'file_scan_enabled': self.config.file_scan_enabled,
                'max_file_size': self.config.max_file_size,
                'log_level': self.config.log_level,
                'log_file': self.config.log_file,
                'max_concurrent_scans': self.config.max_concurrent_scans,
                'cache_size': self.config.cache_size,
                'cache_ttl': self.config.cache_ttl,
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            logger.info("Configuration saved", path=self.config_path)
            
        except Exception as e:
            logger.error("Failed to save configuration", error=str(e))
            raise
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        if self.config is None:
            self.load_config()
        
        for key, value in updates.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                logger.warning("Unknown config key", key=key)
        
        self.save_config()
    
    def validate_config(self) -> bool:
        """Validate current configuration."""
        if self.config is None:
            return False
        
        # Check required fields
        required_fields = ['agent_id', 'agent_name', 'server_url']
        for field in required_fields:
            if not getattr(self.config, field):
                logger.error("Missing required config field", field=field)
                return False
        
        # Validate server URL
        if not self.config.server_url.startswith(('http://', 'https://')):
            logger.error("Invalid server URL", url=self.config.server_url)
            return False
        
        logger.info("Configuration validation passed")
        return True

# Global config manager instance
config_manager = ConfigManager()
