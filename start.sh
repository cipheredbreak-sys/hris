#!/bin/bash

# HRIS Start Script - Start both backend and frontend
# Run this after initial setup to start the servers

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}🚀 Starting HRIS Application...${NC}"
echo "================================"

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo -e "${RED}❌ manage.py not found. Please run this script from the HRIS root directory.${NC}"
    exit 1
fi

# Function to start backend
start_backend() {
    echo -e "${BLUE}🐍 Starting Django Backend...${NC}"
    
    # Activate virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo -e "${GREEN}✅ Virtual environment activated${NC}"
    else
        echo -e "${YELLOW}⚠️  Virtual environment not found. Run ./setup.sh first.${NC}"
        exit 1
    fi
    
    # Start Django server on port 8089
    echo -e "${BLUE}🌐 Starting Django server on http://localhost:8089${NC}"
    python manage.py runserver 8089 &
    BACKEND_PID=$!
    echo "Backend PID: $BACKEND_PID"
}

# Function to start frontend
start_frontend() {
    if [ -d "broker-console-frontend" ]; then
        echo -e "${BLUE}⚛️  Starting React Frontend...${NC}"
        cd broker-console-frontend
        
        # Check if node_modules exists
        if [ -d "node_modules" ]; then
            echo -e "${BLUE}🌐 Starting React server on http://localhost:3000${NC}"
            npm start &
            FRONTEND_PID=$!
            echo "Frontend PID: $FRONTEND_PID"
            cd ..
        else
            echo -e "${YELLOW}⚠️  node_modules not found. Run ./setup.sh first.${NC}"
            cd ..
        fi
    else
        echo -e "${YELLOW}⚠️  Frontend directory not found, skipping...${NC}"
    fi
}

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down servers...${NC}"
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
        echo "Backend stopped"
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
        echo "Frontend stopped"
    fi
    exit 0
}

# Trap Ctrl+C
trap cleanup INT

# Start servers
start_backend
sleep 2  # Give backend time to start
start_frontend

echo ""
echo -e "${GREEN}🎉 Applications started successfully!${NC}"
echo ""
echo "📍 Access points:"
echo "   🔗 Backend Admin: http://localhost:8089/admin/"
echo "   🔗 Authentication: http://localhost:8089/accounts/login/"
echo "   🔗 API Docs: http://localhost:8089/swagger/"
if [ -d "broker-console-frontend" ]; then
    echo "   🔗 Frontend: http://localhost:3000/"
fi
echo ""
echo "🔑 Admin credentials:"
echo "   📧 Email: admin@hris.com"
echo "   🔒 Password: Admin123!@#"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop both servers${NC}"

# Wait for user to stop
wait