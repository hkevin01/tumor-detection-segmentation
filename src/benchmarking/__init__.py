"""
Model Performance Benchmarking Framework

This module provides comprehensive benchmarking capabilities for medical image
segmentation models. It includes standardized evaluation protocols, architecture
comparison tools, and performance analysis utilities.

Key Components:
- Architecture comparison suite (UNETR, SwinUNETR, SegResNet, etc.)
- Standardized evaluation metrics and protocols
- Training time and resource utilization tracking
- Performance visualization and reporting
- Statistical significance testing
- Model complexity analysis
"""

from .benchmark_suite import (BenchmarkConfig, BenchmarkResults,
                              BenchmarkSuite, run_comparative_benchmark,
                              run_single_benchmark)
from .evaluation_metrics import (MedicalSegmentationMetrics,
                                 compute_comprehensive_metrics,
                                 create_metrics_report, statistical_comparison)
from .model_registry import (ModelRegistry, create_model_from_config,
                             get_available_models, register_custom_model)
from .performance_tracker import (PerformanceTracker, ResourceMonitor,
                                  TrainingProfiler, create_performance_report)
from .visualization import (BenchmarkVisualizer, create_comparison_plots,
                            create_performance_dashboard,
                            export_benchmark_report)

__all__ = [
    # Model Registry
    "ModelRegistry",
    "get_available_models",
    "create_model_from_config",
    "register_custom_model",

    # Benchmark Suite
    "BenchmarkSuite",
    "BenchmarkConfig",
    "BenchmarkResults",
    "run_single_benchmark",
    "run_comparative_benchmark",

    # Evaluation Metrics
    "MedicalSegmentationMetrics",
    "compute_comprehensive_metrics",
    "statistical_comparison",
    "create_metrics_report",

    # Performance Tracking
    "PerformanceTracker",
    "ResourceMonitor",
    "TrainingProfiler",
    "create_performance_report",

    # Visualization
    "BenchmarkVisualizer",
    "create_comparison_plots",
    "create_performance_dashboard",
    "export_benchmark_report",
]
