#!/bin/bash

# Project Reorganization - Phase 3: File Movement and Consolidation
echo "📦 Starting Project Reorganization - Phase 3"
echo "=============================================="

# Execute previous phases first
chmod +x reorganize_phase1.sh reorganize_phase2.sh
./reorganize_phase1.sh
./reorganize_phase2.sh

echo ""
echo "🔄 Moving files to optimal locations..."

# 1. Move and consolidate AI/ML core files
echo "🧠 Organizing AI/ML components..."

# Keep the most comprehensive medical AI backend (medical_ai_backend.py is most complete)
if [ -f "src/medical_ai_backend.py" ]; then
    mv src/medical_ai_backend.py lib/ai/models/medical_ai_engine.py
    echo "   ✅ Moved medical AI backend to lib/ai/models/medical_ai_engine.py"
fi

# Move FastAPI backend
if [ -f "src/medical_imaging_api.py" ]; then
    mv src/medical_imaging_api.py app/api/medical_imaging_api.py
    echo "   ✅ Moved API to app/api/medical_imaging_api.py"
fi

# Remove redundant medical AI file (keeping the more comprehensive one)
if [ -f "src/medical_imaging_ai.py" ]; then
    rm src/medical_imaging_ai.py
    echo "   🗑️  Removed redundant medical_imaging_ai.py"
fi

# 2. Organize training components
echo "🏋️  Organizing training components..."
if [ -d "src/training" ]; then
    mv src/training/* lib/ai/training/ 2>/dev/null
    rmdir src/training 2>/dev/null
    echo "   ✅ Moved training components to lib/ai/training/"
fi

# Remove redundant top-level train.py (keep the one in training/)
if [ -f "src/train.py" ]; then
    rm src/train.py
    echo "   🗑️  Removed redundant top-level train.py"
fi

# 3. Organize data processing
echo "📊 Organizing data components..."
if [ -d "src/data" ]; then
    mv src/data/* lib/ai/data/ 2>/dev/null
    rmdir src/data 2>/dev/null
    echo "   ✅ Moved data components to lib/ai/data/"
fi

# Move top-level data files
if [ -f "src/dataset.py" ]; then
    mv src/dataset.py lib/ai/data/
    echo "   ✅ Moved dataset.py to lib/ai/data/"
fi

if [ -f "src/data_preprocessing.py" ]; then
    mv src/data_preprocessing.py lib/ai/data/
    echo "   ✅ Moved data_preprocessing.py to lib/ai/data/"
fi

# 4. Organize evaluation components  
echo "📈 Organizing evaluation components..."
if [ -d "src/evaluation" ]; then
    mv src/evaluation/* lib/ai/evaluation/ 2>/dev/null
    rmdir src/evaluation 2>/dev/null
    echo "   ✅ Moved evaluation components to lib/ai/evaluation/"
fi

if [ -f "src/evaluate.py" ]; then
    mv src/evaluate.py lib/ai/evaluation/
    echo "   ✅ Moved evaluate.py to lib/ai/evaluation/"
fi

# 5. Organize inference components
echo "🔮 Organizing inference components..."
if [ -d "src/inference" ]; then
    mv src/inference/* lib/ai/inference/ 2>/dev/null
    rmdir src/inference 2>/dev/null
    echo "   ✅ Moved inference components to lib/ai/inference/"
fi

if [ -f "src/inference.py" ]; then
    mv src/inference.py lib/ai/inference/
    echo "   ✅ Moved inference.py to lib/ai/inference/"
fi

# 6. Organize medical imaging specific components
echo "🏥 Organizing medical imaging components..."
if [ -d "src/patient_analysis" ]; then
    mv src/patient_analysis/* lib/medical/analysis/ 2>/dev/null
    rmdir src/patient_analysis 2>/dev/null
    echo "   ✅ Moved patient analysis to lib/medical/analysis/"
fi

if [ -d "src/reporting" ]; then
    mv src/reporting/* lib/medical/reports/ 2>/dev/null
    rmdir src/reporting 2>/dev/null
    echo "   ✅ Moved reporting to lib/medical/reports/"
fi

if [ -d "src/fusion" ]; then
    mv src/fusion/* lib/medical/imaging/ 2>/dev/null
    rmdir src/fusion 2>/dev/null
    echo "   ✅ Moved fusion components to lib/medical/imaging/"
fi

# 7. Organize utilities
echo "🔧 Organizing utility components..."
if [ -d "src/utils" ]; then
    mv src/utils/* lib/utils/ 2>/dev/null
    rmdir src/utils 2>/dev/null
    echo "   ✅ Moved utils to lib/utils/"
fi

if [ -f "src/utils.py" ]; then
    mv src/utils.py lib/utils/
    echo "   ✅ Moved utils.py to lib/utils/"
fi

# 8. Move DICOM components from src/components
echo "🖼️  Organizing DICOM components..."
if [ -d "src/components" ]; then
    mv src/components/* lib/medical/dicom/ 2>/dev/null
    rmdir src/components 2>/dev/null
    echo "   ✅ Moved DICOM components to lib/medical/dicom/"
fi

# 9. Clean up empty src directory and README
if [ -f "src/README.md" ]; then
    mv src/README.md docs/developer/
    echo "   ✅ Moved src README to docs/developer/"
fi

if [ -f "src/__init__.py" ]; then
    rm src/__init__.py  # Will recreate optimized versions
    echo "   🗑️  Removed old __init__.py"
fi

# Remove src directory if empty
if [ -d "src" ] && [ -z "$(ls -A src)" ]; then
    rmdir src
    echo "   🗑️  Removed empty src directory"
fi

# 10. Organize frontend properly
echo "⚛️  Organizing frontend components..."
if [ -d "frontend" ]; then
    # Move frontend to app directory
    mv frontend app/
    echo "   ✅ Moved frontend to app/frontend/"
fi

# 11. Organize configuration files
echo "⚙️  Organizing configuration files..."
if [ -f "config.json" ]; then
    mv config.json config/environments/default.json
    echo "   ✅ Moved config.json to config/environments/default.json"
fi

# 12. Organize deployment and scripts
echo "🚀 Organizing deployment files..."
deployment_files=(
    "Dockerfile"
    "docker-compose.yml" 
    "start_medical_gui.sh"
    "quick_setup.sh"
    "run_gui.sh"
)

for file in "${deployment_files[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" deployments/scripts/
        echo "   ✅ Moved $file to deployments/scripts/"
    fi
done

# 13. Organize documentation
echo "📚 Organizing documentation..."
doc_files=(
    "MEDICAL_GUI_README.md:user-guide/README.md"
    "IMPLEMENTATION_SUMMARY.md:developer/implementation.md"
    "GIT_SETUP_GUIDE.md:developer/git-setup.md"
    "GUI_README.md:user-guide/gui-guide.md"
    "GUI_STATUS.md:developer/gui-status.md"
    "DICOM_VIEWER_COMPLETE.md:developer/dicom-viewer.md"
    "REORGANIZATION_SUMMARY.md:developer/reorganization.md"
    "STEPS.md:developer/steps.md"
)

for doc_mapping in "${doc_files[@]}"; do
    IFS=':' read -r source target <<< "$doc_mapping"
    if [ -f "$source" ]; then
        mv "$source" "docs/$target"
        echo "   ✅ Moved $source to docs/$target"
    fi
done

# 14. Organize test and demo files
echo "🧪 Organizing test and demo files..."
test_files=(
    "test_system.py"
    "test_gui.py"
    "demo_system.py"
    "system_status.sh"
)

for file in "${test_files[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" tools/
        echo "   ✅ Moved $file to tools/"
    fi
done

# Move existing tests directory
if [ -d "tests" ]; then
    mv tests/* tests/unit/ 2>/dev/null
    echo "   ✅ Reorganized tests into unit tests"
fi

# 15. Organize other important files
echo "📄 Organizing remaining files..."

# Move notebooks to examples
if [ -d "notebooks" ]; then
    mv notebooks examples/
    echo "   ✅ Moved notebooks to examples/"
fi

# Move setup files to tools
setup_files=(
    "setup.py"
    "setup_enhanced_gui.sh"
    "setup_git.sh"
    "git_status.sh"
    "install_powershell.sh"
)

for file in "${setup_files[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" tools/
        echo "   ✅ Moved $file to tools/"
    fi
done

# Move requirements to root (keep there) but create environment-specific ones
if [ -f "requirements.txt" ]; then
    cp requirements.txt config/environments/requirements-default.txt
    echo "   ✅ Copied requirements to config/environments/"
fi

echo ""
echo "✅ Phase 3 Complete: File movement and consolidation finished"
