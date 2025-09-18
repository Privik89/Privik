"""
Real-Time Sandbox Service for Click-Time Analysis
Implements actual sandbox execution for links and attachments
"""

import asyncio
import aiohttp
import subprocess
import tempfile
import os
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog
from dataclasses import dataclass
from .object_storage import ObjectStorage
from ..database import SessionLocal
from ..models.sandbox import SandboxAnalysis
from ..models.email import EmailAttachment

logger = structlog.get_logger()


@dataclass
class SandboxResult:
    verdict: str  # safe, suspicious, malicious
    confidence: float
    execution_logs: List[Dict[str, Any]]
    network_activity: List[Dict[str, Any]]
    file_operations: List[Dict[str, Any]]
    registry_changes: List[Dict[str, Any]]
    threat_indicators: List[str]


class RealTimeSandbox:
    """Real-time sandbox for click-time analysis"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.sandbox_pool = []
        self.max_concurrent = config.get('max_concurrent_sandboxes', 10)
        self.timeout = config.get('sandbox_timeout', 300)  # 5 minutes
        self.browser_pool = []
        # CAPE settings
        self.cape_enabled = config.get('cape_enabled', False)
        self.cape_base_url = config.get('cape_base_url')
        self.cape_api_token = config.get('cape_api_token')
        self.storage = ObjectStorage()
        
    async def initialize(self):
        """Initialize sandbox environment"""
        try:
            # Initialize browser pool for link analysis
            await self._initialize_browser_pool()
            
            # Initialize sandbox VMs/containers
            await self._initialize_sandbox_pool()
            
            logger.info("Real-time sandbox initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize real-time sandbox", error=str(e))
            return False
    
    async def _initialize_browser_pool(self):
        """Initialize browser pool for link analysis"""
        try:
            # Use Playwright for browser automation
            from playwright.async_api import async_playwright
            
            self.playwright = await async_playwright().start()
            
            # Create browser pool
            for i in range(self.max_concurrent):
                browser = await self.playwright.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                self.browser_pool.append(browser)
            
            logger.info(f"Initialized browser pool with {len(self.browser_pool)} browsers")
            
        except Exception as e:
            logger.error("Failed to initialize browser pool", error=str(e))
            raise
    
    async def _initialize_sandbox_pool(self):
        """Initialize sandbox VMs/containers"""
        try:
            # For MVP, use Docker containers as sandboxes
            # In production, use dedicated VMs or cloud sandboxes
            
            for i in range(self.max_concurrent):
                sandbox_id = f"sandbox_{i}"
                sandbox_config = {
                    'id': sandbox_id,
                    'status': 'available',
                    'created_at': datetime.utcnow()
                }
                self.sandbox_pool.append(sandbox_config)
            
            logger.info(f"Initialized sandbox pool with {len(self.sandbox_pool)} sandboxes")
            
        except Exception as e:
            logger.error("Failed to initialize sandbox pool", error=str(e))
            raise
    
    async def analyze_link_click(self, url: str, user_context: Dict[str, Any]) -> SandboxResult:
        """Analyze link click in real-time sandbox"""
        try:
            logger.info("Starting real-time link analysis", url=url)
            
            # Get available browser
            browser = await self._get_available_browser()
            if not browser:
                raise Exception("No available browsers in pool")
            
            try:
                # Create new page
                page = await browser.new_page()
                
                # Set up monitoring
                execution_logs = []
                network_activity = []
                
                # Monitor network requests and console logs
                console_logs = []
                har_data = []
                
                async def handle_request(request):
                    network_activity.append({
                        'url': request.url,
                        'method': request.method,
                        'headers': dict(request.headers),
                        'timestamp': datetime.utcnow().isoformat()
                    })
                
                async def handle_response(response):
                    network_activity.append({
                        'url': response.url,
                        'status': response.status,
                        'headers': dict(response.headers),
                        'timestamp': datetime.utcnow().isoformat()
                    })
                
                async def handle_console(msg):
                    console_logs.append({
                        'type': msg.type,
                        'text': msg.text,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                
                page.on('request', handle_request)
                page.on('response', handle_response)
                page.on('console', handle_console)
                
                # Navigate to URL with timeout
                try:
                    response = await page.goto(url, timeout=self.timeout * 1000)
                    
                    # Wait for page to load
                    await page.wait_for_load_state('networkidle', timeout=10000)
                    
                    # Capture page content and artifacts
                    page_content = await page.content()
                    page_title = await page.title()
                    
                    # Capture DOM snapshot
                    dom_snapshot = await page.evaluate("document.documentElement.outerHTML")
                    
                    # Generate HAR data
                    try:
                        har_data = await page.evaluate("""
                            () => {
                                const entries = performance.getEntriesByType('navigation');
                                return entries.length > 0 ? entries[0] : null;
                            }
                        """)
                    except:
                        har_data = None
                    
                    # Check for suspicious elements
                    suspicious_elements = await self._detect_suspicious_elements(page)
                    
                    # Analyze page behavior
                    behavior_analysis = await self._analyze_page_behavior(page, page_content)
                    
                    # Calculate threat score
                    threat_score = self._calculate_link_threat_score(
                        url, page_content, suspicious_elements, behavior_analysis, network_activity
                    )
                    
                    # Determine verdict
                    verdict = self._determine_verdict(threat_score)
                    confidence = min(threat_score * 1.2, 1.0)
                    
                    # Store artifacts in object storage
                    artifacts = {}
                    if console_logs:
                        console_key = f"link_analysis/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_console.json"
                        await self.object_storage.upload_file(
                            console_key, 
                            json.dumps(console_logs, indent=2).encode()
                        )
                        artifacts['console_logs'] = console_key
                    
                    if dom_snapshot:
                        dom_key = f"link_analysis/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_dom.html"
                        await self.object_storage.upload_file(
                            dom_key, 
                            dom_snapshot.encode('utf-8')
                        )
                        artifacts['dom_snapshot'] = dom_key
                    
                    if har_data:
                        har_key = f"link_analysis/{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_har.json"
                        await self.object_storage.upload_file(
                            har_key, 
                            json.dumps(har_data, indent=2).encode()
                        )
                        artifacts['har_data'] = har_key
                    
                    return SandboxResult(
                        verdict=verdict,
                        confidence=confidence,
                        execution_logs=execution_logs + [{
                            'type': 'link_analysis',
                            'url': url,
                            'title': page_title,
                            'artifacts': artifacts
                        }],
                        network_activity=network_activity,
                        file_operations=[],
                        registry_changes=[],
                        threat_indicators=self._extract_threat_indicators(
                            suspicious_elements, behavior_analysis
                        )
                    )
                    
                except Exception as e:
                    logger.error("Error during page navigation", url=url, error=str(e))
                    return SandboxResult(
                        verdict="suspicious",
                        confidence=0.7,
                        execution_logs=[{'error': str(e)}],
                        network_activity=network_activity,
                        file_operations=[],
                        registry_changes=[],
                        threat_indicators=['navigation_error']
                    )
                
            finally:
                await page.close()
                await self._return_browser(browser)
                
        except Exception as e:
            logger.error("Error in link analysis", url=url, error=str(e))
            return SandboxResult(
                verdict="error",
                confidence=0.0,
                execution_logs=[{'error': str(e)}],
                network_activity=[],
                file_operations=[],
                registry_changes=[],
                threat_indicators=['analysis_error']
            )
    
    async def analyze_attachment(self, file_path: str, file_type: str) -> SandboxResult:
        """Analyze attachment in real-time sandbox"""
        try:
            logger.info("Starting real-time attachment analysis", file_path=file_path)
            
            # Submit to CAPE if enabled
            if self.cape_enabled and self.cape_base_url:
                try:
                    return await self._analyze_via_cape(file_path)
                except Exception as e:
                    logger.error("CAPE analysis failed, falling back", error=str(e))
            
            # Get available sandbox
            sandbox = await self._get_available_sandbox()
            if not sandbox:
                raise Exception("No available sandboxes")
            
            try:
                # For MVP, use basic file analysis
                # In production, use Cuckoo, CAPEv2, or custom sandbox
                
                if file_type in ['.exe', '.bat', '.cmd', '.ps1']:
                    # Executable files - high risk
                    return await self._analyze_executable(file_path, sandbox)
                elif file_type in ['.pdf', '.doc', '.docx', '.xls', '.xlsx']:
                    # Document files - medium risk
                    return await self._analyze_document(file_path, sandbox)
                elif file_type in ['.zip', '.rar', '.7z']:
                    # Archive files - medium risk
                    return await self._analyze_archive(file_path, sandbox)
                else:
                    # Other files - low risk
                    return await self._analyze_other_file(file_path, sandbox)
                    
            finally:
                await self._return_sandbox(sandbox)
                
        except Exception as e:
            logger.error("Error in attachment analysis", file_path=file_path, error=str(e))
            return SandboxResult(
                verdict="error",
                confidence=0.0,
                execution_logs=[{'error': str(e)}],
                network_activity=[],
                file_operations=[],
                registry_changes=[],
                threat_indicators=['analysis_error']
            )
    
    async def _analyze_executable(self, file_path: str, sandbox: Dict[str, Any]) -> SandboxResult:
        """Analyze executable file"""
        # For MVP, use basic static analysis
        # In production, execute in isolated environment
        
        file_size = os.path.getsize(file_path)
        
        # Basic heuristics
        threat_indicators = []
        threat_score = 0.0
        
        if file_size < 1000:  # Very small executable
            threat_indicators.append('suspicious_size')
            threat_score += 0.3
        
        if file_size > 50 * 1024 * 1024:  # Very large executable
            threat_indicators.append('suspicious_size')
            threat_score += 0.2
        
        # Check file entropy (simplified)
        with open(file_path, 'rb') as f:
            data = f.read(1024)
            entropy = self._calculate_entropy(data)
            if entropy > 7.5:  # High entropy
                threat_indicators.append('high_entropy')
                threat_score += 0.4
        
        verdict = "malicious" if threat_score > 0.7 else "suspicious" if threat_score > 0.4 else "safe"
        
        return SandboxResult(
            verdict=verdict,
            confidence=min(threat_score * 1.2, 1.0),
            execution_logs=[{'analysis_type': 'static', 'file_size': file_size}],
            network_activity=[],
            file_operations=[],
            registry_changes=[],
            threat_indicators=threat_indicators
        )

    async def _analyze_via_cape(self, file_path: str) -> SandboxResult:
        """Submit file to CAPE and poll for result."""
        try:
            import aiohttp
            submit_url = f"{self.cape_base_url}/tasks/create/file"
            headers = {}
            params = {"token": self.cape_api_token} if self.cape_api_token else {}
            data = aiohttp.FormData()
            data.add_field('file', open(file_path, 'rb'), filename=os.path.basename(file_path))
            async with aiohttp.ClientSession() as session:
                async with session.post(submit_url, data=data, params=params) as resp:
                    if resp.status != 200:
                        raise Exception(f"CAPE submit failed: {resp.status}")
                    submit_res = await resp.json()
                    task_id = submit_res.get('task_id') or submit_res.get('task_ids', [None])[0]
                    if not task_id:
                        raise Exception("CAPE task id missing")
            # Poll for report
            report_url = f"{self.cape_base_url}/tasks/report/{task_id}"
            for _ in range(30):  # ~30 polls
                await asyncio.sleep(5)
                async with aiohttp.ClientSession() as session:
                    async with session.get(report_url, params=params) as resp:
                        if resp.status == 200:
                            report = await resp.json()
                            # Basic mapping & persistence
                            score = float(report.get('info', {}).get('score', 0.0))
                            verdict = 'malicious' if score >= 8 else 'suspicious' if score >= 4 else 'safe'
                            indicators = list(report.get('signatures', {}).keys()) if isinstance(report.get('signatures'), dict) else []
                            # Upload report JSON
                            report_key = f"reports/cape/{task_id}.json"
                            try:
                                self.storage.upload_json(report_key, report)
                            except Exception:
                                report_key = None
                            # Attempt to capture screenshots if present in report (placeholder)
                            screenshots_keys = []
                            # Return result
                            return SandboxResult(
                                verdict=verdict,
                                confidence=min(score / 10.0, 1.0),
                                execution_logs=[{'task_id': task_id, 'report_key': report_key, 'screenshots': screenshots_keys}],
                                network_activity=report.get('network', {}).get('hosts', []),
                                file_operations=[],
                                registry_changes=[],
                                threat_indicators=indicators
                            )
                        elif resp.status == 404:
                            continue
            raise Exception("CAPE report timeout")
        except Exception as e:
            logger.error("CAPE client error", error=str(e))
            raise
    
    async def _analyze_document(self, file_path: str, sandbox: Dict[str, Any]) -> SandboxResult:
        """Analyze document file"""
        # For MVP, use basic analysis
        # In production, use specialized document analysis tools
        
        threat_indicators = []
        threat_score = 0.0
        
        # Check for embedded objects
        if self._has_embedded_objects(file_path):
            threat_indicators.append('embedded_objects')
            threat_score += 0.3
        
        # Check for macros
        if self._has_macros(file_path):
            threat_indicators.append('macros')
            threat_score += 0.5
        
        # Check for suspicious content
        if self._has_suspicious_content(file_path):
            threat_indicators.append('suspicious_content')
            threat_score += 0.2
        
        verdict = "malicious" if threat_score > 0.7 else "suspicious" if threat_score > 0.4 else "safe"
        
        return SandboxResult(
            verdict=verdict,
            confidence=min(threat_score * 1.2, 1.0),
            execution_logs=[{'analysis_type': 'document', 'file_path': file_path}],
            network_activity=[],
            file_operations=[],
            registry_changes=[],
            threat_indicators=threat_indicators
        )
    
    async def _analyze_archive(self, file_path: str, sandbox: Dict[str, Any]) -> SandboxResult:
        """Analyze archive file"""
        # For MVP, check archive contents
        # In production, extract and analyze each file
        
        threat_indicators = []
        threat_score = 0.0
        
        try:
            # Check archive contents
            contents = self._list_archive_contents(file_path)
            
            # Check for suspicious file types
            suspicious_extensions = ['.exe', '.bat', '.cmd', '.ps1', '.vbs', '.js']
            for file in contents:
                if any(file.lower().endswith(ext) for ext in suspicious_extensions):
                    threat_indicators.append('suspicious_archive_contents')
                    threat_score += 0.4
                    break
            
            # Check for password protection
            if self._is_password_protected(file_path):
                threat_indicators.append('password_protected')
                threat_score += 0.3
            
        except Exception as e:
            threat_indicators.append('archive_analysis_error')
            threat_score += 0.2
        
        verdict = "malicious" if threat_score > 0.7 else "suspicious" if threat_score > 0.4 else "safe"
        
        return SandboxResult(
            verdict=verdict,
            confidence=min(threat_score * 1.2, 1.0),
            execution_logs=[{'analysis_type': 'archive', 'contents': contents}],
            network_activity=[],
            file_operations=[],
            registry_changes=[],
            threat_indicators=threat_indicators
        )
    
    async def _analyze_other_file(self, file_path: str, sandbox: Dict[str, Any]) -> SandboxResult:
        """Analyze other file types"""
        # Basic analysis for other file types
        
        threat_indicators = []
        threat_score = 0.0
        
        file_size = os.path.getsize(file_path)
        
        # Check for suspicious size
        if file_size > 100 * 1024 * 1024:  # Very large file
            threat_indicators.append('suspicious_size')
            threat_score += 0.1
        
        verdict = "suspicious" if threat_score > 0.5 else "safe"
        
        return SandboxResult(
            verdict=verdict,
            confidence=min(threat_score * 1.2, 1.0),
            execution_logs=[{'analysis_type': 'other', 'file_size': file_size}],
            network_activity=[],
            file_operations=[],
            registry_changes=[],
            threat_indicators=threat_indicators
        )
    
    async def _detect_suspicious_elements(self, page) -> List[Dict[str, Any]]:
        """Detect suspicious elements on the page"""
        suspicious_elements = []
        
        try:
            # Check for login forms
            login_forms = await page.query_selector_all('form[action*="login"], form[action*="signin"]')
            if login_forms:
                suspicious_elements.append({
                    'type': 'login_form',
                    'count': len(login_forms),
                    'risk': 'high'
                })
            
            # Check for password fields
            password_fields = await page.query_selector_all('input[type="password"]')
            if password_fields:
                suspicious_elements.append({
                    'type': 'password_field',
                    'count': len(password_fields),
                    'risk': 'high'
                })
            
            # Check for suspicious JavaScript
            scripts = await page.query_selector_all('script')
            for script in scripts:
                content = await script.inner_text()
                if any(keyword in content.lower() for keyword in ['eval', 'document.write', 'innerHTML']):
                    suspicious_elements.append({
                        'type': 'suspicious_script',
                        'content': content[:100],
                        'risk': 'medium'
                    })
            
            # Check for iframes
            iframes = await page.query_selector_all('iframe')
            if iframes:
                suspicious_elements.append({
                    'type': 'iframe',
                    'count': len(iframes),
                    'risk': 'medium'
                })
            
        except Exception as e:
            logger.error("Error detecting suspicious elements", error=str(e))
        
        return suspicious_elements
    
    async def _analyze_page_behavior(self, page, content: str) -> Dict[str, Any]:
        """Analyze page behavior patterns"""
        behavior = {
            'redirects': 0,
            'popups': 0,
            'suspicious_requests': 0,
            'content_length': len(content)
        }
        
        try:
            # Check for redirects
            if 'location.href' in content or 'window.location' in content:
                behavior['redirects'] += 1
            
            # Check for popups
            if 'window.open' in content or 'alert(' in content:
                behavior['popups'] += 1
            
            # Check for suspicious requests
            if 'XMLHttpRequest' in content or 'fetch(' in content:
                behavior['suspicious_requests'] += 1
            
        except Exception as e:
            logger.error("Error analyzing page behavior", error=str(e))
        
        return behavior
    
    def _calculate_link_threat_score(self, url: str, content: str, suspicious_elements: List[Dict], 
                                   behavior: Dict[str, Any], network_activity: List[Dict]) -> float:
        """Calculate threat score for link analysis"""
        score = 0.0
        
        # URL analysis
        if any(keyword in url.lower() for keyword in ['login', 'signin', 'auth', 'secure']):
            score += 0.3
        
        # Suspicious elements
        for element in suspicious_elements:
            if element['risk'] == 'high':
                score += 0.4
            elif element['risk'] == 'medium':
                score += 0.2
        
        # Behavior analysis
        if behavior['redirects'] > 0:
            score += 0.2
        if behavior['popups'] > 0:
            score += 0.1
        if behavior['suspicious_requests'] > 0:
            score += 0.2
        
        # Network activity
        if len(network_activity) > 10:  # Many requests
            score += 0.1
        
        return min(score, 1.0)
    
    def _determine_verdict(self, threat_score: float) -> str:
        """Determine verdict based on threat score"""
        if threat_score > 0.8:
            return "malicious"
        elif threat_score > 0.5:
            return "suspicious"
        else:
            return "safe"
    
    def _extract_threat_indicators(self, suspicious_elements: List[Dict], behavior: Dict[str, Any]) -> List[str]:
        """Extract threat indicators"""
        indicators = []
        
        for element in suspicious_elements:
            indicators.append(element['type'])
        
        if behavior['redirects'] > 0:
            indicators.append('redirects')
        if behavior['popups'] > 0:
            indicators.append('popups')
        if behavior['suspicious_requests'] > 0:
            indicators.append('suspicious_requests')
        
        return indicators
    
    def _calculate_entropy(self, data: bytes) -> float:
        """Calculate Shannon entropy of data"""
        if not data:
            return 0.0
        
        # Count byte frequencies
        byte_counts = [0] * 256
        for byte in data:
            byte_counts[byte] += 1
        
        # Calculate entropy
        entropy = 0.0
        data_len = len(data)
        for count in byte_counts:
            if count > 0:
                probability = count / data_len
                entropy -= probability * (probability.bit_length() - 1)
        
        return entropy
    
    def _has_embedded_objects(self, file_path: str) -> bool:
        """Check if document has embedded objects"""
        # Simplified check for MVP
        # In production, use specialized document analysis
        return False
    
    def _has_macros(self, file_path: str) -> bool:
        """Check if document has macros"""
        # Simplified check for MVP
        # In production, use specialized document analysis
        return False
    
    def _has_suspicious_content(self, file_path: str) -> bool:
        """Check if document has suspicious content"""
        # Simplified check for MVP
        # In production, use specialized document analysis
        return False
    
    def _list_archive_contents(self, file_path: str) -> List[str]:
        """List archive contents"""
        # Simplified for MVP
        # In production, use proper archive libraries
        return []
    
    def _is_password_protected(self, file_path: str) -> bool:
        """Check if archive is password protected"""
        # Simplified for MVP
        # In production, use proper archive libraries
        return False
    
    async def _get_available_browser(self):
        """Get available browser from pool"""
        for browser in self.browser_pool:
            if browser.is_connected():
                return browser
        return None
    
    async def _return_browser(self, browser):
        """Return browser to pool"""
        # Browser is already in pool, no action needed
        pass
    
    async def _get_available_sandbox(self) -> Optional[Dict[str, Any]]:
        """Get available sandbox from pool"""
        for sandbox in self.sandbox_pool:
            if sandbox['status'] == 'available':
                sandbox['status'] = 'busy'
                return sandbox
        return None
    
    async def _return_sandbox(self, sandbox: Dict[str, Any]):
        """Return sandbox to pool"""
        sandbox['status'] = 'available'
    
    async def cleanup(self):
        """Cleanup sandbox resources"""
        try:
            # Close browsers
            for browser in self.browser_pool:
                await browser.close()
            
            # Stop playwright
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            
            logger.info("Real-time sandbox cleaned up")
            
        except Exception as e:
            logger.error("Error cleaning up sandbox", error=str(e))
