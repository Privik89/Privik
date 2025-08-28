"""
Privik Endpoint Agent File Monitor
Monitors file system for suspicious files and changes
"""

import asyncio
import time
import os
import hashlib
import magic
from typing import Dict, Any, List, Optional, Set
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import structlog

from ..config import AgentConfig
from ..security import SecurityManager
from ..communication import ServerCommunicator

logger = structlog.get_logger()

class FileEventHandler(FileSystemEventHandler):
    """Handles file system events."""
    
    def __init__(self, file_monitor):
        self.file_monitor = file_monitor
    
    def on_created(self, event):
        """Handle file creation events."""
        if not event.is_directory:
            asyncio.create_task(self.file_monitor._handle_file_event('created', event.src_path))
    
    def on_modified(self, event):
        """Handle file modification events."""
        if not event.is_directory:
            asyncio.create_task(self.file_monitor._handle_file_event('modified', event.src_path))
    
    def on_moved(self, event):
        """Handle file move events."""
        if not event.is_directory:
            asyncio.create_task(self.file_monitor._handle_file_event('moved', event.dest_path))

class FileMonitor:
    """Monitors file system for suspicious files and changes."""
    
    def __init__(self, config: AgentConfig, security_manager: SecurityManager, 
                 communicator: ServerCommunicator):
        """Initialize the file monitor."""
        self.config = config
        self.security_manager = security_manager
        self.communicator = communicator
        self.running = False
        self.observer = None
        self.event_handler = None
        self.scanned_files: Set[str] = set()
        
        # File patterns to monitor
        self.suspicious_extensions = [
            '.exe', '.bat', '.cmd', '.com', '.pif', '.scr', '.vbs', '.js',
            '.jar', '.msi', '.dmg', '.app', '.deb', '.rpm', '.sh', '.py',
            '.ps1', '.pl', '.rb', '.php', '.asp', '.aspx'
        ]
        
        # Suspicious file names
        self.suspicious_names = [
            'invoice', 'receipt', 'document', 'scan', 'photo', 'image',
            'payment', 'bank', 'security', 'update', 'install', 'setup'
        ]
        
        # File size limits
        self.max_file_size = self.config.max_file_size
    
    async def initialize(self) -> bool:
        """Initialize the file monitor."""
        try:
            logger.info("Initializing file monitor")
            
            # Verify watch directories exist
            valid_directories = []
            for directory in self.config.file_watch_directories:
                if os.path.exists(directory):
                    valid_directories.append(directory)
                else:
                    logger.warning("Watch directory not found", path=directory)
            
            if not valid_directories:
                logger.warning("No valid watch directories found")
                return False
            
            # Create event handler
            self.event_handler = FileEventHandler(self)
            
            # Create observer
            self.observer = Observer()
            
            # Schedule watching for each directory
            for directory in valid_directories:
                self.observer.schedule(self.event_handler, directory, recursive=True)
                logger.info("Scheduled directory for monitoring", path=directory)
            
            logger.info("File monitor initialized", directory_count=len(valid_directories))
            return True
            
        except Exception as e:
            logger.error("Failed to initialize file monitor", error=str(e))
            return False
    
    async def start_monitoring(self):
        """Start file monitoring."""
        try:
            self.running = True
            logger.info("Starting file monitoring")
            
            # Start the observer
            self.observer.start()
            
            # Initial scan of existing files
            await self._initial_scan()
            
            # Keep monitoring running
            while self.running:
                await asyncio.sleep(1)
            
        except Exception as e:
            logger.error("File monitoring error", error=str(e))
        finally:
            self.running = False
            if self.observer:
                self.observer.stop()
                self.observer.join()
            logger.info("File monitoring stopped")
    
    async def _initial_scan(self):
        """Perform initial scan of existing files."""
        try:
            logger.info("Starting initial file scan")
            
            for directory in self.config.file_watch_directories:
                if not os.path.exists(directory):
                    continue
                
                await self._scan_directory(directory)
            
            logger.info("Initial file scan completed")
            
        except Exception as e:
            logger.error("Error during initial scan", error=str(e))
    
    async def _scan_directory(self, directory: str):
        """Scan a directory for files."""
        try:
            for root, dirs, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    await self._analyze_file(file_path)
                    
        except Exception as e:
            logger.error("Error scanning directory", directory=directory, error=str(e))
    
    async def _handle_file_event(self, event_type: str, file_path: str):
        """Handle file system events."""
        try:
            # Check if file still exists
            if not os.path.exists(file_path):
                return
            
            # Analyze the file
            await self._analyze_file(file_path, event_type)
            
        except Exception as e:
            logger.error("Error handling file event", 
                        event_type=event_type, 
                        file_path=file_path, 
                        error=str(e))
    
    async def _analyze_file(self, file_path: str, event_type: str = "scan"):
        """Analyze a file for threats."""
        try:
            # Check if we've already analyzed this file
            file_hash = self.security_manager.hash_file(file_path)
            if file_hash in self.scanned_files:
                return
            
            # Get file information
            file_info = await self._get_file_info(file_path)
            
            # Check if file should be analyzed
            if not self._should_analyze_file(file_info):
                return
            
            # Analyze file for threats
            analysis_result = await self._analyze_file_content(file_info)
            
            if analysis_result['threat_score'] > 0:
                # Send analysis to server
                await self.communicator.send_file_analysis(analysis_result)
                logger.info("Threat detected in file", 
                           file=file_path,
                           threat_score=analysis_result['threat_score'],
                           event_type=event_type)
            
            # Mark as scanned
            self.scanned_files.add(file_hash)
            
        except Exception as e:
            logger.error("Error analyzing file", file=file_path, error=str(e))
    
    async def _get_file_info(self, file_path: str) -> Dict[str, Any]:
        """Get comprehensive file information."""
        try:
            stat = os.stat(file_path)
            
            file_info = {
                'path': file_path,
                'name': os.path.basename(file_path),
                'size': stat.st_size,
                'created': stat.st_ctime,
                'modified': stat.st_mtime,
                'accessed': stat.st_atime,
                'extension': os.path.splitext(file_path)[1].lower(),
                'mime_type': None,
                'hash': None,
            }
            
            # Get MIME type
            try:
                file_info['mime_type'] = magic.from_file(file_path, mime=True)
            except Exception:
                pass
            
            # Get file hash
            try:
                file_info['hash'] = self.security_manager.hash_file(file_path)
            except Exception:
                pass
            
            return file_info
            
        except Exception as e:
            logger.error("Error getting file info", file=file_path, error=str(e))
            return {'path': file_path, 'error': str(e)}
    
    def _should_analyze_file(self, file_info: Dict[str, Any]) -> bool:
        """Determine if a file should be analyzed."""
        try:
            # Skip files that are too large
            if file_info.get('size', 0) > self.max_file_size:
                return False
            
            # Skip files without extension
            extension = file_info.get('extension', '')
            if not extension:
                return False
            
            # Check if extension is suspicious
            if extension in self.suspicious_extensions:
                return True
            
            # Check if filename contains suspicious words
            filename = file_info.get('name', '').lower()
            for suspicious_name in self.suspicious_names:
                if suspicious_name in filename:
                    return True
            
            # Check MIME type
            mime_type = file_info.get('mime_type', '').lower()
            if any(exec_type in mime_type for exec_type in ['executable', 'application/x-']):
                return True
            
            return False
            
        except Exception as e:
            logger.error("Error checking if file should be analyzed", error=str(e))
            return False
    
    async def _analyze_file_content(self, file_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze file content for threats."""
        try:
            analysis = {
                'file_path': file_info['path'],
                'file_name': file_info['name'],
                'file_size': file_info['size'],
                'file_hash': file_info['hash'],
                'mime_type': file_info['mime_type'],
                'extension': file_info['extension'],
                'threat_score': 0,
                'threat_indicators': [],
                'analysis_type': 'file_monitor',
                'timestamp': int(time.time()),
            }
            
            # Analyze file extension
            ext_score, ext_indicators = self._analyze_extension(file_info['extension'])
            analysis['threat_score'] += ext_score
            analysis['threat_indicators'].extend(ext_indicators)
            
            # Analyze file name
            name_score, name_indicators = self._analyze_filename(file_info['name'])
            analysis['threat_score'] += name_score
            analysis['threat_indicators'].extend(name_indicators)
            
            # Analyze MIME type
            mime_score, mime_indicators = self._analyze_mime_type(file_info['mime_type'])
            analysis['threat_score'] += mime_score
            analysis['threat_indicators'].extend(mime_indicators)
            
            # Analyze file size
            size_score, size_indicators = self._analyze_file_size(file_info['size'])
            analysis['threat_score'] += size_score
            analysis['threat_indicators'].extend(size_indicators)
            
            # Perform content analysis if file is small enough
            if file_info['size'] < 1024 * 1024:  # 1MB
                content_score, content_indicators = await self._analyze_file_content_simple(file_info['path'])
                analysis['threat_score'] += content_score
                analysis['threat_indicators'].extend(content_indicators)
            
            return analysis
            
        except Exception as e:
            logger.error("Error analyzing file content", error=str(e))
            return {'threat_score': 0, 'error': str(e)}
    
    def _analyze_extension(self, extension: str) -> tuple:
        """Analyze file extension for threats."""
        score = 0
        indicators = []
        
        try:
            extension_lower = extension.lower()
            
            # High-risk extensions
            high_risk = ['.exe', '.bat', '.cmd', '.com', '.pif', '.scr']
            if extension_lower in high_risk:
                score += 30
                indicators.append(f"high_risk_extension_{extension_lower}")
            
            # Medium-risk extensions
            medium_risk = ['.vbs', '.js', '.jar', '.msi', '.dmg', '.app']
            if extension_lower in medium_risk:
                score += 20
                indicators.append(f"medium_risk_extension_{extension_lower}")
            
            # Script extensions
            script_extensions = ['.py', '.ps1', '.pl', '.rb', '.php', '.asp', '.aspx']
            if extension_lower in script_extensions:
                score += 15
                indicators.append(f"script_extension_{extension_lower}")
            
            return score, indicators
            
        except Exception as e:
            logger.error("Error analyzing extension", error=str(e))
            return 0, []
    
    def _analyze_filename(self, filename: str) -> tuple:
        """Analyze filename for threats."""
        score = 0
        indicators = []
        
        try:
            filename_lower = filename.lower()
            
            # Check for suspicious names
            for suspicious_name in self.suspicious_names:
                if suspicious_name in filename_lower:
                    score += 10
                    indicators.append(f"suspicious_name_{suspicious_name}")
            
            # Check for double extensions
            if filename_lower.count('.') > 1:
                score += 15
                indicators.append("double_extension")
            
            # Check for random-looking names
            if len(filename) > 20 and not any(char.isalpha() for char in filename):
                score += 10
                indicators.append("random_filename")
            
            return score, indicators
            
        except Exception as e:
            logger.error("Error analyzing filename", error=str(e))
            return 0, []
    
    def _analyze_mime_type(self, mime_type: str) -> tuple:
        """Analyze MIME type for threats."""
        score = 0
        indicators = []
        
        try:
            if not mime_type:
                return 0, []
            
            mime_lower = mime_type.lower()
            
            # Executable types
            executable_types = ['application/x-executable', 'application/x-msdownload']
            if any(exec_type in mime_lower for exec_type in executable_types):
                score += 25
                indicators.append("executable_mime_type")
            
            # Script types
            script_types = ['text/x-python', 'text/x-php', 'text/x-shellscript']
            if any(script_type in mime_lower for script_type in script_types):
                score += 15
                indicators.append("script_mime_type")
            
            # Archive types
            archive_types = ['application/zip', 'application/x-rar', 'application/x-7z-compressed']
            if any(archive_type in mime_lower for archive_type in archive_types):
                score += 5
                indicators.append("archive_mime_type")
            
            return score, indicators
            
        except Exception as e:
            logger.error("Error analyzing MIME type", error=str(e))
            return 0, []
    
    def _analyze_file_size(self, size: int) -> tuple:
        """Analyze file size for threats."""
        score = 0
        indicators = []
        
        try:
            # Very small files might be scripts
            if size < 1024:  # 1KB
                score += 5
                indicators.append("very_small_file")
            
            # Very large files might be suspicious
            if size > 100 * 1024 * 1024:  # 100MB
                score += 10
                indicators.append("very_large_file")
            
            return score, indicators
            
        except Exception as e:
            logger.error("Error analyzing file size", error=str(e))
            return 0, []
    
    async def _analyze_file_content_simple(self, file_path: str) -> tuple:
        """Perform simple content analysis on file."""
        score = 0
        indicators = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(4096)  # Read first 4KB
            
            content_lower = content.lower()
            
            # Check for suspicious strings
            suspicious_strings = [
                'powershell', 'cmd', 'exec', 'system', 'shell',
                'download', 'wget', 'curl', 'http', 'ftp',
                'registry', 'regedit', 'startup', 'autostart'
            ]
            
            for suspicious_string in suspicious_strings:
                if suspicious_string in content_lower:
                    score += 5
                    indicators.append(f"suspicious_content_{suspicious_string}")
            
            # Check for encoded content
            if 'base64' in content_lower or 'encoded' in content_lower:
                score += 10
                indicators.append("encoded_content")
            
            return score, indicators
            
        except Exception as e:
            logger.error("Error analyzing file content", error=str(e))
            return 0, []
    
    async def get_status(self) -> Dict[str, Any]:
        """Get file monitor status."""
        return {
            'running': self.running,
            'scanned_files_count': len(self.scanned_files),
            'watch_directories': self.config.file_watch_directories,
            'max_file_size': self.max_file_size,
        }
    
    async def stop(self):
        """Stop the file monitor."""
        self.running = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
        logger.info("File monitor stopped")
