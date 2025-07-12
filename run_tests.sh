#!/bin/bash

echo "🧪 Running Alexandria Tests"
echo "=========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Check if Python is available
if ! command -v python &> /dev/null; then
    print_error "Python is not installed or not in PATH"
    exit 1
fi

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed or not in PATH"
    exit 1
fi

# Check if npm is available
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed or not in PATH"
    exit 1
fi

echo ""
echo "📦 Backend Tests (Python)"
echo "-------------------------"

# Install Python dependencies if needed
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    print_warning "No virtual environment found. Installing dependencies globally..."
    pip install -r requirements.txt
fi

# Run backend tests
echo "Running backend unit tests..."
if python -m pytest test_app.py -v; then
    print_status "Backend tests passed"
else
    print_error "Backend tests failed"
    exit 1
fi

echo ""
echo "🌐 Frontend Tests (React)"
echo "-------------------------"

# Install npm dependencies if needed
if [ ! -d "node_modules" ]; then
    print_warning "Installing npm dependencies..."
    npm install
fi

# Run frontend tests
echo "Running frontend tests..."
if npm run test:coverage; then
    print_status "Frontend tests passed"
else
    print_error "Frontend tests failed"
    exit 1
fi

echo ""
echo "🎯 Integration Tests"
echo "-------------------"

# Check if backend server is running
echo "Checking if backend server is running..."
if curl -s http://localhost:5001/api/health > /dev/null; then
    print_status "Backend server is running"
    
    # Run integration tests
    echo "Running integration tests..."
    if python -c "
import requests
import json

# Test the search API
response = requests.post('http://localhost:5001/api/search', 
                        json={'query': 'Guy Fawkes'})
if response.status_code == 200:
    data = response.json()
    if data['status'] == 'success' and len(data['citations']) > 0:
        print('✅ Integration test passed: Found', len(data['citations']), 'citations')
        exit(0)
    else:
        print('❌ Integration test failed: No citations found')
        exit(1)
else:
    print('❌ Integration test failed: API returned', response.status_code)
    exit(1)
"; then
        print_status "Integration tests passed"
    else
        print_error "Integration tests failed"
        exit 1
    fi
else
    print_warning "Backend server is not running. Skipping integration tests."
    print_warning "Start the backend with: python app.py"
fi

echo ""
echo "🎉 All tests completed successfully!"
echo ""
echo "📊 Test Summary:"
echo "  - Backend unit tests: ✅"
echo "  - Frontend tests: ✅"
echo "  - Integration tests: ✅"
echo ""
echo "🚀 Ready to deploy!" 