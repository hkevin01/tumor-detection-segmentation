#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Hyperparameter search space definitions for medical image segmentation models.

This module defines comprehensive search spaces for different model architectures
including UNETR, SwinUNETR, and SegResNet, optimized for medical imaging tasks.
"""

from typing import Any, Dict

import optuna


class HyperparameterSearchSpace:
    """
    Defines hyperparameter search spaces for different model architectures.

    Supports:
    - UNETR (Vision Transformer-based segmentation)
    - SwinUNETR (Swin Transformer-based segmentation)
    - SegResNet (Residual network segmentation)
    - U-Net (Classic CNN-based segmentation)
    """

    @staticmethod
    def suggest_unetr_params(trial: optuna.Trial) -> Dict[str, Any]:
        """
        Suggest hyperparameters for UNETR model.

        Args:
            trial: Optuna trial object

        Returns:
            Dictionary of suggested hyperparameters
        """
        params = {
            # Model architecture
            "model_arch": "unetr",
            "model_img_size": trial.suggest_categorical(
                "model_img_size", [[96, 96, 96], [128, 128, 128], [160, 160, 160]]
            ),
            "model_feature_size": trial.suggest_categorical(
                "model_feature_size", [16, 32, 48, 64]
            ),
            "model_hidden_size": trial.suggest_categorical(
                "model_hidden_size", [768, 1024, 1536]
            ),
            "model_mlp_dim": trial.suggest_categorical(
                "model_mlp_dim", [2048, 3072, 4096]
            ),
            "model_num_heads": trial.suggest_categorical(
                "model_num_heads", [8, 12, 16]
            ),
            "model_dropout_rate": trial.suggest_float(
                "model_dropout_rate", 0.0, 0.3
            ),

            # Training parameters
            "train_learning_rate": trial.suggest_float(
                "train_learning_rate", 1e-5, 1e-2, log=True
            ),
            "train_batch_size": trial.suggest_categorical(
                "train_batch_size", [2, 4, 8, 16]
            ),
            "train_optimizer": trial.suggest_categorical(
                "train_optimizer", ["Adam", "AdamW", "SGD"]
            ),
            "train_weight_decay": trial.suggest_float(
                "train_weight_decay", 1e-6, 1e-2, log=True
            ),
            "train_momentum": trial.suggest_float(
                "train_momentum", 0.9, 0.99
            ) if trial.params.get("train_optimizer") == "SGD" else 0.9,

            # Learning rate scheduling
            "train_lr_scheduler": trial.suggest_categorical(
                "train_lr_scheduler", ["cosine", "polynomial", "step", "exponential"]
            ),
            "train_warmup_epochs": trial.suggest_int(
                "train_warmup_epochs", 0, 10
            ),

            # Data augmentation
            "data_aug_prob": trial.suggest_float(
                "data_aug_prob", 0.0, 0.8
            ),
            "data_spatial_prob": trial.suggest_float(
                "data_spatial_prob", 0.0, 0.8
            ),
            "data_intensity_prob": trial.suggest_float(
                "data_intensity_prob", 0.0, 0.8
            ),

            # Training strategy
            "train_amp": trial.suggest_categorical(
                "train_amp", [True, False]
            ),
            "train_sw_batch_size": trial.suggest_categorical(
                "train_sw_batch_size", [4, 8, 16]
            ),
            "train_infer_overlap": trial.suggest_float(
                "train_infer_overlap", 0.25, 0.75
            )
        }

        return params

    @staticmethod
    def suggest_swinunetr_params(trial: optuna.Trial) -> Dict[str, Any]:
        """
        Suggest hyperparameters for SwinUNETR model.

        Args:
            trial: Optuna trial object

        Returns:
            Dictionary of suggested hyperparameters
        """
        params = {
            # Model architecture
            "model_arch": "swinunetr",
            "model_img_size": trial.suggest_categorical(
                "model_img_size", [[96, 96, 96], [128, 128, 128], [160, 160, 160]]
            ),
            "model_feature_size": trial.suggest_categorical(
                "model_feature_size", [24, 48, 96]
            ),
            "model_depths": trial.suggest_categorical(
                "model_depths", [[2, 2, 2, 2], [2, 2, 6, 2], [2, 2, 18, 2]]
            ),
            "model_num_heads": trial.suggest_categorical(
                "model_num_heads", [[3, 6, 12, 24], [4, 8, 16, 32]]
            ),
            "model_window_size": trial.suggest_categorical(
                "model_window_size", [[7, 7, 7], [8, 8, 8]]
            ),
            "model_dropout_rate": trial.suggest_float(
                "model_dropout_rate", 0.0, 0.3
            ),
            "model_attn_drop_rate": trial.suggest_float(
                "model_attn_drop_rate", 0.0, 0.2
            ),

            # Training parameters (similar to UNETR)
            "train_learning_rate": trial.suggest_float(
                "train_learning_rate", 1e-5, 1e-2, log=True
            ),
            "train_batch_size": trial.suggest_categorical(
                "train_batch_size", [2, 4, 8]  # Smaller for SwinUNETR
            ),
            "train_optimizer": trial.suggest_categorical(
                "train_optimizer", ["Adam", "AdamW"]
            ),
            "train_weight_decay": trial.suggest_float(
                "train_weight_decay", 1e-6, 1e-2, log=True
            ),

            # Learning rate scheduling
            "train_lr_scheduler": trial.suggest_categorical(
                "train_lr_scheduler", ["cosine", "polynomial"]
            ),
            "train_warmup_epochs": trial.suggest_int(
                "train_warmup_epochs", 0, 10
            ),

            # Data augmentation
            "data_aug_prob": trial.suggest_float(
                "data_aug_prob", 0.0, 0.8
            ),
            "data_spatial_prob": trial.suggest_float(
                "data_spatial_prob", 0.0, 0.8
            ),
            "data_intensity_prob": trial.suggest_float(
                "data_intensity_prob", 0.0, 0.8
            ),

            # Training strategy
            "train_amp": trial.suggest_categorical(
                "train_amp", [True, False]
            ),
            "train_sw_batch_size": trial.suggest_categorical(
                "train_sw_batch_size", [2, 4, 8]
            ),
            "train_infer_overlap": trial.suggest_float(
                "train_infer_overlap", 0.25, 0.75
            )
        }

        return params

    @staticmethod
    def suggest_segresnet_params(trial: optuna.Trial) -> Dict[str, Any]:
        """
        Suggest hyperparameters for SegResNet model.

        Args:
            trial: Optuna trial object

        Returns:
            Dictionary of suggested hyperparameters
        """
        params = {
            # Model architecture
            "model_arch": "segresnet",
            "model_init_filters": trial.suggest_categorical(
                "model_init_filters", [8, 16, 32]
            ),
            "model_blocks_down": trial.suggest_categorical(
                "model_blocks_down", [[1, 2, 2, 4], [2, 2, 4, 4], [1, 2, 4, 8]]
            ),
            "model_blocks_up": trial.suggest_categorical(
                "model_blocks_up", [[1, 1, 1], [2, 2, 1], [1, 2, 2]]
            ),
            "model_dropout_prob": trial.suggest_float(
                "model_dropout_prob", 0.0, 0.3
            ),

            # Training parameters
            "train_learning_rate": trial.suggest_float(
                "train_learning_rate", 1e-5, 1e-2, log=True
            ),
            "train_batch_size": trial.suggest_categorical(
                "train_batch_size", [4, 8, 16, 32]
            ),
            "train_optimizer": trial.suggest_categorical(
                "train_optimizer", ["Adam", "AdamW", "SGD"]
            ),
            "train_weight_decay": trial.suggest_float(
                "train_weight_decay", 1e-6, 1e-2, log=True
            ),
            "train_momentum": trial.suggest_float(
                "train_momentum", 0.9, 0.99
            ) if trial.params.get("train_optimizer") == "SGD" else 0.9,

            # Learning rate scheduling
            "train_lr_scheduler": trial.suggest_categorical(
                "train_lr_scheduler", ["cosine", "polynomial", "step"]
            ),
            "train_warmup_epochs": trial.suggest_int(
                "train_warmup_epochs", 0, 5
            ),

            # Data augmentation
            "data_aug_prob": trial.suggest_float(
                "data_aug_prob", 0.0, 0.8
            ),
            "data_spatial_prob": trial.suggest_float(
                "data_spatial_prob", 0.0, 0.8
            ),
            "data_intensity_prob": trial.suggest_float(
                "data_intensity_prob", 0.0, 0.8
            ),

            # Training strategy
            "train_amp": trial.suggest_categorical(
                "train_amp", [True, False]
            ),
            "train_sw_batch_size": trial.suggest_categorical(
                "train_sw_batch_size", [4, 8, 16]
            ),
            "train_infer_overlap": trial.suggest_float(
                "train_infer_overlap", 0.25, 0.75
            )
        }

        return params

    @staticmethod
    def suggest_unet_params(trial: optuna.Trial) -> Dict[str, Any]:
        """
        Suggest hyperparameters for U-Net model.

        Args:
            trial: Optuna trial object

        Returns:
            Dictionary of suggested hyperparameters
        """
        params = {
            # Model architecture
            "model_arch": "unet",
            "model_channels": trial.suggest_categorical(
                "model_channels", [[16, 32, 64, 128], [32, 64, 128, 256], [64, 128, 256, 512]]
            ),
            "model_strides": trial.suggest_categorical(
                "model_strides", [[2, 2, 2], [2, 2, 2, 2]]
            ),
            "model_num_res_units": trial.suggest_int(
                "model_num_res_units", 0, 3
            ),
            "model_dropout": trial.suggest_float(
                "model_dropout", 0.0, 0.3
            ),

            # Training parameters
            "train_learning_rate": trial.suggest_float(
                "train_learning_rate", 1e-5, 1e-2, log=True
            ),
            "train_batch_size": trial.suggest_categorical(
                "train_batch_size", [4, 8, 16, 32]
            ),
            "train_optimizer": trial.suggest_categorical(
                "train_optimizer", ["Adam", "AdamW", "SGD"]
            ),
            "train_weight_decay": trial.suggest_float(
                "train_weight_decay", 1e-6, 1e-2, log=True
            ),
            "train_momentum": trial.suggest_float(
                "train_momentum", 0.9, 0.99
            ) if trial.params.get("train_optimizer") == "SGD" else 0.9,

            # Learning rate scheduling
            "train_lr_scheduler": trial.suggest_categorical(
                "train_lr_scheduler", ["cosine", "polynomial", "step"]
            ),
            "train_warmup_epochs": trial.suggest_int(
                "train_warmup_epochs", 0, 5
            ),

            # Data augmentation
            "data_aug_prob": trial.suggest_float(
                "data_aug_prob", 0.0, 0.8
            ),
            "data_spatial_prob": trial.suggest_float(
                "data_spatial_prob", 0.0, 0.8
            ),
            "data_intensity_prob": trial.suggest_float(
                "data_intensity_prob", 0.0, 0.8
            ),

            # Training strategy
            "train_amp": trial.suggest_categorical(
                "train_amp", [True, False]
            ),
            "train_sw_batch_size": trial.suggest_categorical(
                "train_sw_batch_size", [4, 8, 16]
            ),
            "train_infer_overlap": trial.suggest_float(
                "train_infer_overlap", 0.25, 0.75
            )
        }

        return params

    @staticmethod
    def get_search_space_for_model(model_arch: str) -> callable:
        """
        Get the search space function for a specific model architecture.

        Args:
            model_arch: Model architecture name

        Returns:
            Function that suggests hyperparameters for the given architecture
        """
        search_spaces = {
            "unetr": HyperparameterSearchSpace.suggest_unetr_params,
            "swinunetr": HyperparameterSearchSpace.suggest_swinunetr_params,
            "segresnet": HyperparameterSearchSpace.suggest_segresnet_params,
            "unet": HyperparameterSearchSpace.suggest_unet_params
        }

        if model_arch.lower() not in search_spaces:
            available = ", ".join(search_spaces.keys())
            raise ValueError(f"Unknown model architecture: {model_arch}. "
                           f"Available: {available}")

        return search_spaces[model_arch.lower()]


class CustomSearchSpace:
    """
    Helper class for creating custom search spaces.
    """

    @staticmethod
    def suggest_loss_function_params(trial: optuna.Trial) -> Dict[str, Any]:
        """
        Suggest hyperparameters for loss functions.

        Args:
            trial: Optuna trial object

        Returns:
            Dictionary of loss function parameters
        """
        loss_type = trial.suggest_categorical(
            "loss_type", ["dice", "focal", "tversky", "combined"]
        )

        params = {"loss_type": loss_type}

        if loss_type == "focal":
            params.update({
                "focal_alpha": trial.suggest_float("focal_alpha", 0.25, 0.75),
                "focal_gamma": trial.suggest_float("focal_gamma", 1.0, 3.0)
            })
        elif loss_type == "tversky":
            params.update({
                "tversky_alpha": trial.suggest_float("tversky_alpha", 0.3, 0.7),
                "tversky_beta": trial.suggest_float("tversky_beta", 0.3, 0.7)
            })
        elif loss_type == "combined":
            params.update({
                "dice_weight": trial.suggest_float("dice_weight", 0.3, 0.7),
                "focal_weight": trial.suggest_float("focal_weight", 0.2, 0.5),
                "boundary_weight": trial.suggest_float("boundary_weight", 0.1, 0.3),
                "focal_alpha": trial.suggest_float("focal_alpha", 0.25, 0.75),
                "focal_gamma": trial.suggest_float("focal_gamma", 1.0, 3.0)
            })

        return params

    @staticmethod
    def suggest_augmentation_params(trial: optuna.Trial) -> Dict[str, Any]:
        """
        Suggest hyperparameters for data augmentation.

        Args:
            trial: Optuna trial object

        Returns:
            Dictionary of augmentation parameters
        """
        return {
            # Spatial augmentations
            "rotation_range": trial.suggest_float("rotation_range", 0, 30),
            "scaling_range": trial.suggest_float("scaling_range", 0.8, 1.2),
            "shearing_range": trial.suggest_float("shearing_range", 0, 10),
            "elastic_sigma": trial.suggest_float("elastic_sigma", 5, 15),
            "elastic_magnitude": trial.suggest_float("elastic_magnitude", 50, 200),

            # Intensity augmentations
            "brightness_range": trial.suggest_float("brightness_range", 0, 0.3),
            "contrast_range": trial.suggest_float("contrast_range", 0.7, 1.3),
            "gamma_range": trial.suggest_float("gamma_range", 0.7, 1.5),
            "noise_std": trial.suggest_float("noise_std", 0, 0.1),

            # Augmentation probabilities
            "spatial_prob": trial.suggest_float("spatial_prob", 0.0, 0.8),
            "intensity_prob": trial.suggest_float("intensity_prob", 0.0, 0.8),
            "elastic_prob": trial.suggest_float("elastic_prob", 0.0, 0.5)
        }


def create_combined_search_space(
    model_arch: str,
    include_loss_params: bool = True,
    include_aug_params: bool = True
) -> callable:
    """
    Create a combined search space function that includes model, loss, and augmentation parameters.

    Args:
        model_arch: Model architecture name
        include_loss_params: Whether to include loss function parameters
        include_aug_params: Whether to include augmentation parameters

    Returns:
        Function that suggests all hyperparameters
    """
    model_search_func = HyperparameterSearchSpace.get_search_space_for_model(model_arch)

    def combined_search_space(trial: optuna.Trial) -> Dict[str, Any]:
        # Get model-specific parameters
        params = model_search_func(trial)

        # Add loss function parameters
        if include_loss_params:
            loss_params = CustomSearchSpace.suggest_loss_function_params(trial)
            params.update({f"loss_{k}": v for k, v in loss_params.items()})

        # Add augmentation parameters
        if include_aug_params:
            aug_params = CustomSearchSpace.suggest_augmentation_params(trial)
            params.update({f"aug_{k}": v for k, v in aug_params.items()})

        return params

    return combined_search_space
