#!/bin/bash

# Invisi-Scan SOC Pipeline - Stop All Services
# This script stops all running services

echo "🛑 Stopping Invisi-Scan SOC Pipeline..."
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to kill process on port
kill_port() {
    local port=$1
    local name=$2
    if lsof -ti:$port >/dev/null 2>&1; then
        echo -e "${YELLOW}Stopping $name on port $port...${NC}"
        kill $(lsof -ti:$port) 2>/dev/null
        sleep 1
        if lsof -ti:$port >/dev/null 2>&1; then
            echo -e "${RED}Force killing $name...${NC}"
            kill -9 $(lsof -ti:$port) 2>/dev/null
        fi
        echo -e "${GREEN}✅ $name stopped${NC}"
    else
        echo -e "${GREEN}ℹ️  $name not running on port $port${NC}"
    fi
}

# Stop services
kill_port 8001 "Backend API (FastAPI)"
kill_port 5173 "Frontend UI (React)"
kill_port 5174 "Frontend UI (React)"

# Kill any remaining processes
echo -e "${YELLOW}Cleaning up any remaining processes...${NC}"
pkill -f "uvicorn api:app" 2>/dev/null
pkill -f "vite" 2>/dev/null

echo ""
echo -e "${GREEN}✅ All services stopped successfully!${NC}"
echo "=========================================="