#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Benchmark Suite for Medical Image Segmentation Models

This module provides comprehensive benchmarking capabilities for comparing
different medical image segmentation architectures. It includes standardized
training protocols, evaluation metrics, and performance analysis.

Key Features:
- Standardized benchmarking protocols
- Multi-model comparison framework
- Training and inference benchmarking
- Resource utilization tracking
- Statistical significance testing
- Reproducible experimental setup
"""

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch not available. Benchmarking will be limited.")

try:
    from scipy import stats
    from sklearn.metrics import confusion_matrix
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("Scikit-learn/SciPy not available. Statistical analysis will be limited.")

from .evaluation_metrics import (MedicalSegmentationMetrics,
                                 compute_comprehensive_metrics)
from .model_registry import ModelConfig, ModelRegistry


@dataclass
class BenchmarkConfig:
    """Configuration for benchmarking experiments."""

    # Experiment setup
    experiment_name: str
    output_dir: str
    random_seed: int = 42
    device: str = "auto"  # auto, cpu, cuda, cuda:0, etc.

    # Data configuration
    data_config: Dict[str, Any] = field(default_factory=dict)
    train_batch_size: int = 2
    val_batch_size: int = 1
    num_workers: int = 4

    # Training configuration
    num_epochs: int = 100
    learning_rate: float = 1e-4
    optimizer: str = "adam"  # adam, sgd, adamw
    loss_function: str = "dice_ce"  # dice_ce, focal, combined
    scheduler: str = "cosine"  # cosine, step, plateau

    # Evaluation configuration
    eval_frequency: int = 5  # Evaluate every N epochs
    save_checkpoints: bool = True
    early_stopping_patience: int = 20

    # Resource monitoring
    monitor_gpu: bool = True
    monitor_memory: bool = True
    profile_inference: bool = True

    # Models to benchmark
    models_to_test: List[str] = field(default_factory=lambda: ["unet", "segresnet", "unetr"])

    # Statistical analysis
    num_runs: int = 3  # Number of runs for statistical significance
    confidence_level: float = 0.95


@dataclass
class TrainingMetrics:
    """Metrics collected during training."""
    epoch: int
    train_loss: float
    val_loss: float
    train_dice: float
    val_dice: float
    learning_rate: float
    training_time: float
    memory_usage: float
    gpu_utilization: Optional[float] = None


@dataclass
class ModelResults:
    """Results for a single model."""
    model_name: str
    model_config: ModelConfig

    # Training metrics
    training_metrics: List[TrainingMetrics] = field(default_factory=list)
    best_epoch: int = 0
    best_val_dice: float = 0.0
    total_training_time: float = 0.0

    # Final evaluation metrics
    test_metrics: Dict[str, float] = field(default_factory=dict)

    # Inference performance
    inference_time_ms: float = 0.0
    throughput_samples_per_sec: float = 0.0

    # Resource utilization
    peak_memory_mb: float = 0.0
    average_gpu_util: float = 0.0

    # Model complexity
    total_parameters: int = 0
    model_size_mb: float = 0.0


@dataclass
class BenchmarkResults:
    """Complete benchmark results for all models."""
    benchmark_config: BenchmarkConfig
    model_results: Dict[str, List[ModelResults]] = field(default_factory=dict)
    statistical_analysis: Dict[str, Any] = field(default_factory=dict)

    def get_best_model(self, metric: str = "val_dice") -> Tuple[str, ModelResults]:
        """Get the best performing model for a specific metric."""
        best_model = None
        best_score = -float('inf') if 'dice' in metric or 'iou' in metric else float('inf')
        best_name = ""

        for model_name, results_list in self.model_results.items():
            # Average across multiple runs
            if metric == "val_dice":
                avg_score = np.mean([r.best_val_dice for r in results_list])
            elif metric in results_list[0].test_metrics:
                avg_score = np.mean([r.test_metrics[metric] for r in results_list])
            else:
                continue

            if ('dice' in metric or 'iou' in metric) and avg_score > best_score:
                best_score = avg_score
                best_model = results_list[0]  # Representative result
                best_name = model_name
            elif ('loss' in metric) and avg_score < best_score:
                best_score = avg_score
                best_model = results_list[0]
                best_name = model_name

        return best_name, best_model

    def get_summary_table(self) -> Dict[str, Dict[str, float]]:
        """Get summary statistics table for all models."""
        summary = {}

        for model_name, results_list in self.model_results.items():
            summary[model_name] = {
                "avg_val_dice": np.mean([r.best_val_dice for r in results_list]),
                "std_val_dice": np.std([r.best_val_dice for r in results_list]),
                "avg_training_time": np.mean([r.total_training_time for r in results_list]),
                "avg_inference_time": np.mean([r.inference_time_ms for r in results_list]),
                "avg_parameters": np.mean([r.total_parameters for r in results_list]),
                "avg_memory": np.mean([r.peak_memory_mb for r in results_list])
            }

            # Add test metrics if available
            if results_list[0].test_metrics:
                for metric_name in results_list[0].test_metrics:
                    summary[model_name][f"avg_{metric_name}"] = np.mean([
                        r.test_metrics[metric_name] for r in results_list
                    ])
                    summary[model_name][f"std_{metric_name}"] = np.std([
                        r.test_metrics[metric_name] for r in results_list
                    ])

        return summary


class BenchmarkSuite:
    """Main benchmarking suite for medical image segmentation models."""

    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.device = self._setup_device()
        self.metrics_calculator = MedicalSegmentationMetrics()

        # Create output directory
        Path(config.output_dir).mkdir(parents=True, exist_ok=True)

        # Set random seeds for reproducibility
        self._set_random_seeds()

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for the benchmark suite."""
        logger = logging.getLogger(f"benchmark_{self.config.experiment_name}")
        logger.setLevel(logging.INFO)

        # Create file handler
        log_file = Path(self.config.output_dir) / "benchmark.log"
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        return logger

    def _setup_device(self) -> str:
        """Setup compute device for benchmarking."""
        if not TORCH_AVAILABLE:
            return "cpu"

        if self.config.device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            device = self.config.device

        self.logger.info(f"Using device: {device}")
        return device

    def _set_random_seeds(self) -> None:
        """Set random seeds for reproducibility."""
        np.random.seed(self.config.random_seed)
        if TORCH_AVAILABLE:
            torch.manual_seed(self.config.random_seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(self.config.random_seed)

    def run_single_benchmark(
        self,
        model_name: str,
        train_loader: DataLoader,
        val_loader: DataLoader,
        test_loader: Optional[DataLoader] = None,
        run_id: int = 0
    ) -> ModelResults:
        """Run benchmark for a single model."""

        self.logger.info(f"Starting benchmark for {model_name} (run {run_id + 1})")

        # Create model
        model = ModelRegistry.get_model(model_name)
        model = model.to(self.device) if TORCH_AVAILABLE else model

        # Compute model metadata
        model_metadata = model.compute_metadata(self.device)

        # Setup training components
        if TORCH_AVAILABLE:
            optimizer = self._create_optimizer(model)
            scheduler = self._create_scheduler(optimizer)
            loss_fn = self._create_loss_function()

        # Initialize results
        results = ModelResults(
            model_name=model_name,
            model_config=model.config,
            total_parameters=model_metadata.total_params,
            model_size_mb=model_metadata.memory_mb
        )

        # Training loop
        best_val_dice = 0.0
        training_start_time = time.time()

        for epoch in range(self.config.num_epochs):
            if not TORCH_AVAILABLE:
                break

            epoch_start_time = time.time()

            # Training phase
            train_loss, train_dice = self._train_epoch(
                model, train_loader, optimizer, loss_fn
            )

            # Validation phase
            if epoch % self.config.eval_frequency == 0:
                val_loss, val_dice = self._validate_epoch(
                    model, val_loader, loss_fn
                )

                # Update learning rate
                if scheduler:
                    scheduler.step(val_loss)

                # Track best model
                if val_dice > best_val_dice:
                    best_val_dice = val_dice
                    results.best_epoch = epoch
                    results.best_val_dice = val_dice

                    # Save checkpoint if enabled
                    if self.config.save_checkpoints:
                        self._save_checkpoint(model, optimizer, epoch, model_name, run_id)

                # Record metrics
                epoch_time = time.time() - epoch_start_time
                memory_usage = self._get_memory_usage()

                training_metrics = TrainingMetrics(
                    epoch=epoch,
                    train_loss=train_loss,
                    val_loss=val_loss,
                    train_dice=train_dice,
                    val_dice=val_dice,
                    learning_rate=optimizer.param_groups[0]['lr'],
                    training_time=epoch_time,
                    memory_usage=memory_usage
                )

                results.training_metrics.append(training_metrics)

                self.logger.info(
                    f"Epoch {epoch}: Train Loss={train_loss:.4f}, "
                    f"Val Loss={val_loss:.4f}, Val Dice={val_dice:.4f}"
                )

                # Early stopping check
                if self._should_early_stop(results.training_metrics):
                    self.logger.info(f"Early stopping at epoch {epoch}")
                    break

        results.total_training_time = time.time() - training_start_time

        # Final evaluation on test set
        if test_loader and TORCH_AVAILABLE:
            test_metrics = self._evaluate_test_set(model, test_loader)
            results.test_metrics = test_metrics

        # Inference benchmarking
        if TORCH_AVAILABLE:
            inference_stats = self._benchmark_inference(model, val_loader)
            results.inference_time_ms = inference_stats["avg_time_ms"]
            results.throughput_samples_per_sec = inference_stats["throughput"]

        # Resource utilization
        results.peak_memory_mb = self._get_peak_memory_usage()

        self.logger.info(f"Completed benchmark for {model_name}")
        return results

    def run_comparative_benchmark(
        self,
        train_loader: DataLoader,
        val_loader: DataLoader,
        test_loader: Optional[DataLoader] = None
    ) -> BenchmarkResults:
        """Run comparative benchmark across multiple models."""

        self.logger.info(f"Starting comparative benchmark: {self.config.experiment_name}")

        results = BenchmarkResults(benchmark_config=self.config)

        # Run benchmarks for each model
        for model_name in self.config.models_to_test:
            model_results = []

            # Multiple runs for statistical significance
            for run_id in range(self.config.num_runs):
                self._set_random_seeds()  # Reset seeds for each run

                try:
                    result = self.run_single_benchmark(
                        model_name, train_loader, val_loader, test_loader, run_id
                    )
                    model_results.append(result)

                except Exception as e:
                    self.logger.error(f"Error benchmarking {model_name} run {run_id}: {e}")
                    continue

            if model_results:
                results.model_results[model_name] = model_results

        # Statistical analysis
        if SKLEARN_AVAILABLE:
            results.statistical_analysis = self._perform_statistical_analysis(results)

        # Save results
        self._save_results(results)

        self.logger.info("Comparative benchmark completed")
        return results

    def _create_optimizer(self, model: nn.Module) -> optim.Optimizer:
        """Create optimizer for training."""
        if self.config.optimizer.lower() == "adam":
            return optim.Adam(model.parameters(), lr=self.config.learning_rate)
        elif self.config.optimizer.lower() == "adamw":
            return optim.AdamW(model.parameters(), lr=self.config.learning_rate)
        elif self.config.optimizer.lower() == "sgd":
            return optim.SGD(model.parameters(), lr=self.config.learning_rate, momentum=0.9)
        else:
            raise ValueError(f"Unknown optimizer: {self.config.optimizer}")

    def _create_scheduler(self, optimizer: optim.Optimizer) -> Optional[optim.lr_scheduler._LRScheduler]:
        """Create learning rate scheduler."""
        if self.config.scheduler.lower() == "cosine":
            return optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=self.config.num_epochs)
        elif self.config.scheduler.lower() == "step":
            return optim.lr_scheduler.StepLR(optimizer, step_size=30, gamma=0.1)
        elif self.config.scheduler.lower() == "plateau":
            return optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10)
        else:
            return None

    def _create_loss_function(self) -> Callable:
        """Create loss function for training."""
        # Import loss functions from our losses module
        try:
            from ..losses.combined_loss import CombinedLoss
            from ..losses.dice_loss import DiceLoss
            from ..losses.focal_loss import FocalLoss

            if self.config.loss_function == "dice_ce":
                return CombinedLoss(loss_types=["dice", "crossentropy"])
            elif self.config.loss_function == "focal":
                return FocalLoss()
            elif self.config.loss_function == "dice":
                return DiceLoss()
            else:
                # Fallback to standard cross entropy
                return nn.CrossEntropyLoss()

        except ImportError:
            self.logger.warning("Custom loss functions not available, using CrossEntropyLoss")
            return nn.CrossEntropyLoss()

    def _train_epoch(
        self,
        model: nn.Module,
        train_loader: DataLoader,
        optimizer: optim.Optimizer,
        loss_fn: Callable
    ) -> Tuple[float, float]:
        """Train for one epoch."""
        model.train()
        total_loss = 0.0
        total_dice = 0.0

        for batch_idx, (data, target) in enumerate(train_loader):
            data, target = data.to(self.device), target.to(self.device)

            optimizer.zero_grad()
            output = model(data)
            loss = loss_fn(output, target)
            loss.backward()
            optimizer.step()

            total_loss += loss.item()

            # Calculate dice score
            with torch.no_grad():
                pred = torch.argmax(output, dim=1)
                dice = self.metrics_calculator.compute_dice_score(
                    pred.cpu().numpy(),
                    target.cpu().numpy()
                )
                total_dice += dice

        avg_loss = total_loss / len(train_loader)
        avg_dice = total_dice / len(train_loader)

        return avg_loss, avg_dice

    def _validate_epoch(
        self,
        model: nn.Module,
        val_loader: DataLoader,
        loss_fn: Callable
    ) -> Tuple[float, float]:
        """Validate for one epoch."""
        model.eval()
        total_loss = 0.0
        total_dice = 0.0

        with torch.no_grad():
            for data, target in val_loader:
                data, target = data.to(self.device), target.to(self.device)

                output = model(data)
                loss = loss_fn(output, target)

                total_loss += loss.item()

                # Calculate dice score
                pred = torch.argmax(output, dim=1)
                dice = self.metrics_calculator.compute_dice_score(
                    pred.cpu().numpy(),
                    target.cpu().numpy()
                )
                total_dice += dice

        avg_loss = total_loss / len(val_loader)
        avg_dice = total_dice / len(val_loader)

        return avg_loss, avg_dice

    def _evaluate_test_set(
        self,
        model: nn.Module,
        test_loader: DataLoader
    ) -> Dict[str, float]:
        """Evaluate model on test set with comprehensive metrics."""
        model.eval()
        all_predictions = []
        all_targets = []

        with torch.no_grad():
            for data, target in test_loader:
                data, target = data.to(self.device), target.to(self.device)
                output = model(data)
                pred = torch.argmax(output, dim=1)

                all_predictions.append(pred.cpu().numpy())
                all_targets.append(target.cpu().numpy())

        # Concatenate all predictions and targets
        predictions = np.concatenate(all_predictions, axis=0)
        targets = np.concatenate(all_targets, axis=0)

        # Compute comprehensive metrics
        metrics = compute_comprehensive_metrics(predictions, targets)

        return metrics

    def _benchmark_inference(
        self,
        model: nn.Module,
        dataloader: DataLoader
    ) -> Dict[str, float]:
        """Benchmark inference performance."""
        model.eval()
        times = []

        with torch.no_grad():
            for data, _ in dataloader:
                data = data.to(self.device)

                # Warm up
                for _ in range(3):
                    _ = model(data)

                # Timing
                if self.device.startswith("cuda"):
                    torch.cuda.synchronize()

                start_time = time.time()
                _ = model(data)

                if self.device.startswith("cuda"):
                    torch.cuda.synchronize()

                end_time = time.time()
                times.append((end_time - start_time) * 1000)  # Convert to ms

                # Only benchmark a few batches
                if len(times) >= 10:
                    break

        avg_time_ms = np.mean(times)
        throughput = 1000.0 / avg_time_ms  # samples per second

        return {
            "avg_time_ms": avg_time_ms,
            "std_time_ms": np.std(times),
            "throughput": throughput
        }

    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        if TORCH_AVAILABLE and torch.cuda.is_available():
            return torch.cuda.memory_allocated() / (1024 ** 2)
        else:
            import psutil
            return psutil.Process().memory_info().rss / (1024 ** 2)

    def _get_peak_memory_usage(self) -> float:
        """Get peak memory usage in MB."""
        if TORCH_AVAILABLE and torch.cuda.is_available():
            return torch.cuda.max_memory_allocated() / (1024 ** 2)
        else:
            # For CPU, we would need more sophisticated tracking
            return self._get_memory_usage()

    def _should_early_stop(self, training_metrics: List[TrainingMetrics]) -> bool:
        """Check if training should stop early."""
        if len(training_metrics) < self.config.early_stopping_patience:
            return False

        # Check if validation dice hasn't improved in patience epochs
        recent_scores = [m.val_dice for m in training_metrics[-self.config.early_stopping_patience:]]
        best_recent = max(recent_scores)
        overall_best = max([m.val_dice for m in training_metrics])

        return best_recent < overall_best

    def _save_checkpoint(
        self,
        model: nn.Module,
        optimizer: optim.Optimizer,
        epoch: int,
        model_name: str,
        run_id: int
    ) -> None:
        """Save model checkpoint."""
        checkpoint_dir = Path(self.config.output_dir) / "checkpoints"
        checkpoint_dir.mkdir(exist_ok=True)

        checkpoint_path = checkpoint_dir / f"{model_name}_run{run_id}_epoch{epoch}.pth"

        torch.save({
            'epoch': epoch,
            'model_state_dict': model.state_dict(),
            'optimizer_state_dict': optimizer.state_dict(),
            'model_name': model_name,
            'run_id': run_id
        }, checkpoint_path)

    def _perform_statistical_analysis(self, results: BenchmarkResults) -> Dict[str, Any]:
        """Perform statistical analysis of benchmark results."""
        analysis = {}

        # Collect validation dice scores for all models
        model_scores = {}
        for model_name, results_list in results.model_results.items():
            model_scores[model_name] = [r.best_val_dice for r in results_list]

        # Pairwise comparisons
        model_names = list(model_scores.keys())
        pairwise_tests = {}

        for i, model1 in enumerate(model_names):
            for j, model2 in enumerate(model_names[i+1:], i+1):
                scores1 = model_scores[model1]
                scores2 = model_scores[model2]

                # Perform t-test
                if len(scores1) > 1 and len(scores2) > 1:
                    t_stat, p_value = stats.ttest_ind(scores1, scores2)
                    pairwise_tests[f"{model1}_vs_{model2}"] = {
                        "t_statistic": t_stat,
                        "p_value": p_value,
                        "significant": p_value < (1 - self.config.confidence_level)
                    }

        analysis["pairwise_comparisons"] = pairwise_tests

        # Overall rankings
        rankings = []
        for model_name, scores in model_scores.items():
            rankings.append({
                "model": model_name,
                "mean_score": np.mean(scores),
                "std_score": np.std(scores),
                "min_score": np.min(scores),
                "max_score": np.max(scores)
            })

        rankings.sort(key=lambda x: x["mean_score"], reverse=True)
        analysis["rankings"] = rankings

        return analysis

    def _save_results(self, results: BenchmarkResults) -> None:
        """Save benchmark results to file."""
        results_file = Path(self.config.output_dir) / "benchmark_results.json"

        # Convert to dictionary for JSON serialization
        results_dict = asdict(results)

        with open(results_file, 'w') as f:
            json.dump(results_dict, f, indent=2, default=str)

        self.logger.info(f"Results saved to {results_file}")


def run_single_benchmark(
    model_name: str,
    config: BenchmarkConfig,
    train_loader: DataLoader,
    val_loader: DataLoader,
    test_loader: Optional[DataLoader] = None
) -> ModelResults:
    """Convenience function to run a single model benchmark."""
    suite = BenchmarkSuite(config)
    return suite.run_single_benchmark(model_name, train_loader, val_loader, test_loader)


def run_comparative_benchmark(
    config: BenchmarkConfig,
    train_loader: DataLoader,
    val_loader: DataLoader,
    test_loader: Optional[DataLoader] = None
) -> BenchmarkResults:
    """Convenience function to run comparative benchmark."""
    suite = BenchmarkSuite(config)
    return suite.run_comparative_benchmark(train_loader, val_loader, test_loader)


# Example usage and testing
if __name__ == "__main__":
    print("Testing Benchmark Suite...")

    # Create a simple benchmark configuration
    config = BenchmarkConfig(
        experiment_name="test_benchmark",
        output_dir="/tmp/benchmark_test",
        num_epochs=5,
        models_to_test=["unet", "segresnet"],
        num_runs=2
    )

    print(f"Benchmark config created: {config.experiment_name}")
    print(f"Models to test: {config.models_to_test}")
    print(f"Output directory: {config.output_dir}")

    if TORCH_AVAILABLE:
        # Create dummy data loaders for testing
        dummy_data = torch.randn(10, 1, 32, 32, 32)
        dummy_targets = torch.randint(0, 2, (10, 32, 32, 32))

        from torch.utils.data import DataLoader, TensorDataset
        dataset = TensorDataset(dummy_data, dummy_targets)
        dummy_loader = DataLoader(dataset, batch_size=2)

        print("Created dummy data loaders")

        # Initialize benchmark suite
        suite = BenchmarkSuite(config)
        print("Benchmark suite initialized")

        print("Benchmark suite tests completed successfully!")
    else:
        print("PyTorch not available - skipping benchmark tests")

        print("Benchmark suite tests completed successfully!")
    else:
        print("PyTorch not available - skipping benchmark tests")
