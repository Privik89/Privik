"""
AI Threat Detection Service for Phase 2
Advanced ML models for email, link, and behavioral threat detection
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import structlog
import json
import hashlib
from dataclasses import dataclass
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import os

logger = structlog.get_logger()


@dataclass
class ThreatPrediction:
    threat_type: str  # phishing, bec, malware, spam
    confidence: float
    threat_score: float
    indicators: List[str]
    model_version: str
    prediction_time: datetime


@dataclass
class ModelMetrics:
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    false_positive_rate: float
    model_version: str
    training_date: datetime


class AIThreatDetection:
    """Advanced AI threat detection system with custom ML models"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.models = {}
        self.vectorizers = {}
        self.scalers = {}
        self.model_metrics = {}
        
        # Model configuration
        self.model_storage_path = config.get('model_storage_path', './models')
        self.retrain_interval = config.get('retrain_interval', 7)  # days
        self.min_training_samples = config.get('min_training_samples', 1000)
        
        # Feature engineering
        self.email_features = EmailFeatureExtractor()
        self.link_features = LinkFeatureExtractor()
        self.behavior_features = BehaviorFeatureExtractor()
        
        # Threat intelligence
        self.threat_intel = ThreatIntelligenceManager(config.get('threat_intel', {}))
        
        # Model versions
        self.current_models = {
            'email_classifier': 'v2.1',
            'link_classifier': 'v2.1',
            'behavior_classifier': 'v2.1',
            'ensemble_classifier': 'v2.1'
        }
        
    async def initialize(self):
        """Initialize AI threat detection system"""
        try:
            logger.info("Initializing AI threat detection system")
            
            # Create model storage directory
            os.makedirs(self.model_storage_path, exist_ok=True)
            
            # Load existing models
            await self._load_models()
            
            # Initialize threat intelligence
            await self.threat_intel.initialize()
            
            # Check if models need retraining
            await self._check_model_health()
            
            logger.info("AI threat detection system initialized successfully")
            return True
            
        except Exception as e:
            logger.error("Failed to initialize AI threat detection system", error=str(e))
            return False
    
    async def _load_models(self):
        """Load existing ML models"""
        try:
            for model_name in self.current_models.keys():
                model_path = os.path.join(self.model_storage_path, f"{model_name}.joblib")
                vectorizer_path = os.path.join(self.model_storage_path, f"{model_name}_vectorizer.joblib")
                scaler_path = os.path.join(self.model_storage_path, f"{model_name}_scaler.joblib")
                
                if os.path.exists(model_path):
                    self.models[model_name] = joblib.load(model_path)
                    logger.info(f"Loaded {model_name} model")
                
                if os.path.exists(vectorizer_path):
                    self.vectorizers[model_name] = joblib.load(vectorizer_path)
                    logger.info(f"Loaded {model_name} vectorizer")
                
                if os.path.exists(scaler_path):
                    self.scalers[model_name] = joblib.load(scaler_path)
                    logger.info(f"Loaded {model_name} scaler")
            
            # If no models exist, train initial models
            if not self.models:
                logger.info("No existing models found, training initial models")
                await self._train_initial_models()
                
        except Exception as e:
            logger.error("Error loading models", error=str(e))
            raise
    
    async def _train_initial_models(self):
        """Train initial ML models with synthetic data"""
        try:
            logger.info("Training initial models with synthetic data")
            
            # Generate synthetic training data
            training_data = await self._generate_synthetic_training_data()
            
            # Train email classifier
            await self._train_email_classifier(training_data['emails'])
            
            # Train link classifier
            await self._train_link_classifier(training_data['links'])
            
            # Train behavior classifier
            await self._train_behavior_classifier(training_data['behaviors'])
            
            # Train ensemble classifier
            await self._train_ensemble_classifier(training_data)
            
            logger.info("Initial models trained successfully")
            
        except Exception as e:
            logger.error("Error training initial models", error=str(e))
            raise
    
    async def _generate_synthetic_training_data(self) -> Dict[str, Any]:
        """Generate synthetic training data for initial model training"""
        try:
            # Email training data
            email_data = {
                'phishing': [
                    "Urgent: Your account will be suspended. Click here to verify: http://fake-bank.com/login",
                    "Congratulations! You've won $1000. Claim your prize now: http://lottery-scam.com",
                    "Security Alert: Unusual login detected. Verify your identity: http://fake-security.com",
                    "Invoice Payment Required: Please pay $500 to avoid service interruption",
                    "Your password will expire in 24 hours. Update now: http://fake-update.com"
                ],
                'bec': [
                    "Hi, I need you to process a wire transfer for $50,000 to vendor account. Urgent.",
                    "Can you send me the bank details for the new supplier? Need to make payment today.",
                    "I'm in a meeting, can you quickly transfer funds to this account? Very urgent.",
                    "Please process the invoice payment to the attached account details.",
                    "I need you to update the vendor payment information immediately."
                ],
                'legitimate': [
                    "Meeting reminder: Project review at 2 PM today in conference room A.",
                    "Please find attached the quarterly report for your review.",
                    "Thank you for your presentation yesterday. Great work on the proposal.",
                    "The team lunch is scheduled for Friday at 12 PM. Please confirm attendance.",
                    "I've updated the project timeline. Please review and let me know your thoughts."
                ]
            }
            
            # Link training data
            link_data = {
                'malicious': [
                    "http://fake-bank-login.com/verify",
                    "https://suspicious-site.net/claim-prize",
                    "http://phishing-site.org/update-account",
                    "https://malicious-domain.com/download",
                    "http://fake-security-alert.com/login"
                ],
                'suspicious': [
                    "https://bit.ly/suspicious-link",
                    "http://short-url.com/redirect",
                    "https://tinyurl.com/suspicious",
                    "http://goo.gl/malicious",
                    "https://t.co/suspicious"
                ],
                'safe': [
                    "https://www.google.com",
                    "https://www.microsoft.com",
                    "https://www.github.com",
                    "https://www.stackoverflow.com",
                    "https://www.linkedin.com"
                ]
            }
            
            # Behavior training data
            behavior_data = {
                'risky': [
                    {"clicks_per_day": 50, "suspicious_click_ratio": 0.3, "time_risk": 0.8},
                    {"clicks_per_day": 30, "suspicious_click_ratio": 0.5, "time_risk": 0.9},
                    {"clicks_per_day": 40, "suspicious_click_ratio": 0.4, "time_risk": 0.7}
                ],
                'normal': [
                    {"clicks_per_day": 10, "suspicious_click_ratio": 0.05, "time_risk": 0.2},
                    {"clicks_per_day": 15, "suspicious_click_ratio": 0.1, "time_risk": 0.3},
                    {"clicks_per_day": 8, "suspicious_click_ratio": 0.02, "time_risk": 0.1}
                ]
            }
            
            return {
                'emails': email_data,
                'links': link_data,
                'behaviors': behavior_data
            }
            
        except Exception as e:
            logger.error("Error generating synthetic training data", error=str(e))
            raise
    
    async def _train_email_classifier(self, email_data: Dict[str, List[str]]):
        """Train email threat classification model"""
        try:
            logger.info("Training email classifier")
            
            # Prepare training data
            texts = []
            labels = []
            
            for threat_type, emails in email_data.items():
                for email in emails:
                    texts.append(email)
                    labels.append(threat_type)
            
            # Create TF-IDF vectorizer
            vectorizer = TfidfVectorizer(
                max_features=5000,
                stop_words='english',
                ngram_range=(1, 3),
                min_df=2
            )
            
            # Fit and transform text data
            X = vectorizer.fit_transform(texts)
            y = np.array(labels)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Train model
            model = GradientBoostingClassifier(
                n_estimators=100,
                learning_rate=0.1,
                max_depth=5,
                random_state=42
            )
            
            model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test)
            accuracy = model.score(X_test, y_test)
            
            # Store model and vectorizer
            self.models['email_classifier'] = model
            self.vectorizers['email_classifier'] = vectorizer
            
            # Save models
            await self._save_model('email_classifier', model, vectorizer)
            
            # Store metrics
            self.model_metrics['email_classifier'] = ModelMetrics(
                accuracy=accuracy,
                precision=0.0,  # Will be calculated properly in production
                recall=0.0,
                f1_score=0.0,
                false_positive_rate=0.0,
                model_version=self.current_models['email_classifier'],
                training_date=datetime.utcnow()
            )
            
            logger.info(f"Email classifier trained with accuracy: {accuracy:.3f}")
            
        except Exception as e:
            logger.error("Error training email classifier", error=str(e))
            raise
    
    async def _train_link_classifier(self, link_data: Dict[str, List[str]]):
        """Train link threat classification model"""
        try:
            logger.info("Training link classifier")
            
            # Prepare training data
            urls = []
            labels = []
            
            for threat_type, links in link_data.items():
                for link in links:
                    urls.append(link)
                    labels.append(threat_type)
            
            # Extract features from URLs
            features = []
            for url in urls:
                feature_vector = self.link_features.extract_features(url)
                features.append(feature_vector)
            
            X = np.array(features)
            y = np.array(labels)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model
            model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            
            model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            accuracy = model.score(X_test_scaled, y_test)
            
            # Store model and scaler
            self.models['link_classifier'] = model
            self.scalers['link_classifier'] = scaler
            
            # Save models
            await self._save_model('link_classifier', model, scaler=scaler)
            
            # Store metrics
            self.model_metrics['link_classifier'] = ModelMetrics(
                accuracy=accuracy,
                precision=0.0,
                recall=0.0,
                f1_score=0.0,
                false_positive_rate=0.0,
                model_version=self.current_models['link_classifier'],
                training_date=datetime.utcnow()
            )
            
            logger.info(f"Link classifier trained with accuracy: {accuracy:.3f}")
            
        except Exception as e:
            logger.error("Error training link classifier", error=str(e))
            raise
    
    async def _train_behavior_classifier(self, behavior_data: Dict[str, List[Dict]]):
        """Train user behavior classification model"""
        try:
            logger.info("Training behavior classifier")
            
            # Prepare training data
            features = []
            labels = []
            
            for behavior_type, behaviors in behavior_data.items():
                for behavior in behaviors:
                    feature_vector = [
                        behavior['clicks_per_day'],
                        behavior['suspicious_click_ratio'],
                        behavior['time_risk']
                    ]
                    features.append(feature_vector)
                    labels.append(behavior_type)
            
            X = np.array(features)
            y = np.array(labels)
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            # Train model
            model = GradientBoostingClassifier(
                n_estimators=50,
                learning_rate=0.1,
                max_depth=3,
                random_state=42
            )
            
            model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            accuracy = model.score(X_test_scaled, y_test)
            
            # Store model and scaler
            self.models['behavior_classifier'] = model
            self.scalers['behavior_classifier'] = scaler
            
            # Save models
            await self._save_model('behavior_classifier', model, scaler=scaler)
            
            # Store metrics
            self.model_metrics['behavior_classifier'] = ModelMetrics(
                accuracy=accuracy,
                precision=0.0,
                recall=0.0,
                f1_score=0.0,
                false_positive_rate=0.0,
                model_version=self.current_models['behavior_classifier'],
                training_date=datetime.utcnow()
            )
            
            logger.info(f"Behavior classifier trained with accuracy: {accuracy:.3f}")
            
        except Exception as e:
            logger.error("Error training behavior classifier", error=str(e))
            raise
    
    async def _train_ensemble_classifier(self, training_data: Dict[str, Any]):
        """Train ensemble classifier that combines all models"""
        try:
            logger.info("Training ensemble classifier")
            
            # This is a simplified ensemble for MVP
            # In production, this would combine predictions from all models
            
            # For now, create a simple rule-based ensemble
            ensemble_model = {
                'type': 'rule_based',
                'rules': {
                    'phishing': 0.7,
                    'bec': 0.6,
                    'malicious_link': 0.8,
                    'risky_behavior': 0.5
                },
                'weights': {
                    'email_classifier': 0.4,
                    'link_classifier': 0.3,
                    'behavior_classifier': 0.3
                }
            }
            
            self.models['ensemble_classifier'] = ensemble_model
            
            # Save ensemble model
            ensemble_path = os.path.join(self.model_storage_path, 'ensemble_classifier.json')
            with open(ensemble_path, 'w') as f:
                json.dump(ensemble_model, f, indent=2)
            
            logger.info("Ensemble classifier trained successfully")
            
        except Exception as e:
            logger.error("Error training ensemble classifier", error=str(e))
            raise
    
    async def predict_email_threat(self, email_data: Dict[str, Any]) -> ThreatPrediction:
        """Predict email threat using AI models"""
        try:
            # Extract email features
            email_features = self.email_features.extract_features(email_data)
            
            # Get email classifier prediction
            if 'email_classifier' in self.models:
                model = self.models['email_classifier']
                vectorizer = self.vectorizers['email_classifier']
                
                # Prepare text for prediction
                email_text = f"{email_data.get('subject', '')} {email_data.get('body_text', '')}"
                X = vectorizer.transform([email_text])
                
                # Get prediction
                prediction = model.predict(X)[0]
                confidence = model.predict_proba(X).max()
                
                # Map prediction to threat type
                threat_type = self._map_prediction_to_threat_type(prediction)
                
                # Calculate threat score
                threat_score = self._calculate_threat_score(threat_type, confidence, email_features)
                
                # Extract indicators
                indicators = self._extract_threat_indicators(email_data, email_features)
                
                return ThreatPrediction(
                    threat_type=threat_type,
                    confidence=confidence,
                    threat_score=threat_score,
                    indicators=indicators,
                    model_version=self.current_models['email_classifier'],
                    prediction_time=datetime.utcnow()
                )
            else:
                # Fallback to heuristic analysis
                return await self._heuristic_email_analysis(email_data)
                
        except Exception as e:
            logger.error("Error predicting email threat", error=str(e))
            return ThreatPrediction(
                threat_type='unknown',
                confidence=0.0,
                threat_score=0.0,
                indicators=['prediction_error'],
                model_version='error',
                prediction_time=datetime.utcnow()
            )
    
    async def predict_link_threat(self, url: str, context: Dict[str, Any]) -> ThreatPrediction:
        """Predict link threat using AI models"""
        try:
            # Extract link features
            link_features = self.link_features.extract_features(url)
            
            # Get link classifier prediction
            if 'link_classifier' in self.models:
                model = self.models['link_classifier']
                scaler = self.scalers['link_classifier']
                
                # Prepare features for prediction
                X = np.array([link_features]).reshape(1, -1)
                X_scaled = scaler.transform(X)
                
                # Get prediction
                prediction = model.predict(X_scaled)[0]
                confidence = model.predict_proba(X_scaled).max()
                
                # Map prediction to threat type
                threat_type = self._map_prediction_to_threat_type(prediction)
                
                # Calculate threat score
                threat_score = self._calculate_threat_score(threat_type, confidence, link_features)
                
                # Extract indicators
                indicators = self._extract_link_indicators(url, link_features)
                
                return ThreatPrediction(
                    threat_type=threat_type,
                    confidence=confidence,
                    threat_score=threat_score,
                    indicators=indicators,
                    model_version=self.current_models['link_classifier'],
                    prediction_time=datetime.utcnow()
                )
            else:
                # Fallback to heuristic analysis
                return await self._heuristic_link_analysis(url)
                
        except Exception as e:
            logger.error("Error predicting link threat", error=str(e))
            return ThreatPrediction(
                threat_type='unknown',
                confidence=0.0,
                threat_score=0.0,
                indicators=['prediction_error'],
                model_version='error',
                prediction_time=datetime.utcnow()
            )
    
    async def predict_behavior_threat(self, user_behavior: Dict[str, Any]) -> ThreatPrediction:
        """Predict user behavior threat using AI models"""
        try:
            # Extract behavior features
            behavior_features = self.behavior_features.extract_features(user_behavior)
            
            # Get behavior classifier prediction
            if 'behavior_classifier' in self.models:
                model = self.models['behavior_classifier']
                scaler = self.scalers['behavior_classifier']
                
                # Prepare features for prediction
                X = np.array([behavior_features]).reshape(1, -1)
                X_scaled = scaler.transform(X)
                
                # Get prediction
                prediction = model.predict(X_scaled)[0]
                confidence = model.predict_proba(X_scaled).max()
                
                # Map prediction to threat type
                threat_type = self._map_prediction_to_threat_type(prediction)
                
                # Calculate threat score
                threat_score = self._calculate_threat_score(threat_type, confidence, behavior_features)
                
                # Extract indicators
                indicators = self._extract_behavior_indicators(user_behavior, behavior_features)
                
                return ThreatPrediction(
                    threat_type=threat_type,
                    confidence=confidence,
                    threat_score=threat_score,
                    indicators=indicators,
                    model_version=self.current_models['behavior_classifier'],
                    prediction_time=datetime.utcnow()
                )
            else:
                # Fallback to heuristic analysis
                return await self._heuristic_behavior_analysis(user_behavior)
                
        except Exception as e:
            logger.error("Error predicting behavior threat", error=str(e))
            return ThreatPrediction(
                threat_type='unknown',
                confidence=0.0,
                threat_score=0.0,
                indicators=['prediction_error'],
                model_version='error',
                prediction_time=datetime.utcnow()
            )
    
    async def ensemble_prediction(self, email_data: Dict[str, Any], 
                                link_data: Dict[str, Any], 
                                behavior_data: Dict[str, Any]) -> ThreatPrediction:
        """Make ensemble prediction combining all models"""
        try:
            # Get individual predictions
            email_pred = await self.predict_email_threat(email_data)
            link_pred = await self.predict_link_threat(link_data.get('url', ''), link_data)
            behavior_pred = await self.predict_behavior_threat(behavior_data)
            
            # Get ensemble model
            ensemble_model = self.models.get('ensemble_classifier', {})
            
            if ensemble_model.get('type') == 'rule_based':
                # Use rule-based ensemble
                threat_score = self._calculate_ensemble_score(
                    email_pred, link_pred, behavior_pred, ensemble_model
                )
                
                # Determine final threat type
                threat_type = self._determine_ensemble_threat_type(
                    email_pred, link_pred, behavior_pred
                )
                
                # Calculate confidence
                confidence = (email_pred.confidence + link_pred.confidence + behavior_pred.confidence) / 3
                
                # Combine indicators
                indicators = list(set(
                    email_pred.indicators + link_pred.indicators + behavior_pred.indicators
                ))
                
                return ThreatPrediction(
                    threat_type=threat_type,
                    confidence=confidence,
                    threat_score=threat_score,
                    indicators=indicators,
                    model_version='ensemble_v2.1',
                    prediction_time=datetime.utcnow()
                )
            else:
                # Fallback to simple averaging
                threat_score = (email_pred.threat_score + link_pred.threat_score + behavior_pred.threat_score) / 3
                confidence = (email_pred.confidence + link_pred.confidence + behavior_pred.confidence) / 3
                
                return ThreatPrediction(
                    threat_type=email_pred.threat_type,
                    confidence=confidence,
                    threat_score=threat_score,
                    indicators=email_pred.indicators,
                    model_version='ensemble_v2.1',
                    prediction_time=datetime.utcnow()
                )
                
        except Exception as e:
            logger.error("Error in ensemble prediction", error=str(e))
            return ThreatPrediction(
                threat_type='unknown',
                confidence=0.0,
                threat_score=0.0,
                indicators=['ensemble_error'],
                model_version='error',
                prediction_time=datetime.utcnow()
            )
    
    def _map_prediction_to_threat_type(self, prediction: str) -> str:
        """Map model prediction to threat type"""
        mapping = {
            'phishing': 'phishing',
            'bec': 'bec',
            'malicious': 'malware',
            'suspicious': 'suspicious',
            'risky': 'risky_behavior',
            'legitimate': 'safe',
            'safe': 'safe'
        }
        return mapping.get(prediction, 'unknown')
    
    def _calculate_threat_score(self, threat_type: str, confidence: float, features: List[float]) -> float:
        """Calculate threat score based on prediction and features"""
        base_scores = {
            'phishing': 0.8,
            'bec': 0.7,
            'malware': 0.9,
            'suspicious': 0.5,
            'risky_behavior': 0.6,
            'safe': 0.1,
            'unknown': 0.3
        }
        
        base_score = base_scores.get(threat_type, 0.3)
        
        # Adjust based on confidence
        adjusted_score = base_score * confidence
        
        # Adjust based on feature indicators
        if features:
            feature_boost = sum(features) / len(features) * 0.2
            adjusted_score += feature_boost
        
        return min(adjusted_score, 1.0)
    
    def _extract_threat_indicators(self, email_data: Dict[str, Any], features: List[float]) -> List[str]:
        """Extract threat indicators from email data"""
        indicators = []
        
        # Check for common phishing indicators
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body_text', '').lower()
        
        if any(word in subject for word in ['urgent', 'action required', 'verify']):
            indicators.append('urgent_language')
        
        if any(word in body for word in ['click here', 'login now', 'verify account']):
            indicators.append('suspicious_links')
        
        if any(word in body for word in ['wire transfer', 'bank transfer', 'urgent payment']):
            indicators.append('bec_indicators')
        
        return indicators
    
    def _extract_link_indicators(self, url: str, features: List[float]) -> List[str]:
        """Extract threat indicators from link data"""
        indicators = []
        
        url_lower = url.lower()
        
        if any(shortener in url_lower for shortener in ['bit.ly', 'tinyurl', 'goo.gl']):
            indicators.append('url_shortener')
        
        if any(keyword in url_lower for keyword in ['login', 'signin', 'verify']):
            indicators.append('login_page')
        
        if any(keyword in url_lower for keyword in ['bank', 'paypal', 'amazon']):
            indicators.append('brand_impersonation')
        
        return indicators
    
    def _extract_behavior_indicators(self, behavior_data: Dict[str, Any], features: List[float]) -> List[str]:
        """Extract threat indicators from behavior data"""
        indicators = []
        
        if behavior_data.get('suspicious_click_ratio', 0) > 0.3:
            indicators.append('high_suspicious_click_ratio')
        
        if behavior_data.get('clicks_per_day', 0) > 30:
            indicators.append('high_click_frequency')
        
        if behavior_data.get('time_risk', 0) > 0.7:
            indicators.append('risky_time_patterns')
        
        return indicators
    
    def _calculate_ensemble_score(self, email_pred: ThreatPrediction, 
                                link_pred: ThreatPrediction, 
                                behavior_pred: ThreatPrediction, 
                                ensemble_model: Dict[str, Any]) -> float:
        """Calculate ensemble threat score"""
        weights = ensemble_model.get('weights', {})
        
        email_weight = weights.get('email_classifier', 0.4)
        link_weight = weights.get('link_classifier', 0.3)
        behavior_weight = weights.get('behavior_classifier', 0.3)
        
        ensemble_score = (
            email_pred.threat_score * email_weight +
            link_pred.threat_score * link_weight +
            behavior_pred.threat_score * behavior_weight
        )
        
        return min(ensemble_score, 1.0)
    
    def _determine_ensemble_threat_type(self, email_pred: ThreatPrediction, 
                                      link_pred: ThreatPrediction, 
                                      behavior_pred: ThreatPrediction) -> str:
        """Determine final threat type from ensemble"""
        # Priority order: malware > phishing > bec > suspicious > risky_behavior > safe
        threat_priority = {
            'malware': 5,
            'phishing': 4,
            'bec': 3,
            'suspicious': 2,
            'risky_behavior': 1,
            'safe': 0
        }
        
        predictions = [email_pred, link_pred, behavior_pred]
        max_priority = -1
        final_threat_type = 'safe'
        
        for pred in predictions:
            priority = threat_priority.get(pred.threat_type, 0)
            if priority > max_priority:
                max_priority = priority
                final_threat_type = pred.threat_type
        
        return final_threat_type
    
    async def _heuristic_email_analysis(self, email_data: Dict[str, Any]) -> ThreatPrediction:
        """Fallback heuristic email analysis"""
        # Simple heuristic analysis when ML models are not available
        threat_score = 0.0
        indicators = []
        
        subject = email_data.get('subject', '').lower()
        body = email_data.get('body_text', '').lower()
        
        # Check for phishing indicators
        if any(word in subject for word in ['urgent', 'verify', 'suspended']):
            threat_score += 0.3
            indicators.append('urgent_language')
        
        if any(word in body for word in ['click here', 'login now']):
            threat_score += 0.2
            indicators.append('suspicious_links')
        
        # Check for BEC indicators
        if any(word in body for word in ['wire transfer', 'bank transfer']):
            threat_score += 0.4
            indicators.append('bec_indicators')
        
        threat_type = 'phishing' if threat_score > 0.5 else 'suspicious' if threat_score > 0.2 else 'safe'
        
        return ThreatPrediction(
            threat_type=threat_type,
            confidence=0.6,
            threat_score=threat_score,
            indicators=indicators,
            model_version='heuristic',
            prediction_time=datetime.utcnow()
        )
    
    async def _heuristic_link_analysis(self, url: str) -> ThreatPrediction:
        """Fallback heuristic link analysis"""
        threat_score = 0.0
        indicators = []
        
        url_lower = url.lower()
        
        # Check for suspicious patterns
        if any(shortener in url_lower for shortener in ['bit.ly', 'tinyurl']):
            threat_score += 0.3
            indicators.append('url_shortener')
        
        if any(keyword in url_lower for keyword in ['login', 'signin']):
            threat_score += 0.4
            indicators.append('login_page')
        
        threat_type = 'malicious' if threat_score > 0.6 else 'suspicious' if threat_score > 0.3 else 'safe'
        
        return ThreatPrediction(
            threat_type=threat_type,
            confidence=0.6,
            threat_score=threat_score,
            indicators=indicators,
            model_version='heuristic',
            prediction_time=datetime.utcnow()
        )
    
    async def _heuristic_behavior_analysis(self, behavior_data: Dict[str, Any]) -> ThreatPrediction:
        """Fallback heuristic behavior analysis"""
        threat_score = 0.0
        indicators = []
        
        if behavior_data.get('suspicious_click_ratio', 0) > 0.3:
            threat_score += 0.4
            indicators.append('high_suspicious_click_ratio')
        
        if behavior_data.get('clicks_per_day', 0) > 30:
            threat_score += 0.2
            indicators.append('high_click_frequency')
        
        threat_type = 'risky_behavior' if threat_score > 0.5 else 'normal'
        
        return ThreatPrediction(
            threat_type=threat_type,
            confidence=0.6,
            threat_score=threat_score,
            indicators=indicators,
            model_version='heuristic',
            prediction_time=datetime.utcnow()
        )
    
    async def _save_model(self, model_name: str, model: Any, vectorizer: Any = None, scaler: Any = None):
        """Save model to disk"""
        try:
            # Save model
            model_path = os.path.join(self.model_storage_path, f"{model_name}.joblib")
            joblib.dump(model, model_path)
            
            # Save vectorizer if provided
            if vectorizer:
                vectorizer_path = os.path.join(self.model_storage_path, f"{model_name}_vectorizer.joblib")
                joblib.dump(vectorizer, vectorizer_path)
            
            # Save scaler if provided
            if scaler:
                scaler_path = os.path.join(self.model_storage_path, f"{model_name}_scaler.joblib")
                joblib.dump(scaler, scaler_path)
            
            logger.info(f"Saved {model_name} model to disk")
            
        except Exception as e:
            logger.error(f"Error saving {model_name} model", error=str(e))
    
    async def _check_model_health(self):
        """Check if models need retraining"""
        try:
            for model_name, metrics in self.model_metrics.items():
                days_since_training = (datetime.utcnow() - metrics.training_date).days
                
                if days_since_training > self.retrain_interval:
                    logger.info(f"{model_name} model is {days_since_training} days old, may need retraining")
                    
        except Exception as e:
            logger.error("Error checking model health", error=str(e))
    
    async def get_model_metrics(self) -> Dict[str, ModelMetrics]:
        """Get model performance metrics"""
        return self.model_metrics
    
    async def retrain_models(self, training_data: Dict[str, Any]):
        """Retrain models with new data"""
        try:
            logger.info("Starting model retraining")
            
            # Retrain email classifier
            if 'emails' in training_data:
                await self._train_email_classifier(training_data['emails'])
            
            # Retrain link classifier
            if 'links' in training_data:
                await self._train_link_classifier(training_data['links'])
            
            # Retrain behavior classifier
            if 'behaviors' in training_data:
                await self._train_behavior_classifier(training_data['behaviors'])
            
            logger.info("Model retraining completed")
            
        except Exception as e:
            logger.error("Error retraining models", error=str(e))
            raise
    
    async def cleanup(self):
        """Cleanup AI threat detection resources"""
        try:
            await self.threat_intel.cleanup()
            logger.info("AI threat detection system cleaned up")
        except Exception as e:
            logger.error("Error cleaning up AI threat detection system", error=str(e))


class EmailFeatureExtractor:
    """Extract features from email data for ML models"""
    
    def extract_features(self, email_data: Dict[str, Any]) -> List[float]:
        """Extract numerical features from email data"""
        features = []
        
        # Text length features
        subject = email_data.get('subject', '')
        body = email_data.get('body_text', '')
        
        features.append(len(subject))
        features.append(len(body))
        features.append(len(subject.split()))
        features.append(len(body.split()))
        
        # URL count
        import re
        url_pattern = r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        urls = re.findall(url_pattern, body)
        features.append(len(urls))
        
        # Suspicious word counts
        suspicious_words = ['urgent', 'verify', 'suspended', 'click', 'login', 'password']
        suspicious_count = sum(1 for word in suspicious_words if word in body.lower())
        features.append(suspicious_count)
        
        # BEC word counts
        bec_words = ['wire transfer', 'bank transfer', 'urgent payment', 'vendor payment']
        bec_count = sum(1 for phrase in bec_words if phrase in body.lower())
        features.append(bec_count)
        
        return features


class LinkFeatureExtractor:
    """Extract features from URL data for ML models"""
    
    def extract_features(self, url: str) -> List[float]:
        """Extract numerical features from URL"""
        features = []
        
        # URL length
        features.append(len(url))
        
        # Domain length
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc
        features.append(len(domain))
        
        # Path length
        features.append(len(parsed.path))
        
        # Query parameter count
        features.append(len(parsed.query.split('&')) if parsed.query else 0)
        
        # Suspicious patterns
        url_lower = url.lower()
        suspicious_patterns = ['bit.ly', 'tinyurl', 'goo.gl', 't.co']
        suspicious_count = sum(1 for pattern in suspicious_patterns if pattern in url_lower)
        features.append(suspicious_count)
        
        # Login-related patterns
        login_patterns = ['login', 'signin', 'auth', 'verify']
        login_count = sum(1 for pattern in login_patterns if pattern in url_lower)
        features.append(login_count)
        
        return features


class BehaviorFeatureExtractor:
    """Extract features from user behavior data for ML models"""
    
    def extract_features(self, behavior_data: Dict[str, Any]) -> List[float]:
        """Extract numerical features from behavior data"""
        features = []
        
        # Click frequency
        features.append(behavior_data.get('clicks_per_day', 0))
        
        # Suspicious click ratio
        features.append(behavior_data.get('suspicious_click_ratio', 0))
        
        # Time risk
        features.append(behavior_data.get('time_risk', 0))
        
        # Additional behavior metrics
        features.append(behavior_data.get('unusual_sender_count', 0))
        features.append(behavior_data.get('external_domain_ratio', 0))
        
        return features


class ThreatIntelligenceManager:
    """Manage threat intelligence feeds and indicators"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.threat_feeds = {}
        self.indicator_cache = {}
        
    async def initialize(self):
        """Initialize threat intelligence manager"""
        try:
            # Initialize threat feeds
            # In production, this would connect to real threat feeds
            logger.info("Threat intelligence manager initialized")
            return True
        except Exception as e:
            logger.error("Failed to initialize threat intelligence manager", error=str(e))
            return False
    
    async def lookup_indicator(self, indicator: str, indicator_type: str) -> Dict[str, Any]:
        """Lookup threat intelligence for an indicator"""
        # Simplified for MVP
        # In production, this would query real threat feeds
        return {
            'indicator': indicator,
            'type': indicator_type,
            'threat_score': 0.0,
            'confidence': 0.0,
            'sources': []
        }
    
    async def cleanup(self):
        """Cleanup threat intelligence resources"""
        pass
