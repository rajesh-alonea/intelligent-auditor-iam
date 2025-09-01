#!/bin/bash

# Orchestrator API Startup Script
echo "🚀 Starting Compliance Orchestrator API..."
echo "🔗 Connecting to SailPoint API"
echo " Loading AI compliance model"
echo ""

# Navigate to orchestrator directory
cd "$(dirname "$0")"

# Activate virtual environment
source ../.venv/bin/activate

# Check dependencies
echo " Checking dependencies..."
python -c "import requests, torch, transformers; print(' Dependencies available')" 2>/dev/null || {
    echo " Installing missing dependencies..."
    pip install requests torch transformers
}

echo " Starting Orchestrator API on port 5003..."
echo " Once started, API will be available at: http://localhost:5003"
echo ""
echo " Available API endpoints:"
echo "   • GET /api/v1/health - Health check"
echo "   • POST /api/v1/audit/start - Start background audit"
echo "   • POST /api/v1/audit/quick - Run quick audit"
echo "   • GET /api/v1/audit/status - Get audit status"
echo "   • GET /api/v1/sailpoint/status - SailPoint status"
echo ""
echo " Requirements:"
echo "   • SailPoint API must be running on port 5002"
echo "   • Trained compliance model should be available"
echo ""
echo "Press Ctrl+C to stop the server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Start the orchestrator API server
python orchestrator_api.py
