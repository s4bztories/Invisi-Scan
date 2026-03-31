#!/bin/bash

# Invisi-Scan SOC Pipeline - One-Click Launcher
# This script starts all services: Backend and Frontend

echo "🚀 Starting Invisi-Scan SOC Pipeline..."
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    if lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        echo -e "${RED}❌ Port $1 is already in use${NC}"
        return 1
    else
        echo -e "${GREEN}✅ Port $1 is available${NC}"
        return 0
    fi
}

# Check ports
echo "Checking port availability..."
check_port 8001 || exit 1
check_port 5173 || check_port 5174 || exit 1

echo ""
echo "Starting services..."

# Start Backend (FastAPI)
echo -e "${BLUE}📡 Starting Backend API (FastAPI) on port 8001...${NC}"
cd backend
source ../venv/bin/activate
uvicorn api:app --reload --port 8001 &
BACKEND_PID=$!
cd ..
echo -e "${GREEN}✅ Backend started (PID: $BACKEND_PID)${NC}"

# Wait a moment
sleep 2

# Start Frontend (React)
echo -e "${BLUE}🎨 Starting Frontend UI (React) on port 5173/5174...${NC}"
cd frontend
npm run dev -- --port 5174 &
FRONTEND_PID=$!
cd ..
echo -e "${GREEN}✅ Frontend started (PID: $FRONTEND_PID)${NC}"

echo ""
echo -e "${GREEN}🎉 All services started successfully!${NC}"
echo "=========================================="
echo -e "${YELLOW}🌐 Access URLs:${NC}"
echo "   Frontend (Main App):    http://localhost:5174"
echo "   Backend API:            http://localhost:8001"
echo "   API Documentation:      http://localhost:8001/docs"
echo ""
echo -e "${YELLOW}👤 Default Login Credentials:${NC}"
echo "   Operator: operator / operator123"
echo "   Admin:    admin / admin123"
echo ""
echo -e "${YELLOW}🛑 To stop all services, press Ctrl+C or run: ./stop.sh${NC}"
echo ""
echo "=========================================="

# Wait for user interrupt
trap "echo -e '\n${RED}🛑 Shutting down services...${NC}'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT

# Keep script running
wait