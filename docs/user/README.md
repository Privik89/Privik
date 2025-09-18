# User Manual

## Overview

This user manual provides comprehensive guidance for using Privik, the zero-trust email security platform. Whether you're an end-user, administrator, or security analyst, this guide will help you effectively use Privik to protect your organization from email-based threats.

## Getting Started

### Accessing Privik

1. **Open your web browser** and navigate to your Privik instance URL
2. **Log in** using your organizational credentials
3. **Complete the initial setup** if this is your first time accessing the platform

### Dashboard Overview

The Privik dashboard provides a comprehensive view of your email security status:

- **Threat Summary**: Overview of detected threats and security events
- **Recent Activity**: Latest email processing and threat detection activities
- **System Status**: Health status of all Privik components
- **Quick Actions**: Common tasks and administrative functions

## User Roles and Permissions

### End User
- View personal email security status
- Access quarantined emails
- Report false positives
- View security notifications

### Security Analyst
- Monitor security incidents
- Investigate threats
- Manage quarantine
- Access detailed analysis reports

### Administrator
- Configure system settings
- Manage users and permissions
- Set up integrations
- Access compliance reports

### Super Administrator
- Full system access
- Manage all tenants (multi-tenant environments)
- Configure advanced security settings
- Access audit logs

## Email Security Features

### Threat Detection

Privik automatically analyzes all incoming emails for various threat types:

#### Phishing Detection
- **Suspicious Links**: URLs that lead to malicious websites
- **Fake Sender**: Emails impersonating legitimate organizations
- **Urgent Language**: Messages designed to create panic and urgency
- **Spoofed Domains**: Domains that mimic legitimate organizations

#### Business Email Compromise (BEC)
- **CEO Fraud**: Emails impersonating executives
- **Invoice Fraud**: Fake invoices and payment requests
- **Vendor Impersonation**: Emails from compromised vendor accounts
- **Wire Transfer Requests**: Unusual financial transaction requests

#### Malware Detection
- **Malicious Attachments**: Files containing malware or viruses
- **Macro-Enabled Documents**: Documents with embedded malicious code
- **Executable Files**: Suspicious executable attachments
- **Archive Bombs**: Compressed files designed to consume resources

#### Spam and Unwanted Content
- **Bulk Email**: Mass marketing and promotional emails
- **Scam Messages**: Fraudulent offers and schemes
- **Adult Content**: Inappropriate or adult-oriented material
- **Political Content**: Political messages and propaganda

### Email Analysis Process

1. **Ingestion**: Emails are received from various sources (Gmail, O365, IMAP)
2. **Parsing**: Email content, headers, and attachments are extracted
3. **AI Analysis**: Machine learning models analyze the email for threats
4. **Sandbox Analysis**: Suspicious attachments and links are analyzed in a sandbox
5. **Policy Evaluation**: Zero-trust policies are applied to determine actions
6. **Action Execution**: Emails are quarantined, blocked, or delivered based on verdict

### Threat Scoring

Privik uses a 0-1 threat scoring system:

- **0.0 - 0.2**: Clean - Safe to deliver
- **0.2 - 0.4**: Low Risk - Potentially unwanted content
- **0.4 - 0.6**: Medium Risk - Suspicious content requiring review
- **0.6 - 0.8**: High Risk - Likely malicious content
- **0.8 - 1.0**: Critical Risk - Confirmed malicious content

## Click-Time Protection

### How It Works

Privik's unique click-time protection analyzes links and attachments when users actually click on them, not just when emails are received:

1. **Link Rewriting**: All links in emails are rewritten to point to Privik's analysis system
2. **Click Detection**: When users click links, Privik intercepts the request
3. **Real-time Analysis**: The destination is analyzed in real-time using sandboxing
4. **Safe Delivery**: Users are redirected to the safe destination or blocked if malicious

### Benefits

- **Zero False Positives**: Links are only blocked if they're actually malicious
- **Real-time Protection**: Protection against newly created threats
- **User Experience**: Seamless experience for legitimate links
- **Comprehensive Coverage**: Protection against all types of malicious links

### User Experience

When you click on a link in an email:

1. **Brief Analysis**: You may see a brief "Analyzing link..." message
2. **Safe Redirect**: You're automatically redirected to the safe destination
3. **Blocked Access**: If malicious, you'll see a warning page with details
4. **Report Option**: You can report false positives or request access

## Quarantine Management

### Accessing Quarantine

1. **Navigate to Quarantine**: Click "Quarantine" in the main menu
2. **View Quarantined Emails**: Browse emails that have been quarantined
3. **Filter and Search**: Use filters to find specific emails
4. **Take Actions**: Release, delete, or whitelist emails

### Quarantine Actions

#### Release Email
- **Purpose**: Deliver a quarantined email to the intended recipient
- **When to Use**: When an email is incorrectly quarantined (false positive)
- **Process**: Click "Release" and confirm the action

#### Delete Email
- **Purpose**: Permanently remove a quarantined email
- **When to Use**: When an email is confirmed to be malicious or unwanted
- **Process**: Click "Delete" and confirm the action

#### Whitelist Sender
- **Purpose**: Prevent future emails from a sender from being quarantined
- **When to Use**: For trusted senders whose emails are being incorrectly blocked
- **Process**: Click "Whitelist Sender" and confirm the action

#### Blacklist Sender
- **Purpose**: Ensure future emails from a sender are automatically blocked
- **When to Use**: For known malicious or unwanted senders
- **Process**: Click "Blacklist Sender" and confirm the action

### Bulk Operations

For managing multiple emails:

1. **Select Emails**: Use checkboxes to select multiple emails
2. **Choose Action**: Select the desired action from the bulk actions menu
3. **Confirm**: Review the selected emails and confirm the action
4. **Monitor Progress**: Track the progress of bulk operations

## Security Incidents

### Incident Dashboard

The Security Incidents dashboard provides a comprehensive view of all security events:

- **Incident List**: Chronological list of all security incidents
- **Severity Levels**: Color-coded severity indicators (Low, Medium, High, Critical)
- **Status Tracking**: Current status of each incident (New, Investigating, Resolved)
- **Timeline View**: Visual timeline of incident progression

### Incident Types

#### Email Threats
- **Phishing Attempts**: Emails designed to steal credentials or information
- **Malware Distribution**: Emails containing malicious attachments or links
- **Business Email Compromise**: Sophisticated attacks targeting business processes
- **Spam and Scams**: Unwanted or fraudulent emails

#### User Behavior Anomalies
- **Unusual Login Patterns**: Logins from unusual locations or times
- **High Email Volume**: Unusually high number of emails sent or received
- **Suspicious Click Patterns**: Unusual clicking behavior on links
- **Data Access Anomalies**: Unusual access to sensitive data

#### System Events
- **Policy Violations**: Violations of security policies
- **Integration Failures**: Failures in external system integrations
- **Performance Issues**: System performance problems
- **Configuration Changes**: Changes to security configurations

### Incident Investigation

#### Viewing Incident Details
1. **Click on Incident**: Select an incident from the dashboard
2. **Review Details**: Examine all available information about the incident
3. **Analyze Evidence**: Review attached evidence and analysis results
4. **Check Timeline**: View the chronological progression of the incident

#### Evidence Analysis
- **Email Content**: Full email content and headers
- **Attachment Analysis**: Sandbox analysis results for attachments
- **Link Analysis**: Analysis results for clicked links
- **User Behavior**: Related user behavior and activity
- **Threat Intelligence**: External threat intelligence data

#### Taking Action
1. **Assess Risk**: Determine the severity and impact of the incident
2. **Contain Threat**: Take immediate action to contain the threat
3. **Investigate Further**: Conduct additional investigation if needed
4. **Resolve Incident**: Mark the incident as resolved when appropriate

## AI Copilot Assistant

### Overview

The AI Copilot Assistant provides intelligent assistance for security analysts:

- **Incident Analysis**: Automated analysis of security incidents
- **Recommendations**: Suggested actions and remediation steps
- **Threat Intelligence**: Contextual threat intelligence information
- **Report Generation**: Automated generation of incident reports

### Using the AI Copilot

#### Ask Questions
1. **Open Chat Interface**: Click on the AI Copilot icon
2. **Type Your Question**: Ask questions about incidents, threats, or security
3. **Get Answers**: Receive detailed, contextual answers
4. **Follow Recommendations**: Implement suggested actions

#### Example Questions
- "What is the risk level of this phishing email?"
- "How should I respond to this business email compromise attempt?"
- "What are the indicators of compromise for this incident?"
- "Generate a report for this security incident"

#### AI-Generated Reports
- **Incident Summaries**: Concise summaries of security incidents
- **Threat Analysis**: Detailed analysis of threats and attack vectors
- **Recommendations**: Specific recommendations for remediation
- **Compliance Reports**: Reports for compliance and audit purposes

## Compliance and Reporting

### Compliance Frameworks

Privik supports multiple compliance frameworks:

#### SOC 2 Type II
- **Security Controls**: Comprehensive security control implementation
- **Availability**: System availability and uptime monitoring
- **Processing Integrity**: Data processing integrity and accuracy
- **Confidentiality**: Data confidentiality and protection measures

#### ISO 27001
- **Information Security Management**: Comprehensive ISMS implementation
- **Risk Management**: Risk assessment and management processes
- **Control Implementation**: Security control implementation and monitoring
- **Continuous Improvement**: Ongoing improvement of security posture

#### GDPR
- **Data Protection**: Personal data protection and privacy measures
- **Consent Management**: User consent and data processing consent
- **Data Subject Rights**: Implementation of data subject rights
- **Breach Notification**: Data breach detection and notification

#### HIPAA
- **Healthcare Data Protection**: Protection of healthcare information
- **Access Controls**: Healthcare data access controls and monitoring
- **Audit Logging**: Comprehensive audit logging for healthcare data
- **Risk Assessment**: Healthcare-specific risk assessment and management

### Generating Reports

#### Automated Reports
1. **Navigate to Reports**: Click "Reports" in the main menu
2. **Select Framework**: Choose the compliance framework
3. **Set Date Range**: Specify the reporting period
4. **Generate Report**: Click "Generate Report" and wait for completion
5. **Download Report**: Download the generated report in PDF or Excel format

#### Custom Reports
1. **Create Custom Report**: Click "Create Custom Report"
2. **Select Metrics**: Choose the metrics and data to include
3. **Configure Filters**: Apply filters to focus on specific data
4. **Schedule Reports**: Set up automatic report generation and delivery
5. **Share Reports**: Share reports with stakeholders via email or dashboard

### Report Types

#### Executive Summary
- **High-level Overview**: Summary of security posture and incidents
- **Key Metrics**: Important security metrics and trends
- **Risk Assessment**: Overall risk assessment and recommendations
- **Compliance Status**: Current compliance status and gaps

#### Detailed Analysis
- **Incident Analysis**: Detailed analysis of security incidents
- **Threat Intelligence**: Comprehensive threat intelligence reports
- **User Behavior**: Analysis of user behavior and anomalies
- **System Performance**: System performance and availability metrics

#### Compliance Reports
- **Control Implementation**: Status of security control implementation
- **Audit Findings**: Results of security audits and assessments
- **Remediation Status**: Status of security remediation efforts
- **Continuous Monitoring**: Ongoing compliance monitoring results

## Integrations

### Email Sources

#### Gmail Integration
1. **Navigate to Integrations**: Go to Settings > Integrations
2. **Select Gmail**: Click "Configure Gmail"
3. **Authorize Access**: Grant Privik access to your Gmail account
4. **Configure Settings**: Set up email processing rules and filters
5. **Test Connection**: Verify the integration is working correctly

#### Microsoft 365 Integration
1. **Select Microsoft 365**: Click "Configure Microsoft 365"
2. **Enter Tenant Information**: Provide your tenant ID and credentials
3. **Grant Permissions**: Grant necessary permissions for email access
4. **Configure Mailboxes**: Select which mailboxes to monitor
5. **Enable Integration**: Activate the integration

#### IMAP/POP3 Integration
1. **Select IMAP/POP3**: Click "Configure IMAP/POP3"
2. **Enter Server Details**: Provide server hostname, port, and credentials
3. **Configure SSL/TLS**: Set up secure connection settings
4. **Test Connection**: Verify connectivity to the email server
5. **Start Monitoring**: Begin monitoring the configured mailboxes

### SIEM Integration

#### Splunk Integration
1. **Configure Splunk**: Go to Settings > SIEM Integration
2. **Enter Splunk Details**: Provide Splunk server URL and authentication
3. **Set Up Event Forwarding**: Configure which events to forward
4. **Test Integration**: Send test events to verify connectivity
5. **Monitor Events**: Monitor event forwarding in the dashboard

#### QRadar Integration
1. **Select QRadar**: Choose QRadar from the SIEM options
2. **Configure Connection**: Enter QRadar server details and API key
3. **Map Event Fields**: Map Privik events to QRadar event fields
4. **Enable Forwarding**: Activate event forwarding to QRadar
5. **Verify Integration**: Check QRadar for received events

### LDAP/Active Directory Integration

#### Active Directory Setup
1. **Navigate to Authentication**: Go to Settings > Authentication
2. **Select Active Directory**: Choose AD from the authentication options
3. **Enter Server Details**: Provide AD server hostname and credentials
4. **Configure User Search**: Set up user search base and filters
5. **Test Authentication**: Verify AD authentication is working

#### LDAP Setup
1. **Select LDAP**: Choose LDAP from the authentication options
2. **Enter LDAP Details**: Provide LDAP server information
3. **Configure Bind DN**: Set up LDAP bind distinguished name
4. **Set User Attributes**: Configure user attribute mappings
5. **Enable Integration**: Activate LDAP authentication

## User Management

### Managing Users

#### Adding Users
1. **Navigate to Users**: Go to Settings > Users
2. **Click Add User**: Click "Add User" button
3. **Enter User Details**: Provide user information and email address
4. **Assign Role**: Select appropriate role and permissions
5. **Send Invitation**: Send invitation email to the new user

#### Editing Users
1. **Select User**: Click on a user from the user list
2. **Edit Details**: Modify user information as needed
3. **Update Permissions**: Change user role and permissions
4. **Save Changes**: Save the updated user information

#### Removing Users
1. **Select User**: Choose the user to remove
2. **Click Remove**: Click "Remove User" button
3. **Confirm Action**: Confirm the user removal
4. **Handle Data**: Decide how to handle user's data and access

### Role Management

#### Creating Roles
1. **Go to Roles**: Navigate to Settings > Roles
2. **Create New Role**: Click "Create New Role"
3. **Define Permissions**: Set specific permissions for the role
4. **Save Role**: Save the new role configuration

#### Assigning Roles
1. **Select User**: Choose the user to assign a role
2. **Edit User**: Click "Edit User"
3. **Select Role**: Choose the appropriate role from the dropdown
4. **Save Changes**: Save the role assignment

## System Administration

### System Settings

#### General Settings
- **System Name**: Configure the system name and branding
- **Time Zone**: Set the system time zone
- **Language**: Configure system language and localization
- **Email Templates**: Customize email notification templates

#### Security Settings
- **Password Policy**: Configure password requirements and policies
- **Session Timeout**: Set user session timeout values
- **Two-Factor Authentication**: Enable and configure 2FA
- **API Security**: Configure API authentication and rate limiting

#### Performance Settings
- **Caching**: Configure caching settings and TTL values
- **Database**: Set database connection and performance parameters
- **Background Tasks**: Configure background task processing
- **Resource Limits**: Set system resource limits and quotas

### Monitoring and Maintenance

#### System Health
- **Health Dashboard**: Monitor system health and performance
- **Service Status**: Check status of all system services
- **Resource Usage**: Monitor CPU, memory, and disk usage
- **Error Logs**: Review system error logs and alerts

#### Backup and Recovery
- **Backup Configuration**: Set up automated backup schedules
- **Recovery Procedures**: Document and test recovery procedures
- **Data Retention**: Configure data retention policies
- **Disaster Recovery**: Plan and test disaster recovery procedures

#### Updates and Patches
- **System Updates**: Apply system updates and patches
- **Security Patches**: Install security patches and updates
- **Version Management**: Track and manage system versions
- **Change Management**: Document and approve system changes

## Troubleshooting

### Common Issues

#### Login Problems
- **Check Credentials**: Verify username and password
- **Reset Password**: Use password reset functionality
- **Check Account Status**: Ensure account is active and not locked
- **Contact Administrator**: Contact system administrator if issues persist

#### Email Delivery Issues
- **Check Quarantine**: Look for emails in quarantine
- **Verify Sender**: Check if sender is whitelisted or blacklisted
- **Review Policies**: Check if policies are blocking legitimate emails
- **Contact Support**: Contact technical support for assistance

#### Performance Issues
- **Check System Status**: Monitor system health and performance
- **Review Logs**: Check system logs for errors or warnings
- **Restart Services**: Restart affected services if necessary
- **Contact Support**: Escalate to technical support if needed

### Getting Help

#### Documentation
- **User Manual**: This comprehensive user manual
- **API Documentation**: Technical API documentation
- **Video Tutorials**: Step-by-step video guides
- **FAQ**: Frequently asked questions and answers

#### Support Channels
- **Email Support**: support@privik.com
- **Phone Support**: +1-800-PRIVIK-1
- **Live Chat**: Available during business hours
- **Community Forum**: User community and discussions

#### Training Resources
- **Online Training**: Self-paced online training courses
- **Webinars**: Regular training webinars and sessions
- **Certification**: Privik certification programs
- **Best Practices**: Security best practices and guidelines

This user manual provides comprehensive guidance for using Privik effectively. For additional support or questions, please contact the Privik support team.
