"""
Privik AI Threat Detection Engine
Advanced machine learning-based threat detection
"""

import asyncio
import time
import json
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import structlog

# AI/ML imports
try:
    import torch
    import torch.nn as nn
    from transformers import AutoTokenizer, AutoModel
    from sklearn.ensemble import RandomForestClassifier, IsolationForest
    from sklearn.feature_extraction.text import TfidfVectorizer
    import joblib
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

from ..config import AgentConfig
from ..security import SecurityManager

logger = structlog.get_logger()

class ThreatDetector:
    """Advanced AI-powered threat detection engine."""
    
    def __init__(self, config: AgentConfig, security_manager: SecurityManager):
        """Initialize the threat detector."""
        self.config = config
        self.security_manager = security_manager
        self.models_loaded = False
        self.models = {}
        
        # AI model paths
        self.model_dir = Path(__file__).parent / "models"
        self.model_dir.mkdir(exist_ok=True)
        
        # Feature extractors
        self.text_vectorizer = None
        self.url_vectorizer = None
        
        # Model configurations
        self.model_configs = {
            'phishing': {
                'type': 'transformer',
                'model_name': 'distilbert-base-uncased',
                'threshold': 0.7
            },
            'malware': {
                'type': 'random_forest',
                'features': ['file_size', 'entropy', 'strings', 'imports'],
                'threshold': 0.6
            },
            'behavior': {
                'type': 'isolation_forest',
                'contamination': 0.1,
                'threshold': 0.5
            },
            'user_risk': {
                'type': 'gradient_boosting',
                'features': ['click_rate', 'download_rate', 'suspicious_actions'],
                'threshold': 0.4
            }
        }
    
    async def initialize(self) -> bool:
        """Initialize AI models and load pre-trained weights."""
        try:
            if not AI_AVAILABLE:
                logger.warning("AI libraries not available, using rule-based detection")
                return False
            
            logger.info("Initializing AI threat detection engine...")
            
            # Load or download models
            await self._load_models()
            
            # Initialize feature extractors
            await self._initialize_feature_extractors()
            
            self.models_loaded = True
            logger.info("AI threat detection engine initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize AI threat detector", error=str(e))
            return False
    
    async def _load_models(self):
        """Load or download AI models."""
        try:
            # Load phishing detection model
            await self._load_phishing_model()
            
            # Load malware classification model
            await self._load_malware_model()
            
            # Load behavior analysis model
            await self._load_behavior_model()
            
            # Load user risk profiling model
            await self._load_user_risk_model()
            
        except Exception as e:
            logger.error("Error loading AI models", error=str(e))
            raise
    
    async def _load_phishing_model(self):
        """Load phishing detection transformer model."""
        try:
            model_config = self.model_configs['phishing']
            model_path = self.model_dir / "phishing_detector"
            
            if model_path.exists():
                # Load local model
                self.models['phishing'] = {
                    'tokenizer': AutoTokenizer.from_pretrained(str(model_path)),
                    'model': AutoModel.from_pretrained(str(model_path))
                }
            else:
                # Download and fine-tune base model
                logger.info("Downloading base phishing detection model...")
                self.models['phishing'] = {
                    'tokenizer': AutoTokenizer.from_pretrained(model_config['model_name']),
                    'model': AutoModel.from_pretrained(model_config['model_name'])
                }
                
                # Save model for future use
                self.models['phishing']['tokenizer'].save_pretrained(str(model_path))
                self.models['phishing']['model'].save_pretrained(str(model_path))
            
            logger.info("Phishing detection model loaded")
            
        except Exception as e:
            logger.error("Error loading phishing model", error=str(e))
    
    async def _load_malware_model(self):
        """Load malware classification model."""
        try:
            model_path = self.model_dir / "malware_classifier.pkl"
            
            if model_path.exists():
                self.models['malware'] = joblib.load(model_path)
            else:
                # Create and train a new model
                self.models['malware'] = RandomForestClassifier(
                    n_estimators=100,
                    max_depth=10,
                    random_state=42
                )
                
                # Train with sample data (in production, use real malware dataset)
                await self._train_malware_model()
                
                # Save model
                joblib.dump(self.models['malware'], model_path)
            
            logger.info("Malware classification model loaded")
            
        except Exception as e:
            logger.error("Error loading malware model", error=str(e))
    
    async def _load_behavior_model(self):
        """Load behavior analysis model."""
        try:
            model_path = self.model_dir / "behavior_analyzer.pkl"
            
            if model_path.exists():
                self.models['behavior'] = joblib.load(model_path)
            else:
                # Create isolation forest for anomaly detection
                self.models['behavior'] = IsolationForest(
                    contamination=0.1,
                    random_state=42
                )
                
                # Train with sample data
                await self._train_behavior_model()
                
                # Save model
                joblib.dump(self.models['behavior'], model_path)
            
            logger.info("Behavior analysis model loaded")
            
        except Exception as e:
            logger.error("Error loading behavior model", error=str(e))
    
    async def _load_user_risk_model(self):
        """Load user risk profiling model."""
        try:
            model_path = self.model_dir / "user_risk_profiler.pkl"
            
            if model_path.exists():
                self.models['user_risk'] = joblib.load(model_path)
            else:
                # Create gradient boosting model
                from sklearn.ensemble import GradientBoostingClassifier
                self.models['user_risk'] = GradientBoostingClassifier(
                    n_estimators=100,
                    learning_rate=0.1,
                    random_state=42
                )
                
                # Train with sample data
                await self._train_user_risk_model()
                
                # Save model
                joblib.dump(self.models['user_risk'], model_path)
            
            logger.info("User risk profiling model loaded")
            
        except Exception as e:
            logger.error("Error loading user risk model", error=str(e))
    
    async def _initialize_feature_extractors(self):
        """Initialize text and URL feature extractors."""
        try:
            # Text vectorizer for email content
            self.text_vectorizer = TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 2),
                stop_words='english'
            )
            
            # URL vectorizer for link analysis
            self.url_vectorizer = TfidfVectorizer(
                max_features=500,
                ngram_range=(1, 3),
                analyzer='char'
            )
            
            logger.info("Feature extractors initialized")
            
        except Exception as e:
            logger.error("Error initializing feature extractors", error=str(e))
    
    async def detect_threats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive threat detection using AI models."""
        try:
            if not self.models_loaded:
                return await self._rule_based_detection(data)
            
            results = {
                'threat_score': 0,
                'ai_confidence': 0,
                'threat_type': None,
                'ai_indicators': [],
                'model_predictions': {}
            }
            
            # Phishing detection
            if 'email_content' in data or 'url' in data:
                phishing_result = await self._detect_phishing(data)
                results['model_predictions']['phishing'] = phishing_result
                if phishing_result['is_threat']:
                    results['threat_score'] += phishing_result['score'] * 0.4
                    results['threat_type'] = 'phishing'
            
            # Malware detection
            if 'file_data' in data:
                malware_result = await self._detect_malware(data)
                results['model_predictions']['malware'] = malware_result
                if malware_result['is_threat']:
                    results['threat_score'] += malware_result['score'] * 0.4
                    results['threat_type'] = 'malware'
            
            # Behavior analysis
            behavior_result = await self._analyze_behavior(data)
            results['model_predictions']['behavior'] = behavior_result
            if behavior_result['is_anomaly']:
                results['threat_score'] += behavior_result['score'] * 0.2
                if not results['threat_type']:
                    results['threat_type'] = 'suspicious_behavior'
            
            # Calculate overall confidence
            predictions = list(results['model_predictions'].values())
            if predictions:
                results['ai_confidence'] = np.mean([p.get('confidence', 0) for p in predictions])
            
            # Normalize threat score
            results['threat_score'] = min(results['threat_score'], 100)
            
            return results
            
        except Exception as e:
            logger.error("Error in AI threat detection", error=str(e))
            return await self._rule_based_detection(data)
    
    async def _detect_phishing(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect phishing using transformer model."""
        try:
            text_content = ""
            if 'email_content' in data:
                text_content = data['email_content']
            elif 'url' in data:
                text_content = data['url']
            
            if not text_content:
                return {'is_threat': False, 'score': 0, 'confidence': 0}
            
            # Tokenize text
            inputs = self.models['phishing']['tokenizer'](
                text_content,
                truncation=True,
                padding=True,
                max_length=512,
                return_tensors='pt'
            )
            
            # Get model predictions
            with torch.no_grad():
                outputs = self.models['phishing']['model'](**inputs)
                predictions = torch.softmax(outputs.logits, dim=1)
                phishing_prob = predictions[0][1].item()
            
            threshold = self.model_configs['phishing']['threshold']
            is_threat = phishing_prob > threshold
            
            return {
                'is_threat': is_threat,
                'score': phishing_prob * 100,
                'confidence': phishing_prob,
                'model_type': 'transformer'
            }
            
        except Exception as e:
            logger.error("Error in phishing detection", error=str(e))
            return {'is_threat': False, 'score': 0, 'confidence': 0}
    
    async def _detect_malware(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Detect malware using machine learning model."""
        try:
            file_data = data.get('file_data', {})
            
            # Extract features
            features = self._extract_malware_features(file_data)
            
            if not features:
                return {'is_threat': False, 'score': 0, 'confidence': 0}
            
            # Make prediction
            prediction = self.models['malware'].predict_proba([features])[0]
            malware_prob = prediction[1]  # Probability of being malware
            
            threshold = self.model_configs['malware']['threshold']
            is_threat = malware_prob > threshold
            
            return {
                'is_threat': is_threat,
                'score': malware_prob * 100,
                'confidence': malware_prob,
                'model_type': 'random_forest',
                'features_used': list(self.model_configs['malware']['features'])
            }
            
        except Exception as e:
            logger.error("Error in malware detection", error=str(e))
            return {'is_threat': False, 'score': 0, 'confidence': 0}
    
    async def _analyze_behavior(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user behavior for anomalies."""
        try:
            behavior_data = data.get('behavior_data', {})
            
            # Extract behavior features
            features = self._extract_behavior_features(behavior_data)
            
            if not features:
                return {'is_anomaly': False, 'score': 0, 'confidence': 0}
            
            # Make prediction
            anomaly_score = self.models['behavior'].score_samples([features])[0]
            normalized_score = 1 - (anomaly_score + 0.5)  # Convert to 0-1 scale
            
            threshold = self.model_configs['behavior']['threshold']
            is_anomaly = normalized_score > threshold
            
            return {
                'is_anomaly': is_anomaly,
                'score': normalized_score * 100,
                'confidence': normalized_score,
                'model_type': 'isolation_forest'
            }
            
        except Exception as e:
            logger.error("Error in behavior analysis", error=str(e))
            return {'is_anomaly': False, 'score': 0, 'confidence': 0}
    
    def _extract_malware_features(self, file_data: Dict[str, Any]) -> List[float]:
        """Extract features for malware classification."""
        try:
            features = []
            
            # File size
            features.append(file_data.get('size', 0))
            
            # Entropy (randomness measure)
            features.append(file_data.get('entropy', 0))
            
            # Number of suspicious strings
            features.append(len(file_data.get('suspicious_strings', [])))
            
            # Number of imports
            features.append(len(file_data.get('imports', [])))
            
            return features
            
        except Exception as e:
            logger.error("Error extracting malware features", error=str(e))
            return []
    
    def _extract_behavior_features(self, behavior_data: Dict[str, Any]) -> List[float]:
        """Extract features for behavior analysis."""
        try:
            features = []
            
            # Click rate
            features.append(behavior_data.get('click_rate', 0))
            
            # Download rate
            features.append(behavior_data.get('download_rate', 0))
            
            # Suspicious action count
            features.append(behavior_data.get('suspicious_actions', 0))
            
            # Time-based patterns
            features.append(behavior_data.get('hour_of_day', 12))
            features.append(behavior_data.get('day_of_week', 3))
            
            return features
            
        except Exception as e:
            logger.error("Error extracting behavior features", error=str(e))
            return []
    
    async def _rule_based_detection(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback to rule-based detection when AI is not available."""
        try:
            threat_score = 0
            indicators = []
            
            # Basic rule-based checks
            if 'email_content' in data:
                content = data['email_content'].lower()
                if any(word in content for word in ['urgent', 'account suspended', 'verify']):
                    threat_score += 20
                    indicators.append('suspicious_keywords')
            
            if 'url' in data:
                url = data['url'].lower()
                if any(domain in url for domain in ['bit.ly', 'tinyurl.com']):
                    threat_score += 15
                    indicators.append('suspicious_domain')
            
            return {
                'threat_score': min(threat_score, 100),
                'ai_confidence': 0,
                'threat_type': 'rule_based' if threat_score > 0 else None,
                'ai_indicators': indicators,
                'model_predictions': {}
            }
            
        except Exception as e:
            logger.error("Error in rule-based detection", error=str(e))
            return {'threat_score': 0, 'ai_confidence': 0}
    
    async def _train_malware_model(self):
        """Train malware classification model with sample data."""
        try:
            # Sample training data (in production, use real malware dataset)
            X_train = [
                [1024, 7.2, 5, 10],    # Benign file
                [2048, 6.8, 3, 8],     # Benign file
                [512, 8.1, 15, 25],    # Malware
                [4096, 7.9, 20, 30],   # Malware
            ]
            y_train = [0, 0, 1, 1]  # 0=benign, 1=malware
            
            self.models['malware'].fit(X_train, y_train)
            logger.info("Malware model trained with sample data")
            
        except Exception as e:
            logger.error("Error training malware model", error=str(e))
    
    async def _train_behavior_model(self):
        """Train behavior analysis model with sample data."""
        try:
            # Sample training data
            X_train = [
                [0.1, 0.05, 0, 12, 3],   # Normal behavior
                [0.2, 0.1, 1, 14, 4],    # Normal behavior
                [0.8, 0.6, 5, 2, 1],     # Anomalous behavior
                [0.9, 0.7, 8, 1, 0],     # Anomalous behavior
            ]
            
            self.models['behavior'].fit(X_train)
            logger.info("Behavior model trained with sample data")
            
        except Exception as e:
            logger.error("Error training behavior model", error=str(e))
    
    async def _train_user_risk_model(self):
        """Train user risk profiling model with sample data."""
        try:
            # Sample training data
            X_train = [
                [0.1, 0.05, 0],    # Low risk user
                [0.2, 0.1, 1],     # Low risk user
                [0.8, 0.6, 5],     # High risk user
                [0.9, 0.7, 8],     # High risk user
            ]
            y_train = [0, 0, 1, 1]  # 0=low risk, 1=high risk
            
            self.models['user_risk'].fit(X_train, y_train)
            logger.info("User risk model trained with sample data")
            
        except Exception as e:
            logger.error("Error training user risk model", error=str(e))
    
    async def update_models(self, model_updates: Dict[str, Any]) -> bool:
        """Update AI models with new training data."""
        try:
            logger.info("Updating AI models...")
            
            # Update each model type
            for model_type, update_data in model_updates.items():
                if model_type in self.models:
                    await self._update_model(model_type, update_data)
            
            logger.info("AI models updated successfully")
            return True
            
        except Exception as e:
            logger.error("Error updating AI models", error=str(e))
            return False
    
    async def _update_model(self, model_type: str, update_data: Dict[str, Any]):
        """Update a specific model with new data."""
        try:
            if model_type == 'malware':
                # Incremental learning for malware model
                X_new = update_data.get('features', [])
                y_new = update_data.get('labels', [])
                
                if X_new and y_new:
                    self.models['malware'].partial_fit(X_new, y_new)
            
            elif model_type == 'behavior':
                # Update behavior model
                X_new = update_data.get('features', [])
                if X_new:
                    self.models['behavior'].fit(X_new)
            
            logger.info(f"Updated {model_type} model")
            
        except Exception as e:
            logger.error(f"Error updating {model_type} model", error=str(e))
