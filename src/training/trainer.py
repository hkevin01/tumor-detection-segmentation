"""
Training module for tumor detection and segmentation models.

This module provides a comprehensive training framework with support for
various model architectures, loss functions, and training strategies.
"""

import os
import json
import time
import logging
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader
    from torch.optim import Optimizer
    from torch.optim.lr_scheduler import _LRScheduler

    from monai.networks.nets import UNet
    from monai.losses import DiceLoss, FocalLoss
    from monai.metrics import DiceMetric
    from monai.utils import set_determinism

    import numpy as np
    from tqdm import tqdm

    DEPENDENCIES_AVAILABLE = True
except ImportError:
    DEPENDENCIES_AVAILABLE = False


class ModelTrainer:
    """
    Comprehensive trainer class for medical image segmentation models.
    """

    def __init__(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        val_loader: Optional[DataLoader] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the trainer.

        Args:
            model: PyTorch model to train
            train_loader: Training data loader
            val_loader: Validation data loader (optional)
            config: Training configuration dictionary
        """
        if not DEPENDENCIES_AVAILABLE:
            raise ImportError(
                "Required dependencies not available. "
                "Please install torch, monai, numpy, and tqdm."
            )

        self.model = model
        self.train_loader = train_loader
        self.val_loader = val_loader
        self.config = config or {}

        # Set device
        self.device = torch.device(
            self.config.get('device', 'cuda' if torch.cuda.is_available() else 'cpu')
        )
        self.model.to(self.device)

        # Initialize training components
        self._setup_loss_function()
        self._setup_optimizer()
        self._setup_scheduler()
        self._setup_metrics()
        self._setup_logging()

        # Training state
        self.current_epoch = 0
        self.best_metric = -1.0
        self.training_history = {'train_loss': [], 'val_loss': [], 'val_metric': []}

    def _setup_loss_function(self):
        """Setup the loss function."""
        loss_type = self.config.get('loss_function', 'dice')

        if loss_type == 'dice':
            self.loss_function = DiceLoss(
                to_onehot_y=True,
                softmax=True,
                include_background=self.config.get('include_background', False)
            )
        elif loss_type == 'focal':
            self.loss_function = FocalLoss(
                to_onehot_y=True,
                gamma=self.config.get('focal_gamma', 2.0)
            )
        elif loss_type == 'combined':
            self.dice_loss = DiceLoss(to_onehot_y=True, softmax=True)
            self.focal_loss = FocalLoss(to_onehot_y=True)
            self.loss_function = self._combined_loss
        else:
            raise ValueError(f"Unknown loss function: {loss_type}")

    def _combined_loss(self, pred, target):
        """Combined Dice + Focal loss."""
        dice_weight = self.config.get('dice_weight', 0.7)
        focal_weight = self.config.get('focal_weight', 0.3)

        dice = self.dice_loss(pred, target)
        focal = self.focal_loss(pred, target)

        return dice_weight * dice + focal_weight * focal

    def _setup_optimizer(self):
        """Setup the optimizer with enhanced parameter support."""
        # Support both top-level config and optimizer sub-config
        optimizer_config = self.config.get('optimizer', {})
        if isinstance(optimizer_config, str):
            optimizer_type = optimizer_config
            optimizer_params = {}
        elif isinstance(optimizer_config, dict):
            optimizer_type = optimizer_config.get('name', 'adam')
            optimizer_params = optimizer_config
        else:
            optimizer_type = self.config.get('optimizer', 'adam')
            optimizer_params = {}

        # Get learning rate from multiple possible locations
        lr = optimizer_params.get('lr',
             self.config.get('learning_rate',
             self.config.get('lr', 0.001)))

        # Get weight decay
        weight_decay = optimizer_params.get('weight_decay',
                       self.config.get('weight_decay', 1e-5))

        if optimizer_type.lower() == 'adam':
            betas = optimizer_params.get('betas', (0.9, 0.999))
            eps = optimizer_params.get('eps', 1e-8)
            amsgrad = optimizer_params.get('amsgrad', False)

            self.optimizer = torch.optim.Adam(
                self.model.parameters(),
                lr=lr,
                betas=betas,
                eps=eps,
                weight_decay=weight_decay,
                amsgrad=amsgrad
            )
            self.logger.info(f"Using Adam optimizer: lr={lr}, betas={betas}, weight_decay={weight_decay}")

        elif optimizer_type.lower() == 'adamw':
            betas = optimizer_params.get('betas', (0.9, 0.999))
            eps = optimizer_params.get('eps', 1e-8)
            amsgrad = optimizer_params.get('amsgrad', False)

            self.optimizer = torch.optim.AdamW(
                self.model.parameters(),
                lr=lr,
                betas=betas,
                eps=eps,
                weight_decay=weight_decay,
                amsgrad=amsgrad
            )
            self.logger.info(f"Using AdamW optimizer: lr={lr}, betas={betas}, weight_decay={weight_decay}")

        elif optimizer_type.lower() == 'sgd':
            momentum = optimizer_params.get('momentum',
                       self.config.get('momentum', 0.9))
            nesterov = optimizer_params.get('nesterov', False)

            self.optimizer = torch.optim.SGD(
                self.model.parameters(),
                lr=lr,
                momentum=momentum,
                weight_decay=weight_decay,
                nesterov=nesterov
            )
            self.logger.info(f"Using SGD optimizer: lr={lr}, momentum={momentum}, weight_decay={weight_decay}")

        else:
            raise ValueError(f"Unknown optimizer: {optimizer_type}")

    def _setup_scheduler(self):
        """Setup learning rate scheduler with enhanced parameter support."""
        # Support both top-level config and scheduler sub-config
        scheduler_config = self.config.get('scheduler', None)

        if scheduler_config is None:
            self.scheduler = None
            self.logger.info("No learning rate scheduler configured")
            return

        if isinstance(scheduler_config, str):
            scheduler_type = scheduler_config
            scheduler_params = {}
        elif isinstance(scheduler_config, dict):
            scheduler_type = scheduler_config.get('name', None)
            scheduler_params = scheduler_config
        else:
            scheduler_type = scheduler_config
            scheduler_params = {}

        if not scheduler_type:
            self.scheduler = None
            return

        if scheduler_type.lower() == 'cosine':
            T_max = scheduler_params.get('T_max',
                    self.config.get('epochs',
                    self.config.get('max_epochs', 100)))
            eta_min = scheduler_params.get('eta_min', 0)

            self.scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
                self.optimizer,
                T_max=T_max,
                eta_min=eta_min
            )
            self.logger.info(f"Using CosineAnnealingLR: T_max={T_max}, eta_min={eta_min}")

        elif scheduler_type.lower() == 'step':
            step_size = scheduler_params.get('step_size',
                        self.config.get('step_size', 30))
            gamma = scheduler_params.get('gamma',
                    self.config.get('gamma', 0.1))

            self.scheduler = torch.optim.lr_scheduler.StepLR(
                self.optimizer,
                step_size=step_size,
                gamma=gamma
            )
            self.logger.info(f"Using StepLR: step_size={step_size}, gamma={gamma}")

        elif scheduler_type.lower() in ['plateau', 'reducelronplateau']:
            mode = scheduler_params.get('mode', 'max')
            factor = scheduler_params.get('factor',
                     self.config.get('factor', 0.5))
            patience = scheduler_params.get('patience',
                       self.config.get('patience', 10))
            threshold = scheduler_params.get('threshold', 1e-4)
            threshold_mode = scheduler_params.get('threshold_mode', 'rel')
            cooldown = scheduler_params.get('cooldown', 0)
            min_lr = scheduler_params.get('min_lr', 1e-7)
            verbose = scheduler_params.get('verbose', True)

            self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
                self.optimizer,
                mode=mode,
                factor=factor,
                patience=patience,
                threshold=threshold,
                threshold_mode=threshold_mode,
                cooldown=cooldown,
                min_lr=min_lr,
                verbose=verbose
            )
            self.logger.info(
                f"Using ReduceLROnPlateau: mode={mode}, factor={factor}, "
                f"patience={patience}, min_lr={min_lr}"
            )

        elif scheduler_type.lower() == 'cosinewarmuprestart':
            T_0 = scheduler_params.get('T_0', 10)
            T_mult = scheduler_params.get('T_mult', 2)
            eta_min = scheduler_params.get('eta_min', 0)

            self.scheduler = torch.optim.lr_scheduler.CosineAnnealingWarmRestarts(
                self.optimizer,
                T_0=T_0,
                T_mult=T_mult,
                eta_min=eta_min
            )
            self.logger.info(f"Using CosineAnnealingWarmRestarts: T_0={T_0}, T_mult={T_mult}")

        elif scheduler_type.lower() == 'exponential':
            gamma = scheduler_params.get('gamma', 0.95)

            self.scheduler = torch.optim.lr_scheduler.ExponentialLR(
                self.optimizer,
                gamma=gamma
            )
            self.logger.info(f"Using ExponentialLR: gamma={gamma}")

        else:
            self.logger.warning(f"Unknown scheduler type: {scheduler_type}, using no scheduler")
            self.scheduler = None

    def _setup_metrics(self):
        """Setup evaluation metrics."""
        self.dice_metric = DiceMetric(
            include_background=False,
            reduction="mean"
        )

    def _setup_logging(self):
        """Setup logging configuration."""
        log_dir = Path(self.config.get('log_dir', './logs'))
        log_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'training.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def train_epoch(self) -> float:
        """
        Train for one epoch.

        Returns:
            Average training loss for the epoch
        """
        self.model.train()
        epoch_loss = 0.0
        num_batches = len(self.train_loader)

        progress_bar = tqdm(
            self.train_loader,
            desc=f"Epoch {self.current_epoch + 1} [Train]",
            leave=False
        )

        for batch_idx, batch_data in enumerate(progress_bar):
            # Move data to device
            inputs = batch_data["image"].to(self.device)
            targets = batch_data["label"].to(self.device)

            # Forward pass
            self.optimizer.zero_grad()
            outputs = self.model(inputs)
            loss = self.loss_function(outputs, targets)

            # Backward pass
            loss.backward()

            # Gradient clipping if configured
            if self.config.get('gradient_clipping', False):
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(),
                    self.config.get('max_grad_norm', 1.0)
                )

            self.optimizer.step()

            # Update metrics
            epoch_loss += loss.item()

            # Update progress bar
            progress_bar.set_postfix({
                'Loss': f"{loss.item():.4f}",
                'Avg Loss': f"{epoch_loss / (batch_idx + 1):.4f}"
            })

        return epoch_loss / num_batches

    def validate_epoch(self) -> Tuple[float, float]:
        """
        Validate for one epoch.

        Returns:
            Tuple of (average validation loss, dice metric)
        """
        if self.val_loader is None:
            return 0.0, 0.0

        self.model.eval()
        epoch_loss = 0.0
        self.dice_metric.reset()

        progress_bar = tqdm(
            self.val_loader,
            desc=f"Epoch {self.current_epoch + 1} [Val]",
            leave=False
        )

        with torch.no_grad():
            for batch_data in progress_bar:
                inputs = batch_data["image"].to(self.device)
                targets = batch_data["label"].to(self.device)

                outputs = self.model(inputs)
                loss = self.loss_function(outputs, targets)
                epoch_loss += loss.item()

                # Compute dice metric
                outputs = torch.argmax(outputs, dim=1, keepdim=True)
                self.dice_metric(y_pred=outputs, y=targets)

                progress_bar.set_postfix({
                    'Val Loss': f"{loss.item():.4f}"
                })

        avg_loss = epoch_loss / len(self.val_loader)
        dice_score = self.dice_metric.aggregate().item()

        return avg_loss, dice_score

    def save_checkpoint(self, is_best: bool = False):
        """Save model checkpoint."""
        checkpoint_dir = Path(self.config.get('checkpoint_dir', './checkpoints'))
        checkpoint_dir.mkdir(exist_ok=True)

        checkpoint = {
            'epoch': self.current_epoch,
            'model_state_dict': self.model.state_dict(),
            'optimizer_state_dict': self.optimizer.state_dict(),
            'best_metric': self.best_metric,
            'training_history': self.training_history,
            'config': self.config
        }

        if self.scheduler:
            checkpoint['scheduler_state_dict'] = self.scheduler.state_dict()

        # Save latest checkpoint
        checkpoint_path = checkpoint_dir / 'latest_checkpoint.pth'
        torch.save(checkpoint, checkpoint_path)

        # Save best model if this is the best so far
        if is_best:
            best_path = checkpoint_dir / 'best_model.pth'
            torch.save(checkpoint, best_path)
            self.logger.info(f"New best model saved to {best_path}")

    def load_checkpoint(self, checkpoint_path: str):
        """Load model checkpoint."""
        checkpoint = torch.load(checkpoint_path, map_location=self.device)

        self.model.load_state_dict(checkpoint['model_state_dict'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        self.current_epoch = checkpoint['epoch']
        self.best_metric = checkpoint['best_metric']
        self.training_history = checkpoint['training_history']

        if self.scheduler and 'scheduler_state_dict' in checkpoint:
            self.scheduler.load_state_dict(checkpoint['scheduler_state_dict'])

        self.logger.info(f"Checkpoint loaded from {checkpoint_path}")

    def train(self, num_epochs: int):
        """
        Main training loop.

        Args:
            num_epochs: Number of epochs to train
        """
        self.logger.info(f"Starting training for {num_epochs} epochs")
        self.logger.info(f"Using device: {self.device}")
        self.logger.info(f"Model parameters: {sum(p.numel() for p in self.model.parameters()):,}")

        start_time = time.time()

        for epoch in range(num_epochs):
            self.current_epoch = epoch

            # Training phase
            train_loss = self.train_epoch()
            self.training_history['train_loss'].append(train_loss)

            # Validation phase
            val_loss, val_dice = self.validate_epoch()
            self.training_history['val_loss'].append(val_loss)
            self.training_history['val_metric'].append(val_dice)

            # Update learning rate scheduler
            if self.scheduler:
                if isinstance(self.scheduler, torch.optim.lr_scheduler.ReduceLROnPlateau):
                    self.scheduler.step(val_dice)
                else:
                    self.scheduler.step()

            # Check if this is the best model so far
            is_best = val_dice > self.best_metric
            if is_best:
                self.best_metric = val_dice

            # Save checkpoint
            if (epoch + 1) % self.config.get('save_frequency', 10) == 0:
                self.save_checkpoint(is_best)

            # Log progress
            current_lr = self.optimizer.param_groups[0]['lr']
            self.logger.info(
                f"Epoch {epoch + 1}/{num_epochs} - "
                f"Train Loss: {train_loss:.4f}, "
                f"Val Loss: {val_loss:.4f}, "
                f"Val Dice: {val_dice:.4f}, "
                f"LR: {current_lr:.6f}"
            )

            # Early stopping check
            if self.config.get('early_stopping', False):
                patience = self.config.get('early_stopping_patience', 20)
                if epoch - self._get_best_epoch() > patience:
                    self.logger.info(f"Early stopping after {epoch + 1} epochs")
                    break

        # Save final checkpoint
        self.save_checkpoint(is_best=False)

        total_time = time.time() - start_time
        self.logger.info(f"Training completed in {total_time:.2f} seconds")
        self.logger.info(f"Best validation Dice score: {self.best_metric:.4f}")

    def _get_best_epoch(self) -> int:
        """Get the epoch with the best validation metric."""
        if not self.training_history['val_metric']:
            return 0
        return np.argmax(self.training_history['val_metric'])


def create_model(config: Dict[str, Any]) -> nn.Module:
    """
    Create a model based on configuration.

    Args:
        config: Configuration dictionary

    Returns:
        Initialized PyTorch model
    """
    if not DEPENDENCIES_AVAILABLE:
        raise ImportError(
            "Required dependencies not available. "
            "Please install torch and monai."
        )

    model_type = config.get('model_type', 'unet')

    if model_type.lower() == 'unet':
        model = UNet(
            dimensions=config.get('dimensions', 3),
            in_channels=config.get('in_channels', 1),
            out_channels=config.get('out_channels', 2),
            channels=config.get('channels', (16, 32, 64, 128, 256)),
            strides=config.get('strides', (2, 2, 2, 2)),
            num_res_units=config.get('num_res_units', 2),
            norm=config.get('norm', 'batch'),
            dropout=config.get('dropout', 0.0)
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    return model


def setup_training(config_path: str) -> Tuple[nn.Module, DataLoader, DataLoader]:
    """
    Setup training components from configuration.

    Args:
        config_path: Path to configuration file

    Returns:
        Tuple of (model, train_loader, val_loader)
    """
    # Load configuration
    with open(config_path, 'r') as f:
        config = json.load(f)

    # Set deterministic behavior
    if config.get('deterministic', True):
        set_determinism(seed=config.get('random_seed', 42))

    # Create model
    model = create_model(config)

    # Create data loaders (placeholder - implement based on your data structure)
    from ..data.dataset import create_data_loaders, get_default_transforms

    transforms = get_default_transforms(config)
    data_loaders = create_data_loaders(config, transforms)

    train_loader = data_loaders.get('train')
    val_loader = data_loaders.get('val')

    return model, train_loader, val_loader
