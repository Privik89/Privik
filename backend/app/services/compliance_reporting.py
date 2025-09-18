"""
Compliance Reporting Service
Generates compliance reports for SOC2, ISO27001, GDPR, HIPAA, etc.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
import structlog
from ..services.cache_manager import cache_manager
from ..services.logging_service import logging_service
from ..database import get_db
from sqlalchemy.orm import Session

logger = structlog.get_logger()

class ComplianceFramework(Enum):
    SOC2_TYPE_II = "soc2_type_ii"
    ISO27001 = "iso27001"
    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    NIST_CSF = "nist_csf"
    CCPA = "ccpa"

class ComplianceReportGenerator:
    """Generates compliance reports for various frameworks"""
    
    def __init__(self):
        self.framework_requirements = {
            ComplianceFramework.SOC2_TYPE_II: {
                "name": "SOC 2 Type II",
                "requirements": [
                    "security_monitoring",
                    "access_controls",
                    "data_integrity",
                    "confidentiality",
                    "availability"
                ],
                "report_sections": [
                    "executive_summary",
                    "system_description",
                    "control_activities",
                    "control_testing",
                    "test_results",
                    "opinion_letter"
                ]
            },
            ComplianceFramework.ISO27001: {
                "name": "ISO 27001",
                "requirements": [
                    "information_security_policies",
                    "organization_of_information_security",
                    "human_resource_security",
                    "asset_management",
                    "access_control",
                    "cryptography",
                    "physical_security",
                    "operations_security",
                    "communications_security",
                    "system_acquisition",
                    "supplier_relationships",
                    "incident_management",
                    "business_continuity",
                    "compliance"
                ],
                "report_sections": [
                    "scope_and_objectives",
                    "risk_assessment",
                    "control_implementation",
                    "monitoring_measurement",
                    "management_review",
                    "continual_improvement"
                ]
            },
            ComplianceFramework.GDPR: {
                "name": "GDPR",
                "requirements": [
                    "lawfulness_of_processing",
                    "data_minimization",
                    "purpose_limitation",
                    "accuracy",
                    "storage_limitation",
                    "integrity_confidentiality",
                    "accountability",
                    "data_subject_rights",
                    "consent_management",
                    "data_breach_notification",
                    "privacy_by_design",
                    "data_protection_impact_assessment"
                ],
                "report_sections": [
                    "data_processing_activities",
                    "legal_basis_assessment",
                    "data_subject_rights_implementation",
                    "technical_organizational_measures",
                    "data_breach_incidents",
                    "compliance_gaps_remediation"
                ]
            }
        }
    
    async def generate_compliance_report(
        self,
        framework: ComplianceFramework,
        start_date: datetime,
        end_date: datetime,
        include_recommendations: bool = True
    ) -> Dict[str, Any]:
        """Generate comprehensive compliance report"""
        try:
            logger.info(f"Generating {framework.value} compliance report", 
                       start_date=start_date.isoformat(),
                       end_date=end_date.isoformat())
            
            framework_config = self.framework_requirements[framework]
            
            # Collect compliance data
            compliance_data = await self._collect_compliance_data(framework, start_date, end_date)
            
            # Generate report sections
            report_sections = {}
            for section in framework_config["report_sections"]:
                report_sections[section] = await self._generate_section_content(
                    section, framework, compliance_data, start_date, end_date
                )
            
            # Calculate compliance score
            compliance_score = await self._calculate_compliance_score(framework, compliance_data)
            
            # Generate recommendations if requested
            recommendations = []
            if include_recommendations:
                recommendations = await self._generate_recommendations(framework, compliance_data)
            
            # Create final report
            report = {
                "report_metadata": {
                    "framework": framework.value,
                    "framework_name": framework_config["name"],
                    "report_id": self._generate_report_id(framework),
                    "generated_at": datetime.now().isoformat(),
                    "reporting_period": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat()
                    },
                    "compliance_score": compliance_score
                },
                "executive_summary": await self._generate_executive_summary(
                    framework, compliance_score, compliance_data
                ),
                "report_sections": report_sections,
                "recommendations": recommendations,
                "appendices": await self._generate_appendices(framework, compliance_data)
            }
            
            # Cache report
            await cache_manager.set(
                f"compliance_report_{report['report_metadata']['report_id']}",
                report,
                ttl=86400 * 365,  # 1 year
                namespace="compliance_reports"
            )
            
            # Log report generation
            await logging_service.log_audit_event(
                logging_service.AuditEvent(
                    event_type='compliance_report_generated',
                    details={
                        'framework': framework.value,
                        'report_id': report['report_metadata']['report_id'],
                        'compliance_score': compliance_score,
                        'period_start': start_date.isoformat(),
                        'period_end': end_date.isoformat()
                    },
                    severity='medium'
                )
            )
            
            logger.info(f"Generated {framework.value} compliance report", 
                       report_id=report['report_metadata']['report_id'],
                       compliance_score=compliance_score)
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating {framework.value} compliance report", error=str(e))
            return {"error": str(e)}
    
    async def _collect_compliance_data(
        self, 
        framework: ComplianceFramework, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict[str, Any]:
        """Collect data required for compliance reporting"""
        try:
            compliance_data = {
                "security_events": await self._get_security_events(start_date, end_date),
                "access_logs": await self._get_access_logs(start_date, end_date),
                "audit_logs": await self._get_audit_logs(start_date, end_date),
                "data_processing_activities": await self._get_data_processing_activities(start_date, end_date),
                "incident_reports": await self._get_incident_reports(start_date, end_date),
                "user_management": await self._get_user_management_data(start_date, end_date),
                "system_configurations": await self._get_system_configurations(),
                "policies_procedures": await self._get_policies_procedures(),
                "training_records": await self._get_training_records(start_date, end_date),
                "vendor_assessments": await self._get_vendor_assessments(start_date, end_date)
            }
            
            return compliance_data
            
        except Exception as e:
            logger.error("Error collecting compliance data", error=str(e))
            return {}
    
    async def _get_security_events(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get security events for compliance reporting"""
        try:
            # Mock security events data
            security_events = [
                {
                    "event_id": "evt_001",
                    "timestamp": (start_date + timedelta(days=1)).isoformat(),
                    "event_type": "authentication_failure",
                    "severity": "medium",
                    "source_ip": "192.168.1.100",
                    "user_id": "user_001",
                    "description": "Multiple failed login attempts",
                    "status": "investigated",
                    "compliance_relevant": True
                },
                {
                    "event_id": "evt_002",
                    "timestamp": (start_date + timedelta(days=5)).isoformat(),
                    "event_type": "suspicious_email",
                    "severity": "high",
                    "source_email": "phishing@malicious.com",
                    "user_id": "user_002",
                    "description": "Phishing email detected and blocked",
                    "status": "resolved",
                    "compliance_relevant": True
                },
                {
                    "event_id": "evt_003",
                    "timestamp": (start_date + timedelta(days=10)).isoformat(),
                    "event_type": "data_access",
                    "severity": "low",
                    "user_id": "user_003",
                    "description": "Legitimate data access",
                    "status": "normal",
                    "compliance_relevant": False
                }
            ]
            
            return security_events
            
        except Exception as e:
            logger.error("Error getting security events", error=str(e))
            return []
    
    async def _get_access_logs(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get access logs for compliance reporting"""
        try:
            # Mock access logs data
            access_logs = [
                {
                    "log_id": "acc_001",
                    "timestamp": (start_date + timedelta(hours=2)).isoformat(),
                    "user_id": "user_001",
                    "action": "login",
                    "resource": "email_system",
                    "ip_address": "192.168.1.100",
                    "user_agent": "Mozilla/5.0...",
                    "success": True,
                    "compliance_relevant": True
                },
                {
                    "log_id": "acc_002",
                    "timestamp": (start_date + timedelta(hours=5)).isoformat(),
                    "user_id": "user_002",
                    "action": "data_export",
                    "resource": "email_data",
                    "ip_address": "192.168.1.101",
                    "user_agent": "PrivikAgent/1.0",
                    "success": True,
                    "compliance_relevant": True
                }
            ]
            
            return access_logs
            
        except Exception as e:
            logger.error("Error getting access logs", error=str(e))
            return []
    
    async def _get_audit_logs(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get audit logs for compliance reporting"""
        try:
            # Mock audit logs data
            audit_logs = [
                {
                    "audit_id": "aud_001",
                    "timestamp": (start_date + timedelta(hours=1)).isoformat(),
                    "user_id": "admin_001",
                    "action": "policy_update",
                    "resource": "email_policy",
                    "details": "Updated email filtering rules",
                    "compliance_relevant": True
                },
                {
                    "audit_id": "aud_002",
                    "timestamp": (start_date + timedelta(days=3)).isoformat(),
                    "user_id": "admin_002",
                    "action": "user_permission_change",
                    "resource": "user_management",
                    "details": "Modified user access permissions",
                    "compliance_relevant": True
                }
            ]
            
            return audit_logs
            
        except Exception as e:
            logger.error("Error getting audit logs", error=str(e))
            return []
    
    async def _get_data_processing_activities(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get data processing activities for GDPR compliance"""
        try:
            # Mock data processing activities
            processing_activities = [
                {
                    "activity_id": "dpa_001",
                    "name": "Email Security Analysis",
                    "purpose": "Threat detection and prevention",
                    "data_categories": ["email_content", "sender_information", "attachment_data"],
                    "legal_basis": "legitimate_interest",
                    "data_subjects": "employees",
                    "retention_period": "90_days",
                    "security_measures": ["encryption", "access_controls", "audit_logging"],
                    "compliance_status": "compliant"
                },
                {
                    "activity_id": "dpa_002",
                    "name": "User Behavior Analysis",
                    "purpose": "Security monitoring and anomaly detection",
                    "data_categories": ["user_activity", "system_interactions", "risk_scores"],
                    "legal_basis": "legitimate_interest",
                    "data_subjects": "employees",
                    "retention_period": "180_days",
                    "security_measures": ["anonymization", "access_controls", "data_minimization"],
                    "compliance_status": "compliant"
                }
            ]
            
            return processing_activities
            
        except Exception as e:
            logger.error("Error getting data processing activities", error=str(e))
            return []
    
    async def _get_incident_reports(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get incident reports for compliance reporting"""
        try:
            # Mock incident reports
            incidents = [
                {
                    "incident_id": "inc_001",
                    "timestamp": (start_date + timedelta(days=2)).isoformat(),
                    "incident_type": "security_incident",
                    "severity": "high",
                    "description": "Phishing campaign targeting employees",
                    "affected_users": 5,
                    "response_time": "15_minutes",
                    "resolution_time": "2_hours",
                    "compliance_impact": "data_breach_prevention",
                    "status": "resolved"
                }
            ]
            
            return incidents
            
        except Exception as e:
            logger.error("Error getting incident reports", error=str(e))
            return []
    
    async def _get_user_management_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get user management data for compliance reporting"""
        try:
            # Mock user management data
            user_data = {
                "total_users": 150,
                "active_users": 142,
                "new_users": 8,
                "deactivated_users": 3,
                "privileged_users": 12,
                "access_reviews_completed": 15,
                "access_reviews_pending": 2,
                "password_policy_compliance": 0.98,
                "mfa_enabled_users": 142,
                "training_completion_rate": 0.95
            }
            
            return user_data
            
        except Exception as e:
            logger.error("Error getting user management data", error=str(e))
            return {}
    
    async def _get_system_configurations(self) -> Dict[str, Any]:
        """Get system configuration data for compliance reporting"""
        try:
            # Mock system configuration data
            system_config = {
                "encryption_enabled": True,
                "encryption_algorithm": "AES-256",
                "backup_enabled": True,
                "backup_frequency": "daily",
                "log_retention_days": 2555,  # 7 years
                "audit_logging_enabled": True,
                "access_controls_enabled": True,
                "network_security_enabled": True,
                "monitoring_enabled": True,
                "incident_response_plan": "implemented"
            }
            
            return system_config
            
        except Exception as e:
            logger.error("Error getting system configurations", error=str(e))
            return {}
    
    async def _get_policies_procedures(self) -> Dict[str, Any]:
        """Get policies and procedures for compliance reporting"""
        try:
            # Mock policies and procedures data
            policies = {
                "information_security_policy": {
                    "version": "2.1",
                    "last_updated": "2024-01-15",
                    "approval_status": "approved",
                    "review_frequency": "annual"
                },
                "data_protection_policy": {
                    "version": "1.8",
                    "last_updated": "2024-01-10",
                    "approval_status": "approved",
                    "review_frequency": "annual"
                },
                "incident_response_procedure": {
                    "version": "1.5",
                    "last_updated": "2024-01-20",
                    "approval_status": "approved",
                    "review_frequency": "semi_annual"
                },
                "access_control_policy": {
                    "version": "2.0",
                    "last_updated": "2024-01-12",
                    "approval_status": "approved",
                    "review_frequency": "annual"
                }
            }
            
            return policies
            
        except Exception as e:
            logger.error("Error getting policies and procedures", error=str(e))
            return {}
    
    async def _get_training_records(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Get training records for compliance reporting"""
        try:
            # Mock training records
            training_records = {
                "security_awareness_training": {
                    "total_participants": 150,
                    "completion_rate": 0.96,
                    "last_conducted": "2024-01-10",
                    "next_scheduled": "2024-07-10"
                },
                "data_protection_training": {
                    "total_participants": 45,
                    "completion_rate": 1.0,
                    "last_conducted": "2024-01-15",
                    "next_scheduled": "2024-07-15"
                },
                "incident_response_training": {
                    "total_participants": 12,
                    "completion_rate": 1.0,
                    "last_conducted": "2024-01-20",
                    "next_scheduled": "2024-04-20"
                }
            }
            
            return training_records
            
        except Exception as e:
            logger.error("Error getting training records", error=str(e))
            return {}
    
    async def _get_vendor_assessments(self, start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get vendor assessment data for compliance reporting"""
        try:
            # Mock vendor assessments
            vendor_assessments = [
                {
                    "vendor_id": "ven_001",
                    "vendor_name": "Cloud Storage Provider",
                    "assessment_date": (start_date + timedelta(days=7)).isoformat(),
                    "assessment_type": "security_assessment",
                    "compliance_status": "compliant",
                    "risk_level": "low",
                    "next_assessment": (end_date + timedelta(days=30)).isoformat()
                },
                {
                    "vendor_id": "ven_002",
                    "vendor_name": "Email Service Provider",
                    "assessment_date": (start_date + timedelta(days=12)).isoformat(),
                    "assessment_type": "data_protection_assessment",
                    "compliance_status": "compliant",
                    "risk_level": "medium",
                    "next_assessment": (end_date + timedelta(days=60)).isoformat()
                }
            ]
            
            return vendor_assessments
            
        except Exception as e:
            logger.error("Error getting vendor assessments", error=str(e))
            return []
    
    async def _generate_section_content(
        self,
        section: str,
        framework: ComplianceFramework,
        compliance_data: Dict[str, Any],
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Generate content for specific report section"""
        try:
            if section == "executive_summary":
                return await self._generate_executive_summary_content(framework, compliance_data)
            elif section == "control_activities":
                return await self._generate_control_activities_content(framework, compliance_data)
            elif section == "test_results":
                return await self._generate_test_results_content(framework, compliance_data)
            elif section == "data_processing_activities":
                return await self._generate_data_processing_content(framework, compliance_data)
            else:
                return {
                    "section": section,
                    "content": f"Section content for {section} in {framework.value}",
                    "status": "placeholder"
                }
                
        except Exception as e:
            logger.error(f"Error generating section content for {section}", error=str(e))
            return {"error": str(e)}
    
    async def _generate_executive_summary_content(
        self,
        framework: ComplianceFramework,
        compliance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate executive summary content"""
        try:
            security_events = compliance_data.get("security_events", [])
            incidents = compliance_data.get("incident_reports", [])
            user_data = compliance_data.get("user_management", {})
            
            summary = {
                "overview": f"Compliance assessment for {framework.value} framework",
                "period_summary": {
                    "security_events": len(security_events),
                    "incidents": len(incidents),
                    "total_users": user_data.get("total_users", 0),
                    "compliance_score": 0.95  # Will be calculated separately
                },
                "key_findings": [
                    "Strong security monitoring and incident response capabilities",
                    "Comprehensive access controls and user management",
                    "Regular security awareness training programs",
                    "Effective data protection measures"
                ],
                "areas_for_improvement": [
                    "Enhance vendor risk management processes",
                    "Implement additional data retention controls",
                    "Strengthen business continuity planning"
                ]
            }
            
            return summary
            
        except Exception as e:
            logger.error("Error generating executive summary content", error=str(e))
            return {"error": str(e)}
    
    async def _generate_control_activities_content(
        self,
        framework: ComplianceFramework,
        compliance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate control activities content"""
        try:
            controls = {
                "access_controls": {
                    "description": "User access management and authentication controls",
                    "implementation_status": "fully_implemented",
                    "effectiveness": "high",
                    "evidence": [
                        "Multi-factor authentication enabled for all users",
                        "Regular access reviews conducted",
                        "Privileged access monitoring in place"
                    ]
                },
                "data_protection": {
                    "description": "Data encryption and protection measures",
                    "implementation_status": "fully_implemented",
                    "effectiveness": "high",
                    "evidence": [
                        "AES-256 encryption for data at rest",
                        "TLS 1.3 for data in transit",
                        "Regular encryption key rotation"
                    ]
                },
                "incident_response": {
                    "description": "Security incident detection and response",
                    "implementation_status": "fully_implemented",
                    "effectiveness": "high",
                    "evidence": [
                        "24/7 security monitoring",
                        "Automated incident detection",
                        "Documented response procedures"
                    ]
                }
            }
            
            return controls
            
        except Exception as e:
            logger.error("Error generating control activities content", error=str(e))
            return {"error": str(e)}
    
    async def _generate_test_results_content(
        self,
        framework: ComplianceFramework,
        compliance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate test results content"""
        try:
            test_results = {
                "access_control_testing": {
                    "test_type": "automated_access_review",
                    "test_date": "2024-01-15",
                    "result": "passed",
                    "findings": [],
                    "recommendations": []
                },
                "encryption_testing": {
                    "test_type": "encryption_validation",
                    "test_date": "2024-01-20",
                    "result": "passed",
                    "findings": [],
                    "recommendations": []
                },
                "incident_response_testing": {
                    "test_type": "tabletop_exercise",
                    "test_date": "2024-01-25",
                    "result": "passed",
                    "findings": ["Minor improvements needed in communication procedures"],
                    "recommendations": ["Update incident communication templates"]
                }
            }
            
            return test_results
            
        except Exception as e:
            logger.error("Error generating test results content", error=str(e))
            return {"error": str(e)}
    
    async def _generate_data_processing_content(
        self,
        framework: ComplianceFramework,
        compliance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate data processing activities content"""
        try:
            processing_activities = compliance_data.get("data_processing_activities", [])
            
            content = {
                "processing_activities": processing_activities,
                "legal_basis_summary": {
                    "legitimate_interest": len([pa for pa in processing_activities if pa.get("legal_basis") == "legitimate_interest"]),
                    "consent": len([pa for pa in processing_activities if pa.get("legal_basis") == "consent"]),
                    "contract": len([pa for pa in processing_activities if pa.get("legal_basis") == "contract"])
                },
                "data_subject_rights": {
                    "access_requests_processed": 12,
                    "rectification_requests_processed": 3,
                    "erasure_requests_processed": 1,
                    "average_response_time": "5_days"
                }
            }
            
            return content
            
        except Exception as e:
            logger.error("Error generating data processing content", error=str(e))
            return {"error": str(e)}
    
    async def _calculate_compliance_score(
        self,
        framework: ComplianceFramework,
        compliance_data: Dict[str, Any]
    ) -> float:
        """Calculate overall compliance score"""
        try:
            # Mock compliance score calculation
            base_score = 0.95
            
            # Adjust based on framework-specific requirements
            if framework == ComplianceFramework.SOC2_TYPE_II:
                # Check SOC2 specific controls
                security_events = compliance_data.get("security_events", [])
                incidents = compliance_data.get("incident_reports", [])
                
                # Reduce score for unresolved incidents
                unresolved_incidents = len([i for i in incidents if i.get("status") != "resolved"])
                if unresolved_incidents > 0:
                    base_score -= 0.05 * unresolved_incidents
            
            elif framework == ComplianceFramework.GDPR:
                # Check GDPR specific requirements
                processing_activities = compliance_data.get("data_processing_activities", [])
                non_compliant_activities = len([pa for pa in processing_activities if pa.get("compliance_status") != "compliant"])
                if non_compliant_activities > 0:
                    base_score -= 0.1 * non_compliant_activities
            
            return max(0.0, min(1.0, base_score))
            
        except Exception as e:
            logger.error("Error calculating compliance score", error=str(e))
            return 0.5
    
    async def _generate_recommendations(
        self,
        framework: ComplianceFramework,
        compliance_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate compliance recommendations"""
        try:
            recommendations = []
            
            # Framework-specific recommendations
            if framework == ComplianceFramework.SOC2_TYPE_II:
                recommendations.extend([
                    {
                        "category": "access_controls",
                        "priority": "medium",
                        "recommendation": "Implement automated access provisioning and deprovisioning",
                        "rationale": "Reduce manual errors and ensure timely access management",
                        "implementation_effort": "medium"
                    },
                    {
                        "category": "monitoring",
                        "priority": "high",
                        "recommendation": "Enhance real-time security monitoring capabilities",
                        "rationale": "Improve detection and response to security incidents",
                        "implementation_effort": "high"
                    }
                ])
            
            elif framework == ComplianceFramework.GDPR:
                recommendations.extend([
                    {
                        "category": "data_protection",
                        "priority": "high",
                        "recommendation": "Implement automated data retention policies",
                        "rationale": "Ensure compliance with data minimization principle",
                        "implementation_effort": "medium"
                    },
                    {
                        "category": "consent_management",
                        "priority": "medium",
                        "recommendation": "Enhance consent tracking and management",
                        "rationale": "Improve data subject rights implementation",
                        "implementation_effort": "medium"
                    }
                ])
            
            return recommendations
            
        except Exception as e:
            logger.error("Error generating recommendations", error=str(e))
            return []
    
    async def _generate_executive_summary(
        self,
        framework: ComplianceFramework,
        compliance_score: float,
        compliance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate executive summary"""
        try:
            summary = {
                "compliance_framework": framework.value,
                "overall_score": compliance_score,
                "score_interpretation": self._interpret_compliance_score(compliance_score),
                "key_highlights": [
                    f"Compliance score: {compliance_score:.1%}",
                    "Strong security controls implementation",
                    "Effective incident response procedures",
                    "Comprehensive audit logging"
                ],
                "areas_of_strength": [
                    "Access control management",
                    "Data encryption and protection",
                    "Security monitoring and alerting",
                    "Incident response capabilities"
                ],
                "improvement_areas": [
                    "Vendor risk management",
                    "Business continuity planning",
                    "Data retention automation"
                ]
            }
            
            return summary
            
        except Exception as e:
            logger.error("Error generating executive summary", error=str(e))
            return {"error": str(e)}
    
    def _interpret_compliance_score(self, score: float) -> str:
        """Interpret compliance score"""
        if score >= 0.95:
            return "Excellent - Fully compliant with minor improvements needed"
        elif score >= 0.85:
            return "Good - Compliant with some areas requiring attention"
        elif score >= 0.70:
            return "Fair - Partially compliant with significant improvements needed"
        else:
            return "Poor - Non-compliant with major remediation required"
    
    async def _generate_appendices(
        self,
        framework: ComplianceFramework,
        compliance_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate report appendices"""
        try:
            appendices = {
                "appendix_a": {
                    "title": "Security Events Summary",
                    "content": compliance_data.get("security_events", [])
                },
                "appendix_b": {
                    "title": "Access Logs Summary",
                    "content": compliance_data.get("access_logs", [])
                },
                "appendix_c": {
                    "title": "System Configurations",
                    "content": compliance_data.get("system_configurations", {})
                },
                "appendix_d": {
                    "title": "Policies and Procedures",
                    "content": compliance_data.get("policies_procedures", {})
                }
            }
            
            return appendices
            
        except Exception as e:
            logger.error("Error generating appendices", error=str(e))
            return {}
    
    def _generate_report_id(self, framework: ComplianceFramework) -> str:
        """Generate unique report ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{framework.value}_report_{timestamp}"
    
    async def get_compliance_reports(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent compliance reports"""
        try:
            # This would typically query cached reports
            # For now, return mock data
            reports = [
                {
                    "report_id": "soc2_type_ii_report_20240115_143022",
                    "framework": "soc2_type_ii",
                    "framework_name": "SOC 2 Type II",
                    "generated_at": "2024-01-15T14:30:22",
                    "compliance_score": 0.95,
                    "reporting_period": {
                        "start_date": "2023-07-01T00:00:00",
                        "end_date": "2023-12-31T23:59:59"
                    }
                },
                {
                    "report_id": "iso27001_report_20240110_091545",
                    "framework": "iso27001",
                    "framework_name": "ISO 27001",
                    "generated_at": "2024-01-10T09:15:45",
                    "compliance_score": 0.92,
                    "reporting_period": {
                        "start_date": "2023-01-01T00:00:00",
                        "end_date": "2023-12-31T23:59:59"
                    }
                }
            ]
            
            return reports[:limit]
            
        except Exception as e:
            logger.error("Error getting compliance reports", error=str(e))
            return []

# Global compliance report generator instance
compliance_report_generator = ComplianceReportGenerator()
