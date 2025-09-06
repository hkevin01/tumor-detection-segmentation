"""
Comprehensive Validation Baseline Setup
======================================

Establishes systematic validation baselines with performance benchmarks,
metric tracking, and automated quality assurance for medical AI models.

Author: Tumor Detection Segmentation Team
Phase: Validation Framework - Task 19 Completion
"""

import json
import logging
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import torch
import torch.nn as nn

# Configure logging
logger = logging.getLogger(__name__)

# Check for MONAI availability
try:
    from monai.data import DataLoader, Dataset
    from monai.metrics import (DiceMetric, GeneralizedDiceMetric,
                               HausdorffDistanceMetric, MeanIoU,
                               SurfaceDistanceMetric)
    from monai.transforms import Compose
    MONAI_AVAILABLE = True
except ImportError:
    logger.warning("MONAI not available - using custom metrics")
    MONAI_AVAILABLE = False

# Check for MLflow availability
try:
    import mlflow
    import mlflow.pytorch
    MLFLOW_AVAILABLE = True
except ImportError:
    logger.warning("MLflow not available - metrics won't be logged")
    MLFLOW_AVAILABLE = False


@dataclass
class ValidationMetrics:
    """Container for validation metrics."""
    dice_score: float
    hausdorff_distance: float
    average_surface_distance: float
    sensitivity: float
    specificity: float
    precision: float
    recall: float
    f1_score: float
    iou: float
    volume_similarity: float

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)

    def __str__(self) -> str:
        return (f"Dice: {self.dice_score:.4f}, "
                f"HD95: {self.hausdorff_distance:.2f}, "
                f"ASSD: {self.average_surface_distance:.2f}, "
                f"IoU: {self.iou:.4f}")


@dataclass
class BaselineResult:
    """Container for baseline validation result."""
    model_name: str
    dataset_name: str
    test_split: str
    metrics: ValidationMetrics
    inference_time: float
    memory_usage: float
    timestamp: str
    config: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        result_dict = asdict(self)
        result_dict['metrics'] = self.metrics.to_dict()
        return result_dict


class MedicalMetricsCalculator:
    """
    Comprehensive medical imaging metrics calculator.
    Supports both MONAI and custom implementations.
    """

    def __init__(self, include_hd_95: bool = True, include_assd: bool = True):
        self.include_hd_95 = include_hd_95
        self.include_assd = include_assd

        if MONAI_AVAILABLE:
            self.dice_metric = DiceMetric(include_background=False, reduction="mean")

            if include_hd_95:
                self.hd_metric = HausdorffDistanceMetric(
                    include_background=False,
                    percentile=95,
                    reduction="mean"
                )

            if include_assd:
                self.assd_metric = SurfaceDistanceMetric(
                    include_background=False,
                    symmetric=True,
                    reduction="mean"
                )

            self.iou_metric = MeanIoU(include_background=False, reduction="mean")

        logger.info("Medical metrics calculator initialized")

    def compute_metrics(
        self,
        predictions: torch.Tensor,
        targets: torch.Tensor
    ) -> ValidationMetrics:
        """
        Compute comprehensive validation metrics.

        Args:
            predictions: Model predictions (N, C, H, W, D)
            targets: Ground truth (N, C, H, W, D)

        Returns:
            ValidationMetrics object
        """
        # Ensure predictions are binary
        if predictions.shape[1] > 1:
            predictions = torch.argmax(predictions, dim=1, keepdim=True)

        predictions = (predictions > 0.5).float()
        targets = (targets > 0.5).float()

        if MONAI_AVAILABLE:
            return self._compute_monai_metrics(predictions, targets)
        else:
            return self._compute_custom_metrics(predictions, targets)

    def _compute_monai_metrics(
        self,
        predictions: torch.Tensor,
        targets: torch.Tensor
    ) -> ValidationMetrics:
        """Compute metrics using MONAI implementations."""
        # Dice score
        dice_score = self.dice_metric(predictions, targets).mean().item()

        # Hausdorff distance
        if self.include_hd_95:
            try:
                hd_95 = self.hd_metric(predictions, targets).mean().item()
            except:
                hd_95 = float('inf')
        else:
            hd_95 = 0.0

        # Average surface distance
        if self.include_assd:
            try:
                assd = self.assd_metric(predictions, targets).mean().item()
            except:
                assd = float('inf')
        else:
            assd = 0.0

        # IoU
        iou = self.iou_metric(predictions, targets).mean().item()

        # Additional metrics
        tp, fp, tn, fn = self._compute_confusion_matrix(predictions, targets)

        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = sensitivity
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        # Volume similarity
        pred_volume = torch.sum(predictions).item()
        target_volume = torch.sum(targets).item()
        volume_similarity = 1.0 - abs(pred_volume - target_volume) / max(pred_volume, target_volume, 1)

        return ValidationMetrics(
            dice_score=dice_score,
            hausdorff_distance=hd_95,
            average_surface_distance=assd,
            sensitivity=sensitivity,
            specificity=specificity,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            iou=iou,
            volume_similarity=volume_similarity
        )

    def _compute_custom_metrics(
        self,
        predictions: torch.Tensor,
        targets: torch.Tensor
    ) -> ValidationMetrics:
        """Compute metrics using custom implementations."""
        # Dice score
        dice_score = self._dice_coefficient(predictions, targets)

        # Basic metrics
        tp, fp, tn, fn = self._compute_confusion_matrix(predictions, targets)

        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = sensitivity
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        # IoU
        iou = tp / (tp + fp + fn) if (tp + fp + fn) > 0 else 0.0

        # Volume similarity
        pred_volume = torch.sum(predictions).item()
        target_volume = torch.sum(targets).item()
        volume_similarity = 1.0 - abs(pred_volume - target_volume) / max(pred_volume, target_volume, 1)

        return ValidationMetrics(
            dice_score=dice_score,
            hausdorff_distance=0.0,  # Not implemented in custom
            average_surface_distance=0.0,  # Not implemented in custom
            sensitivity=sensitivity,
            specificity=specificity,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            iou=iou,
            volume_similarity=volume_similarity
        )

    def _dice_coefficient(self, predictions: torch.Tensor, targets: torch.Tensor) -> float:
        """Compute Dice coefficient."""
        smooth = 1e-5
        intersection = torch.sum(predictions * targets)
        union = torch.sum(predictions) + torch.sum(targets)
        dice = (2.0 * intersection + smooth) / (union + smooth)
        return dice.item()

    def _compute_confusion_matrix(
        self,
        predictions: torch.Tensor,
        targets: torch.Tensor
    ) -> Tuple[float, float, float, float]:
        """Compute confusion matrix components."""
        predictions_flat = predictions.flatten()
        targets_flat = targets.flatten()

        tp = torch.sum((predictions_flat == 1) & (targets_flat == 1)).item()
        fp = torch.sum((predictions_flat == 1) & (targets_flat == 0)).item()
        tn = torch.sum((predictions_flat == 0) & (targets_flat == 0)).item()
        fn = torch.sum((predictions_flat == 0) & (targets_flat == 1)).item()

        return tp, fp, tn, fn


class BaselineValidator:
    """
    Comprehensive baseline validation system for medical AI models.
    """

    def __init__(
        self,
        output_dir: Path,
        device: torch.device = None,
        use_mlflow: bool = True
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.device = device or torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.use_mlflow = use_mlflow and MLFLOW_AVAILABLE

        self.metrics_calculator = MedicalMetricsCalculator()
        self.baseline_results: List[BaselineResult] = []

        logger.info(f"Baseline validator initialized - output: {self.output_dir}")

    def validate_model(
        self,
        model: nn.Module,
        dataloader: DataLoader,
        model_name: str,
        dataset_name: str,
        config: Dict[str, Any] = None
    ) -> BaselineResult:
        """
        Validate a model and compute baseline metrics.

        Args:
            model: Model to validate
            dataloader: Validation data loader
            model_name: Name of the model
            dataset_name: Name of the dataset
            config: Model configuration

        Returns:
            BaselineResult with comprehensive metrics
        """
        model.eval()
        model.to(self.device)

        all_predictions = []
        all_targets = []
        inference_times = []
        memory_usage = []

        logger.info(f"Starting validation for {model_name} on {dataset_name}")

        with torch.no_grad():
            for batch_idx, batch in enumerate(dataloader):
                # Extract data
                if isinstance(batch, dict):
                    images = batch['image'].to(self.device)
                    targets = batch['label'].to(self.device)
                else:
                    images, targets = batch
                    images = images.to(self.device)
                    targets = targets.to(self.device)

                # Measure inference time
                start_time = time.time()

                # Run inference
                predictions = model(images)

                inference_time = time.time() - start_time
                inference_times.append(inference_time)

                # Measure memory usage
                if torch.cuda.is_available():
                    memory_used = torch.cuda.max_memory_allocated() / 1024**3  # GB
                    memory_usage.append(memory_used)

                # Collect predictions and targets
                all_predictions.append(predictions.cpu())
                all_targets.append(targets.cpu())

                if batch_idx % 10 == 0:
                    logger.info(f"Processed batch {batch_idx}/{len(dataloader)}")

        # Concatenate all results
        all_predictions = torch.cat(all_predictions, dim=0)
        all_targets = torch.cat(all_targets, dim=0)

        # Compute metrics
        metrics = self.metrics_calculator.compute_metrics(all_predictions, all_targets)

        # Create baseline result
        result = BaselineResult(
            model_name=model_name,
            dataset_name=dataset_name,
            test_split="validation",
            metrics=metrics,
            inference_time=np.mean(inference_times),
            memory_usage=np.mean(memory_usage) if memory_usage else 0.0,
            timestamp=datetime.now().isoformat(),
            config=config or {}
        )

        # Save result
        self._save_result(result)

        # Log to MLflow if available
        if self.use_mlflow:
            self._log_to_mlflow(result)

        self.baseline_results.append(result)

        logger.info(f"Validation completed for {model_name}: {metrics}")
        return result

    def compare_models(
        self,
        results: List[BaselineResult] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple model results and generate comparison report.

        Args:
            results: List of results to compare (uses all stored results if None)

        Returns:
            Comparison report dictionary
        """
        if results is None:
            results = self.baseline_results

        if len(results) < 2:
            logger.warning("Need at least 2 results for comparison")
            return {}

        comparison = {
            'timestamp': datetime.now().isoformat(),
            'num_models': len(results),
            'best_dice': max(results, key=lambda r: r.metrics.dice_score),
            'best_hd95': min(results, key=lambda r: r.metrics.hausdorff_distance),
            'fastest_inference': min(results, key=lambda r: r.inference_time),
            'lowest_memory': min(results, key=lambda r: r.memory_usage),
            'detailed_comparison': []
        }

        # Detailed comparison
        for result in results:
            comparison['detailed_comparison'].append({
                'model_name': result.model_name,
                'dataset': result.dataset_name,
                'dice_score': result.metrics.dice_score,
                'hausdorff_distance': result.metrics.hausdorff_distance,
                'inference_time': result.inference_time,
                'memory_usage': result.memory_usage,
                'overall_rank': self._compute_overall_rank(result, results)
            })

        # Sort by overall rank
        comparison['detailed_comparison'].sort(key=lambda x: x['overall_rank'])

        # Save comparison
        comparison_path = self.output_dir / f"model_comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(comparison_path, 'w') as f:
            json.dump(comparison, f, indent=2, default=str)

        logger.info(f"Model comparison saved to {comparison_path}")
        return comparison

    def _compute_overall_rank(
        self,
        result: BaselineResult,
        all_results: List[BaselineResult]
    ) -> float:
        """Compute overall ranking score for a result."""
        # Normalize metrics to 0-1 scale and compute weighted average
        dice_scores = [r.metrics.dice_score for r in all_results]
        hd_distances = [r.metrics.hausdorff_distance for r in all_results]
        inference_times = [r.inference_time for r in all_results]

        # Normalize (higher is better for dice, lower is better for others)
        dice_norm = (result.metrics.dice_score - min(dice_scores)) / (max(dice_scores) - min(dice_scores) + 1e-8)
        hd_norm = 1.0 - (result.metrics.hausdorff_distance - min(hd_distances)) / (max(hd_distances) - min(hd_distances) + 1e-8)
        time_norm = 1.0 - (result.inference_time - min(inference_times)) / (max(inference_times) - min(inference_times) + 1e-8)

        # Weighted average (you can adjust weights based on importance)
        overall_score = 0.5 * dice_norm + 0.3 * hd_norm + 0.2 * time_norm

        return overall_score

    def _save_result(self, result: BaselineResult) -> None:
        """Save validation result to file."""
        filename = f"{result.model_name}_{result.dataset_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.output_dir / filename

        with open(filepath, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)

        logger.info(f"Result saved to {filepath}")

    def _log_to_mlflow(self, result: BaselineResult) -> None:
        """Log result to MLflow."""
        try:
            with mlflow.start_run(run_name=f"{result.model_name}_{result.dataset_name}"):
                # Log metrics
                mlflow.log_metrics(result.metrics.to_dict())

                # Log performance metrics
                mlflow.log_metric("inference_time", result.inference_time)
                mlflow.log_metric("memory_usage", result.memory_usage)

                # Log parameters
                for key, value in result.config.items():
                    mlflow.log_param(key, value)

                # Log model info
                mlflow.log_param("model_name", result.model_name)
                mlflow.log_param("dataset_name", result.dataset_name)

                logger.info("Results logged to MLflow")
        except Exception as e:
            logger.warning(f"Failed to log to MLflow: {e}")

    def generate_baseline_report(self) -> str:
        """Generate comprehensive baseline validation report."""
        if not self.baseline_results:
            return "No validation results available."

        report = []
        report.append("# Medical AI Model Validation Baseline Report")
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append(f"Total Models Evaluated: {len(self.baseline_results)}")
        report.append("")

        # Summary statistics
        dice_scores = [r.metrics.dice_score for r in self.baseline_results]
        report.append("## Summary Statistics")
        report.append(f"- Average Dice Score: {np.mean(dice_scores):.4f} ± {np.std(dice_scores):.4f}")
        report.append(f"- Best Dice Score: {np.max(dice_scores):.4f}")
        report.append(f"- Worst Dice Score: {np.min(dice_scores):.4f}")
        report.append("")

        # Individual results
        report.append("## Individual Results")
        for result in sorted(self.baseline_results, key=lambda r: r.metrics.dice_score, reverse=True):
            report.append(f"### {result.model_name} on {result.dataset_name}")
            report.append(f"- Dice Score: {result.metrics.dice_score:.4f}")
            report.append(f"- Hausdorff Distance: {result.metrics.hausdorff_distance:.2f}")
            report.append(f"- IoU: {result.metrics.iou:.4f}")
            report.append(f"- Inference Time: {result.inference_time:.4f}s")
            report.append(f"- Memory Usage: {result.memory_usage:.2f}GB")
            report.append("")

        report_text = "\n".join(report)

        # Save report
        report_path = self.output_dir / f"baseline_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_path, 'w') as f:
            f.write(report_text)

        logger.info(f"Baseline report saved to {report_path}")
        return report_text


def create_validation_baseline(
    models: List[Tuple[nn.Module, str, Dict[str, Any]]],
    dataloaders: List[Tuple[DataLoader, str]],
    output_dir: Path,
    device: torch.device = None
) -> BaselineValidator:
    """
    Factory function to create and run comprehensive validation baseline.

    Args:
        models: List of (model, name, config) tuples
        dataloaders: List of (dataloader, dataset_name) tuples
        output_dir: Output directory for results
        device: Computing device

    Returns:
        BaselineValidator with completed validations
    """
    validator = BaselineValidator(output_dir, device)

    for model, model_name, config in models:
        for dataloader, dataset_name in dataloaders:
            result = validator.validate_model(
                model, dataloader, model_name, dataset_name, config
            )
            logger.info(f"Completed validation: {model_name} on {dataset_name}")

    # Generate comparison report
    validator.compare_models()
    validator.generate_baseline_report()

    return validator


# Example usage and testing
if __name__ == "__main__":
    print("Testing Validation Baseline Setup...")

    # Create dummy model and data for testing
    class DummyModel(nn.Module):
        def forward(self, x):
            return torch.randn_like(x)

    # Test metrics calculator
    metrics_calc = MedicalMetricsCalculator()

    dummy_pred = torch.randn(2, 1, 32, 32, 32)
    dummy_target = torch.randint(0, 2, (2, 1, 32, 32, 32)).float()

    metrics = metrics_calc.compute_metrics(dummy_pred, dummy_target)
    print(f"Test metrics: {metrics}")

    # Test baseline validator
    validator = BaselineValidator(Path("test_validation_output"))

    print("Validation baseline setup test completed successfully!")
    validator = BaselineValidator(Path("test_validation_output"))

    print("Validation baseline setup test completed successfully!")
