"""
Attachment Validator Service
Comprehensive attachment validation and security analysis
"""

import os
import hashlib
import structlog
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum
import mimetypes
import zipfile
import tarfile
from datetime import datetime
import re
import base64
import io

logger = structlog.get_logger()


class AttachmentRisk(Enum):
    """Attachment risk levels"""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AttachmentType(Enum):
    """Attachment types"""
    DOCUMENT = "document"
    IMAGE = "image"
    ARCHIVE = "archive"
    EXECUTABLE = "executable"
    SCRIPT = "script"
    UNKNOWN = "unknown"


class ThreatType(Enum):
    """Threat types"""
    MALWARE = "malware"
    PHISHING = "phishing"
    EXPLOIT = "exploit"
    MACRO_VIRUS = "macro_virus"
    SCRIPT_MALWARE = "script_malware"
    ARCHIVE_BOMB = "archive_bomb"
    DOUBLE_EXTENSION = "double_extension"
    ENCRYPTED = "encrypted"
    SUSPICIOUS_CONTENT = "suspicious_content"


@dataclass
class AttachmentValidation:
    """Attachment validation result"""
    filename: str
    file_size: int
    mime_type: str
    detected_type: AttachmentType
    risk_level: AttachmentRisk
    threat_types: List[ThreatType]
    indicators: List[str]
    is_safe: bool
    validation_time: float
    metadata: Dict[str, Any]


class AttachmentValidator:
    """Service for comprehensive attachment validation and security analysis"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_file_size = config.get('max_file_size', 50 * 1024 * 1024)  # 50MB
        self.max_archive_size = config.get('max_archive_size', 100 * 1024 * 1024)  # 100MB
        self.max_archive_files = config.get('max_archive_files', 1000)
        self.max_archive_depth = config.get('max_archive_depth', 10)
        
        # Dangerous file extensions
        self.dangerous_extensions = {
            '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
            '.jar', '.msi', '.dmg', '.app', '.deb', '.rpm', '.sh', '.ps1',
            '.py', '.pl', '.rb', '.php', '.asp', '.jsp', '.war', '.ear'
        }
        
        # Suspicious file extensions
        self.suspicious_extensions = {
            '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf',
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'
        }
        
        # Safe file extensions
        self.safe_extensions = {
            '.txt', '.csv', '.json', '.xml', '.html', '.css', '.js',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg',
            '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac'
        }
        
        # Dangerous MIME types
        self.dangerous_mime_types = {
            'application/x-executable',
            'application/x-msdownload',
            'application/x-msdos-program',
            'application/x-winexe',
            'application/x-msi',
            'application/x-java-archive',
            'application/x-sh',
            'application/x-powershell'
        }
        
        # Suspicious MIME types
        self.suspicious_mime_types = {
            'application/msword',
            'application/vnd.ms-excel',
            'application/vnd.ms-powerpoint',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'application/vnd.openxmlformats-officedocument.presentationml.presentation',
            'application/pdf',
            'application/zip',
            'application/x-rar-compressed',
            'application/x-7z-compressed'
        }
        
        # Macro signatures
        self.macro_signatures = [
            b'VBA',
            b'Macro',
            b'Sub ',
            b'Function ',
            b'Dim ',
            b'Set ',
            b'CreateObject',
            b'Shell',
            b'Run',
            b'Execute'
        ]
        
        # Suspicious content patterns
        self.suspicious_patterns = [
            b'powershell',
            b'cmd.exe',
            b'regsvr32',
            b'rundll32',
            b'wscript',
            b'cscript',
            b'eval(',
            b'exec(',
            b'system(',
            b'shell_exec'
        ]
    
    async def validate_attachment(
        self, 
        filename: str, 
        file_content: bytes, 
        mime_type: str = None
    ) -> AttachmentValidation:
        """
        Validate attachment for security threats
        
        Args:
            filename: Original filename
            file_content: File content as bytes
            mime_type: MIME type (if known)
            
        Returns:
            AttachmentValidation with comprehensive results
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Validating attachment: {filename}")
            
            # Basic file information
            file_size = len(file_content)
            file_extension = os.path.splitext(filename)[1].lower()
            
            # Detect MIME type if not provided
            if not mime_type:
                mime_type = self._detect_mime_type(file_content, filename)
            
            # Determine attachment type
            detected_type = self._determine_attachment_type(file_extension, mime_type)
            
            # Run validation checks
            risk_level, threat_types, indicators, metadata = await self._run_validation_checks(
                filename, file_content, file_extension, mime_type, detected_type
            )
            
            # Determine if file is safe
            is_safe = risk_level in [AttachmentRisk.SAFE, AttachmentRisk.LOW]
            
            validation_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = AttachmentValidation(
                filename=filename,
                file_size=file_size,
                mime_type=mime_type,
                detected_type=detected_type,
                risk_level=risk_level,
                threat_types=threat_types,
                indicators=indicators,
                is_safe=is_safe,
                validation_time=validation_time,
                metadata=metadata
            )
            
            logger.info(f"Attachment validation complete: {filename} - {risk_level.value}")
            return result
            
        except Exception as e:
            logger.error(f"Error validating attachment {filename}: {e}")
            return AttachmentValidation(
                filename=filename,
                file_size=len(file_content) if file_content else 0,
                mime_type=mime_type or "unknown",
                detected_type=AttachmentType.UNKNOWN,
                risk_level=AttachmentRisk.CRITICAL,
                threat_types=[ThreatType.SUSPICIOUS_CONTENT],
                indicators=[f"Validation error: {str(e)}"],
                is_safe=False,
                validation_time=(datetime.utcnow() - start_time).total_seconds(),
                metadata={"error": str(e)}
            )
    
    def _detect_mime_type(self, file_content: bytes, filename: str) -> str:
        """Detect MIME type from file content"""
        try:
            # Try python-magic if available
            try:
                import magic
                mime_type = magic.from_buffer(file_content, mime=True)
                if mime_type:
                    return mime_type
            except (ImportError, Exception):
                pass
            
            # Fallback to mimetypes
            mime_type, _ = mimetypes.guess_type(filename)
            if mime_type:
                return mime_type
            
            # Check file signature
            return self._detect_mime_type_by_signature(file_content)
            
        except Exception as e:
            logger.error(f"Error detecting MIME type: {e}")
            return "application/octet-stream"
    
    def _detect_mime_type_by_signature(self, file_content: bytes) -> str:
        """Detect MIME type by file signature"""
        if not file_content:
            return "application/octet-stream"
        
        # Common file signatures
        signatures = {
            b'\x50\x4B\x03\x04': 'application/zip',
            b'\x50\x4B\x05\x06': 'application/zip',
            b'\x50\x4B\x07\x08': 'application/zip',
            b'\x52\x61\x72\x21': 'application/x-rar-compressed',
            b'\x7F\x45\x4C\x46': 'application/x-executable',
            b'\x4D\x5A': 'application/x-msdownload',
            b'\x25\x50\x44\x46': 'application/pdf',
            b'\xD0\xCF\x11\xE0': 'application/msword',
            b'\xFF\xD8\xFF': 'image/jpeg',
            b'\x89\x50\x4E\x47': 'image/png',
            b'\x47\x49\x46\x38': 'image/gif',
            b'\x42\x4D': 'image/bmp',
            b'\x49\x44\x33': 'audio/mpeg',
            b'\xFF\xFB': 'audio/mpeg',
            b'\x00\x00\x00\x20': 'video/mp4',
            b'\x00\x00\x00\x18': 'video/mp4'
        }
        
        for signature, mime_type in signatures.items():
            if file_content.startswith(signature):
                return mime_type
        
        return "application/octet-stream"
    
    def _determine_attachment_type(self, file_extension: str, mime_type: str) -> AttachmentType:
        """Determine attachment type"""
        # Check for executables
        if file_extension in self.dangerous_extensions or mime_type in self.dangerous_mime_types:
            return AttachmentType.EXECUTABLE
        
        # Check for scripts
        script_extensions = {'.js', '.vbs', '.ps1', '.py', '.pl', '.rb', '.php', '.asp', '.jsp'}
        if file_extension in script_extensions:
            return AttachmentType.SCRIPT
        
        # Check for archives
        archive_extensions = {'.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz'}
        archive_mime_types = {'application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed'}
        if file_extension in archive_extensions or mime_type in archive_mime_types:
            return AttachmentType.ARCHIVE
        
        # Check for images
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.svg'}
        image_mime_types = {'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/tiff', 'image/svg+xml'}
        if file_extension in image_extensions or mime_type in image_mime_types:
            return AttachmentType.IMAGE
        
        # Check for documents
        doc_extensions = {'.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.pdf', '.txt', '.csv'}
        doc_mime_types = {'application/msword', 'application/vnd.ms-excel', 'application/vnd.ms-powerpoint', 'application/pdf', 'text/plain'}
        if file_extension in doc_extensions or mime_type in doc_mime_types:
            return AttachmentType.DOCUMENT
        
        return AttachmentType.UNKNOWN
    
    async def _run_validation_checks(
        self, 
        filename: str, 
        file_content: bytes, 
        file_extension: str, 
        mime_type: str, 
        detected_type: AttachmentType
    ) -> Tuple[AttachmentRisk, List[ThreatType], List[str], Dict[str, Any]]:
        """Run comprehensive validation checks"""
        threat_types = []
        indicators = []
        metadata = {}
        risk_level = AttachmentRisk.SAFE
        
        # Check file size
        if len(file_content) > self.max_file_size:
            threat_types.append(ThreatType.SUSPICIOUS_CONTENT)
            indicators.append(f"File size exceeds limit: {len(file_content)} bytes")
            risk_level = AttachmentRisk.HIGH
        
        # Check file extension
        if file_extension in self.dangerous_extensions:
            threat_types.append(ThreatType.MALWARE)
            indicators.append(f"Dangerous file extension: {file_extension}")
            risk_level = AttachmentRisk.CRITICAL
        
        # Check MIME type
        if mime_type in self.dangerous_mime_types:
            threat_types.append(ThreatType.MALWARE)
            indicators.append(f"Dangerous MIME type: {mime_type}")
            risk_level = AttachmentRisk.CRITICAL
        
        # Check for double extension
        if self._has_double_extension(filename):
            threat_types.append(ThreatType.DOUBLE_EXTENSION)
            indicators.append("Double file extension detected")
            risk_level = AttachmentRisk.HIGH
        
        # Check for suspicious content
        suspicious_content = self._check_suspicious_content(file_content)
        if suspicious_content:
            threat_types.append(ThreatType.SUSPICIOUS_CONTENT)
            indicators.extend(suspicious_content)
            risk_level = max(risk_level, AttachmentRisk.MEDIUM)
        
        # Check for macros in documents
        if detected_type == AttachmentType.DOCUMENT:
            macro_indicators = self._check_for_macros(file_content)
            if macro_indicators:
                threat_types.append(ThreatType.MACRO_VIRUS)
                indicators.extend(macro_indicators)
                risk_level = max(risk_level, AttachmentRisk.HIGH)
        
        # Check archives
        if detected_type == AttachmentType.ARCHIVE:
            archive_indicators = await self._check_archive(file_content, filename)
            if archive_indicators:
                threat_types.append(ThreatType.ARCHIVE_BOMB)
                indicators.extend(archive_indicators)
                risk_level = max(risk_level, AttachmentRisk.HIGH)
        
        # Check for encryption
        if self._is_encrypted(file_content):
            threat_types.append(ThreatType.ENCRYPTED)
            indicators.append("File appears to be encrypted")
            risk_level = max(risk_level, AttachmentRisk.MEDIUM)
        
        # Calculate file hash
        file_hash = hashlib.sha256(file_content).hexdigest()
        metadata['file_hash'] = file_hash
        
        return risk_level, threat_types, indicators, metadata
    
    def _has_double_extension(self, filename: str) -> bool:
        """Check for double file extension"""
        try:
            # Remove the last extension
            name_without_ext = os.path.splitext(filename)[0]
            # Check if there's another extension
            second_ext = os.path.splitext(name_without_ext)[1]
            return bool(second_ext)
        except Exception:
            return False
    
    def _check_suspicious_content(self, file_content: bytes) -> List[str]:
        """Check for suspicious content patterns"""
        indicators = []
        
        try:
            # Convert to lowercase for pattern matching
            content_lower = file_content.lower()
            
            for pattern in self.suspicious_patterns:
                if pattern in content_lower:
                    indicators.append(f"Suspicious content pattern: {pattern.decode()}")
            
            # Check for high entropy (random-looking content)
            if self._has_high_entropy(file_content):
                indicators.append("High entropy content detected")
            
            # Check for embedded URLs
            url_pattern = rb'https?://[^\s<>"\']+'
            urls = re.findall(url_pattern, file_content)
            if len(urls) > 10:  # Many URLs
                indicators.append(f"Many embedded URLs: {len(urls)}")
            
        except Exception as e:
            logger.error(f"Error checking suspicious content: {e}")
        
        return indicators
    
    def _check_for_macros(self, file_content: bytes) -> List[str]:
        """Check for macro content in documents"""
        indicators = []
        
        try:
            for signature in self.macro_signatures:
                if signature in file_content:
                    indicators.append(f"Macro signature detected: {signature.decode()}")
            
            # Check for VBA project
            if b'VBA' in file_content and b'Project' in file_content:
                indicators.append("VBA project detected")
            
        except Exception as e:
            logger.error(f"Error checking for macros: {e}")
        
        return indicators
    
    async def _check_archive(self, file_content: bytes, filename: str) -> List[str]:
        """Check archive for security issues"""
        indicators = []
        
        try:
            # Check file size
            if len(file_content) > self.max_archive_size:
                indicators.append(f"Archive size exceeds limit: {len(file_content)} bytes")
                return indicators
            
            # Try to open archive
            if filename.lower().endswith('.zip'):
                try:
                    with zipfile.ZipFile(io.BytesIO(file_content)) as zip_file:
                        file_list = zip_file.namelist()
                        
                        # Check number of files
                        if len(file_list) > self.max_archive_files:
                            indicators.append(f"Too many files in archive: {len(file_list)}")
                        
                        # Check for dangerous files
                        for file_name in file_list:
                            file_ext = os.path.splitext(file_name)[1].lower()
                            if file_ext in self.dangerous_extensions:
                                indicators.append(f"Dangerous file in archive: {file_name}")
                            
                            # Check for deeply nested paths
                            if file_name.count('/') > self.max_archive_depth:
                                indicators.append(f"Deeply nested file: {file_name}")
                        
                        # Check for archive bombs (small archive, many files)
                        if len(file_list) > 100 and len(file_content) < 1024 * 1024:  # 1MB
                            indicators.append("Potential archive bomb detected")
                
                except zipfile.BadZipFile:
                    indicators.append("Corrupted ZIP archive")
                except Exception as e:
                    indicators.append(f"Error reading ZIP archive: {str(e)}")
            
            elif filename.lower().endswith('.rar'):
                # RAR files are more complex to handle
                indicators.append("RAR archive detected - manual review recommended")
            
        except Exception as e:
            logger.error(f"Error checking archive: {e}")
            indicators.append(f"Archive validation error: {str(e)}")
        
        return indicators
    
    def _is_encrypted(self, file_content: bytes) -> bool:
        """Check if file appears to be encrypted"""
        try:
            # Check for high entropy
            if self._has_high_entropy(file_content):
                return True
            
            # Check for common encryption signatures
            encryption_signatures = [
                b'-----BEGIN PGP',
                b'-----BEGIN RSA',
                b'-----BEGIN CERTIFICATE',
                b'-----BEGIN ENCRYPTED',
                b'-----BEGIN PRIVATE KEY'
            ]
            
            for signature in encryption_signatures:
                if signature in file_content:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def _has_high_entropy(self, data: bytes) -> bool:
        """Check if data has high entropy (appears random)"""
        try:
            if len(data) < 100:
                return False
            
            # Count byte frequencies
            byte_counts = [0] * 256
            for byte in data:
                byte_counts[byte] += 1
            
            # Calculate entropy
            entropy = 0
            data_len = len(data)
            for count in byte_counts:
                if count > 0:
                    probability = count / data_len
                    entropy -= probability * (probability.bit_length() - 1)
            
            # High entropy threshold (7.5 bits per byte)
            return entropy > 7.5
            
        except Exception:
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get attachment validator statistics"""
        return {
            'max_file_size': self.max_file_size,
            'max_archive_size': self.max_archive_size,
            'max_archive_files': self.max_archive_files,
            'max_archive_depth': self.max_archive_depth,
            'dangerous_extensions_count': len(self.dangerous_extensions),
            'suspicious_extensions_count': len(self.suspicious_extensions),
            'safe_extensions_count': len(self.safe_extensions)
        }


# Global instance
attachment_validator = None


def get_attachment_validator(config: Dict[str, Any] = None) -> AttachmentValidator:
    """Get the global attachment validator instance"""
    global attachment_validator
    if attachment_validator is None:
        default_config = {
            'max_file_size': 50 * 1024 * 1024,  # 50MB
            'max_archive_size': 100 * 1024 * 1024,  # 100MB
            'max_archive_files': 1000,
            'max_archive_depth': 10
        }
        config = config or default_config
        attachment_validator = AttachmentValidator(config)
    return attachment_validator
