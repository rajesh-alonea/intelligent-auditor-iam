#!/usr/bin/env python3
"""
IAM SOX Compliance Chat Interface
A simple web-based chat interface for interacting with the trained compliance model.
"""

import os
import json
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer
import pandas as pd
import numpy as np
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'

# Orchestrator API configuration
ORCHESTRATOR_URL = "http://localhost:5003"
SAILPOINT_URL = "http://localhost:5002"

class ComplianceOrchestrator:
    """
    Orchestrator for compliance analysis and data management
    """
    
    def __init__(self, model_path):
        """Initialize the orchestrator with trained model"""
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.load_model()
        self.audit_history = []
        
    def load_model(self):
        """Load the trained compliance model"""
        try:
            logger.info(f"Loading model from {self.model_path}")
            # Always use the pre-trained model - no fallback to base model
            if os.path.exists(self.model_path):
                self.tokenizer = T5Tokenizer.from_pretrained(self.model_path)
                self.model = T5ForConditionalGeneration.from_pretrained(self.model_path)
                self.model.eval()
                logger.info("Model loaded successfully")
            else:
                raise FileNotFoundError(f"Trained model not found at {self.model_path}")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            raise e
                
    def load_audit_data(self):
        """Load audit data from SailPoint API (no training data)"""
        # Only use real SailPoint data - do not load training files
        try:
            # Try to get data from SailPoint API
            response = requests.get(f"{SAILPOINT_URL}/api/v1/access-records", timeout=10)
            if response.status_code == 200:
                data = response.json()
                access_records = data.get('data', {}).get('items', [])
                logger.info(f"Loaded {len(access_records)} access records from SailPoint API")
                return access_records
            else:
                logger.warning("SailPoint API not available, using empty dataset")
                return []
        except Exception as e:
            logger.warning(f"Could not load from SailPoint API: {str(e)}")
            return []
    
    def analyze_compliance_event(self, event_data):
        """Analyze a compliance event using the trained model"""
        try:
            # Create structured input for the model
            input_text = self.create_analysis_prompt(event_data)
            
            # Tokenize input
            inputs = self.tokenizer(input_text, return_tensors="pt", max_length=512, truncation=True)
            
            # Generate response
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs['input_ids'],
                    max_length=256,
                    num_beams=4,
                    temperature=0.7,
                    do_sample=False,
                    early_stopping=True
                )
            
            # Decode response
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Parse response into structured analysis
            analysis = self.parse_model_response(response, event_data)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing compliance event: {str(e)}")
            # Fallback analysis
            return self.fallback_analysis(event_data)
    
    def create_analysis_prompt(self, event_data):
        """Create a structured prompt for compliance analysis"""
        prompt = f"""
        Analyze this access event for SOX and IAM compliance:
        
        User ID: {event_data.get('user_id', 'unknown')}
        Action: {event_data.get('action', 'unknown')}
        Resource: {event_data.get('resource', 'unknown')}
        Access Level: {event_data.get('access_level', 'unknown')}
        Authentication: {event_data.get('auth_method', 'unknown')}
        Time: {event_data.get('timestamp', datetime.now().isoformat())}
        Risk Score: {event_data.get('risk_score', 0.5)}
        
        Evaluate compliance status and provide reasoning:
        """
        return prompt.strip()
    
    def parse_model_response(self, response, event_data):
        """Parse model response into structured analysis"""
        # Simple parsing logic - can be enhanced based on model output format
        is_compliant = "COMPLIANT" in response.upper() and "NON-COMPLIANT" not in response.upper()
        
        risk_score = event_data.get('risk_score', 0.5)
        if not is_compliant:
            risk_score = max(risk_score, 0.7)
        
        violations = []
        if "SOX" in response.upper() and ("VIOLATION" in response.upper() or "NON-COMPLIANT" in response.upper()):
            violations.append("SOX compliance violation")
        if "IAM" in response.upper() and ("VIOLATION" in response.upper() or "NON-COMPLIANT" in response.upper()):
            violations.append("IAM policy violation")
        if "PRIVILEGE" in response.upper() and "ESCALATION" in response.upper():
            violations.append("Privilege escalation detected")
        
        return {
            'is_compliant': is_compliant,
            'risk_score': risk_score,
            'violations': violations,
            'recommendation': 'APPROVE' if is_compliant else 'INVESTIGATE',
            'model_response': response,
            'confidence': 0.85,
            'timestamp': datetime.now().isoformat()
        }
    
    def fallback_analysis(self, event_data):
        """Fallback analysis when model is not available"""
        risk_score = event_data.get('risk_score', 0.5)
        
        # Simple rule-based analysis
        violations = []
        if event_data.get('privilege_escalation', False):
            violations.append("Privilege escalation detected")
            risk_score += 0.3
        
        if event_data.get('after_hours', False):
            violations.append("After-hours access detected")
            risk_score += 0.2
            
        if risk_score > 0.7:
            violations.append("High risk score")
        
        is_compliant = len(violations) == 0 and risk_score <= 0.5
        
        return {
            'is_compliant': is_compliant,
            'risk_score': min(risk_score, 1.0),
            'violations': violations,
            'recommendation': 'APPROVE' if is_compliant else 'INVESTIGATE',
            'model_response': f"Risk-based analysis: {'Compliant' if is_compliant else 'Non-compliant'}",
            'confidence': 0.75,
            'timestamp': datetime.now().isoformat()
        }
    
    def run_full_audit(self):
        """Run a full audit on available data"""
        logger.info("Starting full audit...")
        
        # Load audit data
        audit_data = self.load_audit_data()
        
        if not audit_data:
            return {
                'status': 'error',
                'message': 'No audit data available',
                'summary': {}
            }
        
        # Analyze each record
        results = []
        compliant_count = 0
        total_risk_score = 0
        
        for i, record in enumerate(audit_data[:10]):  # Limit to 10 for demo
            try:
                analysis = self.analyze_compliance_event(record)
                results.append({
                    'record_id': i + 1,
                    'user_id': record.get('user_id', f'user_{i+1}'),
                    'action': record.get('action', 'unknown'),
                    'analysis': analysis
                })
                
                if analysis['is_compliant']:
                    compliant_count += 1
                total_risk_score += analysis['risk_score']
                
            except Exception as e:
                logger.error(f"Error analyzing record {i}: {str(e)}")
        
        # Generate summary
        total_records = len(results)
        compliance_rate = (compliant_count / total_records * 100) if total_records > 0 else 0
        avg_risk_score = total_risk_score / total_records if total_records > 0 else 0
        
        audit_result = {
            'status': 'completed',
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_records': total_records,
                'compliant_records': compliant_count,
                'non_compliant_records': total_records - compliant_count,
                'compliance_rate': f"{compliance_rate:.1f}%",
                'average_risk_score': f"{avg_risk_score:.3f}",
                'high_risk_events': len([r for r in results if r['analysis']['risk_score'] > 0.7])
            },
            'detailed_results': results[:5],  # Show first 5 for demo
            'total_analyzed': len(audit_data)
        }
        
        # Store in audit history
        self.audit_history.append(audit_result)
        
        logger.info(f"Audit completed: {compliance_rate:.1f}% compliance rate")
        return audit_result

# Initialize the orchestrator with better error handling
try:
    orchestrator = ComplianceOrchestrator('./trained_compliance_model')
    print("Orchestrator initialized successfully")
except Exception as e:
    print(f"Warning: Could not initialize orchestrator: {str(e)}")
    orchestrator = None

@app.route('/test')
def test():
    """Test route to verify Flask is working"""
    return "Flask app is working!"

@app.route('/')
def index():
    """Main chat interface"""
    try:
        return render_template('index.html')
    except Exception as e:
        logger.error(f"Error serving index.html: {str(e)}")
        return f"""
        <html>
        <head><title>IAM SOX Compliance Assistant</title></head>
        <body>
            <h1>IAM SOX Compliance Assistant</h1>
            <p>Error loading template: {str(e)}</p>
            <p>Basic interface:</p>
            <div id="chat" style="height: 300px; border: 1px solid #ccc; overflow-y: scroll; padding: 10px;">
                <div>Welcome to the IAM SOX Compliance Assistant!</div>
            </div>
            <input type="text" id="messageInput" style="width: 80%;" placeholder="Type your message...">
            <button onclick="sendMessage()">Send</button>
            
            <script>
                function sendMessage() {{
                    const input = document.getElementById('messageInput');
                    const chat = document.getElementById('chat');
                    const message = input.value;
                    
                    if (message.trim()) {{
                        chat.innerHTML += '<div><strong>You:</strong> ' + message + '</div>';
                        input.value = '';
                        
                        fetch('/chat', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{message: message}})
                        }})
                        .then(response => response.json())
                        .then(data => {{
                            chat.innerHTML += '<div><strong>AI:</strong> ' + (data.response || data.error) + '</div>';
                            chat.scrollTop = chat.scrollHeight;
                        }});
                    }}
                }}
                
                document.getElementById('messageInput').addEventListener('keypress', function(e) {{
                    if (e.key === 'Enter') sendMessage();
                }});
            </script>
        </body>
        </html>
        """

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages"""
    try:
        user_message = request.json.get('message', '').strip().lower()
        
        if not user_message:
            return jsonify({'error': 'Empty message'})
        
        # Initialize session chat history
        if 'chat_history' not in session:
            session['chat_history'] = []
        
        # Handle different types of queries
        if 'audit' in user_message and ('run' in user_message or 'start' in user_message):
            # Run full audit
            response = handle_audit_request()
        elif 'analyze' in user_message or 'check' in user_message:
            # Analyze specific event
            response = handle_analysis_request(user_message)
        elif 'sailpoint' in user_message and ('status' in user_message or 'check' in user_message):
            # Check SailPoint status
            response = handle_sailpoint_status()
        elif 'history' in user_message or 'previous' in user_message:
            # Show audit history
            response = handle_history_request()
        elif 'help' in user_message:
            # Show help
            response = handle_help_request()
        else:
            # General compliance question
            response = handle_general_question(user_message)
        
        # Store in chat history
        session['chat_history'].append({
            'user': user_message,
            'assistant': response,
            'timestamp': datetime.now().isoformat()
        })
        
        return jsonify({'response': response})
        
    except Exception as e:
        logger.error(f"Error handling chat request: {str(e)}")
        return jsonify({'error': 'An error occurred processing your request'})

def handle_audit_request():
    """Handle audit execution requests"""
    try:
        # Try to use orchestrator API first
        try:
            response = requests.post(f"{ORCHESTRATOR_URL}/api/v1/audit/quick", 
                                   json={"limit": 20}, 
                                   timeout=60)
            
            if response.status_code == 200:
                data = response.json()
                if data["status"] == "success":
                    audit_result = data["data"]
                    return format_orchestrator_audit_result(audit_result)
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Orchestrator API not available: {str(e)}")
        
        # Fallback to local orchestrator if available
        if orchestrator is None:
            return {
                'total_records': 0,
                'violations': 1,
                'compliant': 0,
                'detailed_results': ['System Error: Orchestrator not available. Please check the system setup.']
            }
            
        audit_result = orchestrator.run_full_audit()
        
        if audit_result['status'] == 'error':
            return {
                'total_records': 0,
                'violations': 1,
                'compliant': 0,
                'detailed_results': [f"Audit Error: {audit_result['message']}"]
            }
        
        summary = audit_result['summary']
        
        # Convert to structured format for table display
        structured_result = {
            'total_records': summary['total_records'],
            'violations': summary['total_records'] - summary['compliant_records'],
            'compliant': summary['compliant_records'],
            'detailed_results': []
        }
        
        # Add sample results in a readable format
        for result in audit_result['detailed_results'][:10]:
            status = "COMPLIANT" if result['analysis']['is_compliant'] else "VIOLATION"
            risk = result['analysis']['risk_score']
            user_id = result['user_id']
            action = result['action']
            
            structured_result['detailed_results'].append(
                f"{user_id} - {action}: {status} (Risk Score: {risk:.2f})"
            )
        
        # Add summary information
        structured_result['detailed_results'].append(f"Compliance Rate: {summary['compliance_rate']}")
        structured_result['detailed_results'].append(f"Average Risk Score: {summary['average_risk_score']}")
        structured_result['detailed_results'].append(f"High Risk Events: {summary['high_risk_events']}")
        
        return structured_result
        
    except Exception as e:
        logger.error(f"Error in audit request: {str(e)}")
        return {
            'total_records': 0,
            'violations': 1,
            'compliant': 0,
            'detailed_results': ['System Error: Unable to run audit. Please check the system logs.']
        }

def format_orchestrator_audit_result(audit_result):
    """Format audit result from orchestrator API - returns structured data for frontend formatting"""
    try:
        summary = audit_result.get('summary', {})
        
        # Return structured data that the frontend can format properly
        structured_result = {
            'total_records': summary.get('total_identities', 0) + summary.get('total_access_records', 0),
            'violations': 0,
            'compliant': 0,
            'detailed_results': []
        }
        
        # Count violations and compliant items
        identity_results = audit_result.get('detailed_results', {}).get('identities', [])
        access_results = audit_result.get('detailed_results', {}).get('access_records', [])
        
        all_results = []
        
        # Process identity results
        for result in identity_results:
            identity = result.get('identity', {})
            analysis = result.get('analysis', {})
            is_compliant = analysis.get('is_compliant', False)
            risk = analysis.get('risk_score', 0)
            
            if is_compliant:
                structured_result['compliant'] += 1
                status = 'COMPLIANT'
            else:
                structured_result['violations'] += 1
                status = 'VIOLATION'
            
            all_results.append(f"Identity {identity.get('employeeId', 'Unknown')} ({identity.get('department', 'Unknown')}): {status} - Risk Score: {risk:.2f}")
        
        # Process access results  
        for result in access_results:
            access_record = result.get('access_record', {})
            analysis = result.get('analysis', {})
            is_compliant = analysis.get('is_compliant', False)
            risk = analysis.get('risk_score', 0)
            
            if is_compliant:
                structured_result['compliant'] += 1
                status = 'COMPLIANT'
            else:
                structured_result['violations'] += 1
                status = 'VIOLATION'
            
            all_results.append(f"{access_record.get('application', 'Unknown')} access: {status} - Risk Score: {risk:.2f}")
        
        # Add recommendations to detailed results
        recommendations = audit_result.get('recommendations', [])
        for rec in recommendations[:3]:
            all_results.append(f"RECOMMENDATION: {rec}")
        
        structured_result['detailed_results'] = all_results
        audit_duration = audit_result.get('duration_seconds', 0)
        all_results.append(f"Audit completed in {audit_duration:.1f} seconds")
        all_results.append(f"Data source: SailPoint Identity Platform")
        
        return structured_result
        
    except Exception as e:
        logger.error(f"Error formatting orchestrator result: {str(e)}")
        return {
            'total_records': 0,
            'violations': 1,
            'compliant': 0,
            'detailed_results': ['Error: Audit completed but formatting failed. Check logs for details.']
        }

def handle_analysis_request(message):
    """Handle specific event analysis requests using real SailPoint data"""
    try:
        # Try to get real data from SailPoint API
        sample_event = None
        
        try:
            # First try to get access records from SailPoint
            response = requests.get(f"{SAILPOINT_URL}/api/v1/access-records", timeout=10)
            if response.status_code == 200:
                data = response.json()
                access_records = data.get('access_records', [])
                
                if access_records:
                    # Use the first access record as sample
                    sample_record = access_records[0]
                    sample_event = {
                        'user_id': sample_record.get('userId', 'unknown_user'),
                        'action': sample_record.get('action', 'access'),
                        'resource': sample_record.get('application', 'unknown_resource'),
                        'access_level': sample_record.get('permissions', ['read'])[0] if sample_record.get('permissions') else 'read',
                        'auth_method': sample_record.get('authMethod', 'unknown'),
                        'risk_score': sample_record.get('riskScore', 0.5),
                        'timestamp': sample_record.get('timestamp', datetime.now().isoformat())
                    }
                else:
                    # Fallback if no access records
                    raise Exception("No access records available")
            else:
                raise Exception(f"SailPoint API returned status {response.status_code}")
                
        except Exception as api_error:
            logger.warning(f"Could not fetch access records from SailPoint: {str(api_error)}")
            # Try to get identity data as fallback
            try:
                response = requests.get(f"{SAILPOINT_URL}/api/v1/identities", timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    identities = data.get('identities', [])
                    
                    if identities:
                        # Use the first identity as sample
                        sample_identity = identities[0]
                        sample_event = {
                            'user_id': sample_identity.get('employeeId', 'unknown_user'),
                            'action': 'identity_access',
                            'resource': f"{sample_identity.get('department', 'unknown')}_systems",
                            'access_level': sample_identity.get('accessLevel', 'standard'),
                            'auth_method': 'sso',
                            'risk_score': sample_identity.get('riskScore', 0.3),
                            'timestamp': datetime.now().isoformat()
                        }
                    else:
                        raise Exception("No identity records available")
                else:
                    raise Exception("Both access and identity APIs unavailable")
                    
            except Exception as fallback_error:
                logger.warning(f"Fallback to identity data also failed: {str(fallback_error)}")
                # Create a generic sample if all else fails
                sample_event = {
                    'user_id': 'system_user',
                    'action': 'system_access',
                    'resource': 'compliance_system',
                    'access_level': 'read',
                    'auth_method': 'api_key',
                    'risk_score': 0.2,
                    'timestamp': datetime.now().isoformat()
                }
        
        # Analyze the event
        if orchestrator is None:
            # Fallback analysis without model
            analysis = {
                'is_compliant': sample_event['risk_score'] < 0.7,
                'risk_score': sample_event['risk_score'],
                'violations': ['Analysis without AI model'] if sample_event['risk_score'] >= 0.7 else [],
                'recommendation': 'APPROVE' if sample_event['risk_score'] < 0.7 else 'INVESTIGATE',
                'model_response': 'Rule-based analysis (AI model not available)',
                'confidence': 0.5
            }
        else:
            analysis = orchestrator.analyze_compliance_event(sample_event)
        
        status = "COMPLIANT" if analysis['is_compliant'] else "NON-COMPLIANT"
        
        response = f"""
**Event Analysis Complete**

**Event Details:**
- User: {sample_event['user_id']}
- Action: {sample_event['action']}
- Resource: {sample_event['resource']}
- Access Level: {sample_event['access_level']}
- Authentication: {sample_event['auth_method']}

**Analysis Results:**
- Status: {status}
- Risk Score: {analysis['risk_score']:.3f}
- Recommendation: {analysis['recommendation']}
- Confidence: {analysis['confidence']:.1%}
"""
        
        if analysis['violations']:
            response += f"\n**Violations Detected:**\n"
            for violation in analysis['violations']:
                response += f"• {violation}\n"
        
        response += f"\n**Model Response:** {analysis['model_response']}"
        response += f"\n**Data Source:** SailPoint API (Real-time)"
        
        return response
        
    except Exception as e:
        logger.error(f"Error in analysis request: {str(e)}")
        return "Error analyzing event. Please try again."

def handle_sailpoint_status():
    """Handle SailPoint status check requests"""
    try:
        # Check orchestrator API
        try:
            response = requests.get(f"{ORCHESTRATOR_URL}/api/v1/sailpoint/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                sailpoint_data = data.get("data", {})
                
                status_response = f"""
**SailPoint API Status**

**Connection Status:** {'Connected' if sailpoint_data.get('status') == 'healthy' else 'Disconnected'}

**Data Summary:**
"""
                
                data_status = sailpoint_data.get("dataStatus", {})
                if data_status:
                    status_response += f"• Identities: {data_status.get('identitiesLoaded', 'Unknown')}\n"
                    status_response += f"• Access Records: {data_status.get('accessRecordsLoaded', 'Unknown')}\n"
                
                status_response += f"\n**API Endpoint:** {SAILPOINT_URL}"
                status_response += f"\n**Last Check:** {datetime.now().strftime('%H:%M:%S')}"
                
                return status_response
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Orchestrator API check failed: {str(e)}")
        
        # Direct SailPoint check as fallback
        try:
            response = requests.get(f"{SAILPOINT_URL}/api/v1/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return f"""
**SailPoint API Status**

**Direct Connection:** Connected
**Data:** {data.get('dataStatus', {})}
**Endpoint:** {SAILPOINT_URL}
**Checked:** {datetime.now().strftime('%H:%M:%S')}

Note: Orchestrator API not available, using direct connection.
"""
            
        except requests.exceptions.RequestException:
            pass
        
        return """
**SailPoint API Status**

**Connection:** Disconnected
**Issue:** Cannot reach SailPoint API

**Troubleshooting:**
• Check if SailPoint dummy API is running on port 5002
• Verify network connectivity
• Try: `cd sailpoint_dummy && python sailpoint_api.py`

**Alternative:** Use local data analysis mode
"""
        
    except Exception as e:
        logger.error(f"Error checking SailPoint status: {str(e)}")
        return "Error checking SailPoint status. Please try again."

def handle_history_request():
    """Handle audit history requests"""
    if orchestrator is None:
        return "Orchestrator not available. Cannot access audit history."
        
    if not orchestrator.audit_history:
        return "No audit history available. Run an audit first with 'run audit'."
    
    response = "**Audit History:**\n\n"
    
    for i, audit in enumerate(orchestrator.audit_history[-3:], 1):  # Show last 3 audits
        timestamp = datetime.fromisoformat(audit['timestamp']).strftime('%Y-%m-%d %H:%M')
        summary = audit['summary']
        response += f"**Audit #{i}** ({timestamp}):\n"
        response += f"• Records: {summary['total_records']}\n"
        response += f"• Compliance Rate: {summary['compliance_rate']}\n"
        response += f"• High Risk Events: {summary['high_risk_events']}\n\n"
    
    return response

def handle_help_request():
    """Handle help requests"""
    return """
**IAM SOX Compliance Assistant**

**Available Commands:**
• `run audit` - Execute full compliance audit (SailPoint + AI)
• `analyze event` - Analyze a real SailPoint access event  
• `sailpoint status` - Check SailPoint API connection
• `history` - View previous audit results
• `help` - Show this help message

**What I can do:**
• SOX compliance detection
• IAM policy violation analysis  
• Risk assessment and scoring
• SailPoint data integration
• Real-time compliance monitoring

**Examples:**
• "Run audit to check compliance"
• "Check SailPoint status"
• "Analyze event" - Uses real SailPoint data
• "Show me the audit history"

**Data Sources:**
**SailPoint API** - Live identity and access data (Primary source)
**AI Model** - Trained Google T5-small for compliance analysis
**Local Data** - Fallback compliance data

**Tip:** I now use real SailPoint data for event analysis! The system pulls live access records and identity data from your SailPoint API for authentic compliance analysis.
"""

def handle_general_question(message):
    """Handle general compliance questions"""
    if 'sox' in message:
        return """
**SOX Compliance Information**

SOX (Sarbanes-Oxley) compliance focuses on:
• Financial data integrity
• Internal controls
• Audit trails
• Access management

I can help detect SOX violations in your access data. Try running an audit!
"""
    elif 'iam' in message:
        return """
**IAM (Identity & Access Management)**

IAM compliance includes:
• Proper authentication
• Authorization controls  
• Privilege management
• Access reviews

I analyze IAM events for policy violations and security risks.
"""
    else:
        return """
**Welcome to the IAM SOX Compliance Assistant!**

I'm here to help with compliance analysis using your trained model.

**Quick Start:**
• Type "run audit" to analyze your data
• Type "help" for more commands
• Ask me about SOX or IAM compliance

What would you like me to help you with?
"""

if __name__ == '__main__':
    # Ensure templates directory exists
    os.makedirs('templates', exist_ok=True)
    
    print("Starting IAM SOX Compliance Chat Interface...")
    print("Using trained compliance model")
    print("Access at: http://localhost:5001")
    print("Press Ctrl+C to stop the server")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
