"""
Model Performance Benchmarking Framework

NASA-STD-8739.8 Requirement Implementation Traceability:
=========================================================

REQ-F-009: Experiment Tracking Dashboard (Benchmarking Component)
- Comprehensive benchmarking capabilities for medical segmentation models
- Performance comparison and visualization across model architectures
- Statistical analysis and reporting for model evaluation
- Experiment tracking integration with MLflow

REQ-F-001: AI Model Training and Management (Model Evaluation)
- Standardized evaluation protocols for multiple architectures
- Model complexity analysis and performance profiling
- Architecture comparison suite (UNETR, SwinUNETR, SegResNet)
- Training time and resource utilization tracking

REQ-NF-P-001: Training Performance (Performance Analysis)
- Training performance benchmarking and optimization analysis
- Resource utilization monitoring and reporting
- Performance visualization for training optimization

REQ-NF-M-001: Maintainability (Benchmarking Framework)
- Standardized benchmarking protocols for consistent evaluation
- Modular benchmarking framework for extensibility
- Comprehensive documentation and reproducible benchmarks

REQ-F-002: Model Inference Engine (Inference Benchmarking)
- Inference performance evaluation and benchmarking
- Clinical workflow performance assessment
- Real-time performance monitoring capabilities

REQ-NF-P-002: Inference Response Time (Performance Validation)
- Benchmark validation for clinical response time requirements
- Performance testing under various clinical scenarios
- Statistical significance testing for performance claims

Technical Implementation:
- Comprehensive medical image segmentation model benchmarking
- Standardized evaluation metrics and statistical analysis
- Professional visualization and reporting capabilities
- Production-ready performance assessment framework

Key Components:
- Architecture comparison suite (UNETR, SwinUNETR, SegResNet, etc.)
- Standardized evaluation metrics and protocols
- Training time and resource utilization tracking
- Performance visualization and reporting
- Statistical significance testing
- Model complexity analysis

Author: Medical Imaging AI Team
Classification: Unclassified
Version: 2.0
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
