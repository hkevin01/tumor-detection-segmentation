#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Visualization for Medical Image Segmentation Benchmarking

This module provides comprehensive visualization capabilities for benchmarking
results including comparison plots, performance dashboards, and detailed
analysis reports.

Key Features:
- Model comparison visualizations
- Performance trend analysis
- Resource utilization plots
- Statistical comparison charts
- Interactive dashboards
- Comprehensive benchmark reports
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

# Optional visualization imports
try:
    import matplotlib.patches as patches
    import matplotlib.pyplot as plt
    import seaborn as sns
    from matplotlib.backends.backend_pdf import PdfPages
    MATPLOTLIB_AVAILABLE = True

    # Set style
    plt.style.use('seaborn-v0_8')
    sns.set_palette("husl")

except ImportError:
    MATPLOTLIB_AVAILABLE = False
    logging.warning("Matplotlib/Seaborn not available. Visualization will be limited.")

try:
    import plotly.express as px
    import plotly.graph_objects as go
    import plotly.offline as pyo
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    logging.warning("Plotly not available. Interactive plots will be limited.")

from .benchmark_suite import BenchmarkResults, ModelResults
from .performance_tracker import PerformanceReport


class BenchmarkVisualizer:
    """Main visualization class for benchmark results."""

    def __init__(self, output_dir: str = "benchmark_plots"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Color palette for consistent visualization
        self.colors = [
            '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
            '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
        ]

    def create_model_comparison_plot(
        self,
        results: BenchmarkResults,
        metric: str = "dice_score",
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """Create model comparison plot for a specific metric."""

        if not MATPLOTLIB_AVAILABLE:
            logging.warning("Matplotlib not available for plotting")
            return None

        # Extract data
        model_names = list(results.model_results.keys())
        metric_values = []
        metric_errors = []

        for model_name in model_names:
            model_results = results.model_results[model_name]

            if metric == "dice_score" or metric == "val_dice":
                values = [r.best_val_dice for r in model_results]
            elif metric in model_results[0].test_metrics:
                values = [r.test_metrics[metric] for r in model_results]
            else:
                logging.warning(f"Metric '{metric}' not found")
                continue

            metric_values.append(np.mean(values))
            metric_errors.append(np.std(values))

        if not metric_values:
            return None

        # Create plot
        fig, ax = plt.subplots(figsize=(10, 6))

        x_pos = np.arange(len(model_names))
        bars = ax.bar(x_pos, metric_values, yerr=metric_errors,
                     capsize=5, color=self.colors[:len(model_names)],
                     alpha=0.8, edgecolor='black', linewidth=1)

        # Customize plot
        ax.set_xlabel('Model', fontsize=12, fontweight='bold')
        ax.set_ylabel(f'{metric.replace("_", " ").title()}', fontsize=12, fontweight='bold')
        ax.set_title(f'Model Comparison - {metric.replace("_", " ").title()}',
                    fontsize=14, fontweight='bold')
        ax.set_xticks(x_pos)
        ax.set_xticklabels(model_names, rotation=45, ha='right')

        # Add value labels on bars
        for bar, value, error in zip(bars, metric_values, metric_errors):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + error + 0.01,
                   f'{value:.3f}±{error:.3f}',
                   ha='center', va='bottom', fontweight='bold')

        # Add grid
        ax.grid(True, alpha=0.3, axis='y')
        ax.set_axisbelow(True)

        plt.tight_layout()

        # Save plot
        if save_path is None:
            save_path = self.output_dir / f"model_comparison_{metric}.png"

        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()

        return str(save_path)

    def create_training_curves(
        self,
        results: BenchmarkResults,
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """Create training curves for all models."""

        if not MATPLOTLIB_AVAILABLE:
            logging.warning("Matplotlib not available for plotting")
            return None

        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        axes = axes.flatten()

        metrics_to_plot = [
            ('train_loss', 'Training Loss'),
            ('val_loss', 'Validation Loss'),
            ('train_dice', 'Training Dice'),
            ('val_dice', 'Validation Dice')
        ]

        for idx, (metric_name, title) in enumerate(metrics_to_plot):
            ax = axes[idx]

            for color_idx, (model_name, model_results_list) in enumerate(results.model_results.items()):
                # Average training curves across runs
                all_curves = []
                max_epochs = 0

                for model_result in model_results_list:
                    if hasattr(model_result, 'training_metrics'):
                        curve = [getattr(tm, metric_name, 0) for tm in model_result.training_metrics]
                        if curve:
                            all_curves.append(curve)
                            max_epochs = max(max_epochs, len(curve))

                if all_curves:
                    # Pad curves to same length and average
                    padded_curves = []
                    for curve in all_curves:
                        padded = curve + [curve[-1]] * (max_epochs - len(curve))
                        padded_curves.append(padded)

                    mean_curve = np.mean(padded_curves, axis=0)
                    std_curve = np.std(padded_curves, axis=0)
                    epochs = range(len(mean_curve))

                    # Plot mean curve with error bands
                    color = self.colors[color_idx % len(self.colors)]
                    ax.plot(epochs, mean_curve, label=model_name, color=color, linewidth=2)
                    ax.fill_between(epochs,
                                   mean_curve - std_curve,
                                   mean_curve + std_curve,
                                   alpha=0.3, color=color)

            ax.set_xlabel('Epoch')
            ax.set_ylabel(title)
            ax.set_title(title)
            ax.legend()
            ax.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save plot
        if save_path is None:
            save_path = self.output_dir / "training_curves.png"

        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()

        return str(save_path)

    def create_performance_overview(
        self,
        results: BenchmarkResults,
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """Create comprehensive performance overview."""

        if not MATPLOTLIB_AVAILABLE:
            logging.warning("Matplotlib not available for plotting")
            return None

        # Get summary data
        summary = results.get_summary_table()
        model_names = list(summary.keys())

        if not model_names:
            return None

        # Create subplots
        fig, axes = plt.subplots(2, 3, figsize=(18, 12))
        axes = axes.flatten()

        # Performance metrics to visualize
        metrics_info = [
            ('avg_val_dice', 'Validation Dice Score', True),
            ('avg_training_time', 'Training Time (s)', False),
            ('avg_inference_time', 'Inference Time (ms)', False),
            ('avg_parameters', 'Number of Parameters (M)', False),
            ('avg_memory', 'Peak Memory (MB)', False),
        ]

        for idx, (metric_key, title, higher_better) in enumerate(metrics_info):
            ax = axes[idx]

            if metric_key in summary[model_names[0]]:
                values = [summary[model][metric_key] for model in model_names]
                errors = [summary[model].get(f'std_{metric_key.replace("avg_", "")}', 0)
                         for model in model_names]

                # Convert parameters to millions
                if 'parameters' in metric_key:
                    values = [v / 1e6 for v in values]
                    errors = [e / 1e6 for e in errors]

                # Create bar plot
                bars = ax.bar(range(len(model_names)), values, yerr=errors,
                             capsize=5, alpha=0.8, edgecolor='black', linewidth=1)

                # Color bars based on performance (best is green)
                if higher_better:
                    best_idx = np.argmax(values)
                else:
                    best_idx = np.argmin(values)

                for i, bar in enumerate(bars):
                    if i == best_idx:
                        bar.set_color('#2ca02c')  # Green for best
                    else:
                        bar.set_color(self.colors[i % len(self.colors)])

                ax.set_title(title, fontweight='bold')
                ax.set_xticks(range(len(model_names)))
                ax.set_xticklabels(model_names, rotation=45, ha='right')
                ax.grid(True, alpha=0.3, axis='y')

                # Add value labels
                for bar, value, error in zip(bars, values, errors):
                    height = bar.get_height()
                    if error > 0:
                        label = f'{value:.3f}±{error:.3f}'
                    else:
                        label = f'{value:.3f}'
                    ax.text(bar.get_x() + bar.get_width()/2., height + error + max(values) * 0.01,
                           label, ha='center', va='bottom', fontsize=9)

        # Use last subplot for model complexity comparison
        ax = axes[5]

        # Scatter plot: parameters vs performance
        if 'avg_parameters' in summary[model_names[0]] and 'avg_val_dice' in summary[model_names[0]]:
            params = [summary[model]['avg_parameters'] / 1e6 for model in model_names]
            dice_scores = [summary[model]['avg_val_dice'] for model in model_names]

            scatter = ax.scatter(params, dice_scores, s=100, alpha=0.7,
                               c=range(len(model_names)), cmap='viridis')

            # Add model name labels
            for i, model in enumerate(model_names):
                ax.annotate(model, (params[i], dice_scores[i]),
                           xytext=(5, 5), textcoords='offset points', fontsize=9)

            ax.set_xlabel('Parameters (M)')
            ax.set_ylabel('Validation Dice Score')
            ax.set_title('Model Complexity vs Performance', fontweight='bold')
            ax.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save plot
        if save_path is None:
            save_path = self.output_dir / "performance_overview.png"

        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()

        return str(save_path)

    def create_resource_utilization_plot(
        self,
        performance_reports: List[PerformanceReport],
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """Create resource utilization visualization."""

        if not MATPLOTLIB_AVAILABLE or not performance_reports:
            logging.warning("Matplotlib not available or no performance reports")
            return None

        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        axes = axes.flatten()

        for idx, report in enumerate(performance_reports[:4]):  # Limit to 4 reports
            ax = axes[idx]

            if not report.resource_snapshots:
                continue

            # Extract time series data
            timestamps = [s.timestamp for s in report.resource_snapshots]
            start_time = timestamps[0]
            relative_times = [(t - start_time) / 60 for t in timestamps]  # Convert to minutes

            cpu_usage = [s.cpu_percent for s in report.resource_snapshots]
            memory_usage = [s.memory_mb / 1024 for s in report.resource_snapshots]  # Convert to GB

            # Plot CPU and memory on same axis with different scales
            ax2 = ax.twinx()

            line1 = ax.plot(relative_times, cpu_usage, 'b-', linewidth=2, label='CPU Usage (%)')
            line2 = ax2.plot(relative_times, memory_usage, 'r-', linewidth=2, label='Memory (GB)')

            ax.set_xlabel('Time (minutes)')
            ax.set_ylabel('CPU Usage (%)', color='b')
            ax2.set_ylabel('Memory Usage (GB)', color='r')
            ax.set_title(f'{report.model_name} - Resource Utilization', fontweight='bold')

            # Combine legends
            lines = line1 + line2
            labels = [l.get_label() for l in lines]
            ax.legend(lines, labels, loc='upper left')

            ax.grid(True, alpha=0.3)

        plt.tight_layout()

        # Save plot
        if save_path is None:
            save_path = self.output_dir / "resource_utilization.png"

        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.close()

        return str(save_path)

    def create_interactive_dashboard(
        self,
        results: BenchmarkResults,
        save_path: Optional[str] = None
    ) -> Optional[str]:
        """Create interactive dashboard using Plotly."""

        if not PLOTLY_AVAILABLE:
            logging.warning("Plotly not available for interactive plots")
            return None

        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=['Model Performance Comparison', 'Training Time vs Accuracy',
                           'Parameter Count vs Performance', 'Memory Usage Comparison'],
            specs=[[{"type": "bar"}, {"type": "scatter"}],
                   [{"type": "scatter"}, {"type": "bar"}]]
        )

        # Get summary data
        summary = results.get_summary_table()
        model_names = list(summary.keys())

        if not model_names:
            return None

        # 1. Model performance comparison (bar chart)
        dice_scores = [summary[model]['avg_val_dice'] for model in model_names]
        dice_errors = [summary[model].get('std_val_dice', 0) for model in model_names]

        fig.add_trace(
            go.Bar(x=model_names, y=dice_scores, error_y=dict(type='data', array=dice_errors),
                   name='Dice Score', marker_color='lightblue'),
            row=1, col=1
        )

        # 2. Training time vs accuracy (scatter)
        if 'avg_training_time' in summary[model_names[0]]:
            training_times = [summary[model]['avg_training_time'] / 3600 for model in model_names]  # Convert to hours

            fig.add_trace(
                go.Scatter(x=training_times, y=dice_scores, mode='markers+text',
                          text=model_names, textposition="top center",
                          marker=dict(size=12, color='red'),
                          name='Training Time vs Accuracy'),
                row=1, col=2
            )

        # 3. Parameter count vs performance (scatter)
        if 'avg_parameters' in summary[model_names[0]]:
            parameters = [summary[model]['avg_parameters'] / 1e6 for model in model_names]  # Convert to millions

            fig.add_trace(
                go.Scatter(x=parameters, y=dice_scores, mode='markers+text',
                          text=model_names, textposition="top center",
                          marker=dict(size=12, color='green'),
                          name='Parameters vs Performance'),
                row=2, col=1
            )

        # 4. Memory usage comparison (bar chart)
        if 'avg_memory' in summary[model_names[0]]:
            memory_usage = [summary[model]['avg_memory'] / 1024 for model in model_names]  # Convert to GB

            fig.add_trace(
                go.Bar(x=model_names, y=memory_usage,
                       name='Memory Usage (GB)', marker_color='orange'),
                row=2, col=2
            )

        # Update layout
        fig.update_layout(
            title_text="Medical Image Segmentation Model Benchmark Dashboard",
            title_x=0.5,
            height=800,
            showlegend=False
        )

        # Update axes labels
        fig.update_xaxes(title_text="Model", row=1, col=1)
        fig.update_yaxes(title_text="Dice Score", row=1, col=1)

        fig.update_xaxes(title_text="Training Time (hours)", row=1, col=2)
        fig.update_yaxes(title_text="Dice Score", row=1, col=2)

        fig.update_xaxes(title_text="Parameters (M)", row=2, col=1)
        fig.update_yaxes(title_text="Dice Score", row=2, col=1)

        fig.update_xaxes(title_text="Model", row=2, col=2)
        fig.update_yaxes(title_text="Memory Usage (GB)", row=2, col=2)

        # Save interactive plot
        if save_path is None:
            save_path = self.output_dir / "interactive_dashboard.html"

        pyo.plot(fig, filename=str(save_path), auto_open=False)

        return str(save_path)


def create_comparison_plots(
    results: BenchmarkResults,
    output_dir: str = "benchmark_plots"
) -> List[str]:
    """Create comprehensive comparison plots."""

    visualizer = BenchmarkVisualizer(output_dir)
    plot_paths = []

    # Model comparison plot
    comparison_path = visualizer.create_model_comparison_plot(results)
    if comparison_path:
        plot_paths.append(comparison_path)

    # Training curves
    curves_path = visualizer.create_training_curves(results)
    if curves_path:
        plot_paths.append(curves_path)

    # Performance overview
    overview_path = visualizer.create_performance_overview(results)
    if overview_path:
        plot_paths.append(overview_path)

    return plot_paths


def create_performance_dashboard(
    results: BenchmarkResults,
    performance_reports: Optional[List[PerformanceReport]] = None,
    output_dir: str = "benchmark_plots"
) -> Dict[str, str]:
    """Create complete performance dashboard."""

    visualizer = BenchmarkVisualizer(output_dir)
    dashboard_files = {}

    # Static plots
    comparison_path = visualizer.create_model_comparison_plot(results)
    if comparison_path:
        dashboard_files['model_comparison'] = comparison_path

    overview_path = visualizer.create_performance_overview(results)
    if overview_path:
        dashboard_files['performance_overview'] = overview_path

    curves_path = visualizer.create_training_curves(results)
    if curves_path:
        dashboard_files['training_curves'] = curves_path

    # Resource utilization if available
    if performance_reports:
        resource_path = visualizer.create_resource_utilization_plot(performance_reports)
        if resource_path:
            dashboard_files['resource_utilization'] = resource_path

    # Interactive dashboard
    interactive_path = visualizer.create_interactive_dashboard(results)
    if interactive_path:
        dashboard_files['interactive_dashboard'] = interactive_path

    return dashboard_files


def export_benchmark_report(
    results: BenchmarkResults,
    performance_reports: Optional[List[PerformanceReport]] = None,
    output_path: str = "benchmark_report.pdf"
) -> str:
    """Export comprehensive benchmark report as PDF."""

    if not MATPLOTLIB_AVAILABLE:
        logging.warning("Matplotlib not available for PDF export")
        return ""

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with PdfPages(output_path) as pdf:
        # Create visualizer
        visualizer = BenchmarkVisualizer()

        # Model comparison page
        plt.figure(figsize=(12, 8))
        visualizer.create_model_comparison_plot(results)
        pdf.savefig(bbox_inches='tight')
        plt.close()

        # Performance overview page
        plt.figure(figsize=(15, 10))
        visualizer.create_performance_overview(results)
        pdf.savefig(bbox_inches='tight')
        plt.close()

        # Training curves page
        plt.figure(figsize=(15, 10))
        visualizer.create_training_curves(results)
        pdf.savefig(bbox_inches='tight')
        plt.close()

        # Resource utilization if available
        if performance_reports:
            plt.figure(figsize=(15, 10))
            visualizer.create_resource_utilization_plot(performance_reports)
            pdf.savefig(bbox_inches='tight')
            plt.close()

        # Summary statistics page
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.axis('off')

        # Create summary table
        summary = results.get_summary_table()
        summary_text = "BENCHMARK RESULTS SUMMARY\n\n"

        for model_name, stats in summary.items():
            summary_text += f"{model_name.upper()}:\n"
            summary_text += f"  Validation Dice: {stats.get('avg_val_dice', 0):.4f} ± {stats.get('std_val_dice', 0):.4f}\n"
            summary_text += f"  Training Time: {stats.get('avg_training_time', 0):.2f}s\n"
            summary_text += f"  Inference Time: {stats.get('avg_inference_time', 0):.2f}ms\n"
            summary_text += f"  Parameters: {stats.get('avg_parameters', 0) / 1e6:.2f}M\n"
            summary_text += f"  Peak Memory: {stats.get('avg_memory', 0):.2f}MB\n\n"

        ax.text(0.1, 0.9, summary_text, transform=ax.transAxes, fontsize=12,
               verticalalignment='top', fontfamily='monospace')

        pdf.savefig(bbox_inches='tight')
        plt.close()

    return str(output_path)


# Example usage and testing
if __name__ == "__main__":
    print("Testing Benchmark Visualization...")

    if MATPLOTLIB_AVAILABLE:
        print("Matplotlib available - creating test visualization")

        # Create test data
        from .benchmark_suite import (BenchmarkConfig, BenchmarkResults,
                                      ModelConfig, ModelResults)

        # Mock benchmark results for testing
        config = BenchmarkConfig(
            experiment_name="test_visualization",
            output_dir="/tmp/test_viz"
        )

        results = BenchmarkResults(benchmark_config=config)

        # Add mock model results
        for i, model_name in enumerate(["unet", "segresnet", "unetr"]):
            model_config = ModelConfig(
                name=model_name,
                architecture=model_name.upper()
            )

            mock_result = ModelResults(
                model_name=model_name,
                model_config=model_config,
                best_val_dice=0.85 + i * 0.02 + np.random.normal(0, 0.01),
                total_training_time=1000 + i * 500 + np.random.normal(0, 100),
                total_parameters=int(1e6 + i * 5e6),
                peak_memory_mb=2000 + i * 1000
            )

            mock_result.test_metrics = {
                "dice_score": mock_result.best_val_dice + np.random.normal(0, 0.005),
                "iou_score": mock_result.best_val_dice - 0.1 + np.random.normal(0, 0.005)
            }

            results.model_results[model_name] = [mock_result]

        # Test visualization
        visualizer = BenchmarkVisualizer("/tmp/test_viz")

        # Test model comparison plot
        comparison_path = visualizer.create_model_comparison_plot(results)
        if comparison_path:
            print(f"Created model comparison plot: {comparison_path}")

        # Test performance overview
        overview_path = visualizer.create_performance_overview(results)
        if overview_path:
            print(f"Created performance overview: {overview_path}")

        print("Visualization tests completed successfully!")
    else:
        print("Matplotlib not available - skipping visualization tests")
        if overview_path:
            print(f"Created performance overview: {overview_path}")

        print("Visualization tests completed successfully!")
    else:
        print("Matplotlib not available - skipping visualization tests")
