#!/usr/bin/env python3
"""
Orchestrator API Server
Provides REST API endpoints for the compliance orchestrator
"""

import os
import sys
import json
import logging
from datetime import datetime
from flask import Flask, jsonify, request
import threading
import time

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from compliance_orchestrator import ComplianceOrchestrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

class OrchestratorService:
    """Service wrapper for the compliance orchestrator"""
    
    def __init__(self):
        self.orchestrator = None
        self.current_audit = None
        self.audit_status = "idle"
        self.initialize_orchestrator()
    
    def initialize_orchestrator(self):
        """Initialize the orchestrator"""
        try:
            self.orchestrator = ComplianceOrchestrator()
            logger.info("Orchestrator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {str(e)}")
            self.orchestrator = None
    
    def start_audit(self, limit=50):
        """Start an audit in the background"""
        if self.audit_status == "running":
            return {"status": "error", "message": "Audit already in progress"}
        
        if not self.orchestrator:
            return {"status": "error", "message": "Orchestrator not available"}
        
        self.audit_status = "running"
        self.current_audit = None
        
        # Run audit in background thread
        audit_thread = threading.Thread(target=self._run_audit_background, args=(limit,))
        audit_thread.daemon = True
        audit_thread.start()
        
        return {
            "status": "started",
            "message": "Audit started in background",
            "timestamp": datetime.now().isoformat()
        }
    
    def _run_audit_background(self, limit):
        """Run audit in background thread"""
        try:
            result = self.orchestrator.run_full_compliance_audit(limit=limit)
            self.current_audit = result
            self.audit_status = "completed"
            logger.info("Background audit completed")
        except Exception as e:
            logger.error(f"Background audit failed: {str(e)}")
            self.current_audit = {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.audit_status = "error"
    
    def get_audit_status(self):
        """Get current audit status"""
        return {
            "status": self.audit_status,
            "current_audit": self.current_audit,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_identity_details(self, identity_id):
        """Get details for a specific identity"""
        if not self.orchestrator:
            return {"error": "Orchestrator not available"}
        
        return self.orchestrator.get_identity_details(identity_id)

# Initialize service
orchestrator_service = OrchestratorService()

@app.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    sailpoint_health = {"status": "unknown"}
    
    if orchestrator_service.orchestrator:
        try:
            sailpoint_health = orchestrator_service.orchestrator.sailpoint.health_check()
        except Exception as e:
            sailpoint_health = {"status": "error", "error": str(e)}
    
    return jsonify({
        "status": "healthy",
        "service": "Compliance Orchestrator API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "orchestrator": "available" if orchestrator_service.orchestrator else "unavailable",
            "sailpoint": sailpoint_health.get("status", "unknown"),
            "ai_model": "available" if orchestrator_service.orchestrator and orchestrator_service.orchestrator.analyzer.model else "unavailable"
        }
    })

@app.route('/api/v1/audit/start', methods=['POST'])
def start_audit():
    """Start a compliance audit"""
    data = request.get_json() or {}
    limit = data.get('limit', 50)
    
    result = orchestrator_service.start_audit(limit)
    
    if result["status"] == "started":
        return jsonify(result), 202  # Accepted
    else:
        return jsonify(result), 400  # Bad Request

@app.route('/api/v1/audit/status', methods=['GET'])
def get_audit_status():
    """Get audit status"""
    status = orchestrator_service.get_audit_status()
    return jsonify(status)

@app.route('/api/v1/audit/results', methods=['GET'])
def get_audit_results():
    """Get latest audit results"""
    status = orchestrator_service.get_audit_status()
    
    if status["status"] == "completed" and status["current_audit"]:
        return jsonify({
            "status": "success",
            "data": status["current_audit"],
            "timestamp": datetime.now().isoformat()
        })
    elif status["status"] == "running":
        return jsonify({
            "status": "in_progress",
            "message": "Audit still running",
            "timestamp": datetime.now().isoformat()
        }), 202
    elif status["status"] == "error":
        return jsonify({
            "status": "error",
            "message": "Audit failed",
            "error": status.get("current_audit", {}),
            "timestamp": datetime.now().isoformat()
        }), 500
    else:
        return jsonify({
            "status": "not_found",
            "message": "No audit results available",
            "timestamp": datetime.now().isoformat()
        }), 404

@app.route('/api/v1/identity/<identity_id>', methods=['GET'])
def get_identity_details(identity_id):
    """Get detailed analysis for a specific identity"""
    try:
        details = orchestrator_service.get_identity_details(identity_id)
        
        if "error" in details:
            return jsonify({
                "status": "error",
                "message": details["error"]
            }), 404
        
        return jsonify({
            "status": "success",
            "data": details,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/v1/audit/quick', methods=['POST'])
def quick_audit():
    """Run a quick audit synchronously"""
    try:
        data = request.get_json() or {}
        limit = data.get('limit', 10)  # Smaller limit for quick audit
        
        if not orchestrator_service.orchestrator:
            return jsonify({
                "status": "error",
                "message": "Orchestrator not available"
            }), 503
        
        # Run quick audit
        result = orchestrator_service.orchestrator.run_full_compliance_audit(limit=limit)
        
        return jsonify({
            "status": "success",
            "data": result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Quick audit failed: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/v1/sailpoint/status', methods=['GET'])
def sailpoint_status():
    """Get SailPoint API status"""
    if not orchestrator_service.orchestrator:
        return jsonify({
            "status": "error",
            "message": "Orchestrator not available"
        }), 503
    
    try:
        health = orchestrator_service.orchestrator.sailpoint.health_check()
        return jsonify({
            "status": "success",
            "data": health,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "status": "error",
        "message": "Endpoint not found",
        "availableEndpoints": [
            "GET  /api/v1/health",
            "POST /api/v1/audit/start",
            "GET  /api/v1/audit/status", 
            "GET  /api/v1/audit/results",
            "POST /api/v1/audit/quick",
            "GET  /api/v1/identity/{id}",
            "GET  /api/v1/sailpoint/status"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "status": "error",
        "message": "Internal server error"
    }), 500

if __name__ == '__main__':
    print("Starting Compliance Orchestrator API...")
    print("Connecting to SailPoint API on port 5002")
    print("Loading AI compliance model")
    print("API available at: http://localhost:5003")
    print("")
    print("Available Endpoints:")
    print("  GET  /api/v1/health                - Health check")
    print("  POST /api/v1/audit/start           - Start background audit")
    print("  GET  /api/v1/audit/status          - Get audit status")
    print("  GET  /api/v1/audit/results         - Get audit results")
    print("  POST /api/v1/audit/quick           - Run quick audit")
    print("  GET  /api/v1/identity/{id}         - Get identity details")
    print("  GET  /api/v1/sailpoint/status      - SailPoint API status")
    print("")
    print("Press Ctrl+C to stop the server")
    
    app.run(debug=True, host='0.0.0.0', port=5003)
