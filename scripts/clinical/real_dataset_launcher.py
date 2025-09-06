#!/usr/bin/env python3
"""
Real Dataset Training Launcher
=============================

Production launcher for training with real medical datasets including
MSD (Medical Segmentation Decathlon) and BraTS datasets.

Author: Tumor Detection Segmentation Team
Phase: Clinical Production
"""

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'real_training_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class RealDatasetTrainingLauncher:
    """Production training launcher for real medical datasets"""

    def __init__(self):
        self.start_time = datetime.now()

        # Dataset configurations
        self.dataset_configs = {
            'msd_brain': {
                'name': 'MSD Task01 BrainTumour',
                'download_url': 'https://msd-for-monai.s3-us-west-2.amazonaws.com/Task01_BrainTumour.tar',
                'config_file': 'config/datasets/msd_task01_brain.json',
                'modalities': ['T1', 'T1c', 'T2', 'FLAIR'],
                'num_classes': 4,
                'description': 'Multi-modal brain tumor segmentation'
            },
            'brats2021': {
                'name': 'BraTS 2021 Challenge',
                'download_url': 'https://www.med.upenn.edu/cbica/brats2021/',
                'config_file': 'config/datasets/brats2021.json',
                'modalities': ['T1', 'T1c', 'T2', 'FLAIR'],
                'num_classes': 4,
                'description': 'BraTS 2021 brain tumor segmentation'
            },
            'custom': {
                'name': 'Custom Dataset',
                'config_file': 'config/datasets/custom.json',
                'description': 'User-provided medical imaging dataset'
            }
        }

        # Model configurations
        self.model_configs = {
            'multimodal_unetr': 'config/recipes/multimodal_unetr.json',
            'dints_nas': 'config/recipes/dints_nas.json',
            'cascade_detector': 'config/recipes/cascade_detector.json',
            'retina_unet3d': 'config/recipes/retina_unet3d.json'
        }

    def check_dependencies(self) -> bool:
        """Check if required dependencies are available"""
        logger.info("🔍 Checking dependencies...")

        required_deps = ['torch', 'monai', 'numpy', 'nibabel']
        missing_deps = []

        for dep in required_deps:
            try:
                __import__(dep)
                logger.info(f"✅ {dep} available")
            except ImportError:
                missing_deps.append(dep)
                logger.error(f"❌ {dep} missing")

        if missing_deps:
            logger.error(f"Missing dependencies: {missing_deps}")
            logger.info("Install with: pip install torch monai numpy nibabel")
            return False

        return True

    def setup_environment(self) -> bool:
        """Setup training environment"""
        logger.info("🔧 Setting up training environment...")

        # Create necessary directories
        directories = [
            'data/raw',
            'data/processed',
            'data/models',
            'outputs/training',
            'outputs/predictions',
            'outputs/visualizations',
            'logs/training',
            'reports/training'
        ]

        for dir_path in directories:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
            logger.info(f"📁 Created directory: {dir_path}")

        # Check for GPU availability
        try:
            import torch
            if torch.cuda.is_available():
                gpu_count = torch.cuda.device_count()
                logger.info(f"🎮 GPU available: {gpu_count} CUDA device(s)")
                for i in range(gpu_count):
                    gpu_name = torch.cuda.get_device_name(i)
                    logger.info(f"  GPU {i}: {gpu_name}")
            else:
                logger.warning("⚠️ No GPU available, training will use CPU")
        except ImportError:
            logger.warning("⚠️ PyTorch not available, cannot check GPU")

        return True

    def download_msd_dataset(self, task: str = 'Task01_BrainTumour') -> bool:
        """Download Medical Segmentation Decathlon dataset"""
        logger.info(f"📥 Downloading MSD {task}...")

        import tarfile
        import urllib.request

        data_dir = Path('data/raw')
        dataset_dir = data_dir / task

        if dataset_dir.exists():
            logger.info(f"✅ Dataset {task} already exists")
            return True

        try:
            # Download dataset
            url = f'https://msd-for-monai.s3-us-west-2.amazonaws.com/{task}.tar'
            tar_path = data_dir / f'{task}.tar'

            logger.info(f"Downloading from: {url}")
            urllib.request.urlretrieve(url, tar_path)

            # Extract dataset
            logger.info("📦 Extracting dataset...")
            with tarfile.open(tar_path, 'r') as tar:
                tar.extractall(data_dir)

            # Clean up tar file
            tar_path.unlink()

            logger.info(f"✅ Dataset {task} downloaded and extracted")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to download dataset: {e}")
            logger.info("💡 You can manually download from: https://msd-for-monai.s3-us-west-2.amazonaws.com/")
            return False

    def create_dataset_config(self, dataset_type: str, dataset_path: str) -> str:
        """Create dataset configuration file"""
        logger.info(f"📝 Creating dataset configuration for {dataset_type}...")

        if dataset_type == 'msd_brain':
            config = {
                "name": "MSD Task01 BrainTumour",
                "description": "Multi-modal brain tumor segmentation from Medical Segmentation Decathlon",
                "task": "segmentation",
                "dimension": 3,
                "modality": {
                    "0": "T1",
                    "1": "T1c",
                    "2": "T2",
                    "3": "FLAIR"
                },
                "labels": {
                    "0": "background",
                    "1": "necrotic_and_non-enhancing_tumor_core",
                    "2": "peritumoral_edema",
                    "3": "GD-enhancing_tumor"
                },
                "numTraining": 484,
                "numTest": 266,
                "image_size": [128, 128, 128],
                "spacing": [1.0, 1.0, 1.0],
                "data_root": dataset_path,
                "training_split": 0.8,
                "validation_split": 0.2,
                "test_split": 0.0,
                "transforms": {
                    "train": [
                        "LoadImaged",
                        "EnsureChannelFirstd",
                        "Orientationd",
                        "Spacingd",
                        "ScaleIntensityRanged",
                        "CropForegroundd",
                        "RandSpatialCropd",
                        "RandFlipd",
                        "RandRotate90d",
                        "RandGaussianNoised",
                        "ToTensord"
                    ],
                    "val": [
                        "LoadImaged",
                        "EnsureChannelFirstd",
                        "Orientationd",
                        "Spacingd",
                        "ScaleIntensityRanged",
                        "CropForegroundd",
                        "ToTensord"
                    ]
                }
            }
        elif dataset_type == 'custom':
            config = {
                "name": "Custom Medical Dataset",
                "description": "User-provided medical imaging dataset",
                "task": "segmentation",
                "dimension": 3,
                "data_root": dataset_path,
                "training_split": 0.7,
                "validation_split": 0.2,
                "test_split": 0.1,
                "transforms": {
                    "train": [
                        "LoadImaged",
                        "EnsureChannelFirstd",
                        "Orientationd",
                        "Spacingd",
                        "ScaleIntensityRanged",
                        "ToTensord"
                    ],
                    "val": [
                        "LoadImaged",
                        "EnsureChannelFirstd",
                        "Orientationd",
                        "Spacingd",
                        "ScaleIntensityRanged",
                        "ToTensord"
                    ]
                }
            }
        else:
            logger.error(f"❌ Unknown dataset type: {dataset_type}")
            return ""

        # Save configuration
        config_path = Path(self.dataset_configs[dataset_type]['config_file'])
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)

        logger.info(f"✅ Dataset configuration saved: {config_path}")
        return str(config_path)

    def launch_training(self, model: str, dataset: str, config_overrides: Dict[str, Any] = None) -> bool:
        """Launch training with specified model and dataset"""
        logger.info(f"🚀 Launching training: {model} on {dataset}")

        # Get model config path
        if model not in self.model_configs:
            logger.error(f"❌ Unknown model: {model}")
            return False

        model_config = self.model_configs[model]

        # Get dataset config path
        if dataset not in self.dataset_configs:
            logger.error(f"❌ Unknown dataset: {dataset}")
            return False

        dataset_config = self.dataset_configs[dataset]['config_file']

        # Check if configs exist
        if not Path(model_config).exists():
            logger.error(f"❌ Model config not found: {model_config}")
            return False

        if not Path(dataset_config).exists():
            logger.error(f"❌ Dataset config not found: {dataset_config}")
            return False

        # Build training command
        cmd = [
            'python', 'src/training/train_enhanced.py',
            '--config', model_config,
            '--dataset-config', dataset_config,
            '--output-dir', f'outputs/training/{model}_{dataset}_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
            '--save-overlays',
            '--save-prob-maps'
        ]

        # Add config overrides
        if config_overrides:
            for key, value in config_overrides.items():
                cmd.extend([f'--{key}', str(value)])

        # Log training command
        logger.info(f"Training command: {' '.join(cmd)}")

        try:
            # Start training process
            logger.info("🎯 Starting training process...")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )

            # Stream output
            for line in process.stdout:
                logger.info(f"TRAINING: {line.strip()}")

            # Wait for completion
            return_code = process.wait()

            if return_code == 0:
                logger.info("✅ Training completed successfully")
                return True
            else:
                logger.error(f"❌ Training failed with return code: {return_code}")
                return False

        except Exception as e:
            logger.error(f"❌ Training failed with error: {e}")
            return False

    def simulate_training_run(self, model: str, dataset: str) -> bool:
        """Simulate training run for demonstration"""
        logger.info(f"🎭 Simulating training: {model} on {dataset}")

        # Training simulation
        import random
        import time

        epochs = 50
        for epoch in range(1, epochs + 1):
            # Simulate training metrics
            train_loss = 1.0 - (epoch * 0.015) + random.uniform(-0.05, 0.05)
            val_loss = train_loss + random.uniform(0.0, 0.1)
            dice_score = min(0.9, epoch * 0.017 + random.uniform(-0.02, 0.02))

            if epoch % 10 == 0:
                logger.info(f"  Epoch {epoch:2d}/{epochs}: Loss={train_loss:.4f}, Val={val_loss:.4f}, Dice={dice_score:.4f}")

            time.sleep(0.1)  # Simulate training time

        # Final results
        final_metrics = {
            'final_dice': 0.847,
            'final_loss': 0.234,
            'best_epoch': 47,
            'training_time_hours': 6.5
        }

        logger.info("✅ Training simulation completed")
        logger.info(f"  Final Dice Score: {final_metrics['final_dice']}")
        logger.info(f"  Training Time: {final_metrics['training_time_hours']} hours")

        return True


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Real Dataset Training Launcher')
    parser.add_argument('--model', default='multimodal_unetr',
                       choices=['multimodal_unetr', 'dints_nas', 'cascade_detector', 'retina_unet3d'],
                       help='Model to train')
    parser.add_argument('--dataset', default='msd_brain',
                       choices=['msd_brain', 'brats2021', 'custom'],
                       help='Dataset to use')
    parser.add_argument('--data-path', type=str,
                       help='Path to dataset (for custom datasets)')
    parser.add_argument('--download', action='store_true',
                       help='Download dataset if not available')
    parser.add_argument('--simulate', action='store_true',
                       help='Run training simulation instead of real training')
    parser.add_argument('--epochs', type=int, default=100,
                       help='Number of training epochs')
    parser.add_argument('--batch-size', type=int, default=2,
                       help='Training batch size')
    parser.add_argument('--learning-rate', type=float, default=1e-4,
                       help='Learning rate')

    args = parser.parse_args()

    logger.info("🏥 Real Dataset Training Launcher")
    logger.info("=" * 50)

    launcher = RealDatasetTrainingLauncher()

    # Check dependencies
    if not args.simulate and not launcher.check_dependencies():
        logger.error("❌ Dependencies check failed")
        return False

    # Setup environment
    if not launcher.setup_environment():
        logger.error("❌ Environment setup failed")
        return False

    # Handle dataset download
    if args.download and args.dataset == 'msd_brain':
        if not launcher.download_msd_dataset():
            logger.error("❌ Dataset download failed")
            return False

    # Create dataset config
    data_path = args.data_path or 'data/raw/Task01_BrainTumour'
    config_path = launcher.create_dataset_config(args.dataset, data_path)

    if not config_path:
        logger.error("❌ Dataset configuration failed")
        return False

    # Launch training
    config_overrides = {
        'epochs': args.epochs,
        'batch-size': args.batch_size,
        'learning-rate': args.learning_rate
    }

    if args.simulate:
        success = launcher.simulate_training_run(args.model, args.dataset)
    else:
        success = launcher.launch_training(args.model, args.dataset, config_overrides)

    if success:
        logger.info("🎉 Training launcher completed successfully!")
        return True
    else:
        logger.error("❌ Training launcher failed")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
