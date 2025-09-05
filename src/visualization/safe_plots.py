#!/usr/bin/env python3
"""
Enhanced Visualization Utilities with Crash Prevention
=====================================================

This module provides crash-safe visualization utilities for medical imaging
workflows with comprehensive error handling and resource management.

Features:
- Memory-safe plot generation
- GPU-aware visualization
- Automatic cleanup on failures
- Interactive plot recovery
- Resource monitoring for complex visualizations
"""

import gc
import logging
import os
from contextlib import contextmanager
from typing import Dict, List, Optional, Tuple

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import matplotlib.patches as patches
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import seaborn as sns
    SEABORN_AVAILABLE = True
except ImportError:
    SEABORN_AVAILABLE = False

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    from src.utils.crash_prevention import (
        emergency_cleanup,
        gpu_safe_context,
        log_system_resources,
        memory_safe_context,
        safe_execution,
    )
    CRASH_PREVENTION_AVAILABLE = True
except ImportError:
    CRASH_PREVENTION_AVAILABLE = False
    # Fallback implementations
    @contextmanager
    def memory_safe_context(*args, **kwargs):
        yield None
    @contextmanager
    def gpu_safe_context(*args, **kwargs):
        yield None
    def safe_execution(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    def emergency_cleanup():
        gc.collect()
    def log_system_resources(logger=None):
        pass

logger = logging.getLogger(__name__)


@safe_execution(max_retries=2, memory_threshold=0.75)
def create_medical_slice_plot_safe(
    image_data: np.ndarray,
    slice_axis: int = 2,
    slice_idx: Optional[int] = None,
    title: str = "Medical Image Slice",
    colormap: str = "gray",
    figsize: Tuple[float, float] = (10, 8),
    save_path: Optional[str] = None
) -> bool:
    """
    Create safe medical image slice visualization.

    Args:
        image_data: 3D medical image array
        slice_axis: Axis along which to slice (0, 1, or 2)
        slice_idx: Slice index (default: middle slice)
        title: Plot title
        colormap: Matplotlib colormap
        figsize: Figure size
        save_path: Path to save figure

    Returns:
        Success status
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.error("Matplotlib not available")
        return False

    if not NUMPY_AVAILABLE:
        logger.error("NumPy not available")
        return False

    logger.info(f"Creating medical slice plot: axis={slice_axis}, title='{title}'")

    with memory_safe_context(threshold=0.75):
        try:
            # Validate input
            if not isinstance(image_data, np.ndarray):
                raise ValueError("Image data must be numpy array")

            if image_data.ndim != 3:
                raise ValueError(f"Expected 3D array, got {image_data.ndim}D")

            if slice_axis not in [0, 1, 2]:
                raise ValueError(f"Invalid slice axis: {slice_axis}")

            # Get slice index
            if slice_idx is None:
                slice_idx = image_data.shape[slice_axis] // 2

            if slice_idx >= image_data.shape[slice_axis]:
                slice_idx = image_data.shape[slice_axis] - 1
                logger.warning(f"Slice index clamped to {slice_idx}")

            # Extract slice
            if slice_axis == 0:
                slice_data = image_data[slice_idx, :, :]
            elif slice_axis == 1:
                slice_data = image_data[:, slice_idx, :]
            else:  # slice_axis == 2
                slice_data = image_data[:, :, slice_idx]

            # Create figure
            fig, ax = plt.subplots(figsize=figsize)

            # Display slice
            im = ax.imshow(slice_data, cmap=colormap, aspect='equal')

            # Add title and labels
            ax.set_title(f"{title} - Slice {slice_idx} (axis {slice_axis})")
            ax.set_xlabel("X")
            ax.set_ylabel("Y")

            # Add colorbar
            plt.colorbar(im, ax=ax, shrink=0.8)

            # Tight layout
            plt.tight_layout()

            # Save if requested
            if save_path:
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
                logger.info(f"Plot saved to: {save_path}")

            log_system_resources(logger)

            return True

        except Exception as e:
            logger.error(f"Medical slice plot failed: {e}")
            emergency_cleanup()
            return False

        finally:
            # Always close figure to prevent memory leaks
            plt.close()


@safe_execution(max_retries=1)
def create_segmentation_overlay_safe(
    base_image: np.ndarray,
    segmentation: np.ndarray,
    class_names: Optional[List[str]] = None,
    alpha: float = 0.5,
    figsize: Tuple[float, float] = (12, 8),
    save_path: Optional[str] = None
) -> bool:
    """
    Create safe segmentation overlay visualization.

    Args:
        base_image: Base medical image (2D)
        segmentation: Segmentation mask (2D)
        class_names: Names for segmentation classes
        alpha: Overlay transparency
        figsize: Figure size
        save_path: Path to save figure

    Returns:
        Success status
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.error("Matplotlib not available")
        return False

    logger.info("Creating segmentation overlay")

    with memory_safe_context(threshold=0.75):
        try:
            # Validate inputs
            if base_image.ndim != 2 or segmentation.ndim != 2:
                raise ValueError("Both images must be 2D")

            if base_image.shape != segmentation.shape:
                raise ValueError("Images must have same shape")

            # Get unique classes
            unique_classes = np.unique(segmentation)
            num_classes = len(unique_classes)

            if class_names is None:
                class_names = [f"Class {i}" for i in unique_classes]
            elif len(class_names) < num_classes:
                class_names.extend([f"Class {i}" for i in range(len(class_names), num_classes)])

            # Create colormap for segmentation
            colors = plt.cm.Set1(np.linspace(0, 1, max(num_classes, 9)))
            colors[0] = [0, 0, 0, 0]  # Make background transparent
            cmap = ListedColormap(colors[:num_classes])

            # Create figure with subplots
            fig, axes = plt.subplots(1, 3, figsize=figsize)

            # Plot base image
            axes[0].imshow(base_image, cmap='gray')
            axes[0].set_title("Original Image")
            axes[0].axis('off')

            # Plot segmentation
            seg_plot = axes[1].imshow(segmentation, cmap=cmap, vmin=0, vmax=num_classes-1)
            axes[1].set_title("Segmentation")
            axes[1].axis('off')

            # Create colorbar for segmentation
            cbar = plt.colorbar(seg_plot, ax=axes[1], shrink=0.6)
            cbar.set_ticks(range(num_classes))
            cbar.set_ticklabels(class_names[:num_classes])

            # Plot overlay
            axes[2].imshow(base_image, cmap='gray')
            masked_seg = np.ma.masked_where(segmentation == 0, segmentation)
            axes[2].imshow(masked_seg, cmap=cmap, alpha=alpha, vmin=0, vmax=num_classes-1)
            axes[2].set_title(f"Overlay (α={alpha})")
            axes[2].axis('off')

            # Add legend for overlay
            legend_elements = []
            for i, class_name in enumerate(class_names[:num_classes]):
                if i > 0:  # Skip background
                    color = colors[i][:3]  # RGB only
                    legend_elements.append(
                        patches.Patch(color=color, label=class_name)
                    )

            if legend_elements:
                axes[2].legend(handles=legend_elements, loc='upper right', bbox_to_anchor=(1.2, 1))

            plt.tight_layout()

            # Save if requested
            if save_path:
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
                logger.info(f"Overlay saved to: {save_path}")

            logger.info("Segmentation overlay created successfully")
            log_system_resources(logger)

            return True

        except Exception as e:
            logger.error(f"Segmentation overlay failed: {e}")
            emergency_cleanup()
            return False

        finally:
            plt.close()


@safe_execution(max_retries=1)
def create_training_metrics_plot_safe(
    metrics_dict: Dict[str, List[float]],
    title: str = "Training Metrics",
    figsize: Tuple[float, float] = (12, 8),
    save_path: Optional[str] = None
) -> bool:
    """
    Create safe training metrics visualization.

    Args:
        metrics_dict: Dictionary with metric names and values
        title: Plot title
        figsize: Figure size
        save_path: Path to save figure

    Returns:
        Success status
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.error("Matplotlib not available")
        return False

    logger.info("Creating training metrics plot")

    with memory_safe_context(threshold=0.70):
        try:
            if not metrics_dict:
                raise ValueError("Empty metrics dictionary")

            # Determine subplot layout
            num_metrics = len(metrics_dict)
            if num_metrics == 1:
                rows, cols = 1, 1
            elif num_metrics == 2:
                rows, cols = 1, 2
            elif num_metrics <= 4:
                rows, cols = 2, 2
            else:
                rows = int(np.ceil(num_metrics / 3))
                cols = 3

            fig, axes = plt.subplots(rows, cols, figsize=figsize)

            # Handle single subplot case
            if num_metrics == 1:
                axes = [axes]
            elif rows == 1 or cols == 1:
                axes = axes.flatten()
            else:
                axes = axes.flatten()

            # Plot each metric
            for i, (metric_name, values) in enumerate(metrics_dict.items()):
                if i >= len(axes):
                    break

                ax = axes[i]

                if not values:
                    ax.text(0.5, 0.5, f"No data for {metric_name}",
                           ha='center', va='center', transform=ax.transAxes)
                    ax.set_title(metric_name)
                    continue

                epochs = range(1, len(values) + 1)

                # Plot metric
                ax.plot(epochs, values, marker='o', linewidth=2, markersize=4)
                ax.set_title(metric_name)
                ax.set_xlabel("Epoch")
                ax.set_ylabel("Value")
                ax.grid(True, alpha=0.3)

                # Add best value annotation
                if metric_name.lower() in ['loss', 'error']:
                    best_idx = np.argmin(values)
                    best_value = values[best_idx]
                    ax.annotate(f'Min: {best_value:.4f}',
                               xy=(best_idx + 1, best_value),
                               xytext=(10, 10), textcoords='offset points',
                               bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                               arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))
                else:
                    best_idx = np.argmax(values)
                    best_value = values[best_idx]
                    ax.annotate(f'Max: {best_value:.4f}',
                               xy=(best_idx + 1, best_value),
                               xytext=(10, 10), textcoords='offset points',
                               bbox=dict(boxstyle='round,pad=0.3', facecolor='lightgreen', alpha=0.7),
                               arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

            # Hide unused subplots
            for i in range(num_metrics, len(axes)):
                axes[i].set_visible(False)

            plt.suptitle(title, fontsize=16)
            plt.tight_layout()

            # Save if requested
            if save_path:
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
                logger.info(f"Metrics plot saved to: {save_path}")

            logger.info("Training metrics plot created successfully")
            return True

        except Exception as e:
            logger.error(f"Training metrics plot failed: {e}")
            emergency_cleanup()
            return False

        finally:
            plt.close()


@safe_execution(max_retries=1)
def create_confusion_matrix_safe(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    class_names: Optional[List[str]] = None,
    normalize: bool = True,
    figsize: Tuple[float, float] = (8, 6),
    save_path: Optional[str] = None
) -> bool:
    """
    Create safe confusion matrix visualization.

    Args:
        y_true: True labels
        y_pred: Predicted labels
        class_names: Class names for labels
        normalize: Whether to normalize values
        figsize: Figure size
        save_path: Path to save figure

    Returns:
        Success status
    """
    if not MATPLOTLIB_AVAILABLE:
        logger.error("Matplotlib not available")
        return False

    logger.info("Creating confusion matrix")

    with memory_safe_context(threshold=0.70):
        try:
            from sklearn.metrics import confusion_matrix

            # Calculate confusion matrix
            cm = confusion_matrix(y_true, y_pred)

            if normalize:
                cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]
                fmt = '.2f'
                title_suffix = ' (Normalized)'
            else:
                fmt = 'd'
                title_suffix = ''

            # Create figure
            fig, ax = plt.subplots(figsize=figsize)

            # Plot heatmap
            if SEABORN_AVAILABLE:
                sns.heatmap(cm, annot=True, fmt=fmt, cmap='Blues',
                           xticklabels=class_names, yticklabels=class_names,
                           ax=ax)
            else:
                im = ax.imshow(cm, interpolation='nearest', cmap='Blues')

                # Add text annotations
                thresh = cm.max() / 2.
                for i in range(cm.shape[0]):
                    for j in range(cm.shape[1]):
                        ax.text(j, i, format(cm[i, j], fmt),
                               ha="center", va="center",
                               color="white" if cm[i, j] > thresh else "black")

                # Add colorbar
                plt.colorbar(im, ax=ax)

                # Set labels
                if class_names:
                    ax.set_xticklabels(class_names)
                    ax.set_yticklabels(class_names)

            ax.set_title(f'Confusion Matrix{title_suffix}')
            ax.set_xlabel('Predicted Label')
            ax.set_ylabel('True Label')

            plt.tight_layout()

            # Save if requested
            if save_path:
                plt.savefig(save_path, dpi=150, bbox_inches='tight')
                logger.info(f"Confusion matrix saved to: {save_path}")

            logger.info("Confusion matrix created successfully")
            return True

        except Exception as e:
            logger.error(f"Confusion matrix failed: {e}")
            emergency_cleanup()
            return False

        finally:
            plt.close()


@contextmanager
def safe_plotting_context(
    style: str = "default",
    backend: str = "Agg",
    dpi: int = 100
):
    """
    Context manager for safe plotting with automatic cleanup.

    Args:
        style: Matplotlib style
        backend: Matplotlib backend
        dpi: DPI setting
    """
    if not MATPLOTLIB_AVAILABLE:
        yield
        return

    # Store original settings
    original_backend = plt.get_backend()
    original_style = plt.rcParams.copy()

    try:
        logger.debug(f"Setting up plotting context: style={style}, backend={backend}")

        # Set new backend
        plt.switch_backend(backend)

        # Set style
        if style != "default":
            plt.style.use(style)

        # Set DPI
        plt.rcParams['figure.dpi'] = dpi
        plt.rcParams['savefig.dpi'] = dpi

        # Enable memory-efficient settings
        plt.rcParams['figure.max_open_warning'] = 10
        plt.rcParams['agg.path.chunksize'] = 10000

        log_system_resources(logger)

        yield

    except Exception as e:
        logger.error(f"Plotting context failed: {e}")
        emergency_cleanup()
        raise e

    finally:
        try:
            # Restore original settings
            plt.rcParams.update(original_style)
            plt.switch_backend(original_backend)

            # Close all figures
            plt.close('all')

            # Force garbage collection
            gc.collect()

            logger.debug("Plotting context cleaned up")

        except Exception as e:
            logger.warning(f"Plotting context cleanup failed: {e}")


@safe_execution(max_retries=1)
def save_plot_safely(
    fig,
    save_path: str,
    dpi: int = 150,
    format: str = 'png',
    bbox_inches: str = 'tight'
) -> bool:
    """
    Safely save matplotlib figure with error handling.

    Args:
        fig: Matplotlib figure
        save_path: Output file path
        dpi: DPI for saved figure
        format: File format
        bbox_inches: Bounding box specification

    Returns:
        Success status
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(save_path), exist_ok=True)

        # Save figure
        fig.savefig(
            save_path,
            dpi=dpi,
            format=format,
            bbox_inches=bbox_inches,
            facecolor='white',
            edgecolor='none'
        )

        logger.info(f"Plot saved successfully: {save_path}")
        return True

    except Exception as e:
        logger.error(f"Failed to save plot: {e}")
        emergency_cleanup()
        return False


if __name__ == "__main__":
    # Test the safe visualization utilities
    logging.basicConfig(level=logging.INFO)

    print("Testing safe visualization utilities...")

    try:
        if NUMPY_AVAILABLE and MATPLOTLIB_AVAILABLE:
            # Test medical slice plot
            dummy_3d = np.random.rand(64, 64, 32)
            if create_medical_slice_plot_safe(dummy_3d, title="Test 3D Image"):
                print("✅ Medical slice plot test passed")

            # Test segmentation overlay
            dummy_image = np.random.rand(64, 64)
            dummy_seg = np.random.randint(0, 3, (64, 64))
            if create_segmentation_overlay_safe(dummy_image, dummy_seg):
                print("✅ Segmentation overlay test passed")

            # Test training metrics plot
            dummy_metrics = {
                'loss': [1.0, 0.8, 0.6, 0.4, 0.3],
                'accuracy': [0.6, 0.7, 0.8, 0.85, 0.9],
                'dice_score': [0.5, 0.6, 0.7, 0.8, 0.85]
            }
            if create_training_metrics_plot_safe(dummy_metrics):
                print("✅ Training metrics plot test passed")

            # Test plotting context
            with safe_plotting_context(style="seaborn-v0_8", backend="Agg"):
                fig, ax = plt.subplots()
                ax.plot([1, 2, 3], [1, 4, 2])
                ax.set_title("Test Plot")
                plt.close(fig)
            print("✅ Safe plotting context test passed")

        print("Safe visualization utilities test completed")

    except Exception as e:
        print(f"❌ Test failed: {e}")
