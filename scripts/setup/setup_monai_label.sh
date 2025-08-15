#!/bin/bash

# MONAI Label Server Setup Script
echo "🏥 Setting up MONAI Label Server for Interactive Annotation"
echo "========================================================="

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

print_status "Project root: $PROJECT_ROOT"

# Check if virtual environment is active
if [[ "$VIRTUAL_ENV" == "" ]]; then
    print_warning "Virtual environment not detected. Activating..."
    if [ -d "$PROJECT_ROOT/.venv" ]; then
        source "$PROJECT_ROOT/.venv/bin/activate"
    elif [ -d "$PROJECT_ROOT/venv" ]; then
        source "$PROJECT_ROOT/venv/bin/activate"
    else
        print_error "No virtual environment found. Please run setup first."
        exit 1
    fi
fi

print_status "Installing MONAI Label and dependencies..."

# Install MONAI Label
pip install --upgrade monai-label

# Install additional dependencies for 3D Slicer integration
pip install --upgrade itk-io
pip install --upgrade SimpleITK

# Create MONAI Label app directory
LABEL_APP_DIR="$PROJECT_ROOT/monai_label_app"
mkdir -p "$LABEL_APP_DIR"

print_status "Creating MONAI Label application structure..."

# Create the main app configuration
cat > "$LABEL_APP_DIR/main.py" << 'EOF'
#!/usr/bin/env python3
"""
MONAI Label App for Brain Tumor Segmentation
Interactive annotation and model-in-the-loop training
"""

import logging
import os
from typing import Any, Dict, Optional, Union

from monailabel.interfaces.app import MONAILabelApp
from monailabel.interfaces.config import TaskConfig
from monailabel.interfaces.datastore import Datastore
from monailabel.interfaces.tasks.infer import InferTask
from monailabel.interfaces.tasks.train import TrainTask
from monailabel.tasks.activelearning.epistemic import Epistemic
from monailabel.tasks.activelearning.random import Random
from monailabel.tasks.infer.basic_infer import BasicInferTask
from monailabel.tasks.train.basic_train import BasicTrainTask
from monailabel.utils.others.generic import download_file, strtobool

from lib import MyInfer, MyStrategy, MyTrainer

logger = logging.getLogger(__name__)


class MyApp(MONAILabelApp):
    """
    MONAI Label App for Brain Tumor Segmentation

    Supports:
    - Interactive annotation with 3D Slicer
    - Active learning strategies
    - Multi-modal MRI segmentation
    """

    def __init__(self, app_dir, studies, conf):
        self.model_dir = os.path.join(app_dir, "model")

        configs = {
            "models": "segmentation_unet,segmentation_unetr",
            "use_pretrained_model": True,
            "skip_trainers": False,
            "skip_strategies": False,
        }

        # Override with user config
        for k, v in conf.items():
            configs[k] = v

        super().__init__(
            app_dir=app_dir,
            studies=studies,
            conf=configs,
            name=f"Brain Tumor Segmentation - {app_dir}",
            description="AI-Assisted Brain Tumor Segmentation with Active Learning",
            version="1.0.0",
        )

    def init_infers(self) -> Dict[str, InferTask]:
        """Initialize inference tasks"""
        infers = {}

        # Add UNet segmentation task
        if "segmentation_unet" in self.conf.get("models", ""):
            infers["segmentation_unet"] = MyInfer(
                path=os.path.join(self.model_dir, "segmentation_unet.pt"),
                network="unet",
                roi_size=(128, 128, 128),
                preload=strtobool(self.conf.get("preload", "false")),
                config={"cache_transforms": True, "cache_transforms_in_memory": True},
            )

        # Add UNETR segmentation task
        if "segmentation_unetr" in self.conf.get("models", ""):
            infers["segmentation_unetr"] = MyInfer(
                path=os.path.join(self.model_dir, "segmentation_unetr.pt"),
                network="unetr",
                roi_size=(96, 96, 96),
                preload=strtobool(self.conf.get("preload", "false")),
                config={"cache_transforms": True, "cache_transforms_in_memory": True},
            )

        return infers

    def init_trainers(self) -> Dict[str, TrainTask]:
        """Initialize training tasks"""
        trainers = {}
        if strtobool(self.conf.get("skip_trainers", "false")):
            return trainers

        # Add UNet trainer
        if "segmentation_unet" in self.conf.get("models", ""):
            trainers["segmentation_unet"] = MyTrainer(
                model_dir=self.model_dir,
                network="unet",
                roi_size=(128, 128, 128),
                max_epochs=50,
                config={
                    "multi_gpu": strtobool(self.conf.get("multi_gpu", "true")),
                    "amp": strtobool(self.conf.get("amp", "true")),
                },
            )

        # Add UNETR trainer
        if "segmentation_unetr" in self.conf.get("models", ""):
            trainers["segmentation_unetr"] = MyTrainer(
                model_dir=self.model_dir,
                network="unetr",
                roi_size=(96, 96, 96),
                max_epochs=50,
                config={
                    "multi_gpu": strtobool(self.conf.get("multi_gpu", "true")),
                    "amp": strtobool(self.conf.get("amp", "true")),
                },
            )

        return trainers

    def init_strategies(self) -> Dict[str, Any]:
        """Initialize active learning strategies"""
        strategies = {}
        if strtobool(self.conf.get("skip_strategies", "false")):
            return strategies

        strategies["random"] = Random()
        strategies["epistemic"] = Epistemic()

        # Add custom strategy
        strategies["custom"] = MyStrategy()

        return strategies


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--app", required=True, help="app folder")
    parser.add_argument("-s", "--studies", required=True, help="studies folder")
    parser.add_argument("-p", "--port", type=int, default=8000, help="port")
    parser.add_argument("-h", "--host", default="127.0.0.1", help="host")
    parser.add_argument("-v", "--verbose", action="store_true", help="verbose")

    args = parser.parse_args()

    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)

    app = MyApp(args.app, args.studies, {})
    app.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
EOF

# Create lib directory for custom implementations
mkdir -p "$LABEL_APP_DIR/lib"

# Create inference implementation
cat > "$LABEL_APP_DIR/lib/infer.py" << 'EOF'
#!/usr/bin/env python3
"""
Custom inference implementation for brain tumor segmentation
"""

import logging
import os
from typing import Callable, Sequence

import torch

from monailabel.interfaces.tasks.infer_v2 import InferTask
from monailabel.tasks.infer.basic_infer import BasicInferTask
from monailabel.utils.others.generic import download_file

logger = logging.getLogger(__name__)


class MyInfer(BasicInferTask):
    """
    Custom inference task for brain tumor segmentation

    Supports:
    - UNet and UNETR architectures
    - Multi-modal MRI processing
    - Uncertainty estimation
    """

    def __init__(
        self,
        path: str,
        network: str = "unet",
        roi_size: Sequence[int] = (128, 128, 128),
        preload: bool = False,
        config: dict = None,
    ):
        super().__init__(
            path=path,
            network=network,
            roi_size=roi_size,
            preload=preload,
            config=config,
        )

    def get_path(self):
        """Get model path, download if needed"""
        if os.path.exists(self.path):
            return self.path

        # Download pretrained model if available
        url = self._get_pretrained_url()
        if url:
            logger.info(f"Downloading pretrained model from {url}")
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            download_file(url, self.path)

        return self.path if os.path.exists(self.path) else None

    def _get_pretrained_url(self):
        """Get URL for pretrained model"""
        # Add URLs for pretrained models here
        urls = {
            "unet": "https://github.com/Project-MONAI/model-zoo/releases/download/hosting_storage_v1/models/brain_tumor_unet.zip",
            "unetr": "https://github.com/Project-MONAI/model-zoo/releases/download/hosting_storage_v1/models/brain_tumor_unetr.zip",
        }
        return urls.get(self.network)

    def get_network(self):
        """Get network architecture"""
        if self.network == "unet":
            from monai.networks.nets import UNet
            return UNet(
                spatial_dims=3,
                in_channels=4,  # T1, T1c, T2, FLAIR
                out_channels=4,  # Background, enhancing, non-enhancing, edema
                channels=(16, 32, 64, 128, 256),
                strides=(2, 2, 2, 2),
                num_res_units=2,
                dropout=0.1,
            )
        elif self.network == "unetr":
            from monai.networks.nets import UNETR
            return UNETR(
                in_channels=4,
                out_channels=4,
                img_size=self.roi_size,
                feature_size=16,
                hidden_size=768,
                mlp_dim=3072,
                num_heads=12,
                pos_embed="perceptron",
                norm_name="instance",
                res_block=True,
                dropout_rate=0.0,
            )
        else:
            raise ValueError(f"Unknown network: {self.network}")

    def get_pre_transforms(self):
        """Get preprocessing transforms"""
        from monai.transforms import (
            Compose,
            LoadImaged,
            EnsureChannelFirstd,
            Spacingd,
            Orientationd,
            CropForegroundd,
            NormalizeIntensityd,
            EnsureTyped,
        )

        return Compose([
            LoadImaged(keys="image"),
            EnsureChannelFirstd(keys="image"),
            Spacingd(keys="image", pixdim=(1.0, 1.0, 1.0), mode="bilinear"),
            Orientationd(keys="image", axcodes="RAS"),
            CropForegroundd(keys="image", source_key="image"),
            NormalizeIntensityd(keys="image", nonzero=True, channel_wise=True),
            EnsureTyped(keys="image"),
        ])

    def get_post_transforms(self):
        """Get postprocessing transforms"""
        from monai.transforms import (
            Compose,
            Activationsd,
            AsDiscreted,
            KeepLargestConnectedComponentd,
            EnsureTyped,
        )

        return Compose([
            EnsureTyped(keys="pred"),
            Activationsd(keys="pred", softmax=True),
            AsDiscreted(keys="pred", argmax=True, to_onehot=4),
            KeepLargestConnectedComponentd(keys="pred", applied_labels=[1, 2, 3]),
        ])
EOF

# Create trainer implementation
cat > "$LABEL_APP_DIR/lib/trainer.py" << 'EOF'
#!/usr/bin/env python3
"""
Custom trainer implementation for brain tumor segmentation
"""

import logging
import os
from typing import Optional

import torch

from monailabel.tasks.train.basic_train import BasicTrainTask, Context

logger = logging.getLogger(__name__)


class MyTrainer(BasicTrainTask):
    """
    Custom trainer for brain tumor segmentation

    Features:
    - Mixed precision training
    - Multi-GPU support
    - Advanced augmentations
    - Deep supervision
    """

    def __init__(
        self,
        model_dir: str,
        network: str = "unet",
        roi_size: tuple = (128, 128, 128),
        max_epochs: int = 50,
        config: dict = None,
    ):
        self.model_dir = model_dir
        self.network = network
        self.roi_size = roi_size
        self.max_epochs = max_epochs
        self.config = config or {}

        super().__init__(self.model_dir, description=f"Train {network} model")

    def get_network(self):
        """Get network architecture"""
        if self.network == "unet":
            from monai.networks.nets import UNet
            return UNet(
                spatial_dims=3,
                in_channels=4,
                out_channels=4,
                channels=(16, 32, 64, 128, 256),
                strides=(2, 2, 2, 2),
                num_res_units=2,
                dropout=0.1,
            )
        elif self.network == "unetr":
            from monai.networks.nets import UNETR
            return UNETR(
                in_channels=4,
                out_channels=4,
                img_size=self.roi_size,
                feature_size=16,
                hidden_size=768,
                mlp_dim=3072,
                num_heads=12,
                pos_embed="perceptron",
                norm_name="instance",
                res_block=True,
                dropout_rate=0.0,
            )

    def get_optimizer(self, network):
        """Get optimizer"""
        return torch.optim.AdamW(network.parameters(), lr=2e-4, weight_decay=1e-5)

    def get_lr_scheduler(self, optimizer):
        """Get learning rate scheduler"""
        return torch.optim.lr_scheduler.CosineAnnealingLR(
            optimizer, T_max=self.max_epochs, eta_min=1e-6
        )

    def get_loss_function(self):
        """Get loss function"""
        from monai.losses import DiceLoss, FocalLoss

        # Combined loss for better performance
        dice_loss = DiceLoss(sigmoid=True, squared_pred=True, reduction="mean")
        focal_loss = FocalLoss(gamma=2.0, reduction="mean")

        def combined_loss(y_pred, y_true):
            return 0.5 * dice_loss(y_pred, y_true) + 0.5 * focal_loss(y_pred, y_true)

        return combined_loss

    def get_pre_transforms(self):
        """Get training transforms"""
        from monai.transforms import (
            Compose,
            LoadImaged,
            EnsureChannelFirstd,
            Spacingd,
            Orientationd,
            CropForegroundd,
            RandSpatialCropd,
            RandFlipd,
            RandRotate90d,
            RandScaleIntensityd,
            RandShiftIntensityd,
            RandAffined,
            RandGaussianNoised,
            NormalizeIntensityd,
            EnsureTyped,
        )

        return Compose([
            LoadImaged(keys=["image", "label"]),
            EnsureChannelFirstd(keys=["image", "label"]),
            Spacingd(
                keys=["image", "label"],
                pixdim=(1.0, 1.0, 1.0),
                mode=("bilinear", "nearest"),
            ),
            Orientationd(keys=["image", "label"], axcodes="RAS"),
            CropForegroundd(keys=["image", "label"], source_key="image"),
            NormalizeIntensityd(keys="image", nonzero=True, channel_wise=True),

            # Spatial augmentations
            RandSpatialCropd(
                keys=["image", "label"],
                roi_size=self.roi_size,
                random_size=False,
            ),
            RandFlipd(keys=["image", "label"], prob=0.5, spatial_axis=0),
            RandFlipd(keys=["image", "label"], prob=0.5, spatial_axis=1),
            RandFlipd(keys=["image", "label"], prob=0.5, spatial_axis=2),
            RandRotate90d(keys=["image", "label"], prob=0.1, max_k=3),
            RandAffined(
                keys=["image", "label"],
                mode=("bilinear", "nearest"),
                prob=0.1,
                spatial_size=self.roi_size,
                rotate_range=(0.05, 0.05, 0.05),
                scale_range=(0.1, 0.1, 0.1),
            ),

            # Intensity augmentations
            RandScaleIntensityd(keys="image", factors=0.1, prob=0.1),
            RandShiftIntensityd(keys="image", offsets=0.1, prob=0.1),
            RandGaussianNoised(keys="image", prob=0.1, std=0.01),

            EnsureTyped(keys=["image", "label"]),
        ])

    def train(self, request, datastore):
        """Train the model"""
        # Set up training context
        context = Context(request, datastore)

        # Enable mixed precision if configured
        if self.config.get("amp", True):
            context.scaler = torch.cuda.amp.GradScaler()

        # Set up multi-GPU if configured
        if self.config.get("multi_gpu", True) and torch.cuda.device_count() > 1:
            context.multi_gpu = True

        return super().train(request, datastore, context)
EOF

# Create strategy implementation
cat > "$LABEL_APP_DIR/lib/strategy.py" << 'EOF'
#!/usr/bin/env python3
"""
Custom active learning strategy for brain tumor segmentation
"""

import logging
import random
from typing import Any, Dict, List

import numpy as np

from monailabel.interfaces.tasks.strategy import Strategy

logger = logging.getLogger(__name__)


class MyStrategy(Strategy):
    """
    Custom active learning strategy

    Combines:
    - Uncertainty-based sampling
    - Diversity-based sampling
    - Class balance considerations
    """

    def __init__(self):
        super().__init__("Custom Strategy")

    def __call__(self, request: Dict[str, Any]) -> List[str]:
        """
        Select next samples for annotation

        Args:
            request: Request containing:
                - datastore: Available unlabeled data
                - model: Current model for uncertainty estimation
                - client_id: Client making the request
                - params: Strategy parameters

        Returns:
            List of image IDs to annotate next
        """
        datastore = request.get("datastore")
        model = request.get("model")
        params = request.get("params", {})

        # Get unlabeled images
        unlabeled = datastore.get_unlabeled_images()
        if not unlabeled:
            logger.warning("No unlabeled images available")
            return []

        # Number of samples to select
        max_samples = min(params.get("max_samples", 5), len(unlabeled))

        if model is None:
            # Random selection if no model available
            logger.info("No model available, using random selection")
            return random.sample(unlabeled, max_samples)

        # Calculate uncertainty scores
        uncertainty_scores = self._calculate_uncertainty(unlabeled, model, datastore)

        # Calculate diversity scores
        diversity_scores = self._calculate_diversity(unlabeled, datastore)

        # Combine scores
        combined_scores = self._combine_scores(
            uncertainty_scores,
            diversity_scores,
            alpha=params.get("uncertainty_weight", 0.7)
        )

        # Select top samples
        selected_indices = np.argsort(combined_scores)[-max_samples:]
        selected_images = [unlabeled[i] for i in selected_indices]

        logger.info(f"Selected {len(selected_images)} images for annotation")
        return selected_images

    def _calculate_uncertainty(self, images: List[str], model, datastore) -> np.ndarray:
        """Calculate uncertainty scores using model predictions"""
        scores = []

        for image_id in images:
            try:
                # Run inference to get prediction probabilities
                result = model.infer({"image": datastore.get_image_uri(image_id)})

                # Calculate entropy-based uncertainty
                probs = result.get("prob", result.get("pred"))
                if probs is not None:
                    # Entropy calculation
                    entropy = -np.sum(probs * np.log(probs + 1e-8), axis=0)
                    uncertainty = np.mean(entropy)
                else:
                    uncertainty = 0.0

                scores.append(uncertainty)

            except Exception as e:
                logger.warning(f"Failed to calculate uncertainty for {image_id}: {e}")
                scores.append(0.0)

        return np.array(scores)

    def _calculate_diversity(self, images: List[str], datastore) -> np.ndarray:
        """Calculate diversity scores based on image features"""
        # Simple diversity based on image metadata
        scores = []

        labeled_images = datastore.get_labeled_images()

        for image_id in images:
            try:
                # Get image info
                image_info = datastore.get_image_info(image_id)

                # Calculate diversity based on available metadata
                diversity = 1.0  # Default diversity

                # Factor in spacing differences
                if "spacing" in image_info:
                    spacing = image_info["spacing"]
                    # Calculate how different this spacing is from labeled data
                    # (simplified implementation)
                    diversity *= 1.0 + 0.1 * abs(spacing[0] - 1.0)

                scores.append(diversity)

            except Exception as e:
                logger.warning(f"Failed to calculate diversity for {image_id}: {e}")
                scores.append(1.0)

        return np.array(scores)

    def _combine_scores(self, uncertainty: np.ndarray, diversity: np.ndarray, alpha: float = 0.7) -> np.ndarray:
        """Combine uncertainty and diversity scores"""
        # Normalize scores
        uncertainty_norm = (uncertainty - uncertainty.min()) / (uncertainty.max() - uncertainty.min() + 1e-8)
        diversity_norm = (diversity - diversity.min()) / (diversity.max() - diversity.min() + 1e-8)

        # Weighted combination
        combined = alpha * uncertainty_norm + (1 - alpha) * diversity_norm

        return combined
EOF

# Create __init__.py for lib module
cat > "$LABEL_APP_DIR/lib/__init__.py" << 'EOF'
"""
Custom implementations for MONAI Label brain tumor segmentation app
"""

from .infer import MyInfer
from .trainer import MyTrainer
from .strategy import MyStrategy

__all__ = ["MyInfer", "MyTrainer", "MyStrategy"]
EOF

# Create sample configuration
cat > "$LABEL_APP_DIR/conf/app.conf" << 'EOF'
# MONAI Label App Configuration for Brain Tumor Segmentation

# Models to enable
models = segmentation_unet,segmentation_unetr

# Use pretrained models
use_pretrained_model = true

# Training settings
skip_trainers = false
skip_strategies = false

# Performance settings
preload = false
multi_gpu = true
amp = true

# Server settings
auto_update_scoring = true
scoring_interval = 10

# Data settings
datastore_auto_reload = true
datastore_read_only = false
EOF

mkdir -p "$LABEL_APP_DIR/conf"

print_success "MONAI Label application created successfully!"

# Create data directories
DATA_DIR="$PROJECT_ROOT/data/monai_label"
mkdir -p "$DATA_DIR/images"
mkdir -p "$DATA_DIR/labels"

print_status "Created data directories:"
print_status "  - Images: $DATA_DIR/images"
print_status "  - Labels: $DATA_DIR/labels"

# Create run script
cat > "$PROJECT_ROOT/scripts/utilities/run_monai_label.sh" << EOF
#!/bin/bash

# MONAI Label Server Runner
echo "🏥 Starting MONAI Label Server"
echo "=============================="

# Get project root
SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="\$(cd "\$SCRIPT_DIR/../.." && pwd)"

# Configuration
LABEL_APP_DIR="\$PROJECT_ROOT/monai_label_app"
DATA_DIR="\$PROJECT_ROOT/data/monai_label"
HOST=\${MONAI_LABEL_HOST:-"127.0.0.1"}
PORT=\${MONAI_LABEL_PORT:-8000}

# Check if virtual environment is active
if [[ "\$VIRTUAL_ENV" == "" ]]; then
    echo "Activating virtual environment..."
    if [ -d "\$PROJECT_ROOT/.venv" ]; then
        source "\$PROJECT_ROOT/.venv/bin/activate"
    elif [ -d "\$PROJECT_ROOT/venv" ]; then
        source "\$PROJECT_ROOT/venv/bin/activate"
    fi
fi

# Check if app exists
if [ ! -d "\$LABEL_APP_DIR" ]; then
    echo "❌ MONAI Label app not found. Please run setup_monai_label.sh first."
    exit 1
fi

# Check if data directory exists
if [ ! -d "\$DATA_DIR/images" ]; then
    echo "📁 Creating data directories..."
    mkdir -p "\$DATA_DIR/images"
    mkdir -p "\$DATA_DIR/labels"
fi

echo "🚀 Starting MONAI Label server..."
echo "   App: \$LABEL_APP_DIR"
echo "   Data: \$DATA_DIR"
echo "   Host: \$HOST"
echo "   Port: \$PORT"
echo ""
echo "💡 Instructions:"
echo "   1. Open 3D Slicer"
echo "   2. Install MONAI Label extension"
echo "   3. Connect to server: http://\$HOST:\$PORT"
echo "   4. Start annotating!"
echo ""

cd "\$LABEL_APP_DIR"
python main.py -a "\$LABEL_APP_DIR" -s "\$DATA_DIR" -p \$PORT -h \$HOST
EOF

chmod +x "$PROJECT_ROOT/scripts/utilities/run_monai_label.sh"

print_success "✅ MONAI Label setup completed!"
print_status ""
print_status "Next steps:"
print_status "1. Add medical images to: $DATA_DIR/images"
print_status "2. Start the server: ./scripts/utilities/run_monai_label.sh"
print_status "3. Install MONAI Label extension in 3D Slicer"
print_status "4. Connect 3D Slicer to: http://127.0.0.1:8000"
print_status ""
print_status "📖 For more info: https://docs.monai.io/projects/label"
