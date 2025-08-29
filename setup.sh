#!/bin/bash

# HRIS Setup Script - Backend and Frontend
# This script sets up the Django backend and React frontend

set -e  # Exit on any error

echo "🚀 HRIS Setup Script Starting..."
echo "================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    print_error "manage.py not found. Please run this script from the HRIS root directory."
    exit 1
fi

echo ""
echo "🐍 BACKEND SETUP"
echo "=================="

# Check Python version
print_info "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_status "Found $PYTHON_VERSION"
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_VERSION=$(python --version)
    print_status "Found $PYTHON_VERSION"
    PYTHON_CMD="python"
else
    print_error "Python not found. Please install Python 3.8+ first."
    exit 1
fi

# Virtual environment setup
print_info "Setting up virtual environment..."
if [ -d "venv" ]; then
    print_warning "Virtual environment already exists, activating..."
else
    print_info "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    print_status "Virtual environment created"
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate
print_status "Virtual environment activated"

# Upgrade pip
print_info "Upgrading pip..."
pip install --upgrade pip

# Install backend dependencies
print_info "Installing Django dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    print_status "Backend dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi

# Database setup
print_info "Setting up database..."
$PYTHON_CMD manage.py makemigrations
$PYTHON_CMD manage.py migrate
print_status "Database setup complete"

# Initialize RBAC system
print_info "Initializing RBAC system..."
$PYTHON_CMD manage.py init_rbac --create-superuser --email="admin@hris.com" --password="Admin123!@#" --create-sample-orgs
print_status "RBAC system initialized"

# Setup social apps
print_info "Setting up social authentication..."
$PYTHON_CMD manage.py setup_social_apps --update-site
print_status "Social authentication configured"

print_status "Backend setup complete!"

echo ""
echo "⚛️  FRONTEND SETUP"
echo "=================="

# Check if frontend directory exists
if [ -d "broker-console-frontend" ]; then
    cd broker-console-frontend
    
    # Check Node.js version
    print_info "Checking Node.js version..."
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        print_status "Found Node.js $NODE_VERSION"
    else
        print_error "Node.js not found. Please install Node.js 16+ first."
        print_info "Download from: https://nodejs.org/"
        exit 1
    fi
    
    # Check npm
    if command -v npm &> /dev/null; then
        NPM_VERSION=$(npm --version)
        print_status "Found npm $NPM_VERSION"
    else
        print_error "npm not found. Please install npm first."
        exit 1
    fi
    
    # Install frontend dependencies
    print_info "Installing React dependencies..."
    if [ -f "package.json" ]; then
        npm install
        print_status "Frontend dependencies installed"
    else
        print_error "package.json not found in broker-console-frontend"
        exit 1
    fi
    
    print_status "Frontend setup complete!"
    cd ..
else
    print_warning "Frontend directory (broker-console-frontend) not found, skipping frontend setup"
fi

echo ""
echo "🎉 SETUP COMPLETE!"
echo "=================="

print_status "Both backend and frontend are ready!"
echo ""
print_info "Next steps:"
echo ""
echo "1. Start the Django backend:"
echo "   source venv/bin/activate"
echo "   python manage.py runserver 8089"
echo ""

if [ -d "broker-console-frontend" ]; then
    echo "2. Start the React frontend (in a new terminal):"
    echo "   cd broker-console-frontend"
    echo "   npm start"
    echo ""
fi

echo "3. Access the application:"
echo "   🔗 Backend Admin: http://localhost:8089/admin/"
echo "   🔗 Authentication: http://localhost:8089/accounts/login/"
echo "   🔗 API Docs: http://localhost:8089/swagger/"

if [ -d "broker-console-frontend" ]; then
    echo "   🔗 Frontend: http://localhost:3000/"
fi

echo ""
echo "4. Admin credentials:"
echo "   📧 Email: admin@hris.com"
echo "   🔑 Password: Admin123!@#"
echo ""

print_info "Environment file:"
echo "   Copy .env.example to .env and configure as needed"
echo "   cp .env.example .env"
echo ""

print_status "Setup script completed successfully! 🎉"

# Test endpoints if user wants
echo ""
read -p "🧪 Would you like to test the endpoints now? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_info "Starting Django server for testing..."
    $PYTHON_CMD manage.py runserver 8089 &
    SERVER_PID=$!
    
    # Wait for server to start
    sleep 3
    
    # Run tests
    python3 test_endpoints.py
    
    # Stop server
    kill $SERVER_PID 2>/dev/null || true
    print_info "Test completed and server stopped"
fi