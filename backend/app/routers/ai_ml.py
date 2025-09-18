"""
AI/ML API Router
Machine learning model training, behavioral analysis, and threat hunting endpoints
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Any, Dict
from ..database import get_db
from ..security.hmac_auth import verify_request
from ..services.ml_training_pipeline import ml_training_pipeline
from ..services.behavioral_analysis import behavioral_analyzer
from ..services.threat_hunting import threat_hunter
from ..services.advanced_sandbox import advanced_sandbox
from datetime import datetime
import structlog

logger = structlog.get_logger()
router = APIRouter()

@router.post("/ml/train")
async def train_ml_models(
    days_back: int = Query(30, description="Number of days to collect training data"),
    background_tasks: BackgroundTasks = None,
    _: dict = Depends(verify_request)
):
    """Train ML models with collected data"""
    try:
        # Run training in background
        if background_tasks:
            background_tasks.add_task(
                ml_training_pipeline.run_full_training_pipeline,
                days_back=days_back
            )
            return {"message": "ML training started in background", "days_back": days_back}
        else:
            result = await ml_training_pipeline.run_full_training_pipeline(days_back=days_back)
            return result
        
    except Exception as e:
        logger.error("Error starting ML training", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start ML training: {str(e)}")

@router.get("/ml/models/status")
async def get_ml_models_status(
    _: dict = Depends(verify_request)
):
    """Get status of ML models"""
    try:
        # Load models if not already loaded
        await ml_training_pipeline.load_models()
        
        model_status = {}
        for model_name, model in ml_training_pipeline.models.items():
            model_status[model_name] = {
                'loaded': model is not None,
                'type': type(model).__name__ if model else None,
                'ready': model is not None
            }
        
        return {
            "models": model_status,
            "total_models": len(ml_training_pipeline.models),
            "loaded_models": sum(1 for m in ml_training_pipeline.models.values() if m is not None)
        }
        
    except Exception as e:
        logger.error("Error getting ML models status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get model status")

@router.post("/ml/predict/email")
async def predict_email_threat(
    email_features: Dict[str, Any],
    _: dict = Depends(verify_request)
):
    """Predict email threat level using trained model"""
    try:
        if not ml_training_pipeline.models.get('email_classifier'):
            raise HTTPException(status_code=400, detail="Email classifier not trained")
        
        prediction = ml_training_pipeline.predict_email_threat(email_features)
        return prediction
        
    except Exception as e:
        logger.error("Error predicting email threat", error=str(e))
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

@router.post("/behavior/update")
async def update_user_behavior(
    user_id: str,
    behavior_event: Dict[str, Any],
    _: dict = Depends(verify_request)
):
    """Update user behavior profile"""
    try:
        await behavioral_analyzer.update_user_behavior(user_id, behavior_event)
        return {"message": "User behavior updated successfully"}
        
    except Exception as e:
        logger.error("Error updating user behavior", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to update behavior: {str(e)}")

@router.get("/behavior/anomalies")
async def detect_behavioral_anomalies(
    _: dict = Depends(verify_request)
):
    """Detect behavioral anomalies across all users"""
    try:
        anomalies = await behavioral_analyzer.detect_behavioral_anomalies()
        return anomalies
        
    except Exception as e:
        logger.error("Error detecting behavioral anomalies", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to detect anomalies")

@router.get("/behavior/user/{user_id}/risk")
async def get_user_risk_prediction(
    user_id: str,
    _: dict = Depends(verify_request)
):
    """Get risk prediction for specific user"""
    try:
        risk_prediction = await behavioral_analyzer.predict_user_risk(user_id)
        return risk_prediction
        
    except Exception as e:
        logger.error("Error getting user risk prediction", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get risk prediction: {str(e)}")

@router.get("/behavior/insights")
async def get_behavioral_insights(
    _: dict = Depends(verify_request)
):
    """Get overall behavioral insights"""
    try:
        insights = await behavioral_analyzer.get_behavioral_insights()
        return insights
        
    except Exception as e:
        logger.error("Error getting behavioral insights", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get behavioral insights")

@router.get("/behavior/clusters")
async def analyze_user_clusters(
    _: dict = Depends(verify_request)
):
    """Analyze user behavior clusters"""
    try:
        clusters = await behavioral_analyzer.analyze_user_clusters()
        return clusters
        
    except Exception as e:
        logger.error("Error analyzing user clusters", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to analyze clusters")

@router.post("/threat-hunting/campaign")
async def run_threat_hunting_campaign(
    campaign_name: str,
    rules: Optional[List[str]] = Query(None, description="Specific rules to execute"),
    time_range: int = Query(7, description="Time range in days"),
    background_tasks: BackgroundTasks = None,
    _: dict = Depends(verify_request)
):
    """Run threat hunting campaign"""
    try:
        if background_tasks:
            background_tasks.add_task(
                threat_hunter.run_threat_hunting_campaign,
                campaign_name=campaign_name,
                rules=rules,
                time_range=time_range
            )
            return {
                "message": "Threat hunting campaign started in background",
                "campaign_name": campaign_name,
                "time_range": time_range
            }
        else:
            result = await threat_hunter.run_threat_hunting_campaign(
                campaign_name=campaign_name,
                rules=rules,
                time_range=time_range
            )
            return result
        
    except Exception as e:
        logger.error("Error running threat hunting campaign", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to run campaign: {str(e)}")

@router.get("/threat-hunting/campaigns")
async def get_threat_hunting_campaigns(
    limit: int = Query(10, description="Maximum number of campaigns to return"),
    _: dict = Depends(verify_request)
):
    """Get recent threat hunting campaigns"""
    try:
        campaigns = await threat_hunter.get_hunting_campaigns(limit=limit)
        return {"campaigns": campaigns}
        
    except Exception as e:
        logger.error("Error getting threat hunting campaigns", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get campaigns")

@router.get("/threat-hunting/rules")
async def get_threat_hunting_rules(
    _: dict = Depends(verify_request)
):
    """Get available threat hunting rules"""
    try:
        rules = []
        for rule_id, rule in threat_hunter.hunting_rules.items():
            rules.append({
                "id": rule_id,
                "name": rule["name"],
                "category": rule["category"],
                "description": rule["description"],
                "severity": rule["severity"],
                "enabled": rule.get("enabled", True)
            })
        
        return {"rules": rules}
        
    except Exception as e:
        logger.error("Error getting threat hunting rules", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get rules")

@router.post("/sandbox/advanced-analyze")
async def advanced_sandbox_analysis(
    file_path: Optional[str] = None,
    url: Optional[str] = None,
    analysis_type: str = "comprehensive",
    _: dict = Depends(verify_request)
):
    """Perform advanced sandbox analysis with evasion detection"""
    try:
        if not file_path and not url:
            raise HTTPException(status_code=400, detail="Either file_path or url must be provided")
        
        result = await advanced_sandbox.analyze_with_evasion_detection(
            file_path=file_path,
            url=url,
            analysis_type=analysis_type
        )
        
        return result
        
    except Exception as e:
        logger.error("Error in advanced sandbox analysis", error=str(e))
        raise HTTPException(status_code=500, detail=f"Sandbox analysis failed: {str(e)}")

@router.get("/ai/status")
async def get_ai_ml_status(
    _: dict = Depends(verify_request)
):
    """Get overall AI/ML system status"""
    try:
        # Get ML models status
        await ml_training_pipeline.load_models()
        model_status = {}
        for model_name, model in ml_training_pipeline.models.items():
            model_status[model_name] = model is not None
        
        # Get behavioral analyzer status
        behavioral_status = {
            "users_tracked": len(behavioral_analyzer.user_profiles),
            "anomaly_detection_ready": True
        }
        
        # Get threat hunting status
        hunting_status = {
            "rules_available": len(threat_hunter.hunting_rules),
            "active_campaigns": len([s for s in threat_hunter.hunting_sessions.values() if not s.get('end_time')])
        }
        
        # Get advanced sandbox status
        sandbox_status = {
            "environments_available": len(advanced_sandbox.environments),
            "evasion_detectors": len(advanced_sandbox.evasion_detectors)
        }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "ml_models": {
                "status": model_status,
                "total_models": len(model_status),
                "loaded_models": sum(1 for loaded in model_status.values() if loaded)
            },
            "behavioral_analysis": behavioral_status,
            "threat_hunting": hunting_status,
            "advanced_sandbox": sandbox_status,
            "overall_status": "operational"
        }
        
    except Exception as e:
        logger.error("Error getting AI/ML status", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to get AI/ML status")
