# Training Code

This directory contains scripts and modules for training deep learning models for tumor detection and segmentation.

## Enhanced Training Script

The main training script `train_enhanced.py` provides a MONAI-focused training pipeline with advanced features:

### Key Features

- **MONAI Dataset Integration**: Supports MONAI Decathlon datasets with automatic download
- **Sliding Window Inference**: Configurable ROI size from model config with CLI overlap control
- **Auto Channel Detection**: Automatically infers input channels from dataset samples
- **Validation Overlays**: Optional visualization of predictions vs ground truth
- **MLflow Logging**: Optional experiment tracking (when MLflow is installed)
- **Mixed Precision**: AMP support for faster training on compatible hardware

### CLI Arguments

```bash
python src/training/train_enhanced.py \
  --config config/recipes/unetr_multimodal.json \
  --dataset-config config/datasets/msd_task01_brain.json \
  --output-dir models/my_experiment \
  --epochs 100 \
  --sw-overlap 0.25 \
  --save-overlays \
  --overlays-max 5 \
  --amp \
  --seed 42
```

#### New CLI Options

- `--sw-overlap`: Sliding window overlap for validation/inference (default: 0.25)
- `--save-overlays`: Save simple validation overlays showing GT vs predictions
- `--overlays-max`: Maximum number of overlay images to save per validation (default: 2)

### Configuration Integration

The trainer automatically:

- Reads ROI size from `config["model"]["img_size"]` for sliding window inference
- Infers input channels from the first training batch
- Selects transform presets based on dataset config (`"brats_like"` or `"ct_liver"`)

### Output Structure

```text
models/my_experiment/
├── best.pt              # Best model checkpoint
├── last.pt              # Final model checkpoint
└── overlays/            # Validation overlays (if --save-overlays)
    ├── val_overlay_000.png
    ├── val_overlay_001.png
    └── ...
```

### Overlay Visualization

When `--save-overlays` is enabled, the trainer saves axial slice overlays during validation:

- Gray background: First modality (e.g., T1 for brain MRI)
- Green overlay: Ground truth segmentation (semi-transparent)
- Red overlay: Model predictions (semi-transparent)

This provides quick visual feedback on model performance during training.
