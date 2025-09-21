"""
ML Training Pipeline Service
Handles machine learning model training and continuous learning
"""

import asyncio
import json
import pickle
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import structlog
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib
from ..core.config import get_settings
from ..services.cache_manager import cache_manager
from ..services.logging_service import logging_service

logger = structlog.get_logger()

class MLTrainingPipeline:
    """Manages ML model training and continuous learning"""
    
    def __init__(self):
        self.models_dir = Path("models")
        self.models_dir.mkdir(exist_ok=True)
        
        self.models = {
            'email_classifier': None,
            'domain_classifier': None,
            'behavior_classifier': None,
            'ensemble_classifier': None
        }
        
        self.feature_extractors = {
            'email_tfidf': TfidfVectorizer(max_features=1000, stop_words='english'),
            'domain_tfidf': TfidfVectorizer(max_features=500, stop_words='english')
        }
        
        self.scalers = {
            'email_scaler': StandardScaler(),
            'domain_scaler': StandardScaler(),
            'behavior_scaler': StandardScaler()
        }
        
        self.label_encoders = {
            'email_labels': LabelEncoder(),
            'domain_labels': LabelEncoder(),
            'behavior_labels': LabelEncoder()
        }
    
    async def collect_training_data(self, days_back: int = 30) -> Dict[str, pd.DataFrame]:
        """Collect training data from various sources"""
        try:
            training_data = {}
            
            # Collect email analysis data
            email_data = await self._collect_email_training_data(days_back)
            if not email_data.empty:
                training_data['emails'] = email_data
                logger.info("Collected email training data", count=len(email_data))
            
            # Collect domain reputation data
            domain_data = await self._collect_domain_training_data(days_back)
            if not domain_data.empty:
                training_data['domains'] = domain_data
                logger.info("Collected domain training data", count=len(domain_data))
            
            # Collect behavioral data
            behavior_data = await self._collect_behavior_training_data(days_back)
            if not behavior_data.empty:
                training_data['behavior'] = behavior_data
                logger.info("Collected behavior training data", count=len(behavior_data))
            
            return training_data
            
        except Exception as e:
            logger.error("Error collecting training data", error=str(e))
            return {}
    
    async def _collect_email_training_data(self, days_back: int) -> pd.DataFrame:
        """Collect email analysis training data"""
        try:
            # This would typically query your database for email analysis results
            # For now, we'll create sample data structure
            sample_data = []
            
            # Sample email features
            email_features = [
                {
                    'subject': 'Urgent: Verify your account',
                    'sender_domain': 'suspicious-domain.com',
                    'has_attachment': True,
                    'attachment_count': 1,
                    'link_count': 2,
                    'urgent_keywords': 1,
                    'threat_score': 0.85,
                    'ai_verdict': 'phishing',
                    'user_feedback': 'confirmed_malicious'
                },
                {
                    'subject': 'Meeting reminder for tomorrow',
                    'sender_domain': 'company.com',
                    'has_attachment': False,
                    'attachment_count': 0,
                    'link_count': 0,
                    'urgent_keywords': 0,
                    'threat_score': 0.15,
                    'ai_verdict': 'safe',
                    'user_feedback': 'confirmed_safe'
                }
            ]
            
            for feature in email_features:
                sample_data.append({
                    'text_content': f"{feature['subject']} from {feature['sender_domain']}",
                    'sender_domain': feature['sender_domain'],
                    'has_attachment': feature['has_attachment'],
                    'attachment_count': feature['attachment_count'],
                    'link_count': feature['link_count'],
                    'urgent_keywords': feature['urgent_keywords'],
                    'threat_score': feature['threat_score'],
                    'label': feature['user_feedback']
                })
            
            return pd.DataFrame(sample_data)
            
        except Exception as e:
            logger.error("Error collecting email training data", error=str(e))
            return pd.DataFrame()
    
    async def _collect_domain_training_data(self, days_back: int) -> pd.DataFrame:
        """Collect domain reputation training data"""
        try:
            # Sample domain features
            domain_features = [
                {
                    'domain': 'malicious-site.com',
                    'age_days': 30,
                    'registrar': 'suspicious_registrar',
                    'has_mx_record': False,
                    'has_spf_record': False,
                    'reputation_score': 0.1,
                    'threat_indicators': 5,
                    'label': 'malicious'
                },
                {
                    'domain': 'trusted-company.com',
                    'age_days': 3650,
                    'registrar': 'legitimate_registrar',
                    'has_mx_record': True,
                    'has_spf_record': True,
                    'reputation_score': 0.9,
                    'threat_indicators': 0,
                    'label': 'legitimate'
                }
            ]
            
            sample_data = []
            for feature in domain_features:
                sample_data.append({
                    'domain': feature['domain'],
                    'age_days': feature['age_days'],
                    'registrar': feature['registrar'],
                    'has_mx_record': feature['has_mx_record'],
                    'has_spf_record': feature['has_spf_record'],
                    'reputation_score': feature['reputation_score'],
                    'threat_indicators': feature['threat_indicators'],
                    'label': feature['label']
                })
            
            return pd.DataFrame(sample_data)
            
        except Exception as e:
            logger.error("Error collecting domain training data", error=str(e))
            return pd.DataFrame()
    
    async def _collect_behavior_training_data(self, days_back: int) -> pd.DataFrame:
        """Collect user behavior training data"""
        try:
            # Sample behavior features
            behavior_features = [
                {
                    'user_id': 'user1',
                    'emails_per_day': 50,
                    'click_rate': 0.3,
                    'attachment_open_rate': 0.1,
                    'suspicious_click_rate': 0.05,
                    'time_variance': 2.5,
                    'label': 'normal'
                },
                {
                    'user_id': 'user2',
                    'emails_per_day': 200,
                    'click_rate': 0.8,
                    'attachment_open_rate': 0.9,
                    'suspicious_click_rate': 0.4,
                    'time_variance': 8.2,
                    'label': 'suspicious'
                }
            ]
            
            sample_data = []
            for feature in behavior_features:
                sample_data.append({
                    'user_id': feature['user_id'],
                    'emails_per_day': feature['emails_per_day'],
                    'click_rate': feature['click_rate'],
                    'attachment_open_rate': feature['attachment_open_rate'],
                    'suspicious_click_rate': feature['suspicious_click_rate'],
                    'time_variance': feature['time_variance'],
                    'label': feature['label']
                })
            
            return pd.DataFrame(sample_data)
            
        except Exception as e:
            logger.error("Error collecting behavior training data", error=str(e))
            return pd.DataFrame()
    
    async def train_email_classifier(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """Train email classification model"""
        try:
            if training_data.empty:
                logger.warning("No email training data available")
                return {"error": "No training data"}
            
            # Prepare features
            X_text = self.feature_extractors['email_tfidf'].fit_transform(training_data['text_content'])
            X_numeric = training_data[['has_attachment', 'attachment_count', 'link_count', 'urgent_keywords', 'threat_score']].values
            
            # Combine features
            X = np.hstack([X_text.toarray(), X_numeric])
            
            # Prepare labels
            y = self.label_encoders['email_labels'].fit_transform(training_data['label'])
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Scale features
            X_train_scaled = self.scalers['email_scaler'].fit_transform(X_train)
            X_test_scaled = self.scalers['email_scaler'].transform(X_test)
            
            # Train multiple models
            models = {
                'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
                'gradient_boosting': GradientBoostingClassifier(n_estimators=100, random_state=42),
                'neural_network': MLPClassifier(hidden_layer_sizes=(100, 50), max_iter=500, random_state=42)
            }
            
            results = {}
            for name, model in models.items():
                # Train model
                model.fit(X_train_scaled, y_train)
                
                # Evaluate
                y_pred = model.predict(X_test_scaled)
                accuracy = accuracy_score(y_test, y_pred)
                
                # Cross-validation
                cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
                
                results[name] = {
                    'accuracy': accuracy,
                    'cv_mean': cv_scores.mean(),
                    'cv_std': cv_scores.std(),
                    'model': model
                }
                
                logger.info(f"Trained {name}", accuracy=accuracy, cv_mean=cv_scores.mean())
            
            # Select best model
            best_model_name = max(results.keys(), key=lambda k: results[k]['cv_mean'])
            best_model = results[best_model_name]['model']
            
            # Save model and components
            model_path = self.models_dir / 'email_classifier.joblib'
            joblib.dump({
                'model': best_model,
                'scaler': self.scalers['email_scaler'],
                'vectorizer': self.feature_extractors['email_tfidf'],
                'label_encoder': self.label_encoders['email_labels'],
                'feature_names': ['text_features', 'has_attachment', 'attachment_count', 'link_count', 'urgent_keywords', 'threat_score']
            }, model_path)
            
            self.models['email_classifier'] = best_model
            
            # Log training completion
            await logging_service.log_application_event(
                'info',
                'Email classifier training completed',
                model_name=best_model_name,
                accuracy=results[best_model_name]['accuracy'],
                cv_score=results[best_model_name]['cv_mean']
            )
            
            return {
                'success': True,
                'best_model': best_model_name,
                'accuracy': results[best_model_name]['accuracy'],
                'cv_score': results[best_model_name]['cv_mean'],
                'all_results': results
            }
            
        except Exception as e:
            logger.error("Error training email classifier", error=str(e))
            await logging_service.log_error_event(e, {'operation': 'email_classifier_training'})
            return {"error": str(e)}
    
    async def train_domain_classifier(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """Train domain classification model"""
        try:
            if training_data.empty:
                logger.warning("No domain training data available")
                return {"error": "No training data"}
            
            # Prepare features
            X = training_data[['age_days', 'has_mx_record', 'has_spf_record', 'reputation_score', 'threat_indicators']].values
            y = self.label_encoders['domain_labels'].fit_transform(training_data['label'])
            
            # Split and scale data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            X_train_scaled = self.scalers['domain_scaler'].fit_transform(X_train)
            X_test_scaled = self.scalers['domain_scaler'].transform(X_test)
            
            # Train model
            model = RandomForestClassifier(n_estimators=100, random_state=42)
            model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
            
            # Save model
            model_path = self.models_dir / 'domain_classifier.joblib'
            joblib.dump({
                'model': model,
                'scaler': self.scalers['domain_scaler'],
                'label_encoder': self.label_encoders['domain_labels'],
                'feature_names': ['age_days', 'has_mx_record', 'has_spf_record', 'reputation_score', 'threat_indicators']
            }, model_path)
            
            self.models['domain_classifier'] = model
            
            logger.info("Trained domain classifier", accuracy=accuracy, cv_mean=cv_scores.mean())
            
            return {
                'success': True,
                'accuracy': accuracy,
                'cv_score': cv_scores.mean()
            }
            
        except Exception as e:
            logger.error("Error training domain classifier", error=str(e))
            return {"error": str(e)}
    
    async def train_behavior_classifier(self, training_data: pd.DataFrame) -> Dict[str, Any]:
        """Train user behavior classification model"""
        try:
            if training_data.empty:
                logger.warning("No behavior training data available")
                return {"error": "No training data"}
            
            # Prepare features
            X = training_data[['emails_per_day', 'click_rate', 'attachment_open_rate', 'suspicious_click_rate', 'time_variance']].values
            y = self.label_encoders['behavior_labels'].fit_transform(training_data['label'])
            
            # Split and scale data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            X_train_scaled = self.scalers['behavior_scaler'].fit_transform(X_train)
            X_test_scaled = self.scalers['behavior_scaler'].transform(X_test)
            
            # Train model
            model = MLPClassifier(hidden_layer_sizes=(50, 25), max_iter=500, random_state=42)
            model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5)
            
            # Save model
            model_path = self.models_dir / 'behavior_classifier.joblib'
            joblib.dump({
                'model': model,
                'scaler': self.scalers['behavior_scaler'],
                'label_encoder': self.label_encoders['behavior_labels'],
                'feature_names': ['emails_per_day', 'click_rate', 'attachment_open_rate', 'suspicious_click_rate', 'time_variance']
            }, model_path)
            
            self.models['behavior_classifier'] = model
            
            logger.info("Trained behavior classifier", accuracy=accuracy, cv_mean=cv_scores.mean())
            
            return {
                'success': True,
                'accuracy': accuracy,
                'cv_score': cv_scores.mean()
            }
            
        except Exception as e:
            logger.error("Error training behavior classifier", error=str(e))
            return {"error": str(e)}
    
    async def train_ensemble_model(self, training_data: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Train ensemble model combining all classifiers"""
        try:
            ensemble_features = []
            ensemble_labels = []
            
            # Combine features from all data sources
            if 'emails' in training_data:
                email_features = training_data['emails'][['threat_score', 'urgent_keywords', 'attachment_count']].values
                ensemble_features.extend(email_features)
                ensemble_labels.extend(['email'] * len(email_features))
            
            if 'domains' in training_data:
                domain_features = training_data['domains'][['reputation_score', 'threat_indicators']].values
                ensemble_features.extend(domain_features)
                ensemble_labels.extend(['domain'] * len(domain_features))
            
            if 'behavior' in training_data:
                behavior_features = training_data['behavior'][['suspicious_click_rate', 'time_variance']].values
                ensemble_features.extend(behavior_features)
                ensemble_labels.extend(['behavior'] * len(behavior_features))
            
            if not ensemble_features:
                return {"error": "No ensemble training data"}
            
            # Convert to numpy arrays
            X = np.array(ensemble_features)
            y = np.array(ensemble_labels)
            
            # Train ensemble model
            model = GradientBoostingClassifier(n_estimators=100, random_state=42)
            model.fit(X, y)
            
            # Save ensemble model
            model_path = self.models_dir / 'ensemble_classifier.joblib'
            joblib.dump({
                'model': model,
                'feature_names': ['threat_score', 'urgent_keywords', 'attachment_count', 'reputation_score', 'threat_indicators', 'suspicious_click_rate', 'time_variance']
            }, model_path)
            
            self.models['ensemble_classifier'] = model
            
            logger.info("Trained ensemble classifier")
            
            return {
                'success': True,
                'feature_count': len(ensemble_features),
                'label_count': len(set(ensemble_labels))
            }
            
        except Exception as e:
            logger.error("Error training ensemble model", error=str(e))
            return {"error": str(e)}
    
    async def run_full_training_pipeline(self, days_back: int = 30) -> Dict[str, Any]:
        """Run complete ML training pipeline"""
        try:
            logger.info("Starting ML training pipeline", days_back=days_back)
            
            # Collect training data
            training_data = await self.collect_training_data(days_back)
            
            if not training_data:
                return {"error": "No training data collected"}
            
            results = {}
            
            # Train individual models
            if 'emails' in training_data:
                email_result = await self.train_email_classifier(training_data['emails'])
                results['email_classifier'] = email_result
            
            if 'domains' in training_data:
                domain_result = await self.train_domain_classifier(training_data['domains'])
                results['domain_classifier'] = domain_result
            
            if 'behavior' in training_data:
                behavior_result = await self.train_behavior_classifier(training_data['behavior'])
                results['behavior_classifier'] = behavior_result
            
            # Train ensemble model
            ensemble_result = await self.train_ensemble_model(training_data)
            results['ensemble_classifier'] = ensemble_result
            
            # Cache models for fast access
            await self._cache_models()
            
            # Log training completion
            await logging_service.log_application_event(
                'info',
                'ML training pipeline completed',
                results=results
            )
            
            return {
                'success': True,
                'training_data_counts': {k: len(v) for k, v in training_data.items()},
                'model_results': results
            }
            
        except Exception as e:
            logger.error("Error in training pipeline", error=str(e))
            await logging_service.log_error_event(e, {'operation': 'full_training_pipeline'})
            return {"error": str(e)}
    
    async def _cache_models(self):
        """Cache trained models for fast access"""
        try:
            for model_name, model in self.models.items():
                if model is not None:
                    await cache_manager.set(
                        f"model_{model_name}",
                        {
                            'model_type': type(model).__name__,
                            'trained_at': datetime.now().isoformat(),
                            'status': 'ready'
                        },
                        ttl=86400,  # 24 hours
                        namespace="ml_models"
                    )
            
            logger.info("Cached ML models")
            
        except Exception as e:
            logger.error("Error caching models", error=str(e))
    
    async def load_models(self):
        """Load pre-trained models from disk"""
        try:
            model_files = {
                'email_classifier': 'email_classifier.joblib',
                'domain_classifier': 'domain_classifier.joblib',
                'behavior_classifier': 'behavior_classifier.joblib',
                'ensemble_classifier': 'ensemble_classifier.joblib'
            }
            
            for model_name, filename in model_files.items():
                model_path = self.models_dir / filename
                if model_path.exists():
                    model_data = joblib.load(model_path)
                    self.models[model_name] = model_data['model']
                    
                    # Load associated components
                    if 'scaler' in model_data:
                        self.scalers[f"{model_name}_scaler"] = model_data['scaler']
                    if 'vectorizer' in model_data:
                        self.feature_extractors[f"{model_name}_vectorizer"] = model_data['vectorizer']
                    if 'label_encoder' in model_data:
                        self.label_encoders[f"{model_name}_encoder"] = model_data['label_encoder']
                    
                    logger.info(f"Loaded {model_name}")
            
        except Exception as e:
            logger.error("Error loading models", error=str(e))
    
    def predict_email_threat(self, email_features: Dict[str, Any]) -> Dict[str, Any]:
        """Predict email threat level using trained model"""
        try:
            if self.models['email_classifier'] is None:
                return {"error": "Email classifier not loaded"}
            
            # Extract features (simplified for example)
            features = np.array([[
                email_features.get('threat_score', 0.5),
                email_features.get('urgent_keywords', 0),
                email_features.get('attachment_count', 0),
                email_features.get('link_count', 0),
                email_features.get('has_attachment', 0)
            ]])
            
            # Scale features
            scaler = self.scalers.get('email_scaler')
            if scaler:
                features = scaler.transform(features)
            
            # Predict
            prediction = self.models['email_classifier'].predict(features)[0]
            probability = self.models['email_classifier'].predict_proba(features)[0]
            
            # Decode label
            label_encoder = self.label_encoders.get('email_labels')
            if label_encoder:
                prediction_label = label_encoder.inverse_transform([prediction])[0]
            else:
                prediction_label = str(prediction)
            
            return {
                'prediction': prediction_label,
                'confidence': float(max(probability)),
                'probabilities': {
                    label_encoder.inverse_transform([i])[0]: float(prob)
                    for i, prob in enumerate(probability)
                } if label_encoder else {}
            }
            
        except Exception as e:
            logger.error("Error predicting email threat", error=str(e))
            return {"error": str(e)}

# Global ML training pipeline instance
ml_training_pipeline = MLTrainingPipeline()
