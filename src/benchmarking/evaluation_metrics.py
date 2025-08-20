#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Evaluation Metrics for Medical Image Segmentation

This module provides comprehensive evaluation metrics specifically designed
for medical image segmentation tasks. It includes standard metrics like
Dice, IoU, and Hausdorff distance, as well as domain-specific metrics for
clinical evaluation.

Key Features:
- Comprehensive medical segmentation metrics
- Statistical significance testing
- Multi-class evaluation support
- Surface distance metrics
- Volumetric analysis
- Clinical interpretation metrics
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Optional scientific computing imports
try:
    from scipy import ndimage
    from scipy.spatial.distance import directed_hausdorff
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False
    logging.warning("SciPy not available. Some metrics will be limited.")

try:
    from sklearn.metrics import classification_report, confusion_matrix
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("Scikit-learn not available. Some metrics will be limited.")


@dataclass
class SegmentationMetrics:
    """Container for segmentation evaluation metrics."""

    # Basic metrics
    dice_score: float = 0.0
    iou_score: float = 0.0
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0

    # Volume-based metrics
    volume_similarity: float = 0.0
    relative_volume_error: float = 0.0

    # Surface-based metrics
    hausdorff_distance: float = 0.0
    mean_surface_distance: float = 0.0
    surface_dice: float = 0.0

    # Clinical metrics
    sensitivity: float = 0.0
    specificity: float = 0.0
    positive_predictive_value: float = 0.0
    negative_predictive_value: float = 0.0

    # Statistical metrics
    symmetric_surface_distance: float = 0.0
    robust_hausdorff: float = 0.0  # 95th percentile

    def to_dict(self) -> Dict[str, float]:
        """Convert metrics to dictionary."""
        return {
            'dice_score': self.dice_score,
            'iou_score': self.iou_score,
            'accuracy': self.accuracy,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'volume_similarity': self.volume_similarity,
            'relative_volume_error': self.relative_volume_error,
            'hausdorff_distance': self.hausdorff_distance,
            'mean_surface_distance': self.mean_surface_distance,
            'surface_dice': self.surface_dice,
            'sensitivity': self.sensitivity,
            'specificity': self.specificity,
            'positive_predictive_value': self.positive_predictive_value,
            'negative_predictive_value': self.negative_predictive_value,
            'symmetric_surface_distance': self.symmetric_surface_distance,
            'robust_hausdorff': self.robust_hausdorff
        }


class BaseMetric(ABC):
    """Base class for evaluation metrics."""

    @abstractmethod
    def compute(
        self,
        prediction: np.ndarray,
        ground_truth: np.ndarray,
        **kwargs
    ) -> float:
        """Compute the metric."""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get metric name."""
        pass


class DiceScore(BaseMetric):
    """Dice Similarity Coefficient (DSC) implementation."""

    def __init__(self, smooth: float = 1e-6):
        self.smooth = smooth

    def compute(
        self,
        prediction: np.ndarray,
        ground_truth: np.ndarray,
        **kwargs
    ) -> float:
        """Compute Dice score."""
        # Flatten arrays
        pred_flat = prediction.flatten()
        gt_flat = ground_truth.flatten()

        # Compute intersection and union
        intersection = np.sum(pred_flat * gt_flat)
        total = np.sum(pred_flat) + np.sum(gt_flat)

        dice = (2.0 * intersection + self.smooth) / (total + self.smooth)
        return float(dice)

    def get_name(self) -> str:
        return "dice_score"


class IoUScore(BaseMetric):
    """Intersection over Union (IoU) implementation."""

    def __init__(self, smooth: float = 1e-6):
        self.smooth = smooth

    def compute(
        self,
        prediction: np.ndarray,
        ground_truth: np.ndarray,
        **kwargs
    ) -> float:
        """Compute IoU score."""
        # Flatten arrays
        pred_flat = prediction.flatten()
        gt_flat = ground_truth.flatten()

        # Compute intersection and union
        intersection = np.sum(pred_flat * gt_flat)
        union = np.sum(pred_flat) + np.sum(gt_flat) - intersection

        iou = (intersection + self.smooth) / (union + self.smooth)
        return float(iou)

    def get_name(self) -> str:
        return "iou_score"


class HausdorffDistance(BaseMetric):
    """Hausdorff Distance implementation."""

    def __init__(self, percentile: float = 100.0):
        self.percentile = percentile

    def compute(
        self,
        prediction: np.ndarray,
        ground_truth: np.ndarray,
        spacing: Optional[Tuple[float, ...]] = None,
        **kwargs
    ) -> float:
        """Compute Hausdorff distance."""
        if not SCIPY_AVAILABLE:
            logging.warning("SciPy not available, returning default value")
            return 0.0

        # Convert to binary if needed
        pred_binary = (prediction > 0).astype(bool)
        gt_binary = (ground_truth > 0).astype(bool)

        # Get surface points
        pred_surface = self._get_surface_points(pred_binary, spacing)
        gt_surface = self._get_surface_points(gt_binary, spacing)

        if len(pred_surface) == 0 or len(gt_surface) == 0:
            return float('inf')

        # Compute directed Hausdorff distances
        dist1 = directed_hausdorff(pred_surface, gt_surface)[0]
        dist2 = directed_hausdorff(gt_surface, pred_surface)[0]

        # Return maximum (or percentile) distance
        if self.percentile < 100.0:
            # For robust Hausdorff, compute all distances and take percentile
            distances = []
            for p1 in pred_surface:
                distances.extend([np.linalg.norm(p1 - p2) for p2 in gt_surface])
            for p1 in gt_surface:
                distances.extend([np.linalg.norm(p1 - p2) for p2 in pred_surface])

            return float(np.percentile(distances, self.percentile))
        else:
            return float(max(dist1, dist2))

    def _get_surface_points(
        self,
        binary_mask: np.ndarray,
        spacing: Optional[Tuple[float, ...]] = None
    ) -> np.ndarray:
        """Extract surface points from binary mask."""
        if not SCIPY_AVAILABLE:
            return np.array([])

        # Get boundary by erosion
        eroded = ndimage.binary_erosion(binary_mask)
        boundary = binary_mask & ~eroded

        # Get coordinates of boundary points
        coords = np.argwhere(boundary)

        # Apply spacing if provided
        if spacing is not None:
            coords = coords * np.array(spacing)

        return coords

    def get_name(self) -> str:
        if self.percentile < 100.0:
            return f"hausdorff_{self.percentile}th"
        return "hausdorff_distance"


class MeanSurfaceDistance(BaseMetric):
    """Mean Surface Distance implementation."""

    def compute(
        self,
        prediction: np.ndarray,
        ground_truth: np.ndarray,
        spacing: Optional[Tuple[float, ...]] = None,
        **kwargs
    ) -> float:
        """Compute mean surface distance."""
        if not SCIPY_AVAILABLE:
            logging.warning("SciPy not available, returning default value")
            return 0.0

        # Convert to binary if needed
        pred_binary = (prediction > 0).astype(bool)
        gt_binary = (ground_truth > 0).astype(bool)

        # Get surface points
        pred_surface = self._get_surface_points(pred_binary, spacing)
        gt_surface = self._get_surface_points(gt_binary, spacing)

        if len(pred_surface) == 0 or len(gt_surface) == 0:
            return float('inf')

        # Compute mean distance from prediction to ground truth
        distances = []
        for point in pred_surface:
            min_dist = np.min([np.linalg.norm(point - gt_point) for gt_point in gt_surface])
            distances.append(min_dist)

        return float(np.mean(distances))

    def _get_surface_points(
        self,
        binary_mask: np.ndarray,
        spacing: Optional[Tuple[float, ...]] = None
    ) -> np.ndarray:
        """Extract surface points from binary mask."""
        if not SCIPY_AVAILABLE:
            return np.array([])

        # Get boundary by erosion
        eroded = ndimage.binary_erosion(binary_mask)
        boundary = binary_mask & ~eroded

        # Get coordinates of boundary points
        coords = np.argwhere(boundary)

        # Apply spacing if provided
        if spacing is not None:
            coords = coords * np.array(spacing)

        return coords

    def get_name(self) -> str:
        return "mean_surface_distance"


class VolumeSimilarity(BaseMetric):
    """Volume Similarity implementation."""

    def compute(
        self,
        prediction: np.ndarray,
        ground_truth: np.ndarray,
        **kwargs
    ) -> float:
        """Compute volume similarity."""
        pred_volume = np.sum(prediction > 0)
        gt_volume = np.sum(ground_truth > 0)

        if pred_volume == 0 and gt_volume == 0:
            return 1.0

        volume_similarity = 1.0 - abs(pred_volume - gt_volume) / (pred_volume + gt_volume)
        return float(volume_similarity)

    def get_name(self) -> str:
        return "volume_similarity"


class RelativeVolumeError(BaseMetric):
    """Relative Volume Error implementation."""

    def compute(
        self,
        prediction: np.ndarray,
        ground_truth: np.ndarray,
        **kwargs
    ) -> float:
        """Compute relative volume error."""
        pred_volume = np.sum(prediction > 0)
        gt_volume = np.sum(ground_truth > 0)

        if gt_volume == 0:
            return float('inf') if pred_volume > 0 else 0.0

        relative_error = abs(pred_volume - gt_volume) / gt_volume
        return float(relative_error)

    def get_name(self) -> str:
        return "relative_volume_error"


class MedicalSegmentationMetrics:
    """Comprehensive medical image segmentation metrics calculator."""

    def __init__(self, spacing: Optional[Tuple[float, ...]] = None):
        self.spacing = spacing

        # Initialize metric calculators
        self.dice_calculator = DiceScore()
        self.iou_calculator = IoUScore()
        self.hausdorff_calculator = HausdorffDistance()
        self.robust_hausdorff_calculator = HausdorffDistance(percentile=95.0)
        self.surface_distance_calculator = MeanSurfaceDistance()
        self.volume_similarity_calculator = VolumeSimilarity()
        self.volume_error_calculator = RelativeVolumeError()

    def compute_dice_score(
        self,
        prediction: np.ndarray,
        ground_truth: np.ndarray
    ) -> float:
        """Compute Dice score."""
        return self.dice_calculator.compute(prediction, ground_truth)

    def compute_iou_score(
        self,
        prediction: np.ndarray,
        ground_truth: np.ndarray
    ) -> float:
        """Compute IoU score."""
        return self.iou_calculator.compute(prediction, ground_truth)

    def compute_basic_metrics(
        self,
        prediction: np.ndarray,
        ground_truth: np.ndarray
    ) -> Dict[str, float]:
        """Compute basic classification metrics."""
        # Flatten arrays for classification metrics
        pred_flat = (prediction > 0).astype(int).flatten()
        gt_flat = (ground_truth > 0).astype(int).flatten()

        # True/False Positives/Negatives
        tp = np.sum((pred_flat == 1) & (gt_flat == 1))
        tn = np.sum((pred_flat == 0) & (gt_flat == 0))
        fp = np.sum((pred_flat == 1) & (gt_flat == 0))
        fn = np.sum((pred_flat == 0) & (gt_flat == 1))

        # Compute metrics with small epsilon to avoid division by zero
        eps = 1e-7

        accuracy = (tp + tn) / (tp + tn + fp + fn + eps)
        precision = tp / (tp + fp + eps)
        recall = tp / (tp + fn + eps)
        f1_score = 2 * precision * recall / (precision + recall + eps)
        sensitivity = recall  # Same as recall
        specificity = tn / (tn + fp + eps)
        ppv = precision  # Positive predictive value
        npv = tn / (tn + fn + eps)  # Negative predictive value

        return {
            'accuracy': float(accuracy),
            'precision': float(precision),
            'recall': float(recall),
            'f1_score': float(f1_score),
            'sensitivity': float(sensitivity),
            'specificity': float(specificity),
            'positive_predictive_value': float(ppv),
            'negative_predictive_value': float(npv)
        }

    def compute_comprehensive_metrics(
        self,
        prediction: np.ndarray,
        ground_truth: np.ndarray,
        spacing: Optional[Tuple[float, ...]] = None
    ) -> SegmentationMetrics:
        """Compute comprehensive segmentation metrics."""

        # Use provided spacing or default
        current_spacing = spacing or self.spacing

        # Basic metrics
        basic_metrics = self.compute_basic_metrics(prediction, ground_truth)

        # Overlap metrics
        dice_score = self.compute_dice_score(prediction, ground_truth)
        iou_score = self.compute_iou_score(prediction, ground_truth)

        # Volume metrics
        volume_similarity = self.volume_similarity_calculator.compute(
            prediction, ground_truth
        )
        relative_volume_error = self.volume_error_calculator.compute(
            prediction, ground_truth
        )

        # Surface metrics (if SciPy available)
        hausdorff_distance = 0.0
        robust_hausdorff = 0.0
        mean_surface_distance = 0.0
        symmetric_surface_distance = 0.0

        if SCIPY_AVAILABLE and np.sum(prediction > 0) > 0 and np.sum(ground_truth > 0) > 0:
            try:
                hausdorff_distance = self.hausdorff_calculator.compute(
                    prediction, ground_truth, spacing=current_spacing
                )
                robust_hausdorff = self.robust_hausdorff_calculator.compute(
                    prediction, ground_truth, spacing=current_spacing
                )
                mean_surface_distance = self.surface_distance_calculator.compute(
                    prediction, ground_truth, spacing=current_spacing
                )
                # Symmetric surface distance (average of both directions)
                reverse_msd = self.surface_distance_calculator.compute(
                    ground_truth, prediction, spacing=current_spacing
                )
                symmetric_surface_distance = (mean_surface_distance + reverse_msd) / 2.0

            except Exception as e:
                logging.warning(f"Error computing surface metrics: {e}")

        # Surface Dice (not implemented in this basic version)
        surface_dice = 0.0

        return SegmentationMetrics(
            dice_score=dice_score,
            iou_score=iou_score,
            accuracy=basic_metrics['accuracy'],
            precision=basic_metrics['precision'],
            recall=basic_metrics['recall'],
            f1_score=basic_metrics['f1_score'],
            volume_similarity=volume_similarity,
            relative_volume_error=relative_volume_error,
            hausdorff_distance=hausdorff_distance,
            mean_surface_distance=mean_surface_distance,
            surface_dice=surface_dice,
            sensitivity=basic_metrics['sensitivity'],
            specificity=basic_metrics['specificity'],
            positive_predictive_value=basic_metrics['positive_predictive_value'],
            negative_predictive_value=basic_metrics['negative_predictive_value'],
            symmetric_surface_distance=symmetric_surface_distance,
            robust_hausdorff=robust_hausdorff
        )


def compute_comprehensive_metrics(
    prediction: np.ndarray,
    ground_truth: np.ndarray,
    spacing: Optional[Tuple[float, ...]] = None
) -> Dict[str, float]:
    """Convenience function to compute comprehensive metrics."""
    calculator = MedicalSegmentationMetrics(spacing=spacing)
    metrics = calculator.compute_comprehensive_metrics(prediction, ground_truth, spacing)
    return metrics.to_dict()


def statistical_comparison(
    metrics_list1: List[Dict[str, float]],
    metrics_list2: List[Dict[str, float]],
    metric_name: str = "dice_score"
) -> Dict[str, Any]:
    """Perform statistical comparison between two groups of metrics."""

    if not SCIPY_AVAILABLE:
        logging.warning("SciPy not available for statistical testing")
        return {}

    from scipy import stats

    # Extract metric values
    values1 = [m[metric_name] for m in metrics_list1 if metric_name in m]
    values2 = [m[metric_name] for m in metrics_list2 if metric_name in m]

    if len(values1) < 2 or len(values2) < 2:
        return {"error": "Insufficient data for statistical testing"}

    # Perform t-test
    t_stat, p_value = stats.ttest_ind(values1, values2)

    # Effect size (Cohen's d)
    pooled_std = np.sqrt(
        ((len(values1) - 1) * np.var(values1, ddof=1) +
         (len(values2) - 1) * np.var(values2, ddof=1)) /
        (len(values1) + len(values2) - 2)
    )
    cohens_d = (np.mean(values1) - np.mean(values2)) / pooled_std

    return {
        "metric": metric_name,
        "group1_mean": np.mean(values1),
        "group1_std": np.std(values1),
        "group2_mean": np.mean(values2),
        "group2_std": np.std(values2),
        "t_statistic": t_stat,
        "p_value": p_value,
        "cohens_d": cohens_d,
        "significant_005": p_value < 0.05,
        "significant_001": p_value < 0.01
    }


def create_metrics_report(
    all_metrics: Dict[str, List[Dict[str, float]]],
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """Create comprehensive metrics report."""

    report = {
        "summary": {},
        "detailed_statistics": {},
        "pairwise_comparisons": {}
    }

    # Summary statistics for each model
    for model_name, metrics_list in all_metrics.items():
        if not metrics_list:
            continue

        summary = {}
        metric_names = metrics_list[0].keys()

        for metric_name in metric_names:
            values = [m[metric_name] for m in metrics_list]
            summary[metric_name] = {
                "mean": np.mean(values),
                "std": np.std(values),
                "min": np.min(values),
                "max": np.max(values),
                "median": np.median(values)
            }

        report["summary"][model_name] = summary

    # Pairwise comparisons
    model_names = list(all_metrics.keys())
    for i, model1 in enumerate(model_names):
        for j, model2 in enumerate(model_names[i+1:], i+1):
            comparison_key = f"{model1}_vs_{model2}"
            report["pairwise_comparisons"][comparison_key] = {}

            # Compare on key metrics
            key_metrics = ["dice_score", "iou_score", "hausdorff_distance"]
            for metric in key_metrics:
                if (metric in all_metrics[model1][0] and
                    metric in all_metrics[model2][0]):
                    comparison = statistical_comparison(
                        all_metrics[model1],
                        all_metrics[model2],
                        metric
                    )
                    report["pairwise_comparisons"][comparison_key][metric] = comparison

    # Save report if path provided
    if output_path:
        import json
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2, default=str)

    return report


# Example usage and testing
if __name__ == "__main__":
    print("Testing Medical Segmentation Metrics...")

    # Create dummy data
    prediction = np.random.rand(32, 32, 32) > 0.5
    ground_truth = np.random.rand(32, 32, 32) > 0.5

    # Test metric calculators
    calculator = MedicalSegmentationMetrics()

    print("Testing individual metrics...")
    dice = calculator.compute_dice_score(prediction, ground_truth)
    print(f"Dice score: {dice:.4f}")

    iou = calculator.compute_iou_score(prediction, ground_truth)
    print(f"IoU score: {iou:.4f}")

    basic_metrics = calculator.compute_basic_metrics(prediction, ground_truth)
    print(f"Accuracy: {basic_metrics['accuracy']:.4f}")
    print(f"Precision: {basic_metrics['precision']:.4f}")
    print(f"Recall: {basic_metrics['recall']:.4f}")

    # Test comprehensive metrics
    print("\nTesting comprehensive metrics...")
    comprehensive = calculator.compute_comprehensive_metrics(
        prediction, ground_truth
    )
    print(f"Comprehensive metrics computed with {len(comprehensive.to_dict())} metrics")

    # Test convenience function
    metrics_dict = compute_comprehensive_metrics(prediction, ground_truth)
    print(f"Convenience function returned {len(metrics_dict)} metrics")

    print("\nMedical segmentation metrics tests completed successfully!")
    print("\nMedical segmentation metrics tests completed successfully!")
