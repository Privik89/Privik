"""
Behavioral Analysis Service
User behavior analysis and anomaly detection
"""

import asyncio
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict, deque
import structlog
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN
from scipy import stats
from ..services.cache_manager import cache_manager
from ..services.logging_service import logging_service

logger = structlog.get_logger()

class BehavioralAnalyzer:
    """Analyzes user behavior patterns and detects anomalies"""
    
    def __init__(self):
        self.user_profiles = {}
        self.behavior_models = {}
        self.anomaly_threshold = 0.1  # 10% of users flagged as anomalous
        self.min_samples_for_profile = 10  # Minimum samples to build user profile
        
        # Behavioral features to track
        self.feature_names = [
            'emails_per_day',
            'click_rate',
            'attachment_open_rate',
            'suspicious_click_rate',
            'time_variance',
            'sender_diversity',
            'attachment_download_rate',
            'link_click_rate',
            'quarantine_override_rate',
            'login_frequency',
            'session_duration',
            'geographic_variance'
        ]
    
    async def update_user_behavior(self, user_id: str, behavior_event: Dict[str, Any]):
        """Update user behavior profile with new event"""
        try:
            if user_id not in self.user_profiles:
                self.user_profiles[user_id] = {
                    'events': deque(maxlen=1000),  # Keep last 1000 events
                    'daily_stats': defaultdict(lambda: defaultdict(int)),
                    'last_updated': datetime.now(),
                    'anomaly_score': 0.0,
                    'risk_level': 'low'
                }
            
            profile = self.user_profiles[user_id]
            profile['events'].append({
                'timestamp': datetime.now(),
                'event_type': behavior_event.get('event_type'),
                'data': behavior_event.get('data', {})
            })
            
            # Update daily statistics
            today = datetime.now().date()
            daily_stats = profile['daily_stats'][today]
            daily_stats['total_events'] += 1
            
            # Update specific counters based on event type
            event_type = behavior_event.get('event_type')
            if event_type == 'email_received':
                daily_stats['emails_received'] += 1
            elif event_type == 'link_clicked':
                daily_stats['links_clicked'] += 1
                if behavior_event.get('data', {}).get('suspicious', False):
                    daily_stats['suspicious_links_clicked'] += 1
            elif event_type == 'attachment_opened':
                daily_stats['attachments_opened'] += 1
            elif event_type == 'quarantine_override':
                daily_stats['quarantine_overrides'] += 1
            elif event_type == 'login':
                daily_stats['logins'] += 1
                daily_stats['session_duration'] += behavior_event.get('data', {}).get('duration', 0)
            
            profile['last_updated'] = datetime.now()
            
            # Recalculate behavior metrics if enough data
            if len(profile['events']) >= self.min_samples_for_profile:
                await self._calculate_user_metrics(user_id)
            
            logger.debug("Updated user behavior", user_id=user_id, event_type=event_type)
            
        except Exception as e:
            logger.error("Error updating user behavior", user_id=user_id, error=str(e))
    
    async def _calculate_user_metrics(self, user_id: str):
        """Calculate behavioral metrics for a user"""
        try:
            profile = self.user_profiles[user_id]
            events = list(profile['events'])
            
            if len(events) < self.min_samples_for_profile:
                return
            
            # Calculate time-based metrics
            timestamps = [event['timestamp'] for event in events]
            time_variance = np.var([ts.hour for ts in timestamps]) if len(timestamps) > 1 else 0
            
            # Calculate email metrics
            email_events = [e for e in events if e['event_type'] == 'email_received']
            emails_per_day = len(email_events) / max(1, (datetime.now() - timestamps[0]).days)
            
            # Calculate click metrics
            click_events = [e for e in events if e['event_type'] == 'link_clicked']
            suspicious_clicks = [e for e in click_events if e.get('data', {}).get('suspicious', False)]
            
            click_rate = len(click_events) / max(1, len(email_events)) if email_events else 0
            suspicious_click_rate = len(suspicious_clicks) / max(1, len(click_events)) if click_events else 0
            
            # Calculate attachment metrics
            attachment_events = [e for e in events if e['event_type'] == 'attachment_opened']
            attachment_open_rate = len(attachment_events) / max(1, len(email_events)) if email_events else 0
            
            # Calculate sender diversity
            sender_domains = set()
            for event in email_events:
                sender = event.get('data', {}).get('sender', '')
                if '@' in sender:
                    sender_domains.add(sender.split('@')[1])
            sender_diversity = len(sender_domains) / max(1, len(email_events)) if email_events else 0
            
            # Calculate quarantine override rate
            override_events = [e for e in events if e['event_type'] == 'quarantine_override']
            quarantine_override_rate = len(override_events) / max(1, len(email_events)) if email_events else 0
            
            # Calculate session metrics
            login_events = [e for e in events if e['event_type'] == 'login']
            total_session_duration = sum(e.get('data', {}).get('duration', 0) for e in login_events)
            avg_session_duration = total_session_duration / max(1, len(login_events))
            
            # Store calculated metrics
            profile['metrics'] = {
                'emails_per_day': emails_per_day,
                'click_rate': click_rate,
                'attachment_open_rate': attachment_open_rate,
                'suspicious_click_rate': suspicious_click_rate,
                'time_variance': time_variance,
                'sender_diversity': sender_diversity,
                'attachment_download_rate': 0.0,  # Placeholder
                'link_click_rate': click_rate,
                'quarantine_override_rate': quarantine_override_rate,
                'login_frequency': len(login_events),
                'session_duration': avg_session_duration,
                'geographic_variance': 0.0  # Placeholder
            }
            
            # Cache user metrics
            await cache_manager.set(
                f"user_metrics_{user_id}",
                profile['metrics'],
                ttl=3600,  # 1 hour
                namespace="user_behavior"
            )
            
            logger.debug("Calculated user metrics", user_id=user_id, metrics=profile['metrics'])
            
        except Exception as e:
            logger.error("Error calculating user metrics", user_id=user_id, error=str(e))
    
    async def detect_behavioral_anomalies(self) -> Dict[str, Any]:
        """Detect behavioral anomalies across all users"""
        try:
            # Collect metrics for all users with enough data
            user_metrics = []
            user_ids = []
            
            for user_id, profile in self.user_profiles.items():
                if 'metrics' in profile and len(profile['events']) >= self.min_samples_for_profile:
                    user_metrics.append(list(profile['metrics'].values()))
                    user_ids.append(user_id)
            
            if len(user_metrics) < 3:  # Need at least 3 users for anomaly detection
                logger.warning("Insufficient users for anomaly detection", user_count=len(user_metrics))
                return {"anomalies": [], "message": "Insufficient data for anomaly detection"}
            
            # Convert to numpy array
            X = np.array(user_metrics)
            
            # Normalize features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Apply anomaly detection
            isolation_forest = IsolationForest(
                contamination=self.anomaly_threshold,
                random_state=42
            )
            anomaly_labels = isolation_forest.fit_predict(X_scaled)
            anomaly_scores = isolation_forest.decision_function(X_scaled)
            
            # Identify anomalous users
            anomalies = []
            for i, (user_id, is_anomaly, score) in enumerate(zip(user_ids, anomaly_labels, anomaly_scores)):
                if is_anomaly == -1:  # Anomalous
                    profile = self.user_profiles[user_id]
                    profile['anomaly_score'] = float(abs(score))
                    profile['risk_level'] = self._determine_risk_level(abs(score))
                    
                    anomalies.append({
                        'user_id': user_id,
                        'anomaly_score': float(abs(score)),
                        'risk_level': profile['risk_level'],
                        'metrics': profile['metrics'],
                        'last_updated': profile['last_updated'].isoformat()
                    })
                    
                    # Log anomaly detection
                    await logging_service.log_audit_event(
                        logging_service.AuditEvent(
                            event_type='behavioral_anomaly_detected',
                            user_id=user_id,
                            details={
                                'anomaly_score': float(abs(score)),
                                'risk_level': profile['risk_level'],
                                'metrics': profile['metrics']
                            },
                            severity='high'
                        )
                    )
            
            # Update behavior models
            self.behavior_models['isolation_forest'] = isolation_forest
            self.behavior_models['scaler'] = scaler
            
            logger.info("Detected behavioral anomalies", anomaly_count=len(anomalies), total_users=len(user_ids))
            
            return {
                'anomalies': anomalies,
                'total_users_analyzed': len(user_ids),
                'anomaly_rate': len(anomalies) / len(user_ids) if user_ids else 0
            }
            
        except Exception as e:
            logger.error("Error detecting behavioral anomalies", error=str(e))
            return {"error": str(e)}
    
    def _determine_risk_level(self, anomaly_score: float) -> str:
        """Determine risk level based on anomaly score"""
        if anomaly_score > 0.5:
            return 'high'
        elif anomaly_score > 0.3:
            return 'medium'
        else:
            return 'low'
    
    async def analyze_user_clusters(self) -> Dict[str, Any]:
        """Analyze user behavior clusters"""
        try:
            # Collect metrics for clustering
            user_metrics = []
            user_ids = []
            
            for user_id, profile in self.user_profiles.items():
                if 'metrics' in profile:
                    user_metrics.append(list(profile['metrics'].values()))
                    user_ids.append(user_id)
            
            if len(user_metrics) < 5:  # Need at least 5 users for clustering
                return {"clusters": [], "message": "Insufficient data for clustering"}
            
            # Convert to numpy array
            X = np.array(user_metrics)
            
            # Normalize features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            
            # Apply clustering
            dbscan = DBSCAN(eps=0.5, min_samples=2)
            cluster_labels = dbscan.fit_predict(X_scaled)
            
            # Organize users by cluster
            clusters = defaultdict(list)
            for user_id, label in zip(user_ids, cluster_labels):
                clusters[label].append({
                    'user_id': user_id,
                    'metrics': self.user_profiles[user_id]['metrics']
                })
            
            # Calculate cluster statistics
            cluster_stats = {}
            for cluster_id, users in clusters.items():
                if cluster_id == -1:  # Noise points
                    continue
                
                # Calculate average metrics for cluster
                avg_metrics = {}
                for feature_name in self.feature_names:
                    values = [user['metrics'].get(feature_name, 0) for user in users]
                    avg_metrics[feature_name] = np.mean(values) if values else 0
                
                cluster_stats[cluster_id] = {
                    'user_count': len(users),
                    'average_metrics': avg_metrics,
                    'users': [user['user_id'] for user in users]
                }
            
            logger.info("Analyzed user clusters", cluster_count=len(cluster_stats))
            
            return {
                'clusters': dict(cluster_stats),
                'noise_users': len(clusters.get(-1, [])),
                'total_users': len(user_ids)
            }
            
        except Exception as e:
            logger.error("Error analyzing user clusters", error=str(e))
            return {"error": str(e)}
    
    async def predict_user_risk(self, user_id: str) -> Dict[str, Any]:
        """Predict risk level for a specific user"""
        try:
            if user_id not in self.user_profiles:
                return {"error": "User not found"}
            
            profile = self.user_profiles[user_id]
            if 'metrics' not in profile:
                return {"error": "Insufficient data for risk prediction"}
            
            # Use cached anomaly score if available
            if 'anomaly_score' in profile:
                risk_level = profile['risk_level']
                anomaly_score = profile['anomaly_score']
            else:
                # Calculate risk based on individual metrics
                metrics = profile['metrics']
                
                # Risk factors
                risk_factors = {
                    'high_suspicious_click_rate': metrics.get('suspicious_click_rate', 0) > 0.3,
                    'high_quarantine_override_rate': metrics.get('quarantine_override_rate', 0) > 0.2,
                    'unusual_email_volume': metrics.get('emails_per_day', 0) > 200,
                    'low_sender_diversity': metrics.get('sender_diversity', 0) < 0.1,
                    'high_time_variance': metrics.get('time_variance', 0) > 50
                }
                
                # Calculate composite risk score
                risk_score = sum(risk_factors.values()) / len(risk_factors)
                risk_level = self._determine_risk_level(risk_score)
                anomaly_score = risk_score
            
            # Generate risk explanation
            risk_explanation = self._generate_risk_explanation(profile['metrics'])
            
            return {
                'user_id': user_id,
                'risk_level': risk_level,
                'anomaly_score': anomaly_score,
                'risk_factors': risk_explanation,
                'last_updated': profile['last_updated'].isoformat()
            }
            
        except Exception as e:
            logger.error("Error predicting user risk", user_id=user_id, error=str(e))
            return {"error": str(e)}
    
    def _generate_risk_explanation(self, metrics: Dict[str, float]) -> List[str]:
        """Generate human-readable risk explanation"""
        explanations = []
        
        if metrics.get('suspicious_click_rate', 0) > 0.3:
            explanations.append(f"High suspicious link click rate ({metrics['suspicious_click_rate']:.2%})")
        
        if metrics.get('quarantine_override_rate', 0) > 0.2:
            explanations.append(f"Frequent quarantine overrides ({metrics['quarantine_override_rate']:.2%})")
        
        if metrics.get('emails_per_day', 0) > 200:
            explanations.append(f"Unusually high email volume ({metrics['emails_per_day']:.0f} emails/day)")
        
        if metrics.get('sender_diversity', 0) < 0.1:
            explanations.append(f"Low sender diversity ({metrics['sender_diversity']:.2%})")
        
        if metrics.get('time_variance', 0) > 50:
            explanations.append(f"Unusual activity timing patterns (variance: {metrics['time_variance']:.1f})")
        
        return explanations
    
    async def get_behavioral_insights(self) -> Dict[str, Any]:
        """Get overall behavioral insights"""
        try:
            insights = {
                'total_users': len(self.user_profiles),
                'users_with_profiles': len([p for p in self.user_profiles.values() if 'metrics' in p]),
                'high_risk_users': len([p for p in self.user_profiles.values() if p.get('risk_level') == 'high']),
                'medium_risk_users': len([p for p in self.user_profiles.values() if p.get('risk_level') == 'medium']),
                'low_risk_users': len([p for p in self.user_profiles.values() if p.get('risk_level') == 'low']),
                'average_metrics': {},
                'top_risk_factors': []
            }
            
            # Calculate average metrics
            all_metrics = []
            for profile in self.user_profiles.values():
                if 'metrics' in profile:
                    all_metrics.append(profile['metrics'])
            
            if all_metrics:
                for feature_name in self.feature_names:
                    values = [m.get(feature_name, 0) for m in all_metrics if feature_name in m]
                    if values:
                        insights['average_metrics'][feature_name] = np.mean(values)
                
                # Identify top risk factors
                risk_factors = defaultdict(int)
                for metrics in all_metrics:
                    if metrics.get('suspicious_click_rate', 0) > 0.3:
                        risk_factors['suspicious_click_rate'] += 1
                    if metrics.get('quarantine_override_rate', 0) > 0.2:
                        risk_factors['quarantine_override_rate'] += 1
                    if metrics.get('emails_per_day', 0) > 200:
                        risk_factors['high_email_volume'] += 1
                
                insights['top_risk_factors'] = sorted(
                    risk_factors.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:5]
            
            return insights
            
        except Exception as e:
            logger.error("Error getting behavioral insights", error=str(e))
            return {"error": str(e)}

# Global behavioral analyzer instance
behavioral_analyzer = BehavioralAnalyzer()
