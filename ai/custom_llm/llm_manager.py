"""
Privik Custom LLM Manager
Manages Privik's proprietary trained language model
"""

import asyncio
import json
import time
from typing import Dict, Any, List, Optional, Union
import structlog

from .llm_client import CustomLLMClient
from .llm_prompts import PromptTemplates
from .llm_analytics import LLMAnalytics

logger = structlog.get_logger()

class CustomLLMManager:
    """Manages Privik's custom trained language model."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the custom LLM manager."""
        self.config = config
        self.client = None
        self.prompts = None
        self.analytics = None
        
        # LLM configuration
        self.model_name = config.get('model_name', 'privik-llm-v1')
        self.model_version = config.get('model_version', '1.0.0')
        self.endpoint_url = config.get('endpoint_url', 'http://localhost:8001')
        self.api_key = config.get('api_key', '')
        
        # Model capabilities
        self.max_tokens = config.get('max_tokens', 4096)
        self.temperature = config.get('temperature', 0.1)
        self.top_p = config.get('top_p', 0.9)
        
        # Specialized capabilities
        self.phishing_detection = config.get('phishing_detection', True)
        self.malware_analysis = config.get('malware_analysis', True)
        self.behavior_analysis = config.get('behavior_analysis', True)
        self.threat_intelligence = config.get('threat_intelligence', True)
        self.soc_assistant = config.get('soc_assistant', True)
        
        # Performance settings
        self.batch_size = config.get('batch_size', 10)
        self.timeout = config.get('timeout', 30)
        self.retry_attempts = config.get('retry_attempts', 3)
        
        # Analytics and monitoring
        self.enable_analytics = config.get('enable_analytics', True)
        self.log_prompts = config.get('log_prompts', False)
        self.performance_monitoring = config.get('performance_monitoring', True)
    
    async def initialize(self) -> bool:
        """Initialize the custom LLM manager."""
        try:
            logger.info("Initializing Privik Custom LLM Manager")
            
            # Initialize components
            self.client = CustomLLMClient(self.config)
            self.prompts = PromptTemplates()
            self.analytics = LLMAnalytics() if self.enable_analytics else None
            
            # Test LLM connection
            if not await self._test_llm_connection():
                logger.error("Failed to connect to custom LLM")
                return False
            
            # Load model capabilities
            await self._load_model_capabilities()
            
            # Initialize analytics
            if self.analytics:
                await self.analytics.initialize()
            
            logger.info(f"Custom LLM Manager initialized: {self.model_name} v{self.model_version}")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize Custom LLM Manager", error=str(e))
            return False
    
    async def _test_llm_connection(self) -> bool:
        """Test connection to the custom LLM."""
        try:
            # Test basic connectivity
            response = await self.client.health_check()
            if response.get('status') == 'healthy':
                logger.info("Custom LLM connection test successful")
                return True
            else:
                logger.error(f"Custom LLM health check failed: {response}")
                return False
                
        except Exception as e:
            logger.error("Custom LLM connection test failed", error=str(e))
            return False
    
    async def _load_model_capabilities(self):
        """Load and validate model capabilities."""
        try:
            capabilities = await self.client.get_model_capabilities()
            
            logger.info("Custom LLM Capabilities:")
            for capability, enabled in capabilities.items():
                status = "✅" if enabled else "❌"
                logger.info(f"  {status} {capability}")
            
            # Update local capabilities
            self.phishing_detection = capabilities.get('phishing_detection', False)
            self.malware_analysis = capabilities.get('malware_analysis', False)
            self.behavior_analysis = capabilities.get('behavior_analysis', False)
            self.threat_intelligence = capabilities.get('threat_intelligence', False)
            self.soc_assistant = capabilities.get('soc_assistant', False)
            
        except Exception as e:
            logger.error("Error loading model capabilities", error=str(e))
    
    async def analyze_email_content(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze email content using custom LLM."""
        try:
            # Prepare email analysis prompt
            prompt = self.prompts.get_email_analysis_prompt(email_data)
            
            # Get LLM response
            response = await self.client.generate_response(
                prompt=prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Parse and structure response
            analysis = self._parse_email_analysis(response)
            
            # Log analytics
            if self.analytics:
                await self.analytics.log_analysis('email', email_data, analysis)
            
            return analysis
            
        except Exception as e:
            logger.error("Error analyzing email content", error=str(e))
            return {'error': str(e)}
    
    async def analyze_file_content(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze file content using custom LLM."""
        try:
            # Prepare file analysis prompt
            prompt = self.prompts.get_file_analysis_prompt(file_data)
            
            # Get LLM response
            response = await self.client.generate_response(
                prompt=prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Parse and structure response
            analysis = self._parse_file_analysis(response)
            
            # Log analytics
            if self.analytics:
                await self.analytics.log_analysis('file', file_data, analysis)
            
            return analysis
            
        except Exception as e:
            logger.error("Error analyzing file content", error=str(e))
            return {'error': str(e)}
    
    async def analyze_user_behavior(self, behavior_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user behavior using custom LLM."""
        try:
            # Prepare behavior analysis prompt
            prompt = self.prompts.get_behavior_analysis_prompt(behavior_data)
            
            # Get LLM response
            response = await self.client.generate_response(
                prompt=prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Parse and structure response
            analysis = self._parse_behavior_analysis(response)
            
            # Log analytics
            if self.analytics:
                await self.analytics.log_analysis('behavior', behavior_data, analysis)
            
            return analysis
            
        except Exception as e:
            logger.error("Error analyzing user behavior", error=str(e))
            return {'error': str(e)}
    
    async def generate_threat_intelligence(self, threat_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate threat intelligence using custom LLM."""
        try:
            # Prepare threat intelligence prompt
            prompt = self.prompts.get_threat_intelligence_prompt(threat_data)
            
            # Get LLM response
            response = await self.client.generate_response(
                prompt=prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Parse and structure response
            intelligence = self._parse_threat_intelligence(response)
            
            # Log analytics
            if self.analytics:
                await self.analytics.log_analysis('threat_intelligence', threat_data, intelligence)
            
            return intelligence
            
        except Exception as e:
            logger.error("Error generating threat intelligence", error=str(e))
            return {'error': str(e)}
    
    async def soc_assistant_query(self, query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """SOC assistant query using custom LLM."""
        try:
            # Prepare SOC assistant prompt
            prompt = self.prompts.get_soc_assistant_prompt(query, context)
            
            # Get LLM response
            response = await self.client.generate_response(
                prompt=prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            # Parse and structure response
            assistant_response = self._parse_soc_assistant_response(response)
            
            # Log analytics
            if self.analytics:
                await self.analytics.log_analysis('soc_assistant', {'query': query, 'context': context}, assistant_response)
            
            return assistant_response
            
        except Exception as e:
            logger.error("Error processing SOC assistant query", error=str(e))
            return {'error': str(e)}
    
    async def batch_analysis(self, data_list: List[Dict[str, Any]], analysis_type: str) -> List[Dict[str, Any]]:
        """Perform batch analysis using custom LLM."""
        try:
            results = []
            
            # Process in batches
            for i in range(0, len(data_list), self.batch_size):
                batch = data_list[i:i + self.batch_size]
                
                # Prepare batch prompt
                prompt = self.prompts.get_batch_analysis_prompt(batch, analysis_type)
                
                # Get LLM response
                response = await self.client.generate_response(
                    prompt=prompt,
                    max_tokens=self.max_tokens * len(batch),
                    temperature=self.temperature
                )
                
                # Parse batch response
                batch_results = self._parse_batch_analysis(response, analysis_type)
                results.extend(batch_results)
                
                # Small delay between batches
                await asyncio.sleep(0.1)
            
            return results
            
        except Exception as e:
            logger.error("Error performing batch analysis", error=str(e))
            return [{'error': str(e)}] * len(data_list)
    
    def _parse_email_analysis(self, response: str) -> Dict[str, Any]:
        """Parse email analysis response."""
        try:
            # Parse JSON response
            if response.startswith('{'):
                return json.loads(response)
            
            # Parse structured text response
            analysis = {
                'threat_score': 0,
                'threat_type': 'unknown',
                'confidence': 0,
                'indicators': [],
                'summary': '',
                'recommendations': []
            }
            
            # Extract structured information from text
            lines = response.split('\n')
            for line in lines:
                if 'threat_score:' in line.lower():
                    try:
                        score = float(line.split(':')[1].strip())
                        analysis['threat_score'] = score
                    except:
                        pass
                elif 'threat_type:' in line.lower():
                    threat_type = line.split(':')[1].strip()
                    analysis['threat_type'] = threat_type
                elif 'confidence:' in line.lower():
                    try:
                        confidence = float(line.split(':')[1].strip())
                        analysis['confidence'] = confidence
                    except:
                        pass
            
            analysis['summary'] = response
            return analysis
            
        except Exception as e:
            logger.error("Error parsing email analysis", error=str(e))
            return {'error': str(e)}
    
    def _parse_file_analysis(self, response: str) -> Dict[str, Any]:
        """Parse file analysis response."""
        try:
            # Similar parsing logic for file analysis
            return self._parse_email_analysis(response)
        except Exception as e:
            logger.error("Error parsing file analysis", error=str(e))
            return {'error': str(e)}
    
    def _parse_behavior_analysis(self, response: str) -> Dict[str, Any]:
        """Parse behavior analysis response."""
        try:
            # Similar parsing logic for behavior analysis
            return self._parse_email_analysis(response)
        except Exception as e:
            logger.error("Error parsing behavior analysis", error=str(e))
            return {'error': str(e)}
    
    def _parse_threat_intelligence(self, response: str) -> Dict[str, Any]:
        """Parse threat intelligence response."""
        try:
            # Similar parsing logic for threat intelligence
            return self._parse_email_analysis(response)
        except Exception as e:
            logger.error("Error parsing threat intelligence", error=str(e))
            return {'error': str(e)}
    
    def _parse_soc_assistant_response(self, response: str) -> Dict[str, Any]:
        """Parse SOC assistant response."""
        try:
            return {
                'response': response,
                'timestamp': int(time.time()),
                'model': self.model_name,
                'version': self.model_version
            }
        except Exception as e:
            logger.error("Error parsing SOC assistant response", error=str(e))
            return {'error': str(e)}
    
    def _parse_batch_analysis(self, response: str, analysis_type: str) -> List[Dict[str, Any]]:
        """Parse batch analysis response."""
        try:
            # Parse batch response
            if response.startswith('['):
                return json.loads(response)
            
            # Parse structured batch response
            results = []
            sections = response.split('---')
            
            for section in sections:
                if section.strip():
                    if analysis_type == 'email':
                        result = self._parse_email_analysis(section)
                    elif analysis_type == 'file':
                        result = self._parse_file_analysis(section)
                    elif analysis_type == 'behavior':
                        result = self._parse_behavior_analysis(section)
                    else:
                        result = {'analysis': section.strip()}
                    
                    results.append(result)
            
            return results
            
        except Exception as e:
            logger.error("Error parsing batch analysis", error=str(e))
            return [{'error': str(e)}]
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get custom LLM model information."""
        try:
            return {
                'model_name': self.model_name,
                'model_version': self.model_version,
                'endpoint_url': self.endpoint_url,
                'capabilities': {
                    'phishing_detection': self.phishing_detection,
                    'malware_analysis': self.malware_analysis,
                    'behavior_analysis': self.behavior_analysis,
                    'threat_intelligence': self.threat_intelligence,
                    'soc_assistant': self.soc_assistant
                },
                'performance': {
                    'max_tokens': self.max_tokens,
                    'temperature': self.temperature,
                    'batch_size': self.batch_size
                }
            }
        except Exception as e:
            logger.error("Error getting model info", error=str(e))
            return {}
    
    async def get_analytics(self) -> Dict[str, Any]:
        """Get LLM analytics and performance metrics."""
        try:
            if self.analytics:
                return await self.analytics.get_metrics()
            else:
                return {'analytics_disabled': True}
        except Exception as e:
            logger.error("Error getting analytics", error=str(e))
            return {}
    
    async def cleanup(self):
        """Cleanup custom LLM manager."""
        try:
            if self.analytics:
                await self.analytics.cleanup()
            logger.info("Custom LLM Manager cleaned up")
        except Exception as e:
            logger.error("Error cleaning up Custom LLM Manager", error=str(e))
