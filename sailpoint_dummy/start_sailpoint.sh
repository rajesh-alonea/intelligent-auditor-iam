#!/bin/bash

# SailPoint Dummy API Startup Script
echo "🚀 Starting SailPoint Dummy API Server..."
echo " Loading sample identity and access data"
echo ""

# Navigate to sailpoint_dummy directory
cd "$(dirname "$0")"

# Activate virtual environment
source ../.venv/bin/activate

# Check if sample data exists
if [ ! -f "sailpoint_sample_data.json" ]; then
    echo " Generating sample data..."
    python generate_sample_data.py
fi

echo " Starting SailPoint API on port 5002..."
echo " Once started, API will be available at: http://localhost:5002"
echo ""
echo " Available API endpoints:"
echo "   • GET /api/v1/health - Health check"
echo "   • GET /api/v1/identities - Get identities"
echo "   • GET /api/v1/access-records - Get access records"
echo "   • GET /api/v1/compliance/violations - Get violations"
echo "   • GET /api/v1/reports/risk-summary - Get risk summary"
echo ""
echo "Press Ctrl+C to stop the server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Start the SailPoint API server
python sailpoint_api.py
