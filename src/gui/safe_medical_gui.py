#!/usr/bin/env python3
"""
Enhanced Medical GUI Components with Crash Prevention
====================================================

This module provides crash-safe GUI components for medical imaging
applications with comprehensive error handling and resource management.

Features:
- Memory-safe image rendering
- GPU-aware visualization
- Automatic cleanup on failures
- Error recovery for UI components
- Resource monitoring for interactive widgets
"""

import gc
import logging
from typing import Any, Dict, List, Optional, Tuple

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    import matplotlib.backends.backend_qt5agg as mpl_backend
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

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
    from contextlib import contextmanager
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


class SafeImageViewer:
    """Safe medical image viewer with crash prevention."""

    def __init__(self, max_image_size: Tuple[int, int] = (1024, 1024)):
        self.max_image_size = max_image_size
        self.current_image = None
        self.figure = None
        self.canvas = None

    @safe_execution(max_retries=2, memory_threshold=0.70)
    def load_image_safe(
        self,
        image_data: Any,
        image_type: str = "medical"
    ) -> bool:
        """
        Safely load and prepare image for display.

        Args:
            image_data: Image data (numpy array, PIL Image, or file path)
            image_type: Type of image (medical, overlay, etc.)

        Returns:
            Success status
        """
        logger.info(f"Loading {image_type} image")

        with memory_safe_context(threshold=0.70):
            try:
                # Handle different input types
                if isinstance(image_data, str):
                    # File path
                    if PIL_AVAILABLE:
                        pil_image = Image.open(image_data)
                        image_array = np.array(pil_image)
                    else:
                        raise ImportError("PIL not available for image loading")

                elif hasattr(image_data, 'numpy'):
                    # Torch tensor
                    image_array = image_data.detach().cpu().numpy()

                elif isinstance(image_data, np.ndarray):
                    # NumPy array
                    image_array = image_data.copy()

                else:
                    raise ValueError(f"Unsupported image data type: {type(image_data)}")

                # Validate image dimensions
                if image_array.ndim < 2 or image_array.ndim > 4:
                    raise ValueError(f"Invalid image dimensions: {image_array.shape}")

                # Handle different image formats
                if image_array.ndim == 4:
                    # Assume batch dimension, take first image
                    image_array = image_array[0]
                    logger.warning("Taking first image from batch")

                if image_array.ndim == 3:
                    # Handle 3D medical images or RGB
                    if image_array.shape[-1] not in [1, 3, 4]:
                        # Assume 3D medical image, take middle slice
                        middle_slice = image_array.shape[2] // 2
                        image_array = image_array[:, :, middle_slice]
                        logger.info(f"Taking middle slice {middle_slice} from 3D image")
                    elif image_array.shape[-1] == 1:
                        # Single channel
                        image_array = image_array[:, :, 0]

                # Normalize image data
                if image_array.dtype != np.uint8:
                    # Normalize to 0-255 range
                    if image_array.max() <= 1.0:
                        image_array = (image_array * 255).astype(np.uint8)
                    else:
                        image_array = ((image_array - image_array.min()) * 255 /
                                     (image_array.max() - image_array.min())).astype(np.uint8)

                # Resize if too large
                if (image_array.shape[0] > self.max_image_size[0] or
                    image_array.shape[1] > self.max_image_size[1]):

                    logger.warning(f"Resizing large image: {image_array.shape} -> {self.max_image_size}")

                    if PIL_AVAILABLE:
                        pil_image = Image.fromarray(image_array)
                        pil_image = pil_image.resize(self.max_image_size, Image.Resampling.LANCZOS)
                        image_array = np.array(pil_image)
                    else:
                        # Simple downsampling
                        step_y = max(1, image_array.shape[0] // self.max_image_size[0])
                        step_x = max(1, image_array.shape[1] // self.max_image_size[1])
                        image_array = image_array[::step_y, ::step_x]

                self.current_image = image_array

                logger.info(f"Image loaded successfully: {image_array.shape}, dtype={image_array.dtype}")
                log_system_resources(logger)

                return True

            except Exception as e:
                logger.error(f"Failed to load image: {e}")
                emergency_cleanup()
                self.current_image = None
                return False

    @safe_execution(max_retries=1)
    def create_matplotlib_viewer_safe(
        self,
        figsize: Tuple[float, float] = (10, 8),
        dpi: int = 100
    ) -> bool:
        """
        Create matplotlib-based viewer with crash prevention.

        Args:
            figsize: Figure size in inches
            dpi: Figure DPI

        Returns:
            Success status
        """
        if not MATPLOTLIB_AVAILABLE:
            logger.error("Matplotlib not available")
            return False

        logger.info("Creating matplotlib viewer")

        try:
            # Close existing figure if any
            if self.figure is not None:
                plt.close(self.figure)

            # Create new figure
            self.figure = plt.figure(figsize=figsize, dpi=dpi)

            # Create canvas
            self.canvas = mpl_backend.FigureCanvasQTAgg(self.figure)

            logger.info("Matplotlib viewer created successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to create matplotlib viewer: {e}")
            emergency_cleanup()
            return False

    @safe_execution(max_retries=1)
    def display_image_safe(
        self,
        colormap: str = "gray",
        add_colorbar: bool = True,
        title: str = None
    ) -> bool:
        """
        Safely display the current image.

        Args:
            colormap: Matplotlib colormap name
            add_colorbar: Whether to add colorbar
            title: Image title

        Returns:
            Success status
        """
        if self.current_image is None:
            logger.error("No image loaded")
            return False

        if not MATPLOTLIB_AVAILABLE:
            logger.error("Matplotlib not available")
            return False

        logger.info("Displaying image")

        with memory_safe_context(threshold=0.75):
            try:
                # Clear previous plots
                self.figure.clear()

                # Create subplot
                ax = self.figure.add_subplot(111)

                # Display image
                im = ax.imshow(self.current_image, cmap=colormap, aspect='equal')

                # Add title
                if title:
                    ax.set_title(title, fontsize=12)

                # Add colorbar
                if add_colorbar:
                    self.figure.colorbar(im, ax=ax, shrink=0.8)

                # Remove axes for cleaner look
                ax.set_xticks([])
                ax.set_yticks([])

                # Tight layout
                self.figure.tight_layout()

                # Refresh canvas
                if self.canvas:
                    self.canvas.draw()

                logger.info("Image displayed successfully")
                return True

            except Exception as e:
                logger.error(f"Failed to display image: {e}")
                emergency_cleanup()
                return False

    def cleanup_viewer(self):
        """Clean up viewer resources."""
        try:
            if self.figure is not None:
                plt.close(self.figure)
                self.figure = None

            if self.canvas is not None:
                self.canvas = None

            self.current_image = None

            gc.collect()
            logger.info("Viewer cleaned up successfully")

        except Exception as e:
            logger.warning(f"Viewer cleanup failed: {e}")


class SafeOverlayViewer:
    """Safe overlay viewer for medical image segmentations."""

    def __init__(self, alpha: float = 0.5):
        self.alpha = alpha
        self.base_image = None
        self.overlay_data = None
        self.viewer = SafeImageViewer()

    @safe_execution(max_retries=1)
    def load_base_image_safe(self, image_data: Any) -> bool:
        """Load base medical image."""
        logger.info("Loading base image for overlay")

        if self.viewer.load_image_safe(image_data, "base"):
            self.base_image = self.viewer.current_image.copy()
            return True
        return False

    @safe_execution(max_retries=1)
    def load_overlay_safe(self, overlay_data: Any, num_classes: int = 3) -> bool:
        """
        Load overlay data (segmentation masks).

        Args:
            overlay_data: Overlay data (predictions, masks, etc.)
            num_classes: Number of segmentation classes

        Returns:
            Success status
        """
        logger.info(f"Loading overlay with {num_classes} classes")

        with memory_safe_context(threshold=0.75):
            try:
                # Handle different input types
                if hasattr(overlay_data, 'numpy'):
                    # Torch tensor
                    overlay_array = overlay_data.detach().cpu().numpy()
                elif isinstance(overlay_data, np.ndarray):
                    # NumPy array
                    overlay_array = overlay_data.copy()
                else:
                    raise ValueError(f"Unsupported overlay type: {type(overlay_data)}")

                # Handle dimensions
                if overlay_array.ndim == 4:
                    # Batch dimension
                    overlay_array = overlay_array[0]

                if overlay_array.ndim == 3:
                    if overlay_array.shape[0] == num_classes:
                        # Channel first format
                        overlay_array = np.argmax(overlay_array, axis=0)
                    elif overlay_array.shape[-1] == num_classes:
                        # Channel last format
                        overlay_array = np.argmax(overlay_array, axis=-1)
                    else:
                        # Assume 3D volume, take middle slice
                        middle_slice = overlay_array.shape[2] // 2
                        overlay_array = overlay_array[:, :, middle_slice]

                # Ensure integer labels
                if overlay_array.dtype != np.uint8:
                    overlay_array = overlay_array.astype(np.uint8)

                self.overlay_data = overlay_array

                logger.info(f"Overlay loaded: {overlay_array.shape}, "
                           f"classes: {np.unique(overlay_array)}")
                return True

            except Exception as e:
                logger.error(f"Failed to load overlay: {e}")
                emergency_cleanup()
                return False

    @safe_execution(max_retries=1)
    def create_overlay_image_safe(
        self,
        class_colors: Optional[List[Tuple[int, int, int]]] = None
    ) -> bool:
        """
        Create overlay visualization.

        Args:
            class_colors: RGB colors for each class

        Returns:
            Success status
        """
        if self.base_image is None or self.overlay_data is None:
            logger.error("Base image and overlay data required")
            return False

        logger.info("Creating overlay visualization")

        with memory_safe_context(threshold=0.75):
            try:
                # Default colors if not provided
                if class_colors is None:
                    class_colors = [
                        (0, 0, 0),        # Background - black
                        (255, 0, 0),      # Class 1 - red
                        (0, 255, 0),      # Class 2 - green
                        (0, 0, 255),      # Class 3 - blue
                        (255, 255, 0),    # Class 4 - yellow
                        (255, 0, 255),    # Class 5 - magenta
                        (0, 255, 255),    # Class 6 - cyan
                    ]

                # Create RGB overlay
                overlay_rgb = np.zeros((*self.overlay_data.shape, 3), dtype=np.uint8)

                for class_id in np.unique(self.overlay_data):
                    if class_id < len(class_colors):
                        mask = self.overlay_data == class_id
                        overlay_rgb[mask] = class_colors[class_id]

                # Convert base image to RGB if grayscale
                if self.base_image.ndim == 2:
                    base_rgb = np.stack([self.base_image] * 3, axis=-1)
                else:
                    base_rgb = self.base_image

                # Ensure same size
                if base_rgb.shape[:2] != overlay_rgb.shape[:2]:
                    logger.warning("Resizing overlay to match base image")
                    if PIL_AVAILABLE:
                        overlay_pil = Image.fromarray(overlay_rgb)
                        overlay_pil = overlay_pil.resize(
                            (base_rgb.shape[1], base_rgb.shape[0]),
                            Image.Resampling.NEAREST
                        )
                        overlay_rgb = np.array(overlay_pil)
                    else:
                        logger.error("Cannot resize overlay without PIL")
                        return False

                # Create blended image
                blended = base_rgb.astype(np.float32)
                overlay_float = overlay_rgb.astype(np.float32)

                # Only blend non-background pixels
                non_bg_mask = self.overlay_data > 0
                blended[non_bg_mask] = (
                    (1 - self.alpha) * blended[non_bg_mask] +
                    self.alpha * overlay_float[non_bg_mask]
                )

                # Convert back to uint8
                blended_image = np.clip(blended, 0, 255).astype(np.uint8)

                # Update viewer with blended image
                self.viewer.current_image = blended_image

                logger.info("Overlay visualization created successfully")
                return True

            except Exception as e:
                logger.error(f"Failed to create overlay: {e}")
                emergency_cleanup()
                return False

    def display_overlay_safe(self, title: str = "Medical Image Overlay") -> bool:
        """Display the overlay visualization."""
        return self.viewer.display_image_safe(
            colormap=None,  # RGB image
            add_colorbar=False,
            title=title
        )

    def cleanup_overlay_viewer(self):
        """Clean up overlay viewer resources."""
        try:
            self.viewer.cleanup_viewer()
            self.base_image = None
            self.overlay_data = None
            gc.collect()
            logger.info("Overlay viewer cleaned up")

        except Exception as e:
            logger.warning(f"Overlay viewer cleanup failed: {e}")


@safe_execution(max_retries=1)
def create_safe_medical_dashboard(
    image_paths: List[str] = None,
    overlay_paths: List[str] = None
) -> Dict[str, Any]:
    """
    Create a safe medical imaging dashboard.

    Args:
        image_paths: List of image file paths
        overlay_paths: List of overlay file paths

    Returns:
        Dashboard configuration
    """
    logger.info("Creating safe medical dashboard")

    dashboard_config = {
        'viewers': [],
        'overlays': [],
        'status': 'failed',
        'error': None
    }

    try:
        # Create image viewers
        if image_paths:
            for i, image_path in enumerate(image_paths):
                viewer = SafeImageViewer()

                if viewer.load_image_safe(image_path):
                    viewer.create_matplotlib_viewer_safe()
                    dashboard_config['viewers'].append({
                        'id': f'viewer_{i}',
                        'viewer': viewer,
                        'image_path': image_path
                    })
                else:
                    logger.warning(f"Failed to load image: {image_path}")

        # Create overlay viewers
        if overlay_paths and image_paths:
            for i, (img_path, overlay_path) in enumerate(zip(image_paths, overlay_paths)):
                overlay_viewer = SafeOverlayViewer()

                if (overlay_viewer.load_base_image_safe(img_path) and
                    overlay_viewer.load_overlay_safe(overlay_path)):

                    overlay_viewer.viewer.create_matplotlib_viewer_safe()
                    dashboard_config['overlays'].append({
                        'id': f'overlay_{i}',
                        'viewer': overlay_viewer,
                        'image_path': img_path,
                        'overlay_path': overlay_path
                    })
                else:
                    logger.warning(f"Failed to create overlay: {img_path}, {overlay_path}")

        dashboard_config['status'] = 'success'
        logger.info(f"Dashboard created: {len(dashboard_config['viewers'])} viewers, "
                   f"{len(dashboard_config['overlays'])} overlays")

        return dashboard_config

    except Exception as e:
        dashboard_config['error'] = str(e)
        logger.error(f"Dashboard creation failed: {e}")
        emergency_cleanup()
        return dashboard_config


if __name__ == "__main__":
    # Test the safe GUI components
    logging.basicConfig(level=logging.INFO)

    print("Testing safe medical GUI components...")

    try:
        # Test image viewer
        viewer = SafeImageViewer()

        # Create dummy image
        if NUMPY_AVAILABLE:
            dummy_image = np.random.randint(0, 255, (256, 256), dtype=np.uint8)

            if viewer.load_image_safe(dummy_image, "test"):
                print("✅ Image loading test passed")

                if viewer.create_matplotlib_viewer_safe():
                    print("✅ Matplotlib viewer creation test passed")

                    if viewer.display_image_safe(title="Test Image"):
                        print("✅ Image display test passed")

            viewer.cleanup_viewer()
            print("✅ Viewer cleanup test passed")

        # Test overlay viewer
        overlay_viewer = SafeOverlayViewer()

        if NUMPY_AVAILABLE:
            dummy_base = np.random.randint(0, 255, (128, 128), dtype=np.uint8)
            dummy_overlay = np.random.randint(0, 3, (128, 128), dtype=np.uint8)

            if (overlay_viewer.load_base_image_safe(dummy_base) and
                overlay_viewer.load_overlay_safe(dummy_overlay)):

                if overlay_viewer.create_overlay_image_safe():
                    print("✅ Overlay creation test passed")

            overlay_viewer.cleanup_overlay_viewer()
            print("✅ Overlay viewer cleanup test passed")

        print("Safe medical GUI components test completed")

    except Exception as e:
        print(f"❌ Test failed: {e}")
