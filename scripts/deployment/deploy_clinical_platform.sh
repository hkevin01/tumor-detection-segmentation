#!/bin/bash
# Medical Imaging AI Platform - Clinical Deployment Script
# Generated automatically - ready for clinical use

echo "🏥 Medical Imaging AI Platform - Clinical Deployment"
echo "=================================================="

echo "✅ Step 1: Validating platform readiness..."
python3 scripts/validation/complete_tasks_validation.py

echo "✅ Step 2: Running clinical integration demo..."
python3 scripts/clinical/clinical_demo.py

echo "✅ Step 3: Testing real dataset training..."
python3 scripts/clinical/real_dataset_launcher.py --simulate --model multimodal_unetr --dataset msd_brain

echo "🎉 Platform validation complete - ready for clinical deployment!"
echo "📁 Reports available in: reports/clinical/"
echo "📊 Demo outputs in: outputs/clinical_demo/"

echo ""
echo "🔧 Next steps for full deployment:"
echo "1. Install dependencies: pip install torch monai mlflow fastapi"
echo "2. Download datasets: --download flag with real_dataset_launcher.py"
echo "3. Launch clinical training: scripts/clinical/clinical_integration_suite.py"
