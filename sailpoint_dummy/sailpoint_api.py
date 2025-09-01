#!/usr/bin/env python3
"""
SailPoint Dummy API Server
Simulates SailPoint IdentityIQ REST API endpoints for testing compliance orchestrator
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class SailPointAPI:
    """
    Dummy SailPoint API that serves sample identity and access data
    """
    
    def __init__(self, data_file=None):
        """Initialize with sample data"""
        if data_file is None:
            # Get the directory where this script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            data_file = os.path.join(script_dir, "sailpoint_sample_data.json")
        self.data_file = data_file
        self.data = self.load_data()
        
    def load_data(self):
        """Load sample SailPoint data"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded {data['metadata']['totalIdentities']} identities and {data['metadata']['totalAccessRecords']} access records")
            return data
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            return {"identities": [], "accessRecords": [], "metadata": {}}
    
    def get_identities(self, limit=None, offset=0, filter_params=None):
        """Get identities with pagination and filtering"""
        identities = self.data.get("identities", [])
        
        # Apply filters if provided
        if filter_params:
            if "status" in filter_params:
                identities = [i for i in identities if i.get("status") == filter_params["status"]]
            if "department" in filter_params:
                identities = [i for i in identities if i.get("department") == filter_params["department"]]
            if "riskScore" in filter_params:
                min_risk = float(filter_params["riskScore"])
                identities = [i for i in identities if i.get("riskScore", 0) >= min_risk]
        
        # Apply pagination
        total = len(identities)
        if limit:
            identities = identities[offset:offset + int(limit)]
        
        return {
            "items": identities,
            "count": len(identities),
            "total": total,
            "offset": offset
        }
    
    def get_identity_by_id(self, identity_id):
        """Get specific identity by ID"""
        identities = self.data.get("identities", [])
        for identity in identities:
            if identity.get("id") == identity_id or identity.get("employeeId") == identity_id:
                return identity
        return None
    
    def get_access_records(self, limit=None, offset=0, identity_id=None, filter_params=None):
        """Get access records with filtering"""
        access_records = self.data.get("accessRecords", [])
        
        # Filter by identity if specified
        if identity_id:
            access_records = [r for r in access_records if r.get("identityId") == identity_id]
        
        # Apply additional filters
        if filter_params:
            if "application" in filter_params:
                access_records = [r for r in access_records if r.get("application") == filter_params["application"]]
            if "riskLevel" in filter_params:
                access_records = [r for r in access_records if r.get("riskLevel") == filter_params["riskLevel"]]
            if "isPrivileged" in filter_params:
                is_privileged = filter_params["isPrivileged"].lower() == "true"
                access_records = [r for r in access_records if r.get("isPrivileged") == is_privileged]
            if "violatesSOD" in filter_params:
                violates_sod = filter_params["violatesSOD"].lower() == "true"
                access_records = [r for r in access_records if r.get("violatesSOD") == violates_sod]
        
        # Apply pagination
        total = len(access_records)
        if limit:
            access_records = access_records[offset:offset + int(limit)]
        
        return {
            "items": access_records,
            "count": len(access_records),
            "total": total,
            "offset": offset
        }
    
    def get_compliance_violations(self, compliance_type=None):
        """Get compliance violations"""
        access_records = self.data.get("accessRecords", [])
        violations = []
        
        for record in access_records:
            compliance = record.get("compliance", {})
            
            if compliance_type:
                if compliance_type in compliance and not compliance[compliance_type]:
                    violations.append({
                        "recordId": record["id"],
                        "identityId": record["identityId"],
                        "application": record["application"],
                        "violationType": compliance_type.upper(),
                        "severity": record.get("riskLevel", "Medium"),
                        "detectedAt": datetime.now().isoformat(),
                        "details": record
                    })
            else:
                # Check all compliance types
                for comp_type, is_compliant in compliance.items():
                    if not is_compliant:
                        violations.append({
                            "recordId": record["id"],
                            "identityId": record["identityId"],
                            "application": record["application"],
                            "violationType": comp_type.upper(),
                            "severity": record.get("riskLevel", "Medium"),
                            "detectedAt": datetime.now().isoformat(),
                            "details": record
                        })
        
        return violations
    
    def get_certification_data(self):
        """Get access certification data"""
        access_records = self.data.get("accessRecords", [])
        
        pending_certifications = [r for r in access_records if r.get("certificationStatus") == "Pending Review"]
        expired_certifications = [r for r in access_records if r.get("certificationStatus") == "Expired"]
        
        return {
            "pendingCertifications": len(pending_certifications),
            "expiredCertifications": len(expired_certifications),
            "totalRequiringReview": len(pending_certifications) + len(expired_certifications),
            "details": {
                "pending": pending_certifications[:10],  # First 10 for demo
                "expired": expired_certifications[:10]
            }
        }

# Initialize SailPoint API
sailpoint_api = SailPointAPI()

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "SailPoint Dummy API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "dataStatus": {
            "identitiesLoaded": len(sailpoint_api.data.get("identities", [])),
            "accessRecordsLoaded": len(sailpoint_api.data.get("accessRecords", []))
        }
    })

@app.route('/api/v1/identities', methods=['GET'])
def get_identities():
    """Get identities with optional filtering and pagination"""
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', 0, type=int)
    
    # Build filter parameters
    filter_params = {}
    if request.args.get('status'):
        filter_params['status'] = request.args.get('status')
    if request.args.get('department'):
        filter_params['department'] = request.args.get('department')
    if request.args.get('riskScore'):
        filter_params['riskScore'] = request.args.get('riskScore')
    
    result = sailpoint_api.get_identities(limit, offset, filter_params)
    
    return jsonify({
        "success": True,
        "data": result,
        "query": {
            "limit": limit,
            "offset": offset,
            "filters": filter_params
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/v1/identities/<identity_id>', methods=['GET'])
def get_identity(identity_id):
    """Get specific identity by ID"""
    identity = sailpoint_api.get_identity_by_id(identity_id)
    
    if identity:
        return jsonify({
            "success": True,
            "data": identity,
            "timestamp": datetime.now().isoformat()
        })
    else:
        return jsonify({
            "success": False,
            "error": "Identity not found",
            "identityId": identity_id
        }), 404

@app.route('/api/v1/access-records', methods=['GET'])
def get_access_records():
    """Get access records with filtering"""
    limit = request.args.get('limit', type=int)
    offset = request.args.get('offset', 0, type=int)
    identity_id = request.args.get('identityId')
    
    # Build filter parameters
    filter_params = {}
    if request.args.get('application'):
        filter_params['application'] = request.args.get('application')
    if request.args.get('riskLevel'):
        filter_params['riskLevel'] = request.args.get('riskLevel')
    if request.args.get('isPrivileged'):
        filter_params['isPrivileged'] = request.args.get('isPrivileged')
    if request.args.get('violatesSOD'):
        filter_params['violatesSOD'] = request.args.get('violatesSOD')
    
    result = sailpoint_api.get_access_records(limit, offset, identity_id, filter_params)
    
    return jsonify({
        "success": True,
        "data": result,
        "query": {
            "limit": limit,
            "offset": offset,
            "identityId": identity_id,
            "filters": filter_params
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/v1/compliance/violations', methods=['GET'])
def get_compliance_violations():
    """Get compliance violations"""
    compliance_type = request.args.get('type')  # sox, gdpr, hipaa, pci
    
    violations = sailpoint_api.get_compliance_violations(compliance_type)
    
    return jsonify({
        "success": True,
        "data": {
            "violations": violations,
            "count": len(violations),
            "complianceType": compliance_type or "all"
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/v1/certifications', methods=['GET'])
def get_certifications():
    """Get certification data"""
    cert_data = sailpoint_api.get_certification_data()
    
    return jsonify({
        "success": True,
        "data": cert_data,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/v1/reports/risk-summary', methods=['GET'])
def get_risk_summary():
    """Get risk summary report"""
    identities = sailpoint_api.data.get("identities", [])
    access_records = sailpoint_api.data.get("accessRecords", [])
    
    # Calculate risk statistics
    high_risk_identities = [i for i in identities if i.get("riskScore", 0) > 0.7]
    high_risk_access = [r for r in access_records if r.get("riskLevel") == "High"]
    privileged_access = [r for r in access_records if r.get("isPrivileged")]
    sod_violations = [r for r in access_records if r.get("violatesSOD")]
    
    summary = {
        "totalIdentities": len(identities),
        "highRiskIdentities": len(high_risk_identities),
        "totalAccessRecords": len(access_records),
        "highRiskAccess": len(high_risk_access),
        "privilegedAccess": len(privileged_access),
        "sodViolations": len(sod_violations),
        "riskMetrics": {
            "averageIdentityRisk": sum(i.get("riskScore", 0) for i in identities) / len(identities) if identities else 0,
            "riskDistribution": {
                "low": len([i for i in identities if i.get("riskScore", 0) <= 0.3]),
                "medium": len([i for i in identities if 0.3 < i.get("riskScore", 0) <= 0.7]),
                "high": len([i for i in identities if i.get("riskScore", 0) > 0.7])
            }
        },
        "complianceStatus": {
            "sox": len([r for r in access_records if not r.get("compliance", {}).get("sox", True)]),
            "gdpr": len([r for r in access_records if not r.get("compliance", {}).get("gdpr", True)]),
            "hipaa": len([r for r in access_records if not r.get("compliance", {}).get("hipaa", True)]),
            "pci": len([r for r in access_records if not r.get("compliance", {}).get("pci", True)])
        }
    }
    
    return jsonify({
        "success": True,
        "data": summary,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/api/v1/identities/<identity_id>/access', methods=['GET'])
def get_identity_access(identity_id):
    """Get all access records for a specific identity"""
    identity = sailpoint_api.get_identity_by_id(identity_id)
    if not identity:
        return jsonify({
            "success": False,
            "error": "Identity not found"
        }), 404
    
    access_records = sailpoint_api.get_access_records(identity_id=identity_id)
    
    return jsonify({
        "success": True,
        "data": {
            "identity": identity,
            "accessRecords": access_records
        },
        "timestamp": datetime.now().isoformat()
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": "Endpoint not found",
        "availableEndpoints": [
            "/api/v1/health",
            "/api/v1/identities",
            "/api/v1/identities/{id}",
            "/api/v1/access-records",
            "/api/v1/compliance/violations",
            "/api/v1/certifications",
            "/api/v1/reports/risk-summary",
            "/api/v1/identities/{id}/access"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": "Internal server error"
    }), 500

if __name__ == '__main__':
    print("Starting SailPoint Dummy API Server...")
    print("Loaded sample identity and access data")
    print("API available at: http://localhost:5002")
    print("")
    print("Available Endpoints:")
    print("  GET  /api/v1/health                    - Health check")
    print("  GET  /api/v1/identities               - Get identities")
    print("  GET  /api/v1/identities/{id}          - Get specific identity")
    print("  GET  /api/v1/access-records           - Get access records")
    print("  GET  /api/v1/compliance/violations    - Get compliance violations")
    print("  GET  /api/v1/certifications          - Get certification data")
    print("  GET  /api/v1/reports/risk-summary     - Get risk summary")
    print("  GET  /api/v1/identities/{id}/access   - Get identity access")
    print("")
    print("Press Ctrl+C to stop the server")
    
    app.run(debug=True, host='0.0.0.0', port=5002)
