#!/bin/bash

# Stop All Services Script
echo "🛑 Stopping IAM SOX Compliance System Services..."
echo "================================================"

cd "$(dirname "$0")"

# Function to stop a service
stop_service() {
    local service_name=$1
    local pid_file="pids/${service_name,,}.pid"
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo "🔄 Stopping $service_name (PID: $pid)..."
            kill "$pid"
            sleep 2
            
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                echo "   Force stopping $service_name..."
                kill -9 "$pid"
            fi
            
            echo " $service_name stopped"
        else
            echo " $service_name was not running"
        fi
        rm -f "$pid_file"
    else
        echo " No PID file found for $service_name"
    fi
}

# Stop services
stop_service "Chat-UI"
stop_service "Orchestrator-API"
stop_service "SailPoint-API"

# Also kill any remaining Flask processes on our ports
echo ""
echo " Checking for remaining processes..."

# Kill processes on specific ports
for port in 5001 5002 5003; do
    local pid=$(lsof -ti:$port 2>/dev/null)
    if [ -n "$pid" ]; then
        echo "🔄 Killing process on port $port (PID: $pid)"
        kill -9 "$pid" 2>/dev/null
    fi
done

# Clean up
rm -rf pids

echo ""
echo " All services stopped"
echo " Log files preserved in logs/ directory"
echo "🚀 To restart: ./start_all.sh"
