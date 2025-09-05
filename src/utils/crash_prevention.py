#!/usr/bin/env python3
"""
Comprehensive Crash Prevention Utilities
==========================================

This module provides crash prevention utilities that can be used throughout the codebase
to prevent memory overflows, GPU crashes, and system instability during medical imaging workflows.

Features:
- Memory monitoring and automatic cleanup
- GPU memory management
- Exception handling decorators
- Process monitoring
- Emergency recovery procedures
- Context managers for safe operations
"""

import functools
import gc
import logging
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import GPUtil
    GPUTIL_AVAILABLE = True
except ImportError:
    GPUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)


class MemoryMonitor:
    """Real-time memory monitoring with automatic cleanup"""

    def __init__(self, threshold: float = 0.85, check_interval: float = 1.0):
        self.threshold = threshold
        self.check_interval = check_interval
        self.monitoring = False
        self.monitor_thread = None
        self.callbacks = []

    def add_cleanup_callback(self, callback: Callable):
        """Add callback to execute when memory threshold exceeded"""
        self.callbacks.append(callback)

    def start_monitoring(self):
        """Start background memory monitoring"""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info(f"Memory monitoring started with {self.threshold*100:.1f}% threshold")

    def stop_monitoring(self):
        """Stop background memory monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        logger.info("Memory monitoring stopped")

    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring:
            try:
                if PSUTIL_AVAILABLE:
                    memory_percent = psutil.virtual_memory().percent / 100.0
                    if memory_percent > self.threshold:
                        logger.warning(f"Memory usage {memory_percent:.1%} exceeds threshold {self.threshold:.1%}")
                        self._execute_cleanup()

                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Memory monitoring error: {e}")
                time.sleep(self.check_interval * 2)

    def _execute_cleanup(self):
        """Execute cleanup callbacks"""
        for callback in self.callbacks:
            try:
                callback()
            except Exception as e:
                logger.error(f"Cleanup callback failed: {e}")


class GPUMonitor:
    """GPU memory monitoring and management"""

    def __init__(self, threshold: float = 0.90):
        self.threshold = threshold

    def get_gpu_usage(self) -> List[Dict[str, float]]:
        """Get current GPU usage statistics"""
        if not GPUTIL_AVAILABLE:
            return []

        try:
            gpus = GPUtil.getGPUs()
            return [{
                'id': gpu.id,
                'memory_used': gpu.memoryUsed,
                'memory_total': gpu.memoryTotal,
                'memory_percent': gpu.memoryUtil,
                'utilization': gpu.load
            } for gpu in gpus]
        except Exception as e:
            logger.error(f"GPU monitoring error: {e}")
            return []

    def clear_gpu_cache(self):
        """Clear GPU cache if PyTorch available"""
        if TORCH_AVAILABLE and torch.cuda.is_available():
            try:
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                logger.info("GPU cache cleared")
            except Exception as e:
                logger.error(f"GPU cache clear failed: {e}")

    def check_gpu_memory(self) -> bool:
        """Check if GPU memory usage is within limits"""
        gpu_stats = self.get_gpu_usage()
        for gpu in gpu_stats:
            if gpu['memory_percent'] > self.threshold:
                logger.warning(f"GPU {gpu['id']} memory usage {gpu['memory_percent']:.1%} exceeds threshold")
                return False
        return True


def safe_execution(max_retries: int = 3,
                  cleanup_on_failure: bool = True,
                  memory_threshold: float = 0.85,
                  gpu_threshold: float = 0.90):
    """
    Decorator for safe execution with automatic cleanup and retry logic

    Args:
        max_retries: Maximum number of retry attempts
        cleanup_on_failure: Whether to run cleanup on failure
        memory_threshold: Memory usage threshold for warnings
        gpu_threshold: GPU memory threshold for warnings
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            memory_monitor = MemoryMonitor(memory_threshold)
            gpu_monitor = GPUMonitor(gpu_threshold)

            # Add cleanup callbacks
            memory_monitor.add_cleanup_callback(lambda: gc.collect())
            memory_monitor.add_cleanup_callback(gpu_monitor.clear_gpu_cache)

            # Start monitoring
            memory_monitor.start_monitoring()

            last_exception = None
            for attempt in range(max_retries + 1):
                try:
                    # Check resources before execution
                    if PSUTIL_AVAILABLE:
                        memory_percent = psutil.virtual_memory().percent / 100.0
                        if memory_percent > memory_threshold:
                            logger.warning(f"High memory usage {memory_percent:.1%} before execution")

                    if not gpu_monitor.check_gpu_memory():
                        gpu_monitor.clear_gpu_cache()

                    # Execute function
                    result = func(*args, **kwargs)
                    memory_monitor.stop_monitoring()
                    return result

                except Exception as e:
                    last_exception = e
                    logger.error(f"Execution failed (attempt {attempt + 1}/{max_retries + 1}): {e}")

                    if cleanup_on_failure:
                        try:
                            gc.collect()
                            gpu_monitor.clear_gpu_cache()
                            time.sleep(1.0)  # Brief pause before retry
                        except Exception as cleanup_error:
                            logger.error(f"Cleanup failed: {cleanup_error}")

                    if attempt < max_retries:
                        logger.info("Retrying in 2 seconds...")
                        time.sleep(2.0)

            memory_monitor.stop_monitoring()
            logger.error(f"All {max_retries + 1} attempts failed")
            raise last_exception

        return wrapper
    return decorator


@contextmanager
def memory_safe_context(threshold: float = 0.85, cleanup_interval: float = 10.0):
    """
    Context manager for memory-safe operations

    Args:
        threshold: Memory usage threshold
        cleanup_interval: Interval between automatic cleanups
    """
    monitor = MemoryMonitor(threshold)

    # Add automatic cleanup
    def auto_cleanup():
        gc.collect()
        if TORCH_AVAILABLE and torch.cuda.is_available():
            torch.cuda.empty_cache()

    monitor.add_cleanup_callback(auto_cleanup)

    try:
        monitor.start_monitoring()
        logger.info("Entered memory-safe context")
        yield monitor
    except Exception as e:
        logger.error(f"Error in memory-safe context: {e}")
        auto_cleanup()
        raise
    finally:
        monitor.stop_monitoring()
        auto_cleanup()
        logger.info("Exited memory-safe context")


@contextmanager
def gpu_safe_context(threshold: float = 0.90):
    """
    Context manager for GPU-safe operations

    Args:
        threshold: GPU memory usage threshold
    """
    gpu_monitor = GPUMonitor(threshold)

    try:
        # Clear cache before starting
        gpu_monitor.clear_gpu_cache()

        # Check initial state
        if not gpu_monitor.check_gpu_memory():
            logger.warning("High GPU memory usage at context start")

        logger.info("Entered GPU-safe context")
        yield gpu_monitor

    except Exception as e:
        logger.error(f"Error in GPU-safe context: {e}")
        gpu_monitor.clear_gpu_cache()
        raise
    finally:
        gpu_monitor.clear_gpu_cache()
        logger.info("Exited GPU-safe context")


def emergency_cleanup():
    """Emergency cleanup procedure"""
    logger.warning("🚨 EMERGENCY CLEANUP TRIGGERED")

    try:
        # Force garbage collection
        gc.collect()
        logger.info("✅ Garbage collection completed")

        # Clear GPU cache
        if TORCH_AVAILABLE and torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            logger.info("✅ GPU cache cleared")

        # Kill high-memory Python processes if needed
        if PSUTIL_AVAILABLE:
            current_process = psutil.Process()
            memory_info = current_process.memory_info()

            # If current process is using > 4GB, reduce priority
            if memory_info.rss > 4 * 1024 * 1024 * 1024:  # 4GB
                try:
                    current_process.nice(19)  # Lowest priority
                    logger.info("✅ Process priority reduced")
                except Exception as e:
                    logger.error(f"Failed to reduce priority: {e}")

        logger.info("✅ Emergency cleanup completed")

    except Exception as e:
        logger.error(f"❌ Emergency cleanup failed: {e}")


def check_system_resources() -> Dict[str, Any]:
    """Check current system resources"""
    resources = {
        'timestamp': time.time(),
        'memory_available': True,
        'gpu_available': True,
        'disk_space_available': True
    }

    try:
        if PSUTIL_AVAILABLE:
            # Memory check
            memory = psutil.virtual_memory()
            resources.update({
                'memory_percent': memory.percent,
                'memory_used_gb': memory.used / (1024**3),
                'memory_total_gb': memory.total / (1024**3),
                'memory_available': memory.percent < 85.0
            })

            # Disk space check
            disk = psutil.disk_usage('/')
            resources.update({
                'disk_percent': (disk.used / disk.total) * 100,
                'disk_free_gb': disk.free / (1024**3),
                'disk_space_available': (disk.free / disk.total) > 0.1  # 10% free
            })

        if GPUTIL_AVAILABLE:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]  # First GPU
                resources.update({
                    'gpu_memory_percent': gpu.memoryUtil * 100,
                    'gpu_memory_used_mb': gpu.memoryUsed,
                    'gpu_memory_total_mb': gpu.memoryTotal,
                    'gpu_available': gpu.memoryUtil < 0.90
                })

    except Exception as e:
        logger.error(f"Resource check failed: {e}")

    return resources


def log_system_resources(logger_instance: Optional[logging.Logger] = None):
    """Log current system resources"""
    if logger_instance is None:
        logger_instance = logger

    resources = check_system_resources()

    logger_instance.info("=== System Resources ===")
    if 'memory_percent' in resources:
        logger_instance.info(f"Memory: {resources['memory_percent']:.1f}% "
                           f"({resources['memory_used_gb']:.1f}GB / {resources['memory_total_gb']:.1f}GB)")
    if 'gpu_memory_percent' in resources:
        logger_instance.info(f"GPU: {resources['gpu_memory_percent']:.1f}% "
                           f"({resources['gpu_memory_used_mb']:.0f}MB / {resources['gpu_memory_total_mb']:.0f}MB)")
    if 'disk_percent' in resources:
        logger_instance.info(f"Disk: {resources['disk_percent']:.1f}% "
                           f"({resources['disk_free_gb']:.1f}GB free)")
    logger_instance.info("======================")


class CrashPrevention:
    """Main crash prevention coordinator"""

    def __init__(self, log_dir: str = "logs/crash_prevention"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.memory_monitor = MemoryMonitor()
        self.gpu_monitor = GPUMonitor()

        # Setup logging
        self._setup_logging()

    def _setup_logging(self):
        """Setup crash prevention logging"""
        log_file = self.log_dir / f"crash_prevention_{int(time.time())}.log"

        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        ))

        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    def start_protection(self):
        """Start comprehensive crash protection"""
        logger.info("🛡️ Starting crash protection system")

        # Add cleanup callbacks
        self.memory_monitor.add_cleanup_callback(lambda: gc.collect())
        self.memory_monitor.add_cleanup_callback(self.gpu_monitor.clear_gpu_cache)
        self.memory_monitor.add_cleanup_callback(emergency_cleanup)

        # Start monitoring
        self.memory_monitor.start_monitoring()

        # Log initial state
        log_system_resources()

    def stop_protection(self):
        """Stop crash protection"""
        logger.info("🛡️ Stopping crash protection system")
        self.memory_monitor.stop_monitoring()

        # Final cleanup
        gc.collect()
        self.gpu_monitor.clear_gpu_cache()


# Global crash prevention instance
_global_crash_prevention = None


def start_global_protection(log_dir: str = "logs/crash_prevention"):
    """Start global crash protection"""
    global _global_crash_prevention
    if _global_crash_prevention is None:
        _global_crash_prevention = CrashPrevention(log_dir)
        _global_crash_prevention.start_protection()


def stop_global_protection():
    """Stop global crash protection"""
    global _global_crash_prevention
    if _global_crash_prevention is not None:
        _global_crash_prevention.stop_protection()
        _global_crash_prevention = None


# Convenience decorators
memory_safe = lambda func: safe_execution()(func)
gpu_safe = lambda func: safe_execution(gpu_threshold=0.80)(func)
ultra_safe = lambda func: safe_execution(max_retries=5, memory_threshold=0.75, gpu_threshold=0.80)(func)


if __name__ == "__main__":
    # Test the crash prevention system
    logging.basicConfig(level=logging.INFO)

    print("Testing crash prevention system...")

    # Test memory monitoring
    with memory_safe_context(threshold=0.5):
        print("Memory safe context active")
        time.sleep(2)

    # Test GPU monitoring
    with gpu_safe_context():
        print("GPU safe context active")
        time.sleep(2)

    # Test safe execution decorator
    @safe_execution(max_retries=2)
    def test_function():
        print("Test function executed safely")
        return "success"

    result = test_function()
    print(f"Result: {result}")

    print("Crash prevention system test completed")
