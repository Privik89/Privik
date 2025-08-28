"""
Privik Custom LLM Prompt Templates
Specialized prompts for cybersecurity analysis
"""

from typing import Dict, Any, List, Optional
import json

class PromptTemplates:
    """Prompt templates for Privik's custom LLM."""
    
    def __init__(self):
        """Initialize prompt templates."""
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for Privik LLM."""
        return """You are Privik, an advanced AI-powered cybersecurity assistant specialized in email security, threat detection, and security operations. You have been trained on extensive cybersecurity data and are designed to help security analysts and organizations protect against email-based threats.

Your capabilities include:
- Phishing email detection and analysis
- Malware analysis and classification
- User behavior analysis and risk assessment
- Threat intelligence generation and correlation
- Security operations center (SOC) assistance
- Incident response guidance and recommendations

Always provide structured, actionable responses with confidence scores and specific recommendations. Focus on accuracy, relevance, and practical security insights."""

    def get_email_analysis_prompt(self, email_data: Dict[str, Any]) -> str:
        """Generate prompt for email analysis."""
        subject = email_data.get('subject', 'No subject')
        sender = email_data.get('sender', 'Unknown sender')
        recipient = email_data.get('recipient', 'Unknown recipient')
        content = email_data.get('content', 'No content')
        attachments = email_data.get('attachments', [])
        links = email_data.get('links', [])
        
        prompt = f"""{self.system_prompt}

TASK: Analyze the following email for potential security threats, particularly phishing attempts, malware, and suspicious behavior.

EMAIL DETAILS:
Subject: {subject}
From: {sender}
To: {recipient}
Content: {content}

ATTACHMENTS: {len(attachments)} files
{chr(10).join([f"- {att.get('name', 'Unknown')} ({att.get('type', 'Unknown type')})" for att in attachments])}

LINKS: {len(links)} links
{chr(10).join([f"- {link}" for link in links])}

ANALYSIS REQUIREMENTS:
1. Determine if this is a phishing email (confidence score 0-100)
2. Identify the threat type (phishing, malware, BEC, spam, legitimate)
3. List specific indicators that support your assessment
4. Provide a threat score (0-100)
5. Give specific recommendations for handling this email
6. Assess the urgency level (low, medium, high, critical)

Please provide your analysis in the following JSON format:
{{
    "threat_score": <0-100>,
    "threat_type": "<threat_category>",
    "confidence": <0-100>,
    "indicators": ["indicator1", "indicator2", ...],
    "summary": "<brief_summary>",
    "recommendations": ["recommendation1", "recommendation2", ...],
    "urgency": "<urgency_level>",
    "ai_analysis": "<detailed_analysis>"
}}"""

        return prompt

    def get_file_analysis_prompt(self, file_data: Dict[str, Any]) -> str:
        """Generate prompt for file analysis."""
        filename = file_data.get('filename', 'Unknown')
        file_type = file_data.get('file_type', 'Unknown')
        file_size = file_data.get('file_size', 0)
        content = file_data.get('content', '')
        metadata = file_data.get('metadata', {})
        
        prompt = f"""{self.system_prompt}

TASK: Analyze the following file for potential malware, suspicious content, or security threats.

FILE DETAILS:
Filename: {filename}
Type: {file_type}
Size: {file_size} bytes
Content: {content[:2000]}...  # Truncated for analysis

METADATA:
{json.dumps(metadata, indent=2)}

ANALYSIS REQUIREMENTS:
1. Determine if this file contains malware or suspicious content (confidence score 0-100)
2. Identify the threat type (malware, suspicious, legitimate, unknown)
3. List specific indicators that support your assessment
4. Provide a threat score (0-100)
5. Give specific recommendations for handling this file
6. Assess the risk level (low, medium, high, critical)

Please provide your analysis in the following JSON format:
{{
    "threat_score": <0-100>,
    "threat_type": "<threat_category>",
    "confidence": <0-100>,
    "indicators": ["indicator1", "indicator2", ...],
    "summary": "<brief_summary>",
    "recommendations": ["recommendation1", "recommendation2", ...],
    "risk_level": "<risk_level>",
    "ai_analysis": "<detailed_analysis>"
}}"""

        return prompt

    def get_behavior_analysis_prompt(self, behavior_data: Dict[str, Any]) -> str:
        """Generate prompt for user behavior analysis."""
        user_id = behavior_data.get('user_id', 'Unknown')
        actions = behavior_data.get('actions', [])
        patterns = behavior_data.get('patterns', {})
        time_period = behavior_data.get('time_period', 'Unknown')
        
        prompt = f"""{self.system_prompt}

TASK: Analyze the following user behavior for potential security risks, anomalies, or suspicious patterns.

USER BEHAVIOR DATA:
User ID: {user_id}
Time Period: {time_period}

ACTIONS:
{chr(10).join([f"- {action}" for action in actions])}

PATTERNS:
{json.dumps(patterns, indent=2)}

ANALYSIS REQUIREMENTS:
1. Determine if this behavior indicates security risks (confidence score 0-100)
2. Identify the risk type (normal, suspicious, compromised, insider_threat)
3. List specific behavioral indicators that support your assessment
4. Provide a risk score (0-100)
5. Give specific recommendations for monitoring or response
6. Assess the urgency level (low, medium, high, critical)

Please provide your analysis in the following JSON format:
{{
    "risk_score": <0-100>,
    "risk_type": "<risk_category>",
    "confidence": <0-100>,
    "indicators": ["indicator1", "indicator2", ...],
    "summary": "<brief_summary>",
    "recommendations": ["recommendation1", "recommendation2", ...],
    "urgency": "<urgency_level>",
    "ai_analysis": "<detailed_analysis>"
}}"""

        return prompt

    def get_threat_intelligence_prompt(self, threat_data: Dict[str, Any]) -> str:
        """Generate prompt for threat intelligence generation."""
        threat_type = threat_data.get('threat_type', 'Unknown')
        indicators = threat_data.get('indicators', [])
        context = threat_data.get('context', {})
        
        prompt = f"""{self.system_prompt}

TASK: Generate comprehensive threat intelligence based on the provided threat data and context.

THREAT DATA:
Threat Type: {threat_type}
Indicators: {indicators}
Context: {json.dumps(context, indent=2)}

THREAT INTELLIGENCE REQUIREMENTS:
1. Analyze the threat indicators and context
2. Identify potential threat actors or campaigns
3. Assess the threat's sophistication level
4. Determine potential impact and targets
5. Provide mitigation strategies and recommendations
6. Suggest additional monitoring and detection measures

Please provide your threat intelligence in the following JSON format:
{{
    "threat_actors": ["actor1", "actor2", ...],
    "campaign_name": "<campaign_name>",
    "sophistication_level": "<low/medium/high/advanced>",
    "potential_impact": "<impact_assessment>",
    "target_industries": ["industry1", "industry2", ...],
    "mitigation_strategies": ["strategy1", "strategy2", ...],
    "detection_measures": ["measure1", "measure2", ...],
    "intelligence_summary": "<detailed_summary>",
    "confidence": <0-100>
}}"""

        return prompt

    def get_soc_assistant_prompt(self, query: str, context: Dict[str, Any] = None) -> str:
        """Generate prompt for SOC assistant queries."""
        context_str = ""
        if context:
            context_str = f"\nCONTEXT:\n{json.dumps(context, indent=2)}"
        
        prompt = f"""{self.system_prompt}

TASK: Provide expert cybersecurity guidance and assistance for the following SOC analyst query.

ANALYST QUERY: {query}{context_str}

RESPONSE REQUIREMENTS:
1. Provide clear, actionable guidance
2. Reference relevant security frameworks and best practices
3. Suggest specific tools, techniques, or procedures
4. Consider the context and urgency of the situation
5. Provide step-by-step recommendations when appropriate
6. Include relevant security references or resources

Please provide a comprehensive, helpful response that assists the SOC analyst in their security operations."""

        return prompt

    def get_batch_analysis_prompt(self, data_list: List[Dict[str, Any]], analysis_type: str) -> str:
        """Generate prompt for batch analysis."""
        data_summary = []
        for i, data in enumerate(data_list):
            if analysis_type == 'email':
                summary = f"Email {i+1}: {data.get('subject', 'No subject')} from {data.get('sender', 'Unknown')}"
            elif analysis_type == 'file':
                summary = f"File {i+1}: {data.get('filename', 'Unknown')} ({data.get('file_type', 'Unknown type')})"
            elif analysis_type == 'behavior':
                summary = f"Behavior {i+1}: User {data.get('user_id', 'Unknown')} - {len(data.get('actions', []))} actions"
            else:
                summary = f"Item {i+1}: {str(data)[:100]}..."
            data_summary.append(summary)
        
        prompt = f"""{self.system_prompt}

TASK: Perform batch analysis of {len(data_list)} {analysis_type} items for security threats and risks.

ITEMS TO ANALYZE:
{chr(10).join(data_summary)}

BATCH ANALYSIS REQUIREMENTS:
1. Analyze each item individually for security threats
2. Provide consistent scoring and categorization
3. Identify patterns or correlations across the batch
4. Prioritize items by threat level
5. Provide batch-level insights and recommendations

Please provide your analysis in the following JSON format:
[
    {{
        "item_id": 1,
        "threat_score": <0-100>,
        "threat_type": "<threat_category>",
        "confidence": <0-100>,
        "priority": "<low/medium/high/critical>",
        "summary": "<brief_summary>"
    }},
    ...
]

BATCH INSIGHTS:
{{
    "total_items": {len(data_list)},
    "threat_distribution": {{"low": X, "medium": Y, "high": Z, "critical": W}},
    "common_patterns": ["pattern1", "pattern2", ...],
    "batch_recommendations": ["recommendation1", "recommendation2", ...]
}}"""

        return prompt

    def get_incident_response_prompt(self, incident_data: Dict[str, Any]) -> str:
        """Generate prompt for incident response guidance."""
        incident_type = incident_data.get('incident_type', 'Unknown')
        severity = incident_data.get('severity', 'Unknown')
        affected_systems = incident_data.get('affected_systems', [])
        timeline = incident_data.get('timeline', [])
        
        prompt = f"""{self.system_prompt}

TASK: Provide comprehensive incident response guidance for the following security incident.

INCIDENT DETAILS:
Type: {incident_type}
Severity: {severity}
Affected Systems: {affected_systems}
Timeline: {json.dumps(timeline, indent=2)}

INCIDENT RESPONSE REQUIREMENTS:
1. Provide immediate containment steps
2. Suggest evidence preservation procedures
3. Recommend investigation techniques
4. Outline communication protocols
5. Suggest recovery and remediation steps
6. Provide lessons learned and prevention measures

Please provide your incident response guidance in the following JSON format:
{{
    "immediate_actions": ["action1", "action2", ...],
    "containment_steps": ["step1", "step2", ...],
    "evidence_preservation": ["procedure1", "procedure2", ...],
    "investigation_techniques": ["technique1", "technique2", ...],
    "communication_protocol": ["protocol1", "protocol2", ...],
    "recovery_steps": ["step1", "step2", ...],
    "prevention_measures": ["measure1", "measure2", ...],
    "response_summary": "<detailed_guidance>"
}}"""

        return prompt

    def get_vulnerability_assessment_prompt(self, vulnerability_data: Dict[str, Any]) -> str:
        """Generate prompt for vulnerability assessment."""
        cve_id = vulnerability_data.get('cve_id', 'Unknown')
        description = vulnerability_data.get('description', 'No description')
        severity = vulnerability_data.get('severity', 'Unknown')
        affected_components = vulnerability_data.get('affected_components', [])
        
        prompt = f"""{self.system_prompt}

TASK: Assess the following vulnerability and provide detailed analysis and recommendations.

VULNERABILITY DETAILS:
CVE ID: {cve_id}
Description: {description}
Severity: {severity}
Affected Components: {affected_components}

VULNERABILITY ASSESSMENT REQUIREMENTS:
1. Analyze the vulnerability's potential impact
2. Assess exploitability and attack vectors
3. Evaluate the risk to the organization
4. Provide mitigation strategies
5. Suggest monitoring and detection measures
6. Recommend patching priorities

Please provide your vulnerability assessment in the following JSON format:
{{
    "impact_analysis": "<impact_assessment>",
    "exploitability": "<exploitability_assessment>",
    "risk_level": "<low/medium/high/critical>",
    "attack_vectors": ["vector1", "vector2", ...],
    "mitigation_strategies": ["strategy1", "strategy2", ...],
    "detection_measures": ["measure1", "measure2", ...],
    "patching_priority": "<priority_level>",
    "assessment_summary": "<detailed_assessment>"
}}"""

        return prompt
