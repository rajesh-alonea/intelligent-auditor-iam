#!/bin/bash

# IAM SOX Compliance Chat Interface Startup Script
echo "🚀 Starting IAM SOX Compliance Chat Interface..."
echo "💻 Using trained Google T5-small model"
echo ""

# Activate virtual environment
source .venv/bin/activate

# Check if Flask is installed
if ! python -c "import flask" 2>/dev/null; then
    echo " Flask not found. Installing..."
    pip install flask
fi

# Check if required model files exist
if [ ! -f "trained_compliance_model/config.json" ]; then
    echo "  Warning: Trained model not found at trained_compliance_model/"
    echo "   The application will fall back to the base Google T5-small model."
fi

# Check if data files exist
if [ ! -f "data/train_data.json" ]; then
    echo "  Warning: Training data not found at data/train_data.json"
    echo "   Some audit features may not work properly."
fi

echo " Starting Flask application..."
echo " Once started, open your browser to: http://localhost:5001"
echo ""
echo " Available features:"
echo "   • Run compliance audits"
echo "   • Analyze access events"
echo "   • SOX violation detection"
echo "   • IAM policy compliance checks"
echo ""
echo "Press Ctrl+C to stop the server"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Start the Flask application
python app.py
