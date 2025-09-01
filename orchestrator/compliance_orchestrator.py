#!/usr/bin/env python3
"""
Compliance Orchestrator
Connects to SailPoint API, collects data, and runs compliance checks using the trained model
"""

import os
import sys
import json
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time

# Add parent directory to path to import from the main app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from transformers import T5ForConditionalGeneration, T5Tokenizer
    import torch
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    print("Warning: Transformers not available. Using fallback analysis.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SailPointConnector:
    """
    Connector to SailPoint API for data collection
    """
    
    def __init__(self, base_url="http://localhost:5002", timeout=30):
        """
        Initialize SailPoint connector
        
        Args:
            base_url (str): Base URL of SailPoint API
            timeout (int): Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
    def health_check(self) -> Dict[str, Any]:
        """Check if SailPoint API is available"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/health", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"SailPoint API health check failed: {str(e)}")
            return {"status": "unhealthy", "error": str(e)}
    
    def get_identities(self, limit: Optional[int] = None, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Fetch identities from SailPoint"""
        try:
            params = {}
            if limit:
                params['limit'] = limit
            if filters:
                params.update(filters)
                
            response = self.session.get(f"{self.base_url}/api/v1/identities", params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch identities: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_access_records(self, limit: Optional[int] = None, filters: Optional[Dict] = None) -> Dict[str, Any]:
        """Fetch access records from SailPoint"""
        try:
            params = {}
            if limit:
                params['limit'] = limit
            if filters:
                params.update(filters)
                
            response = self.session.get(f"{self.base_url}/api/v1/access-records", params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch access records: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_compliance_violations(self, compliance_type: Optional[str] = None) -> Dict[str, Any]:
        """Fetch compliance violations from SailPoint"""
        try:
            params = {}
            if compliance_type:
                params['type'] = compliance_type
                
            response = self.session.get(f"{self.base_url}/api/v1/compliance/violations", params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch compliance violations: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_risk_summary(self) -> Dict[str, Any]:
        """Fetch risk summary from SailPoint"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/reports/risk-summary", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch risk summary: {str(e)}")
            return {"success": False, "error": str(e)}

class ComplianceAnalyzer:
    """
    Compliance analyzer using trained T5 model
    """
    
    def __init__(self, model_path="../trained_compliance_model"):
        """Initialize compliance analyzer with trained model"""
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.load_model()
        
    def load_model(self):
        """Load the trained compliance model"""
        if not HAS_TRANSFORMERS:
            logger.warning("Transformers not available. Using rule-based analysis.")
            return
            
        try:
            model_path = os.path.join(os.path.dirname(__file__), self.model_path)
            if os.path.exists(model_path):
                logger.info(f"Loading trained model from {model_path}")
                self.tokenizer = T5Tokenizer.from_pretrained(model_path)
                self.model = T5ForConditionalGeneration.from_pretrained(model_path)
                self.model.eval()
                logger.info("Trained model loaded successfully")
            else:
                logger.info("Trained model not found, using base model")
                self.tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-small")
                self.model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-small")
                self.model.eval()
                logger.info("Base model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model: {str(e)}")
            self.model = None
            self.tokenizer = None
    
    def analyze_identity_risk(self, identity: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze identity risk using AI model"""
        try:
            # Create analysis prompt
            prompt = self._create_identity_prompt(identity)
            
            if self.model and self.tokenizer:
                # Use AI model
                analysis = self._ai_analysis(prompt, identity)
            else:
                # Use rule-based analysis
                analysis = self._rule_based_identity_analysis(identity)
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing identity: {str(e)}")
            return self._default_analysis()
    
    def analyze_access_compliance(self, access_record: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze access record compliance"""
        try:
            prompt = self._create_access_prompt(access_record)
            
            if self.model and self.tokenizer:
                analysis = self._ai_analysis(prompt, access_record)
            else:
                analysis = self._rule_based_access_analysis(access_record)
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing access record: {str(e)}")
            return self._default_analysis()
    
    def _create_identity_prompt(self, identity: Dict[str, Any]) -> str:
        """Create prompt for identity analysis"""
        return f"""
        Analyze this identity for compliance risks:
        
        Identity: {identity.get('id', 'unknown')}
        Employee: {identity.get('employeeId', 'unknown')}
        Department: {identity.get('department', 'unknown')}
        Job Title: {identity.get('jobTitle', 'unknown')}
        Status: {identity.get('status', 'unknown')}
        Risk Score: {identity.get('riskScore', 0)}
        Last Login: {identity.get('lastLogin', 'unknown')}
        Clearance: {identity.get('attributes', {}).get('clearanceLevel', 'unknown')}
        
        Assess compliance risks and provide recommendations:
        """
    
    def _create_access_prompt(self, access_record: Dict[str, Any]) -> str:
        """Create prompt for access analysis"""
        return f"""
        Analyze this access record for compliance:
        
        Identity: {access_record.get('identityId', 'unknown')}
        Application: {access_record.get('application', 'unknown')}
        Entitlement: {access_record.get('entitlement', 'unknown')}
        Privileged: {access_record.get('isPrivileged', False)}
        SOD Violation: {access_record.get('violatesSOD', False)}
        Risk Level: {access_record.get('riskLevel', 'unknown')}
        Certification: {access_record.get('certificationStatus', 'unknown')}
        
        Compliance Status:
        SOX: {access_record.get('compliance', {}).get('sox', True)}
        GDPR: {access_record.get('compliance', {}).get('gdpr', True)}
        
        Evaluate compliance and provide analysis:
        """
    
    def _ai_analysis(self, prompt: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform AI-based analysis"""
        try:
            inputs = self.tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs['input_ids'],
                    max_length=256,
                    num_beams=4,
                    do_sample=False,
                    early_stopping=True
                )
            
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Parse response and create analysis
            return self._parse_ai_response(response, data)
            
        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}")
            return self._rule_based_access_analysis(data)
    
    def _parse_ai_response(self, response: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse AI model response into structured analysis"""
        is_compliant = "compliant" in response.lower() and "non-compliant" not in response.lower()
        
        violations = []
        if "sox" in response.lower() and ("violation" in response.lower() or "non-compliant" in response.lower()):
            violations.append("SOX compliance violation")
        if "segregation" in response.lower() or "sod" in response.lower():
            violations.append("Segregation of duties violation")
        if "privilege" in response.lower() and "escalation" in response.lower():
            violations.append("Privilege escalation risk")
        
        risk_score = data.get('riskScore', 0.5)
        if not is_compliant:
            risk_score = max(risk_score, 0.7)
        
        return {
            "is_compliant": is_compliant,
            "risk_score": risk_score,
            "violations": violations,
            "recommendation": "APPROVE" if is_compliant else "INVESTIGATE",
            "ai_response": response,
            "confidence": 0.85,
            "analysis_type": "ai_model",
            "timestamp": datetime.now().isoformat()
        }
    
    def _rule_based_identity_analysis(self, identity: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based identity analysis"""
        violations = []
        risk_score = identity.get('riskScore', 0.5)
        
        # Check various risk factors
        if identity.get('status') == 'Terminated':
            violations.append("Terminated user with active accounts")
            risk_score += 0.5
        
        if risk_score > 0.7:
            violations.append("High risk score")
        
        if identity.get('attributes', {}).get('clearanceLevel') == 'Restricted':
            violations.append("Restricted clearance requires review")
        
        # Check last login
        last_login = identity.get('lastLogin')
        if last_login:
            try:
                last_login_date = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
                days_since_login = (datetime.now() - last_login_date.replace(tzinfo=None)).days
                if days_since_login > 90:
                    violations.append("No login activity for 90+ days")
                    risk_score += 0.2
            except:
                pass
        
        is_compliant = len(violations) == 0 and risk_score <= 0.5
        
        return {
            "is_compliant": is_compliant,
            "risk_score": min(risk_score, 1.0),
            "violations": violations,
            "recommendation": "APPROVE" if is_compliant else "INVESTIGATE",
            "ai_response": f"Rule-based analysis: {'Compliant' if is_compliant else 'Non-compliant'}",
            "confidence": 0.75,
            "analysis_type": "rule_based",
            "timestamp": datetime.now().isoformat()
        }
    
    def _rule_based_access_analysis(self, access_record: Dict[str, Any]) -> Dict[str, Any]:
        """Rule-based access analysis"""
        violations = []
        risk_score = 0.3
        
        # Check compliance flags
        compliance = access_record.get('compliance', {})
        for comp_type, is_compliant in compliance.items():
            if not is_compliant:
                violations.append(f"{comp_type.upper()} compliance violation")
                risk_score += 0.2
        
        # Check other risk factors
        if access_record.get('violatesSOD'):
            violations.append("Segregation of duties violation")
            risk_score += 0.3
        
        if access_record.get('isPrivileged'):
            violations.append("Privileged access requires review")
            risk_score += 0.2
        
        if access_record.get('certificationStatus') == 'Expired':
            violations.append("Expired certification")
            risk_score += 0.2
        
        if access_record.get('riskLevel') == 'High':
            violations.append("High risk access")
            risk_score += 0.2
        
        is_compliant = len(violations) == 0 and risk_score <= 0.5
        
        return {
            "is_compliant": is_compliant,
            "risk_score": min(risk_score, 1.0),
            "violations": violations,
            "recommendation": "APPROVE" if is_compliant else "INVESTIGATE",
            "ai_response": f"Rule-based analysis: {'Compliant' if is_compliant else 'Non-compliant'}",
            "confidence": 0.75,
            "analysis_type": "rule_based",
            "timestamp": datetime.now().isoformat()
        }
    
    def _default_analysis(self) -> Dict[str, Any]:
        """Default analysis when all else fails"""
        return {
            "is_compliant": False,
            "risk_score": 0.5,
            "violations": ["Analysis failed"],
            "recommendation": "MANUAL_REVIEW",
            "ai_response": "Unable to complete analysis",
            "confidence": 0.0,
            "analysis_type": "default",
            "timestamp": datetime.now().isoformat()
        }

class ComplianceOrchestrator:
    """
    Main orchestrator that coordinates data collection and compliance analysis
    """
    
    def __init__(self, sailpoint_url="http://localhost:5002", model_path="../trained_compliance_model"):
        """Initialize the compliance orchestrator"""
        self.sailpoint = SailPointConnector(sailpoint_url)
        self.analyzer = ComplianceAnalyzer(model_path)
        self.audit_results = []
        
    def run_full_compliance_audit(self, limit: Optional[int] = 50) -> Dict[str, Any]:
        """Run a full compliance audit"""
        logger.info("Starting full compliance audit...")
        
        # Check SailPoint connectivity
        health = self.sailpoint.health_check()
        if health.get("status") != "healthy":
            return {
                "status": "error",
                "message": f"SailPoint API unavailable: {health.get('error', 'Unknown error')}",
                "timestamp": datetime.now().isoformat()
            }
        
        audit_start = datetime.now()
        
        # Collect data from SailPoint
        identities_response = self.sailpoint.get_identities(limit=limit)
        access_response = self.sailpoint.get_access_records(limit=limit)
        violations_response = self.sailpoint.get_compliance_violations()
        risk_summary_response = self.sailpoint.get_risk_summary()
        
        if not identities_response.get("success") or not access_response.get("success"):
            return {
                "status": "error",
                "message": "Failed to collect data from SailPoint",
                "timestamp": datetime.now().isoformat()
            }
        
        # Analyze identities
        identity_results = []
        identities = identities_response["data"]["items"]
        
        logger.info(f"Analyzing {len(identities)} identities...")
        for identity in identities:
            analysis = self.analyzer.analyze_identity_risk(identity)
            identity_results.append({
                "identity": identity,
                "analysis": analysis
            })
        
        # Analyze access records
        access_results = []
        access_records = access_response["data"]["items"]
        
        logger.info(f"Analyzing {len(access_records)} access records...")
        for access_record in access_records:
            analysis = self.analyzer.analyze_access_compliance(access_record)
            access_results.append({
                "access_record": access_record,
                "analysis": analysis
            })
        
        # Generate summary
        audit_end = datetime.now()
        
        total_identities = len(identity_results)
        compliant_identities = len([r for r in identity_results if r["analysis"]["is_compliant"]])
        
        total_access = len(access_results)
        compliant_access = len([r for r in access_results if r["analysis"]["is_compliant"]])
        
        high_risk_items = len([r for r in identity_results + access_results if r["analysis"]["risk_score"] > 0.7])
        
        audit_result = {
            "status": "completed",
            "audit_id": f"audit_{int(audit_start.timestamp())}",
            "start_time": audit_start.isoformat(),
            "end_time": audit_end.isoformat(),
            "duration_seconds": (audit_end - audit_start).total_seconds(),
            "summary": {
                "total_identities": total_identities,
                "compliant_identities": compliant_identities,
                "identity_compliance_rate": f"{(compliant_identities/total_identities*100):.1f}%" if total_identities > 0 else "0%",
                "total_access_records": total_access,
                "compliant_access_records": compliant_access,
                "access_compliance_rate": f"{(compliant_access/total_access*100):.1f}%" if total_access > 0 else "0%",
                "high_risk_items": high_risk_items,
                "overall_compliance_rate": f"{((compliant_identities + compliant_access)/(total_identities + total_access)*100):.1f}%" if (total_identities + total_access) > 0 else "0%"
            },
            "sailpoint_data": {
                "violations": violations_response.get("data", {}),
                "risk_summary": risk_summary_response.get("data", {})
            },
            "detailed_results": {
                "identities": identity_results[:5],  # First 5 for demo
                "access_records": access_results[:5]  # First 5 for demo
            },
            "recommendations": self._generate_recommendations(identity_results, access_results)
        }
        
        # Store audit result
        self.audit_results.append(audit_result)
        
        logger.info(f"Audit completed: {audit_result['summary']['overall_compliance_rate']} overall compliance")
        return audit_result
    
    def get_identity_details(self, identity_id: str) -> Dict[str, Any]:
        """Get detailed analysis for a specific identity"""
        # Get identity from SailPoint
        identity_response = self.sailpoint.get_identities(filters={"id": identity_id})
        
        if not identity_response.get("success") or not identity_response["data"]["items"]:
            return {"error": "Identity not found"}
        
        identity = identity_response["data"]["items"][0]
        
        # Get access records for this identity
        access_response = self.sailpoint.get_access_records(filters={"identityId": identity_id})
        
        # Analyze identity and access
        identity_analysis = self.analyzer.analyze_identity_risk(identity)
        
        access_analyses = []
        if access_response.get("success"):
            for access_record in access_response["data"]["items"]:
                analysis = self.analyzer.analyze_access_compliance(access_record)
                access_analyses.append({
                    "access_record": access_record,
                    "analysis": analysis
                })
        
        return {
            "identity": identity,
            "identity_analysis": identity_analysis,
            "access_records": access_analyses,
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_recommendations(self, identity_results: List[Dict], access_results: List[Dict]) -> List[str]:
        """Generate recommendations based on audit results"""
        recommendations = []
        
        # Identity recommendations
        high_risk_identities = [r for r in identity_results if r["analysis"]["risk_score"] > 0.7]
        if high_risk_identities:
            recommendations.append(f"Review {len(high_risk_identities)} high-risk identities")
        
        terminated_users = [r for r in identity_results if r["identity"].get("status") == "Terminated"]
        if terminated_users:
            recommendations.append(f"Disable access for {len(terminated_users)} terminated users")
        
        # Access recommendations
        sod_violations = [r for r in access_results if "segregation" in " ".join(r["analysis"]["violations"]).lower()]
        if sod_violations:
            recommendations.append(f"Address {len(sod_violations)} segregation of duties violations")
        
        expired_certs = [r for r in access_results if r["access_record"].get("certificationStatus") == "Expired"]
        if expired_certs:
            recommendations.append(f"Renew {len(expired_certs)} expired certifications")
        
        privileged_access = [r for r in access_results if r["access_record"].get("isPrivileged")]
        if privileged_access:
            recommendations.append(f"Review {len(privileged_access)} privileged access grants")
        
        if not recommendations:
            recommendations.append("No major compliance issues detected")
        
        return recommendations

def main():
    """Main function for testing the orchestrator"""
    print("🚀 Starting Compliance Orchestrator...")
    
    # Initialize orchestrator
    orchestrator = ComplianceOrchestrator()
    
    # Check SailPoint connectivity
    health = orchestrator.sailpoint.health_check()
    if health.get("status") == "healthy":
        print("SailPoint API connection successful")
        print(f"Data available: {health.get('dataStatus', {})}")
    else:
        print("SailPoint API connection failed")
        print("Make sure the SailPoint dummy API is running on port 5002")
        return
    
    # Run a sample audit
    print("\nRunning sample compliance audit...")
    audit_result = orchestrator.run_full_compliance_audit(limit=10)
    
    if audit_result["status"] == "completed":
        print("Audit completed successfully!")
        print(f"Summary:")
        summary = audit_result["summary"]
        print(f"   - Overall Compliance: {summary['overall_compliance_rate']}")
        print(f"   - Identity Compliance: {summary['identity_compliance_rate']}")
        print(f"   - Access Compliance: {summary['access_compliance_rate']}")
        print(f"   - High Risk Items: {summary['high_risk_items']}")
        
        print(f"\nRecommendations:")
        for rec in audit_result["recommendations"]:
            print(f"   - {rec}")
    else:
        print(f"Audit failed: {audit_result.get('message', 'Unknown error')}")

if __name__ == "__main__":
    main()
