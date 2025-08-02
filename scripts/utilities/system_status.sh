#!/bin/bash

# Medical Imaging AI System Status
echo "🏥 Medical Imaging AI System Status"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo ""
print_status "✅ System Status Summary:"

# Check if backend is running
if curl -s http://localhost:8000/health > /dev/null 2>&1 || lsof -i :8000 > /dev/null 2>&1; then
    print_success "🚀 Backend API is running on http://localhost:8000"
    print_status "   📚 Documentation: http://localhost:8000/docs"
else
    print_warning "⚠️  Backend API is not running"
fi

# Check if frontend is running
if lsof -i :3000 > /dev/null 2>&1; then
    print_success "🌐 Frontend is running on http://localhost:3000"
else
    print_warning "⚠️  Frontend is not running"
fi

# Check frontend dependencies
if [ -f "gui/frontend/node_modules/.bin/react-scripts" ]; then
    print_success "✅ Frontend dependencies are properly installed"
else
    print_error "❌ Frontend dependencies need fixing"
fi

# Check virtual environment
if [ -d ".venv" ] && [ -n "$VIRTUAL_ENV" ]; then
    print_success "✅ Python virtual environment is active"
elif [ -d ".venv" ]; then
    print_warning "⚠️  Virtual environment exists but not activated"
else
    print_error "❌ Virtual environment not found"
fi

echo ""
print_status "🛠️  Available Commands:"
echo ""
echo "   🚀 Start Full System:"
echo "      ./scripts/utilities/start_medical_gui.sh"
echo ""
echo "   🔧 Fix Frontend Issues:"
echo "      ./scripts/setup/fix_frontend.sh"
echo ""
echo "   ⚡ Quick Setup/Reinstall:"
echo "      ./scripts/setup/quick_setup.sh"
echo ""
echo "   📊 Check Git Status:"
echo "      ./scripts/utilities/git_status.sh"
echo ""
echo "   🖥️  Run API Only:"
echo "      ./scripts/utilities/run_gui.sh"
echo ""

print_status "🎯 Quick Actions:"
if ! curl -s http://localhost:8000/health > /dev/null 2>&1 && ! lsof -i :8000 > /dev/null 2>&1; then
    echo "   1. Start the backend: ./scripts/utilities/start_medical_gui.sh"
fi

if [ ! -f "gui/frontend/node_modules/.bin/react-scripts" ]; then
    echo "   2. Fix frontend: ./scripts/setup/fix_frontend.sh"
fi

if ! lsof -i :3000 > /dev/null 2>&1 && [ -f "gui/frontend/node_modules/.bin/react-scripts" ]; then
    echo "   3. Start frontend: cd gui/frontend && npm start"
fi

echo ""
print_success "🎉 Your Medical Imaging AI project is organized and ready!"
echo ""
print_status "💡 Tips:"
echo "   • The API documentation is interactive - try it at http://localhost:8000/docs"
echo "   • Frontend takes 30-60 seconds to start completely"
echo "   • Use Ctrl+C to stop running services"
echo "   • Check ./docs/ for detailed documentation"
