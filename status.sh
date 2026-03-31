#!/bin/bash

# Invisi-Scan SOC Pipeline - Service Status Checker
# This script checks the status of all services

echo "📊 Invisi-Scan SOC Pipeline - Service Status"
echo "============================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check service
check_service() {
    local port=$1
    local name=$2
    local url=$3

    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo -e "${GREEN}✅ $name: RUNNING on $url${NC}"
        return 0
    else
        echo -e "${RED}❌ $name: STOPPED${NC}"
        return 1
    fi
}

# Check services
check_service 8001 "Backend API (FastAPI)" "http://localhost:8001"
check_service 5173 "Frontend UI (React)" "http://localhost:5173" || check_service 5174 "Frontend UI (React)" "http://localhost:5174"

echo ""
echo -e "${BLUE}💡 Commands:${NC}"
echo "   Start all:  ./run.sh"
echo "   Stop all:   ./stop.sh"
echo "   Check status: ./status.sh"
echo ""
echo "============================================"