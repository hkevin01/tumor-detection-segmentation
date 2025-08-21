#!/bin/bash
# Enhanced Docker Entrypoint for Phase 4 Integrations

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Tumor Detection Phase 4 Container${NC}"
echo -e "${BLUE}Advanced Medical AI Integrations${NC}"
echo -e "${BLUE}========================================${NC}"

# Initialize nnU-Net environment
echo -e "${GREEN}Setting up nnU-Net environment...${NC}"
mkdir -p "$nnUNet_raw" "$nnUNet_preprocessed" "$nnUNet_results"

# Verify framework installations
echo -e "${GREEN}Verifying installations...${NC}"
python -c "
import torch
import nnunetv2
import monai
import detectron2

print(f'✓ PyTorch {torch.__version__} (CUDA: {torch.cuda.is_available()})')
print(f'✓ nnU-Net {nnunetv2.__version__}')
print(f'✓ MONAI {monai.__version__}')
print(f'✓ Detectron2 installed')
print('All frameworks ready!')
"

# Download sample models if needed
if [ ! -z "$DOWNLOAD_MODELS" ] && [ "$DOWNLOAD_MODELS" = "true" ]; then
    echo -e "${GREEN}Downloading sample pretrained models...${NC}"
    python -c "
from src.integrations.model_downloader import download_sample_models
download_sample_models()
"
fi

echo -e "${GREEN}Container initialization complete!${NC}"

# Execute the main command
exec "$@"
