#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Model Registry for Medical Image Segmentation Benchmarking

This module provides a registry system for managing different medical image
segmentation architectures. It includes implementations and factories for
popular models like UNETR, SwinUNETR, SegResNet, and others, with standardized
interfaces for benchmarking.

Key Features:
- Model factory with standardized interfaces
- Pre-configured architectures for medical imaging
- Model complexity analysis
- Memory and computational requirements tracking
- Support for custom model registration
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

import torch
import torch.nn as nn

# Import medical imaging libraries
try:
    from monai.networks.nets import (UNETR, AttentionUnet, BasicUNet, DynUNet,
                                     SegResNet, SwinUNETR, UNet, ViT, VNet)
    MONAI_AVAILABLE = True
except ImportError:
    MONAI_AVAILABLE = False
    logging.warning("MONAI not available. Some models will not be available.")

try:
    import segmentation_models_pytorch as smp
    SMP_AVAILABLE = True
except ImportError:
    SMP_AVAILABLE = False
    logging.warning("segmentation_models_pytorch not available.")


@dataclass
class ModelConfig:
    """Configuration for a segmentation model."""
    name: str
    architecture: str
    input_channels: int = 1
    output_channels: int = 2
    spatial_dims: int = 3
    image_size: Tuple[int, ...] = (96, 96, 96)
    model_params: Dict[str, Any] = field(default_factory=dict)
    training_params: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    paper_reference: str = ""
    complexity: str = "medium"  # low, medium, high, very_high


@dataclass
class ModelMetadata:
    """Metadata for model analysis."""
    total_params: int
    trainable_params: int
    memory_mb: float
    flops: Optional[int] = None
    inference_time_ms: Optional[float] = None
    model_size_mb: Optional[float] = None


class BaseSegmentationModel(ABC, nn.Module):
    """Base class for all segmentation models in the registry."""

    def __init__(self, config: ModelConfig):
        super().__init__()
        self.config = config
        self.metadata: Optional[ModelMetadata] = None

    @abstractmethod
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass of the model."""
        pass

    def get_model_info(self) -> Dict[str, Any]:
        """Get comprehensive model information."""
        return {
            "name": self.config.name,
            "architecture": self.config.architecture,
            "config": self.config,
            "metadata": self.metadata
        }

    def compute_metadata(self, device: str = "cpu") -> ModelMetadata:
        """Compute model metadata including parameters and memory usage."""
        # Count parameters
        total_params = sum(p.numel() for p in self.parameters())
        trainable_params = sum(p.numel() for p in self.parameters() if p.requires_grad)

        # Estimate memory usage
        param_size = sum(p.numel() * p.element_size() for p in self.parameters())
        buffer_size = sum(b.numel() * b.element_size() for b in self.buffers())
        memory_mb = (param_size + buffer_size) / (1024 ** 2)

        # Create dummy input for forward pass timing
        dummy_input = torch.randn(1, self.config.input_channels, *self.config.image_size)

        # Time inference
        self.eval()
        with torch.no_grad():
            if device != "cpu" and torch.cuda.is_available():
                self.cuda()
                dummy_input = dummy_input.cuda()
                torch.cuda.synchronize()

            import time
            start_time = time.time()
            _ = self(dummy_input)
            if device != "cpu" and torch.cuda.is_available():
                torch.cuda.synchronize()
            inference_time_ms = (time.time() - start_time) * 1000

        self.metadata = ModelMetadata(
            total_params=total_params,
            trainable_params=trainable_params,
            memory_mb=memory_mb,
            inference_time_ms=inference_time_ms
        )

        return self.metadata


class UNETRModel(BaseSegmentationModel):
    """UNETR (UNEt TRansformers) implementation."""

    def __init__(self, config: ModelConfig):
        super().__init__(config)

        if not MONAI_AVAILABLE:
            raise ImportError("MONAI is required for UNETR model")

        # Default UNETR parameters
        default_params = {
            "img_size": config.image_size,
            "in_channels": config.input_channels,
            "out_channels": config.output_channels,
            "feature_size": 16,
            "hidden_size": 768,
            "mlp_dim": 3072,
            "num_heads": 12,
            "pos_embed": "perceptron",
            "norm_name": "instance",
            "res_block": True,
            "dropout_rate": 0.0,
            "spatial_dims": config.spatial_dims
        }

        # Update with user parameters
        default_params.update(config.model_params)

        self.model = UNETR(**default_params)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)


class SwinUNETRModel(BaseSegmentationModel):
    """Swin UNETR implementation."""

    def __init__(self, config: ModelConfig):
        super().__init__(config)

        if not MONAI_AVAILABLE:
            raise ImportError("MONAI is required for SwinUNETR model")

        # Default SwinUNETR parameters
        default_params = {
            "img_size": config.image_size,
            "in_channels": config.input_channels,
            "out_channels": config.output_channels,
            "depths": [2, 2, 2, 2],
            "num_heads": [3, 6, 12, 24],
            "feature_size": 24,
            "norm_name": "instance",
            "drop_rate": 0.0,
            "attn_drop_rate": 0.0,
            "dropout_path_rate": 0.0,
            "normalize": True,
            "use_checkpoint": False,
            "spatial_dims": config.spatial_dims
        }

        # Update with user parameters
        default_params.update(config.model_params)

        self.model = SwinUNETR(**default_params)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)


class SegResNetModel(BaseSegmentationModel):
    """SegResNet implementation."""

    def __init__(self, config: ModelConfig):
        super().__init__(config)

        if not MONAI_AVAILABLE:
            raise ImportError("MONAI is required for SegResNet model")

        # Default SegResNet parameters
        default_params = {
            "spatial_dims": config.spatial_dims,
            "in_channels": config.input_channels,
            "out_channels": config.output_channels,
            "init_filters": 8,
            "blocks_down": [1, 2, 2, 4],
            "blocks_up": [1, 1, 1],
            "norm": "group",
            "act": "RELU",
            "dropout_prob": None,
            "bias": True,
            "upsample_mode": "deconv"
        }

        # Update with user parameters
        default_params.update(config.model_params)

        self.model = SegResNet(**default_params)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)


class UNetModel(BaseSegmentationModel):
    """Standard U-Net implementation."""

    def __init__(self, config: ModelConfig):
        super().__init__(config)

        if MONAI_AVAILABLE:
            # Use MONAI UNet if available
            default_params = {
                "spatial_dims": config.spatial_dims,
                "in_channels": config.input_channels,
                "out_channels": config.output_channels,
                "channels": [16, 32, 64, 128, 256],
                "strides": [2, 2, 2, 2],
                "num_res_units": 2,
                "norm": "batch",
                "act": "PRELU",
                "dropout": 0.0
            }

            # Update with user parameters
            default_params.update(config.model_params)

            self.model = UNet(**default_params)
        else:
            # Fallback implementation
            raise NotImplementedError("Fallback U-Net implementation not yet available")

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)


class AttentionUNetModel(BaseSegmentationModel):
    """Attention U-Net implementation."""

    def __init__(self, config: ModelConfig):
        super().__init__(config)

        if not MONAI_AVAILABLE:
            raise ImportError("MONAI is required for AttentionUNet model")

        # Default AttentionUNet parameters
        default_params = {
            "spatial_dims": config.spatial_dims,
            "in_channels": config.input_channels,
            "out_channels": config.output_channels,
            "channels": [16, 32, 64, 128, 256],
            "strides": [2, 2, 2, 2],
            "norm": "batch",
            "act": "PRELU",
            "dropout": 0.0
        }

        # Update with user parameters
        default_params.update(config.model_params)

        self.model = AttentionUnet(**default_params)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)


class VNetModel(BaseSegmentationModel):
    """V-Net implementation."""

    def __init__(self, config: ModelConfig):
        super().__init__(config)

        if not MONAI_AVAILABLE:
            raise ImportError("MONAI is required for VNet model")

        # Default VNet parameters
        default_params = {
            "spatial_dims": config.spatial_dims,
            "in_channels": config.input_channels,
            "out_channels": config.output_channels,
            "act": "elu",
            "norm": "batch",
            "bias": False,
            "dropout_prob": 0.5,
            "dropout_dim": 3
        }

        # Update with user parameters
        default_params.update(config.model_params)

        self.model = VNet(**default_params)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)


class ModelRegistry:
    """Registry for managing segmentation models."""

    _models: Dict[str, Callable[[ModelConfig], BaseSegmentationModel]] = {}
    _default_configs: Dict[str, ModelConfig] = {}

    @classmethod
    def register_model(
        cls,
        name: str,
        model_class: Callable[[ModelConfig], BaseSegmentationModel],
        default_config: Optional[ModelConfig] = None
    ) -> None:
        """Register a new model in the registry."""
        cls._models[name] = model_class
        if default_config:
            cls._default_configs[name] = default_config

    @classmethod
    def get_model(
        cls,
        name: str,
        config: Optional[ModelConfig] = None
    ) -> BaseSegmentationModel:
        """Get a model instance by name."""
        if name not in cls._models:
            available_models = list(cls._models.keys())
            raise ValueError(f"Model '{name}' not found. Available: {available_models}")

        if config is None:
            if name in cls._default_configs:
                config = cls._default_configs[name]
            else:
                raise ValueError(f"No default config for '{name}' and no config provided")

        return cls._models[name](config)

    @classmethod
    def list_models(cls) -> List[str]:
        """List all registered models."""
        return list(cls._models.keys())

    @classmethod
    def get_model_info(cls, name: str) -> Dict[str, Any]:
        """Get information about a registered model."""
        if name not in cls._models:
            raise ValueError(f"Model '{name}' not found")

        info = {
            "name": name,
            "class": cls._models[name].__name__,
            "has_default_config": name in cls._default_configs
        }

        if name in cls._default_configs:
            info["default_config"] = cls._default_configs[name]

        return info


# Register available models
def _register_default_models():
    """Register default models with their configurations."""

    # UNETR configurations
    if MONAI_AVAILABLE:
        unetr_config = ModelConfig(
            name="unetr_base",
            architecture="UNETR",
            input_channels=1,
            output_channels=2,
            spatial_dims=3,
            image_size=(96, 96, 96),
            description="Vision Transformer based U-Net for 3D medical image segmentation",
            paper_reference="Hatamizadeh et al. UNETR: Transformers for 3D Medical Image Segmentation",
            complexity="high"
        )
        ModelRegistry.register_model("unetr", UNETRModel, unetr_config)

        # SwinUNETR configurations
        swin_unetr_config = ModelConfig(
            name="swin_unetr_base",
            architecture="SwinUNETR",
            input_channels=1,
            output_channels=2,
            spatial_dims=3,
            image_size=(96, 96, 96),
            description="Swin Transformer based U-Net for 3D medical image segmentation",
            paper_reference="Hatamizadeh et al. Swin UNETR: Swin Transformers for Semantic Segmentation",
            complexity="very_high"
        )
        ModelRegistry.register_model("swin_unetr", SwinUNETRModel, swin_unetr_config)

        # SegResNet configurations
        segresnet_config = ModelConfig(
            name="segresnet_base",
            architecture="SegResNet",
            input_channels=1,
            output_channels=2,
            spatial_dims=3,
            image_size=(96, 96, 96),
            description="Residual Encoder-Decoder CNN for 3D medical image segmentation",
            paper_reference="Myronenko. 3D MRI brain tumor segmentation using autoencoder regularization",
            complexity="medium"
        )
        ModelRegistry.register_model("segresnet", SegResNetModel, segresnet_config)

        # U-Net configurations
        unet_config = ModelConfig(
            name="unet_base",
            architecture="UNet",
            input_channels=1,
            output_channels=2,
            spatial_dims=3,
            image_size=(96, 96, 96),
            description="Standard U-Net for 3D medical image segmentation",
            paper_reference="Ronneberger et al. U-Net: Convolutional Networks for Biomedical Image Segmentation",
            complexity="low"
        )
        ModelRegistry.register_model("unet", UNetModel, unet_config)

        # Attention U-Net configurations
        att_unet_config = ModelConfig(
            name="attention_unet_base",
            architecture="AttentionUNet",
            input_channels=1,
            output_channels=2,
            spatial_dims=3,
            image_size=(96, 96, 96),
            description="Attention-gated U-Net for 3D medical image segmentation",
            paper_reference="Oktay et al. Attention U-Net: Learning Where to Look",
            complexity="medium"
        )
        ModelRegistry.register_model("attention_unet", AttentionUNetModel, att_unet_config)

        # V-Net configurations
        vnet_config = ModelConfig(
            name="vnet_base",
            architecture="VNet",
            input_channels=1,
            output_channels=2,
            spatial_dims=3,
            image_size=(96, 96, 96),
            description="V-Net for 3D medical image segmentation",
            paper_reference="Milletari et al. V-Net: Fully Convolutional Neural Networks",
            complexity="medium"
        )
        ModelRegistry.register_model("vnet", VNetModel, vnet_config)


# Initialize default models
_register_default_models()


def get_available_models() -> List[str]:
    """Get list of available models."""
    return ModelRegistry.list_models()


def create_model_from_config(name: str, config: Optional[ModelConfig] = None) -> BaseSegmentationModel:
    """Create model instance from configuration."""
    return ModelRegistry.get_model(name, config)


def register_custom_model(
    name: str,
    model_class: Callable[[ModelConfig], BaseSegmentationModel],
    default_config: Optional[ModelConfig] = None
) -> None:
    """Register a custom model."""
    ModelRegistry.register_model(name, model_class, default_config)


def get_model_comparison_table() -> List[Dict[str, Any]]:
    """Get comparison table of all available models."""
    models = []
    for model_name in ModelRegistry.list_models():
        model_info = ModelRegistry.get_model_info(model_name)
        models.append(model_info)
    return models


# Example usage and testing
if __name__ == "__main__":
    print("Testing Model Registry...")

    # List available models
    print(f"\nAvailable models: {get_available_models()}")

    # Test model creation
    if MONAI_AVAILABLE:
        print("\nTesting model creation...")

        try:
            # Create UNETR model
            unetr_model = create_model_from_config("unetr")
            print(f"Created UNETR model: {unetr_model.config.name}")

            # Compute metadata
            metadata = unetr_model.compute_metadata()
            print(f"UNETR Parameters: {metadata.total_params:,}")
            print(f"UNETR Memory: {metadata.memory_mb:.2f} MB")
            print(f"UNETR Inference: {metadata.inference_time_ms:.2f} ms")

            # Create SegResNet model
            segresnet_model = create_model_from_config("segresnet")
            print(f"\nCreated SegResNet model: {segresnet_model.config.name}")

            # Test forward pass
            dummy_input = torch.randn(1, 1, 96, 96, 96)
            with torch.no_grad():
                output = unetr_model(dummy_input)
                print(f"UNETR output shape: {output.shape}")

                output = segresnet_model(dummy_input)
                print(f"SegResNet output shape: {output.shape}")

            print("\nModel registry tests completed successfully!")

        except Exception as e:
            print(f"Error during model testing: {e}")
    else:
        print("MONAI not available - skipping model tests")
                print(f"SegResNet output shape: {output.shape}")

            print("\nModel registry tests completed successfully!")

        except Exception as e:
            print(f"Error during model testing: {e}")
    else:
        print("MONAI not available - skipping model tests")
