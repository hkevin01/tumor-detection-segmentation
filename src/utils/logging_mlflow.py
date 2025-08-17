#!/usr/bin/env python3
"""
MLflow experiment tracking for medical imaging experiments
Provides comprehensive logging for model training, evaluation, and artifacts
"""

import json
import logging
import os
import tempfile
import warnings
from typing import Any, Dict, List, Optional

import numpy as np
import torch

try:
    import mlflow
    import mlflow.pytorch
    from mlflow.tracking import MlflowClient
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False
    warnings.warn("MLflow not available. Install with: pip install mlflow")

try:
    from monai.metrics import DiceMetric, HausdorffDistanceMetric
    MONAI_AVAILABLE = True
except ImportError:
    MONAI_AVAILABLE = False

logger = logging.getLogger(__name__)


class MedicalImagingMLflowLogger:
    """
    MLflow logger specifically designed for medical imaging experiments

    Features:
    - Automatic metric tracking (Dice, HD95, etc.)
    - Model artifact logging
    - Segmentation mask artifacts
    - Dataset tracking
    - Hyperparameter optimization integration
    """

    def __init__(
        self,
        experiment_name: str = "medical_imaging_experiments",
        tracking_uri: str = None,
        artifact_location: str = None,
        tags: Dict[str, str] = None,
    ):
        if not MLFLOW_AVAILABLE:
            raise ImportError("MLflow is required. Install with: pip install mlflow")

        # Set tracking URI
        if tracking_uri:
            mlflow.set_tracking_uri(tracking_uri)
        elif "MLFLOW_TRACKING_URI" not in os.environ:
            # Default to local directory
            mlflow.set_tracking_uri("file:./mlruns")

        # Set or create experiment
        try:
            self.experiment = mlflow.get_experiment_by_name(experiment_name)
            if self.experiment is None:
                experiment_id = mlflow.create_experiment(
                    experiment_name,
                    artifact_location=artifact_location
                )
                self.experiment = mlflow.get_experiment(experiment_id)
        except Exception as e:
            logger.warning(f"Could not set up MLflow experiment: {e}")
            self.experiment = None

        self.client = MlflowClient()
        self.current_run = None
        self.default_tags = tags or {}

        # Initialize metrics calculators if MONAI is available
        if MONAI_AVAILABLE:
            self.dice_metric = DiceMetric(include_background=False, reduction="mean")
            self.hd_metric = HausdorffDistanceMetric(
                include_background=False,
                reduction="mean",
                percentile=95
            )

    def start_run(
        self,
        run_name: str = None,
        tags: Dict[str, str] = None,
        nested: bool = False,
    ) -> mlflow.ActiveRun:
        """Start a new MLflow run"""
        if not MLFLOW_AVAILABLE:
            return None

        # Combine default tags with run-specific tags
        all_tags = {**self.default_tags}
        if tags:
            all_tags.update(tags)

        self.current_run = mlflow.start_run(
            run_name=run_name,
            experiment_id=self.experiment.experiment_id if self.experiment else None,
            tags=all_tags,
            nested=nested,
        )

        return self.current_run

    def end_run(self):
        """End the current MLflow run"""
        if MLFLOW_AVAILABLE and self.current_run:
            mlflow.end_run()
            self.current_run = None

    def log_hyperparameters(self, params: Dict[str, Any]):
        """Log hyperparameters"""
        if not MLFLOW_AVAILABLE:
            return

        # Convert complex objects to strings
        clean_params = {}
        for key, value in params.items():
            if isinstance(value, (dict, list)):
                clean_params[key] = json.dumps(value)
            elif isinstance(value, (torch.dtype, type)):
                clean_params[key] = str(value)
            else:
                clean_params[key] = value

        mlflow.log_params(clean_params)

    def log_metrics(
        self,
        metrics: Dict[str, float],
        step: Optional[int] = None,
        epoch: Optional[int] = None,
    ):
        """Log metrics with optional step/epoch"""
        if not MLFLOW_AVAILABLE:
            return

        if epoch is not None and step is None:
            step = epoch

        for key, value in metrics.items():
            if isinstance(value, (int, float)) and not np.isnan(value):
                mlflow.log_metric(key, value, step=step)

    def log_segmentation_metrics(
        self,
        predictions: torch.Tensor,
        targets: torch.Tensor,
        class_names: List[str] = None,
        step: Optional[int] = None,
    ):
        """Log comprehensive segmentation metrics"""
        if not MLFLOW_AVAILABLE or not MONAI_AVAILABLE:
            return

        class_names = class_names or [f"class_{i}" for i in range(predictions.shape[1])]

        # Calculate Dice scores
        self.dice_metric(predictions, targets)
        dice_scores = self.dice_metric.aggregate()

        # Calculate Hausdorff distances
        try:
            self.hd_metric(predictions, targets)
            hd_scores = self.hd_metric.aggregate()
        except Exception:
            hd_scores = torch.zeros_like(dice_scores)

        # Log per-class metrics
        metrics = {}
        for i, class_name in enumerate(class_names):
            if i < len(dice_scores):
                metrics[f"dice_{class_name}"] = dice_scores[i].item()
            if i < len(hd_scores):
                metrics[f"hd95_{class_name}"] = hd_scores[i].item()

        # Log average metrics
        metrics["dice_mean"] = dice_scores.mean().item()
        metrics["hd95_mean"] = hd_scores.mean().item()

        self.log_metrics(metrics, step=step)

        # Reset metrics for next calculation
        self.dice_metric.reset()
        self.hd_metric.reset()

    def log_model(
        self,
        model: torch.nn.Module,
        model_name: str = "model",
        input_example: torch.Tensor = None,
        conda_env: str = None,
    ):
        """Log PyTorch model"""
        if not MLFLOW_AVAILABLE:
            return

        # Create conda environment if not provided
        if conda_env is None:
            conda_env = {
                "channels": ["pytorch", "conda-forge"],
                "dependencies": [
                    "python=3.9",
                    "pytorch",
                    "torchvision",
                    "monai",
                    "numpy",
                    "scikit-learn",
                ],
                "pip": [
                    "mlflow",
                ]
            }

        mlflow.pytorch.log_model(
            pytorch_model=model,
            artifact_path=model_name,
            conda_env=conda_env,
            input_example=input_example,
        )

    def log_artifact(self, path: str, artifact_path: str = None):
        """Log a single artifact file or directory."""
        if not MLFLOW_AVAILABLE:
            return
        try:
            mlflow.log_artifact(path, artifact_path)
        except Exception as e:
            logger.warning(f"Could not log artifact {path}: {e}")

    def log_checkpoint(self, checkpoint_path: str, name: str = "checkpoints"):
        """Log a checkpoint file under a named artifact path."""
        self.log_artifact(checkpoint_path, artifact_path=name)

    def log_segmentation_overlay(
        self,
        image: np.ndarray,
        prediction: np.ndarray,
        target: Optional[np.ndarray] = None,
        slice_idx: int = None,
        artifact_name: str = "segmentation_overlay",
    ):
        """Log segmentation overlay visualization"""
        if not MLFLOW_AVAILABLE:
            return

        try:
            import matplotlib.pyplot as plt
            from matplotlib.colors import ListedColormap

            # Select middle slice if not specified
            if slice_idx is None:
                slice_idx = image.shape[-1] // 2

            # Create figure
            fig, axes = plt.subplots(1, 3 if target is not None else 2, figsize=(15, 5))
            if target is None:
                axes = [axes[0], axes[1]]

            # Display image
            axes[0].imshow(image[..., slice_idx], cmap="gray")
            axes[0].set_title("Original Image")
            axes[0].axis("off")

            # Display prediction overlay
            axes[1].imshow(image[..., slice_idx], cmap="gray")
            pred_masked = np.ma.masked_where(
                prediction[..., slice_idx] == 0, prediction[..., slice_idx]
            )
            axes[1].imshow(pred_masked, alpha=0.5, cmap="viridis")
            axes[1].set_title("Prediction Overlay")
            axes[1].axis("off")

            # Display target overlay if available
            if target is not None:
                axes[2].imshow(image[..., slice_idx], cmap="gray")
                target_masked = np.ma.masked_where(
                    target[..., slice_idx] == 0, target[..., slice_idx]
                )
                axes[2].imshow(target_masked, alpha=0.5, cmap="plasma")
                axes[2].set_title("Ground Truth Overlay")
                axes[2].axis("off")

            plt.tight_layout()

            # Save and log
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                plt.savefig(tmp.name, dpi=150, bbox_inches="tight")
                mlflow.log_artifact(tmp.name, artifact_name)
                os.unlink(tmp.name)

            plt.close(fig)

        except ImportError:
            logger.warning("Matplotlib not available for visualization")
        except Exception as e:
            logger.warning(f"Could not create segmentation overlay: {e}")

    def log_dataset_info(
        self,
        dataset_config: Dict[str, Any],
        train_size: int = None,
        val_size: int = None,
        test_size: int = None,
    ):
        """Log dataset information"""
        if not MLFLOW_AVAILABLE:
            return

        # Log dataset configuration
        self.log_hyperparameters({"dataset_config": dataset_config})

        # Log dataset sizes
        if train_size is not None:
            mlflow.log_metric("dataset_train_size", train_size)
        if val_size is not None:
            mlflow.log_metric("dataset_val_size", val_size)
        if test_size is not None:
            mlflow.log_metric("dataset_test_size", test_size)

    def log_training_config(
        self,
        model_config: Dict[str, Any],
        training_config: Dict[str, Any],
        optimizer_config: Dict[str, Any] = None,
    ):
        """Log comprehensive training configuration"""
        if not MLFLOW_AVAILABLE:
            return

        # Log all configurations
        configs = {
            "model": model_config,
            "training": training_config,
        }

        if optimizer_config:
            configs["optimizer"] = optimizer_config

        for config_type, config in configs.items():
            for key, value in config.items():
                param_key = f"{config_type}_{key}"
                if isinstance(value, (dict, list)):
                    self.log_hyperparameters({param_key: json.dumps(value)})
                else:
                    self.log_hyperparameters({param_key: value})

    def log_system_info(self):
        """Log system information"""
        if not MLFLOW_AVAILABLE:
            return

        import platform

        import psutil

        system_info = {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "cpu_count": psutil.cpu_count(),
            "memory_gb": psutil.virtual_memory().total / 1e9,
        }

        # GPU information
        if torch.cuda.is_available():
            system_info.update({
                "cuda_available": True,
                "cuda_version": torch.version.cuda,
                "gpu_count": torch.cuda.device_count(),
                "gpu_name": torch.cuda.get_device_name(0),
            })
        else:
            system_info["cuda_available"] = False

        self.log_hyperparameters(system_info)

    def create_nested_run(self, run_name: str, tags: Dict[str, str] = None):
        """Create a nested run (useful for hyperparameter optimization)"""
        return self.start_run(run_name=run_name, tags=tags, nested=True)

    def log_confusion_matrix(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        class_names: List[str] = None,
        artifact_name: str = "confusion_matrix",
    ):
        """Log confusion matrix visualization"""
        if not MLFLOW_AVAILABLE:
            return

        try:
            import matplotlib.pyplot as plt
            import seaborn as sns
            from sklearn.metrics import confusion_matrix

            # Calculate confusion matrix
            cm = confusion_matrix(y_true.flatten(), y_pred.flatten())

            # Create visualization
            plt.figure(figsize=(10, 8))
            sns.heatmap(
                cm,
                annot=True,
                fmt="d",
                cmap="Blues",
                xticklabels=class_names or range(cm.shape[1]),
                yticklabels=class_names or range(cm.shape[0]),
            )
            plt.title("Confusion Matrix")
            plt.xlabel("Predicted")
            plt.ylabel("Actual")

            # Save and log
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                plt.savefig(tmp.name, dpi=150, bbox_inches="tight")
                mlflow.log_artifact(tmp.name, artifact_name)
                os.unlink(tmp.name)

            plt.close()

        except ImportError:
            logger.warning("Required packages not available for confusion matrix")
        except Exception as e:
            logger.warning(f"Could not create confusion matrix: {e}")


def setup_mlflow_tracking(
    experiment_name: str = "medical_imaging",
    tracking_uri: str = None,
    artifact_location: str = None,
) -> MedicalImagingMLflowLogger:
    """
    Setup MLflow tracking for medical imaging experiments

    Args:
        experiment_name: Name of the MLflow experiment
        tracking_uri: MLflow tracking server URI
        artifact_location: Location to store artifacts

    Returns:
        Configured MLflow logger
    """
    return MedicalImagingMLflowLogger(
        experiment_name=experiment_name,
        tracking_uri=tracking_uri,
        artifact_location=artifact_location,
        tags={
            "project": "tumor_detection_segmentation",
            "framework": "monai",
            "domain": "medical_imaging",
        }
    )


if __name__ == "__main__":
    print("MLflow Experiment Tracking for Medical Imaging")
    print("=" * 50)

    if not MLFLOW_AVAILABLE:
        print("❌ MLflow not available. Please install with: pip install mlflow")
        exit(1)

    # Test MLflow logger
    logger_instance = setup_mlflow_tracking("test_experiment")

    # Start a test run
    with logger_instance.start_run("test_run"):
        # Log test parameters
        logger_instance.log_hyperparameters({
            "model": "unet",
            "batch_size": 2,
            "learning_rate": 0.001,
            "spatial_size": [96, 96, 96],
        })

        # Log test metrics
        logger_instance.log_metrics({
            "dice_score": 0.85,
            "hausdorff_distance": 2.5,
            "loss": 0.15,
        }, step=1)

        # Log system info
        logger_instance.log_system_info()

        print("✅ Test run logged successfully!")

    print(f"📊 Check your MLflow UI at: {mlflow.get_tracking_uri()}")
    print("   Run: mlflow ui --port 5000")
    print("   Run: mlflow ui --port 5000")
