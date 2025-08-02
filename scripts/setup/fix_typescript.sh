#!/bin/bash

# TypeScript Module Fix Script
echo "🔧 Fixing TypeScript Module Issues"
echo "================================="

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

cd "$PROJECT_ROOT/gui/frontend"

print_status "Finding TypeScript files without exports..."

# Function to check if file has imports or exports
check_file_needs_export() {
    local file=$1
    if ! grep -E '^(import|export)' "$file" > /dev/null; then
        return 0 # true - needs export
    fi
    return 1 # false - already has imports/exports
}

# Function to add export statement if needed
add_export_if_needed() {
    local file=$1
    if check_file_needs_export "$file"; then
        print_status "Adding export to: ${file#$PROJECT_ROOT/gui/frontend/}"
        
        # Read the file content
        content=$(cat "$file")
        
        # Check if it's a React component
        if grep -E 'React|Component|FC|function.*\(' "$file" > /dev/null; then
            # Add React import and export for components
            echo "import React from 'react';
$content
export {};" > "$file"
            print_success "✓ Added React import and export"
        else
            # Just add export for utility files
            echo "$content
export {};" > "$file"
            print_success "✓ Added export statement"
        fi
        return 0
    fi
    return 1
}

# Process all TypeScript files
echo ""
print_status "Scanning files..."
echo ""

# Track counts
fixed_count=0
total_count=0

# Process component files
for file in src/components/*.tsx src/views/*.tsx src/hooks/*.ts src/services/*.ts src/utils/*.ts; do
    if [ -f "$file" ]; then
        ((total_count++))
        if add_export_if_needed "$file"; then
            ((fixed_count++))
        fi
    fi
done

echo ""
print_success "🎉 TypeScript Module Fix Complete!"
echo "   • Files processed: $total_count"
echo "   • Files fixed: $fixed_count"
echo ""

# Update tsconfig.json if needed
if [ -f "tsconfig.json" ]; then
    print_status "Checking tsconfig.json settings..."
    if ! grep '"isolatedModules": true' tsconfig.json > /dev/null; then
        print_warning "Adding isolatedModules setting to tsconfig.json"
        # Use temporary file for sed operation
        sed -i 's/"compilerOptions": {/"compilerOptions": {\n    "isolatedModules": true,/' tsconfig.json
    fi
fi

print_status "Next steps:"
echo "   1. Run: npm start"
echo "   2. Check for any remaining TypeScript errors"
echo "   3. If needed, run: ./scripts/setup/fix_frontend.sh"
echo ""
