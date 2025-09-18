"""
LDAP/Active Directory Authentication Service
Enterprise authentication with LDAP and AD integration
"""

import asyncio
import ssl
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import structlog
from ldap3 import Server, Connection, ALL, SUBTREE, Tls
from ldap3.core.exceptions import LDAPException, LDAPBindError, LDAPSocketOpenError
from ..services.cache_manager import cache_manager
from ..services.logging_service import logging_service

logger = structlog.get_logger()

class LDAPServerType(Enum):
    ACTIVE_DIRECTORY = "active_directory"
    OPENLDAP = "openldap"
    FREEIPA = "freeipa"
    GENERIC_LDAP = "generic_ldap"

class LDAPAuthService:
    """LDAP/Active Directory authentication service"""
    
    def __init__(self):
        self.active_connections = {}
        self.user_cache = {}
        self.group_cache = {}
        self.ldap_configs = {
            LDAPServerType.ACTIVE_DIRECTORY: {
                "name": "Active Directory",
                "default_attributes": ["sAMAccountName", "displayName", "mail", "memberOf", "userPrincipalName"],
                "default_search_base": "CN=Users,DC=domain,DC=com",
                "default_port": 389,
                "secure_port": 636
            },
            LDAPServerType.OPENLDAP: {
                "name": "OpenLDAP",
                "default_attributes": ["uid", "cn", "mail", "memberOf", "ou"],
                "default_search_base": "ou=people,dc=domain,dc=com",
                "default_port": 389,
                "secure_port": 636
            },
            LDAPServerType.FREEIPA: {
                "name": "FreeIPA",
                "default_attributes": ["uid", "cn", "mail", "memberOf", "krbPrincipalName"],
                "default_search_base": "cn=users,cn=accounts,dc=domain,dc=com",
                "default_port": 389,
                "secure_port": 636
            }
        }
    
    async def configure_ldap_server(
        self,
        server_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Configure LDAP server connection"""
        try:
            logger.info("Configuring LDAP server", server=server_config.get("server_name"))
            
            # Validate configuration
            validation_result = await self._validate_ldap_config(server_config)
            if not validation_result.get("valid"):
                return {"success": False, "error": validation_result.get("error")}
            
            # Test connection
            connection_test = await self._test_ldap_connection(server_config)
            if not connection_test.get("success"):
                return {"success": False, "error": connection_test.get("error")}
            
            # Store configuration
            server_id = self._generate_server_id(server_config.get("server_name"))
            self.active_connections[server_id] = {
                "config": server_config,
                "configured_at": datetime.now(),
                "status": "configured",
                "last_test": datetime.now()
            }
            
            # Cache configuration
            await cache_manager.set(
                f"ldap_server_{server_id}",
                server_config,
                ttl=86400,  # 24 hours
                namespace="ldap_servers"
            )
            
            logger.info("LDAP server configured successfully", server_id=server_id)
            
            return {
                "success": True,
                "server_id": server_id,
                "server_name": server_config.get("server_name"),
                "configured_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Error configuring LDAP server", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _validate_ldap_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate LDAP configuration"""
        try:
            required_fields = [
                "server_name", "server_host", "server_type", 
                "bind_dn", "bind_password", "user_search_base"
            ]
            
            missing_fields = [field for field in required_fields if field not in config]
            if missing_fields:
                return {
                    "valid": False,
                    "error": f"Missing required fields: {', '.join(missing_fields)}"
                }
            
            # Validate server type
            server_type = config.get("server_type")
            if server_type not in [t.value for t in LDAPServerType]:
                return {
                    "valid": False,
                    "error": f"Invalid server type: {server_type}"
                }
            
            # Validate port
            port = config.get("port", 389)
            if not isinstance(port, int) or port < 1 or port > 65535:
                return {
                    "valid": False,
                    "error": "Invalid port number"
                }
            
            return {"valid": True}
            
        except Exception as e:
            logger.error("Error validating LDAP config", error=str(e))
            return {"valid": False, "error": str(e)}
    
    async def _test_ldap_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test LDAP connection"""
        try:
            # Create server object
            server = self._create_ldap_server(config)
            
            # Create connection
            connection = Connection(
                server,
                user=config["bind_dn"],
                password=config["bind_password"],
                auto_bind=True,
                raise_exceptions=True
            )
            
            # Test search
            search_base = config["user_search_base"]
            search_filter = config.get("user_search_filter", "(objectClass=*)")
            search_scope = SUBTREE
            
            connection.search(
                search_base=search_base,
                search_filter=search_filter,
                search_scope=search_scope,
                attributes=["*"],
                size_limit=1
            )
            
            # Close connection
            connection.unbind()
            
            return {
                "success": True,
                "message": "LDAP connection test successful",
                "entries_found": len(connection.entries)
            }
            
        except LDAPBindError as e:
            logger.error("LDAP bind error", error=str(e))
            return {"success": False, "error": "Authentication failed - check bind credentials"}
        except LDAPSocketOpenError as e:
            logger.error("LDAP socket error", error=str(e))
            return {"success": False, "error": "Connection failed - check server host and port"}
        except LDAPException as e:
            logger.error("LDAP error", error=str(e))
            return {"success": False, "error": f"LDAP error: {str(e)}"}
        except Exception as e:
            logger.error("Unexpected error testing LDAP connection", error=str(e))
            return {"success": False, "error": str(e)}
    
    def _create_ldap_server(self, config: Dict[str, Any]) -> Server:
        """Create LDAP server object"""
        try:
            host = config["server_host"]
            port = config.get("port", 389)
            use_ssl = config.get("use_ssl", False)
            use_tls = config.get("use_tls", False)
            
            if use_ssl:
                # SSL connection
                server = Server(
                    host,
                    port=port,
                    use_ssl=True,
                    get_info=ALL,
                    tls=Tls(
                        validate=ssl.CERT_REQUIRED,
                        version=ssl.PROTOCOL_TLSv1_2
                    ) if config.get("verify_ssl", True) else None
                )
            elif use_tls:
                # TLS connection
                server = Server(
                    host,
                    port=port,
                    use_ssl=False,
                    get_info=ALL,
                    tls=Tls(
                        validate=ssl.CERT_REQUIRED,
                        version=ssl.PROTOCOL_TLSv1_2
                    ) if config.get("verify_ssl", True) else None
                )
            else:
                # Unencrypted connection
                server = Server(host, port=port, get_info=ALL)
            
            return server
            
        except Exception as e:
            logger.error("Error creating LDAP server", error=str(e))
            raise
    
    async def authenticate_user(
        self,
        username: str,
        password: str,
        server_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Authenticate user against LDAP"""
        try:
            logger.info("Authenticating user via LDAP", username=username, server_id=server_id)
            
            # Get LDAP server configuration
            if server_id:
                server_config = await self._get_server_config(server_id)
                if not server_config:
                    return {"success": False, "error": "LDAP server not found"}
            else:
                # Use first available server
                if not self.active_connections:
                    return {"success": False, "error": "No LDAP servers configured"}
                server_id = list(self.active_connections.keys())[0]
                server_config = self.active_connections[server_id]["config"]
            
            # Authenticate user
            auth_result = await self._perform_ldap_auth(server_config, username, password)
            
            if auth_result.get("success"):
                # Get user details
                user_details = await self._get_user_details(server_config, username)
                
                # Get user groups
                user_groups = await self._get_user_groups(server_config, username)
                
                # Cache user information
                await self._cache_user_info(username, user_details, user_groups)
                
                # Log successful authentication
                await logging_service.log_audit_event(
                    logging_service.AuditEvent(
                        event_type='ldap_authentication_success',
                        user_id=username,
                        details={
                            'server_id': server_id,
                            'user_groups': user_groups,
                            'authentication_method': 'ldap'
                        },
                        severity='low'
                    )
                )
                
                return {
                    "success": True,
                    "username": username,
                    "user_details": user_details,
                    "user_groups": user_groups,
                    "server_id": server_id
                }
            else:
                # Log failed authentication
                await logging_service.log_audit_event(
                    logging_service.AuditEvent(
                        event_type='ldap_authentication_failure',
                        user_id=username,
                        details={
                            'server_id': server_id,
                            'error': auth_result.get("error"),
                            'authentication_method': 'ldap'
                        },
                        severity='medium'
                    )
                )
                
                return auth_result
            
        except Exception as e:
            logger.error("Error authenticating user via LDAP", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def _get_server_config(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get server configuration"""
        try:
            # Try to get from active connections first
            if server_id in self.active_connections:
                return self.active_connections[server_id]["config"]
            
            # Try to get from cache
            cached_config = await cache_manager.get(f"ldap_server_{server_id}", namespace="ldap_servers")
            if cached_config:
                return cached_config
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting server config for {server_id}", error=str(e))
            return None
    
    async def _perform_ldap_auth(
        self,
        server_config: Dict[str, Any],
        username: str,
        password: str
    ) -> Dict[str, Any]:
        """Perform LDAP authentication"""
        try:
            # Create server and connection
            server = self._create_ldap_server(server_config)
            
            # Construct user DN
            user_dn = self._construct_user_dn(server_config, username)
            
            # Create connection for user authentication
            connection = Connection(
                server,
                user=user_dn,
                password=password,
                auto_bind=True,
                raise_exceptions=True
            )
            
            # Close connection after successful bind
            connection.unbind()
            
            return {"success": True, "message": "Authentication successful"}
            
        except LDAPBindError as e:
            logger.warning("LDAP authentication failed", username=username, error=str(e))
            return {"success": False, "error": "Invalid username or password"}
        except LDAPException as e:
            logger.error("LDAP error during authentication", error=str(e))
            return {"success": False, "error": f"LDAP error: {str(e)}"}
        except Exception as e:
            logger.error("Unexpected error during LDAP authentication", error=str(e))
            return {"success": False, "error": str(e)}
    
    def _construct_user_dn(self, server_config: Dict[str, Any], username: str) -> str:
        """Construct user DN for authentication"""
        try:
            server_type = LDAPServerType(server_config["server_type"])
            user_search_base = server_config["user_search_base"]
            
            if server_type == LDAPServerType.ACTIVE_DIRECTORY:
                # Active Directory: username@domain or CN=username,OU=Users,DC=domain,DC=com
                domain = server_config.get("domain")
                if domain:
                    return f"{username}@{domain}"
                else:
                    return f"CN={username},{user_search_base}"
            
            elif server_type == LDAPServerType.OPENLDAP:
                # OpenLDAP: uid=username,ou=people,dc=domain,dc=com
                return f"uid={username},{user_search_base}"
            
            elif server_type == LDAPServerType.FREEIPA:
                # FreeIPA: uid=username,cn=users,cn=accounts,dc=domain,dc=com
                return f"uid={username},{user_search_base}"
            
            else:
                # Generic LDAP
                return f"uid={username},{user_search_base}"
                
        except Exception as e:
            logger.error("Error constructing user DN", error=str(e))
            raise
    
    async def _get_user_details(
        self,
        server_config: Dict[str, Any],
        username: str
    ) -> Dict[str, Any]:
        """Get user details from LDAP"""
        try:
            server = self._create_ldap_server(server_config)
            connection = Connection(
                server,
                user=server_config["bind_dn"],
                password=server_config["bind_password"],
                auto_bind=True
            )
            
            # Construct search filter
            search_filter = self._construct_user_search_filter(server_config, username)
            search_base = server_config["user_search_base"]
            attributes = server_config.get("user_attributes", ["*"])
            
            # Search for user
            connection.search(
                search_base=search_base,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=attributes
            )
            
            if connection.entries:
                user_entry = connection.entries[0]
                user_details = {}
                
                # Extract attributes
                for attr in user_entry.entry_attributes:
                    values = user_entry[attr].values
                    if len(values) == 1:
                        user_details[attr] = values[0]
                    else:
                        user_details[attr] = values
                
                connection.unbind()
                return user_details
            else:
                connection.unbind()
                return {}
                
        except Exception as e:
            logger.error("Error getting user details from LDAP", error=str(e))
            return {}
    
    def _construct_user_search_filter(self, server_config: Dict[str, Any], username: str) -> str:
        """Construct user search filter"""
        try:
            server_type = LDAPServerType(server_config["server_type"])
            
            if server_type == LDAPServerType.ACTIVE_DIRECTORY:
                # Active Directory: (sAMAccountName=username)
                return f"(sAMAccountName={username})"
            
            elif server_type == LDAPServerType.OPENLDAP:
                # OpenLDAP: (uid=username)
                return f"(uid={username})"
            
            elif server_type == LDAPServerType.FREEIPA:
                # FreeIPA: (uid=username)
                return f"(uid={username})"
            
            else:
                # Generic LDAP
                return f"(uid={username})"
                
        except Exception as e:
            logger.error("Error constructing user search filter", error=str(e))
            raise
    
    async def _get_user_groups(
        self,
        server_config: Dict[str, Any],
        username: str
    ) -> List[str]:
        """Get user groups from LDAP"""
        try:
            server = self._create_ldap_server(server_config)
            connection = Connection(
                server,
                user=server_config["bind_dn"],
                password=server_config["bind_password"],
                auto_bind=True
            )
            
            # Search for user groups
            search_filter = self._construct_user_search_filter(server_config, username)
            search_base = server_config["user_search_base"]
            
            connection.search(
                search_base=search_base,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=["memberOf"]
            )
            
            groups = []
            if connection.entries:
                user_entry = connection.entries[0]
                if "memberOf" in user_entry.entry_attributes:
                    member_of = user_entry["memberOf"].values
                    for group_dn in member_of:
                        # Extract group name from DN
                        group_name = self._extract_group_name(group_dn)
                        if group_name:
                            groups.append(group_name)
            
            connection.unbind()
            return groups
            
        except Exception as e:
            logger.error("Error getting user groups from LDAP", error=str(e))
            return []
    
    def _extract_group_name(self, group_dn: str) -> Optional[str]:
        """Extract group name from DN"""
        try:
            # Extract CN value from DN
            # Format: CN=GroupName,OU=Groups,DC=domain,DC=com
            if group_dn.startswith("CN="):
                cn_part = group_dn.split(",")[0]
                return cn_part[3:]  # Remove "CN=" prefix
            return None
            
        except Exception as e:
            logger.error("Error extracting group name from DN", error=str(e))
            return None
    
    async def _cache_user_info(
        self,
        username: str,
        user_details: Dict[str, Any],
        user_groups: List[str]
    ):
        """Cache user information"""
        try:
            user_info = {
                "username": username,
                "user_details": user_details,
                "user_groups": user_groups,
                "cached_at": datetime.now().isoformat()
            }
            
            # Cache for 1 hour
            await cache_manager.set(
                f"ldap_user_{username}",
                user_info,
                ttl=3600,
                namespace="ldap_users"
            )
            
            # Store in memory cache as well
            self.user_cache[username] = user_info
            
        except Exception as e:
            logger.error("Error caching user info", error=str(e))
    
    async def get_cached_user_info(self, username: str) -> Optional[Dict[str, Any]]:
        """Get cached user information"""
        try:
            # Check memory cache first
            if username in self.user_cache:
                return self.user_cache[username]
            
            # Check persistent cache
            cached_info = await cache_manager.get(f"ldap_user_{username}", namespace="ldap_users")
            if cached_info:
                # Update memory cache
                self.user_cache[username] = cached_info
                return cached_info
            
            return None
            
        except Exception as e:
            logger.error("Error getting cached user info", error=str(e))
            return None
    
    async def search_users(
        self,
        search_query: str,
        server_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search users in LDAP"""
        try:
            # Get server configuration
            if server_id:
                server_config = await self._get_server_config(server_id)
                if not server_config:
                    return []
            else:
                if not self.active_connections:
                    return []
                server_id = list(self.active_connections.keys())[0]
                server_config = self.active_connections[server_id]["config"]
            
            server = self._create_ldap_server(server_config)
            connection = Connection(
                server,
                user=server_config["bind_dn"],
                password=server_config["bind_password"],
                auto_bind=True
            )
            
            # Construct search filter
            search_filter = f"(|(cn=*{search_query}*)(uid=*{search_query}*)(mail=*{search_query}*))"
            search_base = server_config["user_search_base"]
            attributes = server_config.get("user_attributes", ["cn", "uid", "mail", "displayName"])
            
            # Search for users
            connection.search(
                search_base=search_base,
                search_filter=search_filter,
                search_scope=SUBTREE,
                attributes=attributes,
                size_limit=limit
            )
            
            users = []
            for entry in connection.entries:
                user_data = {}
                for attr in entry.entry_attributes:
                    values = entry[attr].values
                    if len(values) == 1:
                        user_data[attr] = values[0]
                    else:
                        user_data[attr] = values
                users.append(user_data)
            
            connection.unbind()
            return users
            
        except Exception as e:
            logger.error("Error searching users in LDAP", error=str(e))
            return []
    
    async def get_ldap_servers(self) -> List[Dict[str, Any]]:
        """Get all configured LDAP servers"""
        try:
            servers = []
            for server_id, connection in self.active_connections.items():
                config = connection["config"]
                server_type = LDAPServerType(config["server_type"])
                
                servers.append({
                    "server_id": server_id,
                    "server_name": config["server_name"],
                    "server_type": config["server_type"],
                    "server_type_name": self.ldap_configs[server_type]["name"],
                    "server_host": config["server_host"],
                    "port": config.get("port", 389),
                    "use_ssl": config.get("use_ssl", False),
                    "use_tls": config.get("use_tls", False),
                    "status": connection["status"],
                    "configured_at": connection["configured_at"].isoformat(),
                    "last_test": connection["last_test"].isoformat()
                })
            
            return servers
            
        except Exception as e:
            logger.error("Error getting LDAP servers", error=str(e))
            return []
    
    async def test_ldap_server(self, server_id: str) -> Dict[str, Any]:
        """Test LDAP server connection"""
        try:
            if server_id not in self.active_connections:
                return {"success": False, "error": "Server not found"}
            
            connection = self.active_connections[server_id]
            config = connection["config"]
            
            # Test connection
            test_result = await self._test_ldap_connection(config)
            
            # Update last test time
            connection["last_test"] = datetime.now()
            connection["status"] = "active" if test_result.get("success") else "error"
            
            return test_result
            
        except Exception as e:
            logger.error(f"Error testing LDAP server {server_id}", error=str(e))
            return {"success": False, "error": str(e)}
    
    async def remove_ldap_server(self, server_id: str) -> Dict[str, Any]:
        """Remove LDAP server configuration"""
        try:
            if server_id not in self.active_connections:
                return {"success": False, "error": "Server not found"}
            
            # Remove from active connections
            del self.active_connections[server_id]
            
            # Remove from cache
            await cache_manager.delete(f"ldap_server_{server_id}", namespace="ldap_servers")
            
            logger.info(f"Removed LDAP server {server_id}")
            
            return {"success": True, "message": "Server removed successfully"}
            
        except Exception as e:
            logger.error(f"Error removing LDAP server {server_id}", error=str(e))
            return {"success": False, "error": str(e)}
    
    def _generate_server_id(self, server_name: str) -> str:
        """Generate unique server ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"ldap_{server_name.lower().replace(' ', '_')}_{timestamp}"

# Global LDAP authentication service instance
ldap_auth_service = LDAPAuthService()
