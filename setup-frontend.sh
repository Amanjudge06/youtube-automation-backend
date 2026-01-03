#!/bin/bash

# YouTube Automation - Frontend & Backend Setup Script
echo "🚀 Setting up YouTube Automation Web Interface..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}$1${NC}"
}

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    print_error "Please run this script from the YouTube Automation project root directory"
    exit 1
fi

print_header "========================================"
print_header "  YouTube Automation Setup"
print_header "========================================"

# Step 1: Update Python dependencies
print_status "Step 1: Installing Python dependencies..."
if [ -f ".venv/bin/python" ]; then
    .venv/bin/pip install -r requirements.txt
else
    pip install -r requirements.txt
fi

# Step 2: Setup Node.js frontend
print_status "Step 2: Setting up React frontend..."

cd frontend

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js first:"
    print_error "https://nodejs.org/"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    print_error "npm is not installed. Please install npm first"
    exit 1
fi

# Install frontend dependencies
print_status "Installing Node.js dependencies..."
npm install

# Build the frontend
print_status "Building React frontend..."
npm run build

cd ..

# Step 3: Create startup scripts
print_status "Step 3: Creating startup scripts..."

# Create development startup script
cat > start-dev.sh << 'EOF'
#!/bin/bash

# Start YouTube Automation in Development Mode
echo "🚀 Starting YouTube Automation in Development Mode..."

# Check if virtual environment exists
if [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
else
    PYTHON_CMD="python"
fi

echo "📱 Starting FastAPI backend on http://localhost:8000"
echo "🎬 Starting frontend development server on http://localhost:3000"

# Start backend in background
$PYTHON_CMD app.py &
BACKEND_PID=$!

# Start frontend in development mode
cd frontend
npm start &
FRONTEND_PID=$!

cd ..

echo "🎯 Backend PID: $BACKEND_PID"
echo "🎯 Frontend PID: $FRONTEND_PID"
echo ""
echo "📱 Access the application at:"
echo "   - Production:  http://localhost:8000"
echo "   - Development: http://localhost:3000"
echo ""
echo "To stop the servers, press Ctrl+C or run: ./stop-dev.sh"

# Save PIDs for cleanup
echo $BACKEND_PID > .backend.pid
echo $FRONTEND_PID > .frontend.pid

# Wait for user interrupt
wait
EOF

# Create production startup script
cat > start-prod.sh << 'EOF'
#!/bin/bash

# Start YouTube Automation in Production Mode
echo "🚀 Starting YouTube Automation in Production Mode..."

# Check if virtual environment exists
if [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
else
    PYTHON_CMD="python"
fi

echo "🎬 Building frontend..."
cd frontend
npm run build
cd ..

echo "📱 Starting production server on http://localhost:8000"
$PYTHON_CMD app.py
EOF

# Create stop script
cat > stop-dev.sh << 'EOF'
#!/bin/bash

echo "🛑 Stopping YouTube Automation servers..."

# Kill backend
if [ -f ".backend.pid" ]; then
    BACKEND_PID=$(cat .backend.pid)
    kill $BACKEND_PID 2>/dev/null
    rm .backend.pid
    echo "✅ Backend stopped"
fi

# Kill frontend
if [ -f ".frontend.pid" ]; then
    FRONTEND_PID=$(cat .frontend.pid)
    kill $FRONTEND_PID 2>/dev/null
    rm .frontend.pid
    echo "✅ Frontend stopped"
fi

# Kill any remaining processes
pkill -f "app.py"
pkill -f "react-scripts"

echo "🎯 All servers stopped"
EOF

# Make scripts executable
chmod +x start-dev.sh
chmod +x start-prod.sh
chmod +x stop-dev.sh

print_status "Step 4: Creating desktop shortcut..."

# Create desktop shortcut (if on macOS/Linux with desktop environment)
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    cat > "YouTube Automation.command" << EOF
#!/bin/bash
cd "$(dirname "$0")"
./start-prod.sh
EOF
    chmod +x "YouTube Automation.command"
    print_status "Created YouTube Automation.command for macOS"
fi

print_header "========================================"
print_header "  ✅ Setup Complete!"
print_header "========================================"

print_status "🎉 YouTube Automation web interface is ready!"
echo ""
print_status "📱 To start the application:"
echo "   Development mode: ./start-dev.sh"
echo "   Production mode:  ./start-prod.sh"
echo ""
print_status "🌐 Access URLs:"
echo "   Production:  http://localhost:8000"
echo "   Development: http://localhost:3000 (with live reload)"
echo ""
print_status "🛑 To stop servers:"
echo "   ./stop-dev.sh (or Ctrl+C)"
echo ""
print_warning "📋 Next Steps:"
echo "   1. Configure your API keys in the Settings tab"
echo "   2. Test the automation from the Dashboard"
echo "   3. Monitor progress in the Logs tab"
echo ""

print_header "🚀 Starting production server now..."
./start-prod.sh