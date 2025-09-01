#!/bin/bash

# Master Startup Script for Complete IAM SOX Compliance System
echo "🚀 IAM SOX Compliance System - Master Startup"
echo "================================================"
echo ""

# Function to start a service in background
start_service() {
    local service_name=$1
    local script_path=$2
    local port=$3
    
    echo "🔄 Starting $service_name..."
    
    # Make script executable
    chmod +x "$script_path"
    
    # Start in background and capture PID
    "$script_path" > "logs/${service_name,,}.log" 2>&1 &
    local pid=$!
    
    echo "$pid" > "pids/${service_name,,}.pid"
    echo " $service_name started (PID: $pid) on port $port"
    
    # Wait a moment for service to start
    sleep 2
}

# Function to check if port is available
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        echo " Port $port is already in use"
        return 1
    fi
    return 0
}

# Setup
echo " Setting up environment..."
cd "$(dirname "$0")"

# Create directories for logs and PIDs
mkdir -p logs pids

# Activate virtual environment
source .venv/bin/activate

# Check ports
echo " Checking port availability..."
check_port 5001 || echo "   Chat UI port 5001 may conflict"
check_port 5002 || echo "   SailPoint API port 5002 may conflict"  
check_port 5003 || echo "   Orchestrator API port 5003 may conflict"

echo ""
echo "🚀 Starting services in sequence..."
echo ""

# 1. Start SailPoint Dummy API
start_service "SailPoint-API" "sailpoint_dummy/start_sailpoint.sh" "5002"

# 2. Start Orchestrator API  
start_service "Orchestrator-API" "orchestrator/start_orchestrator.sh" "5003"

# 3. Start Chat UI
start_service "Chat-UI" "start_chat.sh" "5001"

echo ""
echo " All services started successfully!"
echo "================================================"
echo ""
echo " Access Points:"
echo "    Chat Interface:     http://localhost:5001"
echo "    SailPoint API:      http://localhost:5002/api/v1/health"
echo "    Orchestrator API:   http://localhost:5003/api/v1/health"
echo ""
echo " Service Logs:"
echo "    Chat UI:           logs/chat-ui.log"
echo "    SailPoint API:     logs/sailpoint-api.log"
echo "    Orchestrator API:  logs/orchestrator-api.log"
echo ""
echo " Management:"
echo "   Stop all services:    ./stop_all.sh"
echo "   View service status:  ./status.sh"
echo ""
echo " Usage:"
echo "   1. Open http://localhost:5001 in your browser"
echo "   2. Try commands like 'run audit' or 'sailpoint status'"
echo "   3. The system will automatically pull data from SailPoint"
echo "   4. AI model analyzes compliance and provides insights"
echo ""
echo "🎯 Ready for compliance analysis!"
