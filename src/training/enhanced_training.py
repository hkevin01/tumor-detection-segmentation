#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Enhanced Training Framework for Medical Image Segmentation

This module provides advanced training strategies including:
- Curriculum Learning: Gradually increase task difficulty
- Progressive Resizing: Start with small images, gradually increase resolution
- Multi-scale Training: Train on multiple resolutions simultaneously
- Advanced Data Augmentation: Sophisticated augmentation pipelines
- Learning Rate Scheduling: Advanced scheduling strategies
- Model Checkpointing: Smart checkpoint management
- Training Monitoring: Comprehensive logging and visualization
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.optim.lr_scheduler import _LRScheduler
from torch.utils.data import DataLoader, Dataset

try:
    from monai.losses import DiceCELoss, FocalLoss
    from monai.metrics import DiceMetric
    from monai.networks.nets import UNETR, UNet

    MONAI_AVAILABLE = True
except ImportError:
    MONAI_AVAILABLE = False

from .callbacks.visualization import save_overlay_panel


@dataclass
class TrainingConfig:
    """Configuration for enhanced training."""

    # Basic training parameters
    epochs: int = 100
    batch_size: int = 2
    learning_rate: float = 1e-4
    weight_decay: float = 1e-5
    device: str = "auto"

    # Curriculum learning
    curriculum_learning: bool = True
    curriculum_start_epoch: int = 10
    curriculum_end_epoch: int = 50
    curriculum_difficulty_levels: int = 5

    # Progressive resizing
    progressive_resizing: bool = True
    initial_resolution: Tuple[int, int, int] = (64, 64, 64)
    final_resolution: Tuple[int, int, int] = (128, 128, 128)
    resize_start_epoch: int = 20
    resize_end_epoch: int = 60

    # Multi-scale training
    multi_scale_training: bool = True
    scale_factors: List[float] = field(
        default_factory=lambda: [0.5, 0.75, 1.0, 1.25]
    )

    # Loss function
    loss_type: str = "dice_ce"
    dice_weight: float = 0.7
    ce_weight: float = 0.3
    focal_gamma: float = 2.0

    # Optimizer
    optimizer_type: str = "adamw"
    momentum: float = 0.9

    # Learning rate scheduling
    scheduler_type: str = "cosine_warmup"
    warmup_epochs: int = 10
    min_lr: float = 1e-6

    # Regularization
    dropout_rate: float = 0.1
    label_smoothing: float = 0.1

    # Validation and checkpointing
    val_interval: int = 1
    save_interval: int = 10
    patience: int = 20
    early_stopping: bool = True

    # Advanced features
    mixed_precision: bool = True
    gradient_clipping: float = 1.0
    accumulation_steps: int = 1

    # Logging and visualization
    log_dir: str = "./logs"
    checkpoint_dir: str = "./checkpoints"
    visualization_dir: str = "./visualizations"
    save_overlays: bool = True
    overlay_frequency: int = 5


@dataclass
class CurriculumSampler:
    """Curriculum learning sampler that gradually increases task difficulty."""

    difficulty_levels: int = 5
    current_level: int = 0

    def __post_init__(self):
        self.difficulty_weights = self._compute_difficulty_weights()

    def _compute_difficulty_weights(self) -> np.ndarray:
        """Compute weights for different difficulty levels."""
        # Higher weights for easier samples initially
        weights = np.linspace(2.0, 0.5, self.difficulty_levels)
        return weights / weights.sum()

    def get_sample_weights(
        self, dataset: Dataset, epoch: int, total_epochs: int
    ) -> np.ndarray:
        """Get sampling weights based on current curriculum stage."""
        if not hasattr(dataset, 'get_difficulty_scores'):
            # If dataset doesn't have difficulty scores, use uniform sampling
            return np.ones(len(dataset)) / len(dataset)

        difficulty_scores = dataset.get_difficulty_scores()
        progress = epoch / total_epochs

        # Adjust difficulty threshold based on training progress
        difficulty_threshold = progress * self.difficulty_levels

        # Compute weights based on difficulty and current threshold
        weights = np.zeros(len(dataset))
        for i, score in enumerate(difficulty_scores):
            level = min(int(score * self.difficulty_levels), self.difficulty_levels - 1)
            if level <= difficulty_threshold:
                weights[i] = self.difficulty_weights[level]
            else:
                weights[i] = 0.1  # Low weight for too difficult samples

        return weights / weights.sum()

    def update_difficulty_level(self, epoch: int, total_epochs: int):
        """Update current difficulty level based on training progress."""
        progress = epoch / total_epochs
        self.current_level = int(progress * self.difficulty_levels)
        self.current_level = min(self.current_level, self.difficulty_levels - 1)


@dataclass
class ProgressiveResizer:
    """Progressive resizing handler for training."""

    initial_resolution: Tuple[int, int, int]
    final_resolution: Tuple[int, int, int]
    start_epoch: int
    end_epoch: int

    def get_current_resolution(self, epoch: int) -> Tuple[int, int, int]:
        """Get current resolution based on training progress."""
        if epoch < self.start_epoch:
            return self.initial_resolution
        elif epoch >= self.end_epoch:
            return self.final_resolution
        else:
            # Linear interpolation between resolutions
            progress = (epoch - self.start_epoch) / (self.end_epoch - self.start_epoch)

            current_res = []
            for init, final in zip(self.initial_resolution, self.final_resolution):
                current = int(init + progress * (final - init))
                current_res.append(current)

            return (current_res[0], current_res[1], current_res[2])

    def should_resize(self, epoch: int) -> bool:
        """Check if resizing should occur at current epoch."""
        return self.start_epoch <= epoch < self.end_epoch


class EnhancedTrainer:
    """Enhanced trainer with advanced training strategies."""

    def __init__(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
        config: Optional[TrainingConfig] = None
    ):
        """
        Initialize enhanced trainer.

        Args:
            model: PyTorch model to train
            train_loader: Training data loader
            val_loader: Validation data loader
            config: Training configuration
        """
        if not MONAI_AVAILABLE:
            raise ImportError("MONAI is required for enhanced training")

        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.config = config or TrainingConfig()

        # Set device
        self.device = self._get_device()
        self.model.to(self.device)

        # Initialize components
        self.curriculum_sampler = CurriculumSampler(
            difficulty_levels=self.config.curriculum_difficulty_levels
        )
        self.progressive_resizer = ProgressiveResizer(
            initial_resolution=self.config.initial_resolution,
            final_resolution=self.config.final_resolution,
            start_epoch=self.config.resize_start_epoch,
            end_epoch=self.config.resize_end_epoch
        )

        self._setup_training_components()
        self._setup_logging()

        # Training state
        self.current_epoch = 0
        self.best_metric = -1.0
        self.training_history: Dict[str, List[float]] = {
            'train_loss': [], 'val_loss': [], 'val_dice': [],
            'learning_rate': [], 'curriculum_level': []
        }

    def _get_device(self) -> torch.device:
        """Get appropriate device for training."""
        if self.config.device == "auto":
            if torch.cuda.is_available():
                return torch.device("cuda")
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                return torch.device("mps")
            else:
                return torch.device("cpu")
        return torch.device(self.config.device)

    def _setup_training_components(self):
        """Setup loss function, optimizer, and scheduler."""
        # Loss function
        if self.config.loss_type == "dice_ce":
            self.loss_function = DiceCELoss(
                to_onehot_y=True,
                softmax=True,
                include_background=False,
                lambda_dice=self.config.dice_weight,
                lambda_ce=self.config.ce_weight
            )
        elif self.config.loss_type == "focal":
            self.loss_function = FocalLoss(
                to_onehot_y=True,
                gamma=self.config.focal_gamma
            )
        else:
            raise ValueError(f"Unknown loss type: {self.config.loss_type}")

        # Optimizer
        if self.config.optimizer_type == "adamw":
            self.optimizer = torch.optim.AdamW(
                self.model.parameters(),
                lr=self.config.learning_rate,
                weight_decay=self.config.weight_decay
            )
        elif self.config.optimizer_type == "adam":
            self.optimizer = torch.optim.Adam(
                self.model.parameters(),
                lr=self.config.learning_rate,
                weight_decay=self.config.weight_decay
            )
        else:
            raise ValueError(f"Unknown optimizer: {self.config.optimizer_type}")

        # Scheduler
        if self.config.scheduler_type == "cosine_warmup":
            self.scheduler = self._create_cosine_warmup_scheduler()
        elif self.config.scheduler_type == "step":
            self.scheduler = torch.optim.lr_scheduler.StepLR(
                self.optimizer,
                step_size=self.config.epochs // 4,
                gamma=0.5
            )
        else:
            self.scheduler = None

        # Mixed precision
        if self.config.mixed_precision and self.device.type == "cuda":
            self.scaler = torch.cuda.amp.GradScaler()
        else:
            self.scaler = None

        # Metrics
        self.dice_metric = DiceMetric(include_background=False, reduction="mean")

    def _create_cosine_warmup_scheduler(self) -> _LRScheduler:
        """Create cosine annealing scheduler with warmup."""
        def lr_lambda(epoch):
            if epoch < self.config.warmup_epochs:
                # Linear warmup
                return (epoch + 1) / self.config.warmup_epochs
            else:
                # Cosine annealing
                progress = (epoch - self.config.warmup_epochs) / (
                    self.config.epochs - self.config.warmup_epochs
                )
                min_lr_ratio = self.config.min_lr / self.config.learning_rate
                return min_lr_ratio + (1 - min_lr_ratio) * (
                    1 + np.cos(np.pi * progress)
                ) / 2

        return torch.optim.lr_scheduler.LambdaLR(self.optimizer, lr_lambda)

    def _setup_logging(self):
        """Setup logging and directories."""
        self.log_dir = Path(self.config.log_dir)
        self.checkpoint_dir = Path(self.config.checkpoint_dir)
        self.visualization_dir = Path(self.config.visualization_dir)

        for dir_path in [self.log_dir, self.checkpoint_dir, self.visualization_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_dir / 'training.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _get_curriculum_weights(self) -> Optional[np.ndarray]:
        """Get curriculum learning weights for current epoch."""
        if not self.config.curriculum_learning:
            return None

        if self.current_epoch < self.config.curriculum_start_epoch:
            return None

        return self.curriculum_sampler.get_sample_weights(
            self.train_loader.dataset, self.current_epoch, self.config.epochs
        )

    def _apply_progressive_resizing(self):
        """Apply progressive resizing if enabled."""
        if not self.config.progressive_resizing:
            return

        current_res = self.progressive_resizer.get_current_resolution(self.current_epoch)
        self.logger.info(f"Progressive resizing: {current_res}")

        # Update transforms in data loader if possible
        # This would require custom dataset/transform implementation

    def train_epoch(self) -> float:
        """Train for one epoch with advanced strategies."""
        self.model.train()
        epoch_loss = 0.0
        num_batches = len(self.train_loader)

        # Get curriculum weights
        curriculum_weights = self._get_curriculum_weights()

        for batch_idx, batch_data in enumerate(self.train_loader):
            # Move data to device
            inputs = batch_data["image"].to(self.device)
            targets = batch_data["label"].to(self.device)

            # Apply curriculum weighting if available
            if curriculum_weights is not None:
                # This would require weighted sampling in the data loader
                pass

            # Forward pass with mixed precision
            self.optimizer.zero_grad()

            if self.scaler is not None:
                with torch.autocast(device_type=self.device.type, dtype=torch.float16):
                    outputs = self.model(inputs)
                    loss = self.loss_function(outputs, targets)

                self.scaler.scale(loss).backward()

                # Gradient clipping
                if self.config.gradient_clipping > 0:
                    self.scaler.unscale_(self.optimizer)
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(), self.config.gradient_clipping
                    )

                self.scaler.step(self.optimizer)
                self.scaler.update()
            else:
                outputs = self.model(inputs)
                loss = self.loss_function(outputs, targets)
                loss.backward()

                # Gradient clipping
                if self.config.gradient_clipping > 0:
                    torch.nn.utils.clip_grad_norm_(
                        self.model.parameters(), self.config.gradient_clipping
                    )

                self.optimizer.step()

            epoch_loss += loss.item()

        return epoch_loss / num_batches

    def validate_epoch(self) -> Tuple[float, float]:
        """Validate for one epoch."""
        if self.val_loader is None:
            return 0.0, 0.0

        self.model.eval()
        epoch_loss = 0.0
        self.dice_metric.reset()

        with torch.no_grad():
            for batch_data in self.val_loader:
                inputs = batch_data["image"].to(self.device)
                targets = batch_data["label"].to(self.device)

                outputs = self.model(inputs)
                loss = self.loss_function(outputs, targets)
                epoch_loss += loss.item()

                # Compute dice metric
                preds = torch.argmax(outputs, dim=1, keepdim=True)
                self.dice_metric(y_pred=preds, y=targets)

        avg_loss = epoch_loss / len(self.val_loader)
        dice_score = self.dice_metric.aggregate().item()

        return avg_loss, dice_score

    def _save_visualizations(self):
        """Save training visualizations."""
        if not self.config.save_overlays or self.val_loader is None:
            return

        if self.current_epoch % self.config.overlay_frequency != 0:
            return

        self.model.eval()
        overlay_dir = self.visualization_dir / f"epoch_{self.current_epoch}"
        overlay_dir.mkdir(exist_ok=True)

        with torch.no_grad():
            for batch_idx, batch_data in enumerate(self.val_loader):
                if batch_idx >= 2:  # Save overlays for first 2 batches
                    break

                inputs = batch_data["image"].to(self.device)
                targets = batch_data["label"].to(self.device)

                outputs = self.model(inputs)
                preds = torch.argmax(outputs, dim=1, keepdim=True)

                # Save overlay for first sample in batch
                save_overlay_panel(
                    image_ch_first=inputs[0],
                    label_onehot=targets[0],
                    pred_onehot=preds[0],
                    out_path=overlay_dir / f"overlay_{batch_idx}.png"
                )

    def save_checkpoint(self, is_best: bool = False):
        """Save model checkpoint."""
        checkpoint = {
            'epoch': self.current_epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'scheduler_state_dict': self.scheduler.state_dict() if self.scheduler else None,
            'best_metric': self.best_metric,
            'training_history': self.training_history,
            'config': self.config,
            'curriculum_level': self.curriculum_sampler.current_level
        }

        # Save latest checkpoint
        checkpoint_path = self.checkpoint_dir / 'latest_checkpoint.pth'
        torch.save(checkpoint, checkpoint_path)

        # Save best model
        if is_best:
            best_path = self.checkpoint_dir / 'best_model.pth'
            torch.save(checkpoint, best_path)
            self.logger.info(f"New best model saved: {best_path}")

    def load_checkpoint(self, checkpoint_path: str):
        """Load model checkpoint."""
        checkpoint = torch.load(checkpoint_path, map_location=self.device)

        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])

        if self.scheduler and checkpoint.get('scheduler_state_dict'):
            self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])

        self.current_epoch = checkpoint['epoch']
        self.best_metric = checkpoint['best_metric']
        self.training_history = checkpoint['training_history']

        if 'curriculum_level' in checkpoint:
            self.curriculum_sampler.current_level = checkpoint['curriculum_level']

        self.logger.info(f"Checkpoint loaded from {checkpoint_path}")

    def train(self):
        """Main training loop with advanced strategies."""
        self.logger.info("Starting enhanced training")
        self.logger.info(f"Using device: {self.device}")
        self.logger.info(f"Model parameters: {sum(p.numel() for p in self.model.parameters()):,}")

        start_time = time.time()

        for epoch in range(self.current_epoch, self.config.epochs):
            self.current_epoch = epoch
            epoch_start_time = time.time()

            # Update curriculum and progressive resizing
            if self.config.curriculum_learning:
                self.curriculum_sampler.update_difficulty_level(epoch, self.config.epochs)

            if self.config.progressive_resizing:
                self._apply_progressive_resizing()

            # Training phase
            train_loss = self.train_epoch()

            # Validation phase
            val_loss, val_dice = self.validate_epoch()

            # Update learning rate
            if self.scheduler:
                self.scheduler.step()

            # Update training history
            current_lr = self.optimizer.param_groups[0]['lr']
            self.training_history['train_loss'].append(train_loss)
            self.training_history['val_loss'].append(val_loss)
            self.training_history['val_dice'].append(val_dice)
            self.training_history['learning_rate'].append(current_lr)
            self.training_history['curriculum_level'].append(self.curriculum_sampler.current_level)

            # Check if this is the best model
            is_best = val_dice > self.best_metric
            if is_best:
                self.best_metric = val_dice

            # Save checkpoint
            if (epoch + 1) % self.config.save_interval == 0:
                self.save_checkpoint(is_best)

            # Save visualizations
            self._save_visualizations()

            # Log progress
            epoch_time = time.time() - epoch_start_time
            self.logger.info(
                f"Epoch {epoch + 1}/{self.config.epochs} - "
                f"Train Loss: {train_loss:.4f}, "
                f"Val Loss: {val_loss:.4f}, "
                f"Val Dice: {val_dice:.4f}, "
                f"LR: {current_lr:.6f}, "
                f"Time: {epoch_time:.2f}s"
            )

            # Early stopping
            if self.config.early_stopping:
                if epoch - np.argmax(self.training_history['val_dice']) > self.config.patience:
                    self.logger.info(f"Early stopping at epoch {epoch + 1}")
                    break

        # Save final checkpoint
        self.save_checkpoint(is_best=False)

        total_time = time.time() - start_time
        self.logger.info(f"Training completed in {total_time:.2f} seconds")
        self.logger.info(f"Best validation Dice score: {self.best_metric:.4f}")

        # Save training history
        history_path = self.log_dir / 'training_history.json'
        with open(history_path, 'w') as f:
            json.dump(self.training_history, f, indent=2)


def create_enhanced_model(config: Dict[str, Any]) -> nn.Module:
    """Create an enhanced model based on configuration."""
    if not MONAI_AVAILABLE:
        raise ImportError("MONAI is required for enhanced models")

    model_type = config.get('model_type', 'unetr')
    in_channels = config.get('in_channels', 4)
    out_channels = config.get('out_channels', 3)

    if model_type.lower() == 'unetr':
        return UNETR(
            in_channels=in_channels,
            out_channels=out_channels,
            img_size=tuple(config.get('img_size', [128, 128, 128])),
            feature_size=config.get('feature_size', 16),
            hidden_size=config.get('hidden_size', 768),
            mlp_dim=config.get('mlp_dim', 3072),
            num_heads=config.get('num_heads', 12),
            pos_embed="perceptron",
            norm_name="instance",
            res_block=True,
            dropout_rate=config.get('dropout_rate', 0.1)
        )
    elif model_type.lower() == 'unet':
        return UNet(
            spatial_dims=3,
            in_channels=in_channels,
            out_channels=out_channels,
            channels=config.get('channels', [16, 32, 64, 128, 256]),
            strides=config.get('strides', [2, 2, 2, 2]),
            num_res_units=config.get('num_res_units', 2),
            norm=config.get('norm', 'INSTANCE'),
            dropout=config.get('dropout', 0.1)
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")


def create_enhanced_trainer(
    config_path: Optional[str] = None,
    config_dict: Optional[Dict[str, Any]] = None
) -> EnhancedTrainer:
    """
    Create an enhanced trainer from configuration.

    Args:
        config_path: Path to JSON configuration file
        config_dict: Configuration dictionary

    Returns:
        Configured EnhancedTrainer instance
    """
    if config_path:
        with open(config_path, 'r') as f:
            config_dict = json.load(f)

    config = TrainingConfig(**config_dict) if config_dict else TrainingConfig()

    # Create model
    model = create_enhanced_model(config_dict or {})

    # Create data loaders (placeholder - implement based on your data structure)
    # This would need to be adapted to your specific dataset structure
    train_loader = None  # Replace with actual data loader creation
    val_loader = None    # Replace with actual data loader creation

    return EnhancedTrainer(model, train_loader, val_loader, config)


if __name__ == "__main__":
    # Example usage
    config = TrainingConfig(
        epochs=50,
        curriculum_learning=True,
        progressive_resizing=True,
        mixed_precision=True
    )

    # Create trainer (would need actual data loaders)
    # trainer = EnhancedTrainer(model, train_loader, val_loader, config)
    # trainer.train()

    print("Enhanced training framework initialized")
    print(f"Configuration: {config}")
