"""
Privik Endpoint Agent Security Module
Handles encryption, authentication, and secure communication
"""

import os
import time
import hashlib
import hmac
import base64
from typing import Dict, Any, Optional, Tuple
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import jwt
import structlog

logger = structlog.get_logger()

class SecurityManager:
    """Manages all security operations for the agent."""
    
    def __init__(self, config):
        self.config = config
        self.session_key = None
        self.session_expiry = None
        self._initialize_crypto()
    
    def _initialize_crypto(self):
        """Initialize cryptographic components."""
        try:
            # Generate or load RSA key pair
            self.private_key_path = os.path.join(
                os.path.dirname(self.config.config_path), 
                "agent_private_key.pem"
            )
            self.public_key_path = os.path.join(
                os.path.dirname(self.config.config_path), 
                "agent_public_key.pem"
            )
            
            if os.path.exists(self.private_key_path):
                self._load_keys()
            else:
                self._generate_keys()
                
            logger.info("Cryptographic components initialized")
            
        except Exception as e:
            logger.error("Failed to initialize crypto", error=str(e))
            raise
    
    def _generate_keys(self):
        """Generate new RSA key pair."""
        try:
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            
            # Save private key
            with open(self.private_key_path, 'wb') as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            # Get public key
            public_key = private_key.public_key()
            
            # Save public key
            with open(self.public_key_path, 'wb') as f:
                f.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
            
            self.private_key = private_key
            self.public_key = public_key
            
            logger.info("New RSA key pair generated")
            
        except Exception as e:
            logger.error("Failed to generate keys", error=str(e))
            raise
    
    def _load_keys(self):
        """Load existing RSA key pair."""
        try:
            # Load private key
            with open(self.private_key_path, 'rb') as f:
                private_key_data = f.read()
                self.private_key = serialization.load_pem_private_key(
                    private_key_data,
                    password=None,
                    backend=default_backend()
                )
            
            # Load public key
            with open(self.public_key_path, 'rb') as f:
                public_key_data = f.read()
                self.public_key = serialization.load_pem_public_key(
                    public_key_data,
                    backend=default_backend()
                )
            
            logger.info("Existing RSA keys loaded")
            
        except Exception as e:
            logger.error("Failed to load keys", error=str(e))
            raise
    
    def generate_jwt_token(self, payload: Dict[str, Any]) -> str:
        """Generate JWT token for authentication."""
        try:
            if not self.config.jwt_secret:
                raise ValueError("JWT secret not configured")
            
            # Add standard claims
            token_payload = {
                'iat': int(time.time()),
                'exp': int(time.time()) + 3600,  # 1 hour expiry
                'agent_id': self.config.agent_id,
                'agent_name': self.config.agent_name,
                **payload
            }
            
            token = jwt.encode(token_payload, self.config.jwt_secret, algorithm='HS256')
            logger.debug("JWT token generated", agent_id=self.config.agent_id)
            
            return token
            
        except Exception as e:
            logger.error("Failed to generate JWT token", error=str(e))
            raise
    
    def verify_jwt_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            if not self.config.jwt_secret:
                raise ValueError("JWT secret not configured")
            
            payload = jwt.decode(token, self.config.jwt_secret, algorithms=['HS256'])
            logger.debug("JWT token verified")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            raise
        except jwt.InvalidTokenError as e:
            logger.error("Invalid JWT token", error=str(e))
            raise
    
    def encrypt_data(self, data: bytes) -> Tuple[bytes, bytes]:
        """Encrypt data using AES-256-GCM."""
        try:
            # Generate random key and IV
            key = os.urandom(32)  # 256-bit key
            iv = os.urandom(12)   # 96-bit IV for GCM
            
            # Create cipher
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv), backend=default_backend())
            encryptor = cipher.encryptor()
            
            # Encrypt data
            ciphertext = encryptor.update(data) + encryptor.finalize()
            
            # Combine IV and ciphertext
            encrypted_data = iv + encryptor.tag + ciphertext
            
            return encrypted_data, key
            
        except Exception as e:
            logger.error("Failed to encrypt data", error=str(e))
            raise
    
    def decrypt_data(self, encrypted_data: bytes, key: bytes) -> bytes:
        """Decrypt data using AES-256-GCM."""
        try:
            # Extract IV, tag, and ciphertext
            iv = encrypted_data[:12]
            tag = encrypted_data[12:28]
            ciphertext = encrypted_data[28:]
            
            # Create cipher
            cipher = Cipher(algorithms.AES(key), modes.GCM(iv, tag), backend=default_backend())
            decryptor = cipher.decryptor()
            
            # Decrypt data
            plaintext = decryptor.update(ciphertext) + decryptor.finalize()
            
            return plaintext
            
        except Exception as e:
            logger.error("Failed to decrypt data", error=str(e))
            raise
    
    def sign_data(self, data: bytes) -> bytes:
        """Sign data using RSA private key."""
        try:
            signature = self.private_key.sign(
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return signature
            
        except Exception as e:
            logger.error("Failed to sign data", error=str(e))
            raise
    
    def verify_signature(self, data: bytes, signature: bytes, public_key) -> bool:
        """Verify signature using RSA public key."""
        try:
            public_key.verify(
                signature,
                data,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            
            return True
            
        except Exception as e:
            logger.error("Signature verification failed", error=str(e))
            return False
    
    def hash_file(self, file_path: str) -> str:
        """Generate SHA-256 hash of file."""
        try:
            hash_sha256 = hashlib.sha256()
            
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            
            return hash_sha256.hexdigest()
            
        except Exception as e:
            logger.error("Failed to hash file", file=file_path, error=str(e))
            raise
    
    def create_secure_headers(self, endpoint: str, method: str = "GET", body: str = "") -> Dict[str, str]:
        """Create secure headers for API requests (JWT + optional HMAC)."""
        try:
            headers = {
                'Authorization': f'Bearer {self.generate_jwt_token({"endpoint": endpoint})}',
                'X-Agent-ID': self.config.agent_id,
                'X-Agent-Name': self.config.agent_name,
                'X-Agent-Version': self.config.version,
                'Content-Type': 'application/json',
            }

            # HMAC signing to match server verify_request
            if self.config.hmac_api_key_id and self.config.hmac_api_secret:
                ts = str(int(time.time()))
                payload = f"{method.upper()}\n{endpoint}\n{ts}\n{body or ''}"
                sig = hmac.new(
                    key=self.config.hmac_api_secret.encode('utf-8'),
                    msg=payload.encode('utf-8'),
                    digestmod=hashlib.sha256
                ).hexdigest()
                headers['X-API-Key'] = self.config.hmac_api_key_id
                headers['X-Timestamp'] = ts
                headers['X-Signature'] = sig
            
            return headers
            
        except Exception as e:
            logger.error("Failed to create secure headers", error=str(e))
            raise
    
    def validate_server_certificate(self, cert_data: bytes) -> bool:
        """Validate server certificate."""
        try:
            if not self.config.certificate_verification:
                return True
            
            # Load certificate
            cert = serialization.load_pem_x509_certificate(cert_data, default_backend())
            
            # Check if certificate is valid
            if cert.not_valid_before > time.time() or cert.not_valid_after < time.time():
                logger.warning("Server certificate is not valid")
                return False
            
            # Additional validation can be added here
            # (e.g., check against trusted CA, verify hostname, etc.)
            
            logger.debug("Server certificate validated")
            return True
            
        except Exception as e:
            logger.error("Certificate validation failed", error=str(e))
            return False
    
    def generate_session_key(self) -> str:
        """Generate a new session key for secure communication."""
        try:
            # Generate random session key
            session_key = base64.b64encode(os.urandom(32)).decode('utf-8')
            self.session_key = session_key
            self.session_expiry = time.time() + 3600  # 1 hour
            
            logger.info("New session key generated")
            return session_key
            
        except Exception as e:
            logger.error("Failed to generate session key", error=str(e))
            raise
    
    def is_session_valid(self) -> bool:
        """Check if current session is still valid."""
        if not self.session_key or not self.session_expiry:
            return False
        
        return time.time() < self.session_expiry
    
    def cleanup(self):
        """Clean up sensitive data from memory."""
        try:
            # Clear session data
            self.session_key = None
            self.session_expiry = None
            
            # Clear private key from memory (if possible)
            if hasattr(self, 'private_key'):
                del self.private_key
            
            logger.info("Security manager cleaned up")
            
        except Exception as e:
            logger.error("Failed to cleanup security manager", error=str(e))
