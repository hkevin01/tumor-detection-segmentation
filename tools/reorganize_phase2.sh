#!/bin/bash

# Project Reorganization - Phase 2: Create Optimal Structure
echo "🏗️  Starting Project Reorganization - Phase 2"
echo "=============================================="

# Create the new optimal directory structure
echo "📁 Creating optimal directory structure..."

# Core application structure
mkdir -p {app,lib,tools,scripts,deployments}

# Backend API structure
mkdir -p app/api/{routes,middleware,models,schemas}
mkdir -p app/core/{config,security,database}

# AI/ML Engine structure  
mkdir -p lib/ai/{models,inference,training,evaluation}
mkdir -p lib/ai/models/{architectures,checkpoints,configs}
mkdir -p lib/ai/data/{preprocessing,loaders,transforms,validation}

# Medical imaging specific
mkdir -p lib/medical/{dicom,imaging,analysis,reports}

# Utilities and shared components
mkdir -p lib/utils/{io,logging,metrics,visualization}

# Frontend structure (keep existing but organize)
mkdir -p app/frontend/{public,assets}

# Configuration and deployment
mkdir -p config/{environments,models,data}
mkdir -p deployments/{docker,kubernetes,scripts}

# Documentation and examples
mkdir -p docs/{api,user-guide,developer,tutorials}
mkdir -p examples/{datasets,notebooks,scripts}

# Testing structure
mkdir -p tests/{unit,integration,e2e,fixtures}

# Data management
mkdir -p data/{raw,processed,models,exports,cache}

echo "✅ Directory structure created successfully"

# List the new structure
echo ""
echo "📋 New Directory Structure:"
tree -d -L 3 app lib config deployments docs examples tests data 2>/dev/null || find . -type d -name "app" -o -name "lib" -o -name "config" -o -name "deployments" -o -name "docs" -o -name "examples" -o -name "tests" -o -name "data" | head -20

echo ""
echo "✅ Phase 2 Complete: Optimal structure created"
