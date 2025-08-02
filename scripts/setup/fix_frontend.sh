#!/bin/bash

# Frontend Setup and Fix Script
echo "🌐 Frontend Setup and Dependency Fix"
echo "===================================="

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

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

# Find frontend directory
FRONTEND_DIR=""
if [ -d "gui/frontend" ]; then
    FRONTEND_DIR="gui/frontend"
    print_status "Found frontend in gui/frontend/"
elif [ -d "frontend" ]; then
    FRONTEND_DIR="frontend"
    print_status "Found frontend in frontend/"
else
    print_error "No frontend directory found!"
    exit 1
fi

cd "$FRONTEND_DIR"

print_status "Current directory: $(pwd)"

# Check if package.json exists
if [ ! -f "package.json" ]; then
    print_error "No package.json found in frontend directory!"
    exit 1
fi

print_status "Fixing TypeScript dependency conflicts..."

# 1. Clean existing node_modules and package-lock.json
if [ -d "node_modules" ]; then
    print_status "Removing existing node_modules..."
    rm -rf node_modules
fi

if [ -f "package-lock.json" ]; then
    print_status "Removing package-lock.json..."
    rm -f package-lock.json
fi

if [ -f "yarn.lock" ]; then
    print_status "Removing yarn.lock..."
    rm -f yarn.lock
fi

# 2. Update TypeScript version in package.json to be compatible
print_status "Checking package.json for TypeScript version..."

# Check if typescript is in dependencies or devDependencies
if grep -q '"typescript"' package.json; then
    print_status "Found TypeScript in package.json, updating to compatible version..."
    
    # Use sed to update TypeScript version to 4.9.5 for compatibility with react-scripts@5.0.1
    sed -i 's/"typescript": "[^"]*"/"typescript": "~4.9.5"/g' package.json
    print_success "Updated TypeScript version to ~4.9.5 for react-scripts compatibility"
fi

# 3. Install dependencies with legacy peer deps
print_status "Installing dependencies with legacy peer deps to resolve conflicts..."
npm install --legacy-peer-deps

if [ $? -eq 0 ]; then
    print_success "Dependencies installed successfully!"
else
    print_warning "Installation with --legacy-peer-deps failed, trying --force..."
    npm install --force
    
    if [ $? -eq 0 ]; then
        print_success "Dependencies installed with --force!"
    else
        print_error "Both installation methods failed. Manual intervention required."
        echo ""
        print_status "You can try:"
        echo "   1. cd $FRONTEND_DIR"
        echo "   2. npm install --legacy-peer-deps --no-audit"
        echo "   3. Or manually fix package.json dependencies"
        exit 1
    fi
fi

# 4. Verify react-scripts is installed
if [ -f "node_modules/.bin/react-scripts" ]; then
    print_success "react-scripts installed successfully!"
else
    print_warning "react-scripts not found, installing separately..."
    npm install react-scripts@5.0.1 --legacy-peer-deps
fi

# 5. Show TypeScript version that was installed
if [ -d "node_modules/typescript" ]; then
    TS_VERSION=$(node -e "console.log(require('./node_modules/typescript/package.json').version)")
    print_success "TypeScript version installed: $TS_VERSION"
fi

echo ""
print_success "🎉 Frontend setup complete!"
echo ""
print_status "You can now:"
echo "   • Start the frontend: npm start"
echo "   • Run the full system: ../../scripts/utilities/start_medical_gui.sh"
echo "   • Build for production: npm run build"
echo ""
print_status "Frontend will be available at: http://localhost:3000"
