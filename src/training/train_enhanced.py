#!/usr/bin/env python3
"""
Enhanced training script for medical imaging models
Supports UNETR, UNet, cascade detection, MONAI Label integration, and MLflow tracking
"""

import argparse
import json
import logging
import os
import sys
import warnings
from pathlib import Path
from typing import Any, Dict

import torch
import torch.nn as nn
from torch.utils.data import DataLoader

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

try:
    # MONAI imports
    from monai.engines import SupervisedEvaluator, SupervisedTrainer
    from monai.handlers import (CheckpointSaver, LrScheduleHandler,
                                StatsHandler, TensorBoardHandler,
                                ValidationHandler, from_engine)
    from monai.losses import DiceFocalLoss, DiceLoss, FocalLoss
    from monai.metrics import DiceMetric, HausdorffDistanceMetric
    from monai.networks.nets import UNETR, UNet
    from monai.optimizers import Novograd
    from monai.transforms import AsDiscrete, Compose
    from monai.utils import set_determinism
    MONAI_AVAILABLE = True
except ImportError:
    MONAI_AVAILABLE = False
    warnings.warn("MONAI not available. Please install with: pip install monai")

# Import our custom modules
try:
    from src.data.preprocess import (EnhancedDataPreprocessing,
                                     create_sample_datasets)
    from src.fusion.attention_fusion import create_multi_modal_model
    from src.models.cascade_detector import create_cascade_pipeline
    from src.utils.logging_mlflow import setup_mlflow_tracking
except ImportError as e:
    print(f"Could not import custom modules: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnhancedTrainer:
    """
    Enhanced trainer with support for multiple architectures and advanced features
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.device = self._setup_device()
        self.mlflow_logger = None

        # Set deterministic behavior
        if config.get("environment", {}).get("deterministic", True):
            seed = config.get("environment", {}).get("seed", 42)
            set_determinism(seed=seed)
            torch.manual_seed(seed)

        # Setup MLflow tracking
        if config.get("logging", {}).get("backend") == "mlflow":
            self.mlflow_logger = setup_mlflow_tracking(
                experiment_name=config["logging"]["experiment_name"],
                tracking_uri=config["logging"].get("tracking_uri")
            )

    def _setup_device(self) -> torch.device:
        """Setup training device"""
        device_config = self.config.get("environment", {}).get("device", "auto")

        if device_config == "auto":
            if torch.cuda.is_available():
                device = torch.device("cuda")
                logger.info(f"Using CUDA device: {torch.cuda.get_device_name(0)}")
            else:
                device = torch.device("cpu")
                logger.info("Using CPU device")
        else:
            device = torch.device(device_config)

        return device

    def _create_model(self) -> nn.Module:
        """Create model based on configuration"""
        model_config = self.config["model"]
        task = self.config["training"]["task"]

        if task == "segmentation":
            if model_config["architecture"] == "unetr":
                model = create_multi_modal_model(
                    model_type="unetr",
                    fusion_mode=model_config.get("fusion_mode", "early"),
                    config=model_config
                )
            elif model_config["architecture"] == "unet":
                model = UNet(
                    spatial_dims=3,
                    in_channels=model_config["in_channels"],
                    out_channels=model_config["out_channels"],
                    channels=(16, 32, 64, 128, 256),
                    strides=(2, 2, 2, 2),
                    num_res_units=2,
                    dropout=model_config.get("dropout_rate", 0.1),
                )
            else:
                raise ValueError(f"Unknown architecture: {model_config['architecture']}")

        elif task == "cascade":
            model = create_cascade_pipeline(model_config)

        else:
            raise ValueError(f"Unknown task: {task}")

        return model.to(self.device)

    def _create_loss_function(self) -> nn.Module:
        """Create loss function based on configuration"""
        loss_config = self.config["loss"]
        task = self.config["training"]["task"]

        if task == "segmentation":
            seg_loss_config = loss_config["segmentation"]

            if seg_loss_config["type"] == "combined":
                components = seg_loss_config["components"]
                losses = []
                weights = []

                for loss_name, loss_params in components.items():
                    weight = loss_params["weight"]
                    params = loss_params["params"]

                    if loss_name == "dice":
                        loss_fn = DiceLoss(**params)
                    elif loss_name == "focal":
                        loss_fn = FocalLoss(**params)
                    else:
                        continue

                    losses.append(loss_fn)
                    weights.append(weight)

                # Create combined loss
                def combined_loss(pred, target):
                    total_loss = 0
                    for loss_fn, weight in zip(losses, weights):
                        total_loss += weight * loss_fn(pred, target)
                    return total_loss

                return combined_loss

            elif seg_loss_config["type"] == "dice_focal":
                return DiceFocalLoss(
                    sigmoid=True,
                    focal_weight=seg_loss_config.get("focal_weight", 1.0),
                    ce_weight=seg_loss_config.get("ce_weight", 1.0)
                )

        return DiceLoss(sigmoid=True)

    def _create_optimizer(self, model: nn.Module):
        """Create optimizer based on configuration"""
        training_config = self.config["training"]

        optimizer_name = training_config.get("optimizer", "adamw").lower()
        lr = training_config["learning_rate"]
        weight_decay = training_config.get("weight_decay", 1e-5)

        if optimizer_name == "adamw":
            return torch.optim.AdamW(
                model.parameters(),
                lr=lr,
                weight_decay=weight_decay
            )
        elif optimizer_name == "adam":
            return torch.optim.Adam(
                model.parameters(),
                lr=lr,
                weight_decay=weight_decay
            )
        elif optimizer_name == "sgd":
            return torch.optim.SGD(
                model.parameters(),
                lr=lr,
                weight_decay=weight_decay,
                momentum=0.9
            )
        elif optimizer_name == "novograd":
            return Novograd(
                model.parameters(),
                lr=lr,
                weight_decay=weight_decay
            )
        else:
            raise ValueError(f"Unknown optimizer: {optimizer_name}")

    def _create_scheduler(self, optimizer):
        """Create learning rate scheduler"""
        training_config = self.config["training"]
        scheduler_name = training_config.get("scheduler", "cosine_annealing")

        if scheduler_name == "cosine_annealing":
            params = training_config.get("scheduler_params", {})
            return torch.optim.lr_scheduler.CosineAnnealingLR(
                optimizer,
                T_max=params.get("T_max", training_config["max_epochs"]),
                eta_min=params.get("eta_min", 1e-6)
            )
        elif scheduler_name == "step":
            params = training_config.get("scheduler_params", {})
            return torch.optim.lr_scheduler.StepLR(
                optimizer,
                step_size=params.get("step_size", 30),
                gamma=params.get("gamma", 0.1)
            )
        else:
            return None

    def _create_datasets(self):
        """Create training and validation datasets"""
        data_config = self.config["data"]

        # Initialize preprocessing
        preprocessor = EnhancedDataPreprocessing(data_config)

        # Create sample datasets for demonstration
        # In practice, you would load your actual dataset here
        datasets = create_sample_datasets("./data/samples")

        # Create transforms
        train_transforms = preprocessor.get_training_transforms()
        val_transforms = preprocessor.get_validation_transforms()

        # Create datasets with caching
        train_dataset = preprocessor.create_dataset(
            datasets["train"],
            train_transforms,
            cache_mode=data_config.get("cache_mode", "persistent"),
            num_workers=self.config["training"].get("num_workers", 4)
        )

        val_dataset = preprocessor.create_dataset(
            datasets["val"],
            val_transforms,
            cache_mode="none",  # Don't cache validation data
        )

        return train_dataset, val_dataset

    def _create_data_loaders(self, train_dataset, val_dataset):
        """Create data loaders"""
        training_config = self.config["training"]

        train_loader = DataLoader(
            train_dataset,
            batch_size=training_config["batch_size"],
            shuffle=True,
            num_workers=training_config.get("num_workers", 4),
            pin_memory=training_config.get("pin_memory", True),
            persistent_workers=training_config.get("persistent_workers", True)
        )

        val_loader = DataLoader(
            val_dataset,
            batch_size=training_config["batch_size"],
            shuffle=False,
            num_workers=training_config.get("num_workers", 4),
            pin_memory=training_config.get("pin_memory", True)
        )

        return train_loader, val_loader

    def train(self):
        """Main training loop"""
        logger.info("Starting enhanced training...")

        # Start MLflow run
        if self.mlflow_logger:
            self.mlflow_logger.start_run()
            self.mlflow_logger.log_training_config(
                self.config["model"],
                self.config["training"],
                {"optimizer": self.config["training"].get("optimizer", "adamw")}
            )
            self.mlflow_logger.log_system_info()

        try:
            # Create model, loss, optimizer
            model = self._create_model()
            loss_function = self._create_loss_function()
            optimizer = self._create_optimizer(model)
            scheduler = self._create_scheduler(optimizer)

            # Log model if MLflow is available
            if self.mlflow_logger:
                # Create dummy input for model logging
                dummy_input = torch.randn(
                    1,
                    self.config["model"]["in_channels"],
                    *self.config["data"]["patch_size"]
                ).to(self.device)

                self.mlflow_logger.log_model(
                    model,
                    input_example=dummy_input.cpu()
                )

            # Create datasets and loaders
            train_dataset, val_dataset = self._create_datasets()
            train_loader, val_loader = self._create_data_loaders(train_dataset, val_dataset)

            if self.mlflow_logger:
                self.mlflow_logger.log_dataset_info(
                    self.config["data"],
                    train_size=len(train_dataset),
                    val_size=len(val_dataset)
                )

            # Setup metrics
            train_metrics = {
                "dice": DiceMetric(include_background=False, reduction="mean")
            }
            val_metrics = {
                "dice": DiceMetric(include_background=False, reduction="mean"),
                "hd95": HausdorffDistanceMetric(
                    include_background=False,
                    reduction="mean",
                    percentile=95
                )
            }

            # Training loop
            max_epochs = self.config["training"]["max_epochs"]
            best_metric = -1

            for epoch in range(max_epochs):
                logger.info(f"Epoch {epoch + 1}/{max_epochs}")

                # Training phase
                model.train()
                train_loss = 0.0

                for batch_idx, batch_data in enumerate(train_loader):
                    inputs = batch_data["image"].to(self.device)
                    targets = batch_data["label"].to(self.device)

                    optimizer.zero_grad()

                    # Forward pass
                    if self.config["training"].get("amp", False):
                        with torch.cuda.amp.autocast():
                            outputs = model(inputs)
                            loss = loss_function(outputs, targets)
                    else:
                        outputs = model(inputs)
                        loss = loss_function(outputs, targets)

                    # Backward pass
                    loss.backward()
                    optimizer.step()

                    train_loss += loss.item()

                    # Log batch metrics
                    if batch_idx % 10 == 0:
                        logger.info(f"  Batch {batch_idx}, Loss: {loss.item():.4f}")

                # Validation phase
                model.eval()
                val_loss = 0.0

                with torch.no_grad():
                    for batch_data in val_loader:
                        inputs = batch_data["image"].to(self.device)
                        targets = batch_data["label"].to(self.device)

                        outputs = model(inputs)
                        loss = loss_function(outputs, targets)
                        val_loss += loss.item()

                        # Calculate metrics
                        outputs_discrete = torch.argmax(outputs, dim=1, keepdim=True)
                        for metric_name, metric_fn in val_metrics.items():
                            metric_fn(outputs_discrete, targets)

                # Aggregate metrics
                val_metrics_values = {}
                for metric_name, metric_fn in val_metrics.items():
                    val_metrics_values[f"val_{metric_name}"] = metric_fn.aggregate().item()
                    metric_fn.reset()

                # Log metrics
                epoch_metrics = {
                    "train_loss": train_loss / len(train_loader),
                    "val_loss": val_loss / len(val_loader),
                    **val_metrics_values
                }

                if self.mlflow_logger:
                    self.mlflow_logger.log_metrics(epoch_metrics, epoch=epoch)

                logger.info(f"  Metrics: {epoch_metrics}")

                # Update learning rate
                if scheduler:
                    scheduler.step()
                    if self.mlflow_logger:
                        self.mlflow_logger.log_metrics(
                            {"learning_rate": optimizer.param_groups[0]["lr"]},
                            epoch=epoch
                        )

                # Save best model
                current_metric = val_metrics_values.get("val_dice", 0)
                if current_metric > best_metric:
                    best_metric = current_metric
                    torch.save(
                        model.state_dict(),
                        os.path.join("./models", "best_model.pth")
                    )
                    logger.info(f"  New best model saved (Dice: {best_metric:.4f})")

            logger.info("Training completed successfully!")

        except Exception as e:
            logger.error(f"Training failed: {e}")
            raise
        finally:
            if self.mlflow_logger:
                self.mlflow_logger.end_run()


def main():
    parser = argparse.ArgumentParser(description="Enhanced Medical Imaging Training")
    parser.add_argument(
        "--config",
        type=str,
        required=True,
        help="Path to configuration file"
    )
    parser.add_argument(
        "--resume",
        type=str,
        help="Path to checkpoint to resume from"
    )

    args = parser.parse_args()

    # Load configuration
    with open(args.config, 'r') as f:
        config = json.load(f)

    # Create output directories
    os.makedirs("./models", exist_ok=True)
    os.makedirs("./logs", exist_ok=True)

    # Initialize and run trainer
    trainer = EnhancedTrainer(config)
    trainer.train()


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
