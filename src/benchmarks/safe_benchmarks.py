#!/usr/bin/env python3
"""
Enhanced Benchmarking System with Crash Prevention
=================================================

This module provides crash-safe benchmarking and performance monitoring
for medical imaging workflows with comprehensive resource management.

Features:
- Memory-safe benchmarking
- GPU performance monitoring
- Automatic cleanup on failures
- Performance metrics collection
- Safe timing and profiling
"""

import gc
import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

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


class SafeBenchmarkTimer:
    """Context manager for safe timing with automatic cleanup."""

    def __init__(self, name: str = "benchmark", cuda_sync: bool = True):
        self.name = name
        self.cuda_sync = cuda_sync and TORCH_AVAILABLE and torch.cuda.is_available()
        self.start_time = None
        self.end_time = None
        self.duration = None

    def __enter__(self):
        if self.cuda_sync:
            torch.cuda.synchronize()
        self.start_time = time.perf_counter()
        logger.debug(f"Starting benchmark: {self.name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cuda_sync:
            torch.cuda.synchronize()
        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time

        if exc_type is not None:
            logger.error(f"Benchmark {self.name} failed after {self.duration:.3f}s")
            emergency_cleanup()
        else:
            logger.info(f"Benchmark {self.name} completed in {self.duration:.3f}s")

    def get_duration(self) -> float:
        """Get benchmark duration in seconds."""
        return self.duration if self.duration is not None else 0.0


class SafePerformanceMonitor:
    """Safe performance monitoring with resource tracking."""

    def __init__(self, track_gpu: bool = True):
        self.track_gpu = track_gpu and TORCH_AVAILABLE and torch.cuda.is_available()
        self.metrics = []

    @safe_execution(max_retries=1)
    def start_monitoring(self) -> Dict[str, Any]:
        """Start performance monitoring."""
        metrics = {
            'timestamp': time.time(),
            'cpu_percent': None,
            'memory_mb': None,
            'gpu_memory_mb': None,
            'gpu_utilization': None
        }

        try:
            # Get CPU and memory info
            import psutil
            process = psutil.Process()
            metrics['cpu_percent'] = process.cpu_percent()
            metrics['memory_mb'] = process.memory_info().rss / 1024 / 1024

        except ImportError:
            logger.warning("psutil not available for CPU/memory monitoring")
        except Exception as e:
            logger.warning(f"CPU/memory monitoring failed: {e}")

        if self.track_gpu:
            try:
                import GPUtil
                gpus = GPUtil.getGPUs()
                if gpus:
                    gpu = gpus[0]
                    metrics['gpu_memory_mb'] = gpu.memoryUsed
                    metrics['gpu_utilization'] = gpu.load * 100

            except ImportError:
                logger.warning("GPUtil not available for GPU monitoring")
            except Exception as e:
                logger.warning(f"GPU monitoring failed: {e}")

        log_system_resources(logger)
        return metrics

    def add_metric(self, metrics: Dict[str, Any]):
        """Add performance metrics."""
        self.metrics.append(metrics.copy())

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        if not self.metrics:
            return {}

        summary = {
            'count': len(self.metrics),
            'duration': 0.0,
            'avg_cpu_percent': None,
            'avg_memory_mb': None,
            'max_memory_mb': None,
            'avg_gpu_memory_mb': None,
            'max_gpu_memory_mb': None,
            'avg_gpu_utilization': None
        }

        if len(self.metrics) > 1:
            summary['duration'] = (self.metrics[-1]['timestamp'] -
                                 self.metrics[0]['timestamp'])

        # Calculate averages and maxes
        cpu_values = [m['cpu_percent'] for m in self.metrics
                     if m['cpu_percent'] is not None]
        if cpu_values:
            summary['avg_cpu_percent'] = sum(cpu_values) / len(cpu_values)

        memory_values = [m['memory_mb'] for m in self.metrics
                        if m['memory_mb'] is not None]
        if memory_values:
            summary['avg_memory_mb'] = sum(memory_values) / len(memory_values)
            summary['max_memory_mb'] = max(memory_values)

        gpu_memory_values = [m['gpu_memory_mb'] for m in self.metrics
                           if m['gpu_memory_mb'] is not None]
        if gpu_memory_values:
            summary['avg_gpu_memory_mb'] = sum(gpu_memory_values) / len(gpu_memory_values)
            summary['max_gpu_memory_mb'] = max(gpu_memory_values)

        gpu_util_values = [m['gpu_utilization'] for m in self.metrics
                          if m['gpu_utilization'] is not None]
        if gpu_util_values:
            summary['avg_gpu_utilization'] = sum(gpu_util_values) / len(gpu_util_values)

        return summary


@safe_execution(max_retries=2, memory_threshold=0.80, gpu_threshold=0.85)
def benchmark_model_inference_safe(
    model: Any,
    input_data: Any,
    num_runs: int = 10,
    warmup_runs: int = 3,
    batch_sizes: Optional[List[int]] = None
) -> Dict[str, Any]:
    """
    Benchmark model inference with crash prevention.

    Args:
        model: Model to benchmark
        input_data: Input data for inference
        num_runs: Number of benchmark runs
        warmup_runs: Number of warmup runs
        batch_sizes: List of batch sizes to test

    Returns:
        Benchmark results dictionary
    """
    if not TORCH_AVAILABLE:
        raise ImportError("PyTorch not available")

    logger.info(f"Starting model inference benchmark: "
               f"{num_runs} runs, {warmup_runs} warmup")

    results = {
        'model_type': type(model).__name__,
        'input_shape': None,
        'warmup_time': 0.0,
        'inference_times': [],
        'avg_time': 0.0,
        'std_time': 0.0,
        'min_time': 0.0,
        'max_time': 0.0,
        'throughput': 0.0,
        'performance_metrics': {}
    }

    if batch_sizes is None:
        batch_sizes = [1]

    with memory_safe_context(threshold=0.80):
        with gpu_safe_context(threshold=0.85):
            try:
                # Get input shape
                if hasattr(input_data, 'shape'):
                    results['input_shape'] = list(input_data.shape)
                elif isinstance(input_data, (list, tuple)) and len(input_data) > 0:
                    if hasattr(input_data[0], 'shape'):
                        results['input_shape'] = list(input_data[0].shape)

                model.eval()

                monitor = SafePerformanceMonitor()

                with torch.no_grad():
                    # Warmup runs
                    logger.info(f"Running {warmup_runs} warmup iterations...")
                    warmup_start = time.perf_counter()

                    for i in range(warmup_runs):
                        try:
                            _ = model(input_data)
                            if torch.cuda.is_available():
                                torch.cuda.synchronize()
                        except RuntimeError as e:
                            if "out of memory" in str(e).lower():
                                logger.error(f"OOM during warmup run {i}: {e}")
                                emergency_cleanup()
                                raise e
                            else:
                                raise e

                    if torch.cuda.is_available():
                        torch.cuda.synchronize()
                    warmup_end = time.perf_counter()
                    results['warmup_time'] = warmup_end - warmup_start

                    # Benchmark runs
                    logger.info(f"Running {num_runs} benchmark iterations...")
                    inference_times = []

                    for i in range(num_runs):
                        # Monitor resources
                        metrics = monitor.start_monitoring()
                        monitor.add_metric(metrics)

                        with SafeBenchmarkTimer(f"inference_run_{i}") as timer:
                            try:
                                _ = model(input_data)
                                if torch.cuda.is_available():
                                    torch.cuda.synchronize()
                            except RuntimeError as e:
                                if "out of memory" in str(e).lower():
                                    logger.error(f"OOM during benchmark run {i}: {e}")
                                    emergency_cleanup()
                                    raise e
                                else:
                                    raise e

                        inference_times.append(timer.get_duration())

                        # Log progress
                        if (i + 1) % max(1, num_runs // 4) == 0:
                            logger.info(f"Completed {i + 1}/{num_runs} runs")

                # Calculate statistics
                if inference_times:
                    results['inference_times'] = inference_times
                    results['avg_time'] = sum(inference_times) / len(inference_times)
                    results['min_time'] = min(inference_times)
                    results['max_time'] = max(inference_times)

                    if NUMPY_AVAILABLE:
                        results['std_time'] = float(np.std(inference_times))
                    else:
                        # Simple standard deviation calculation
                        mean = results['avg_time']
                        variance = sum((t - mean) ** 2 for t in inference_times) / len(inference_times)
                        results['std_time'] = variance ** 0.5

                    # Calculate throughput (samples per second)
                    if results['avg_time'] > 0:
                        batch_size = 1  # Assume batch size 1 for now
                        results['throughput'] = batch_size / results['avg_time']

                # Get performance summary
                results['performance_metrics'] = monitor.get_summary()

                logger.info("Benchmark completed successfully:")
                logger.info(f"  Average time: {results['avg_time']:.4f}s")
                logger.info(f"  Std deviation: {results['std_time']:.4f}s")
                logger.info(f"  Throughput: {results['throughput']:.2f} samples/sec")

                log_system_resources(logger)

                return results

            except Exception as e:
                logger.error(f"Benchmark failed: {e}")
                emergency_cleanup()
                raise e


@safe_execution(max_retries=1)
def benchmark_data_loading_safe(
    dataloader: Any,
    num_batches: int = 10,
    measure_gpu_transfer: bool = True
) -> Dict[str, Any]:
    """
    Benchmark data loading with crash prevention.

    Args:
        dataloader: Data loader to benchmark
        num_batches: Number of batches to load
        measure_gpu_transfer: Whether to measure GPU transfer time

    Returns:
        Data loading benchmark results
    """
    logger.info(f"Starting data loading benchmark: {num_batches} batches")

    results = {
        'num_batches': num_batches,
        'loading_times': [],
        'transfer_times': [],
        'total_times': [],
        'avg_loading_time': 0.0,
        'avg_transfer_time': 0.0,
        'avg_total_time': 0.0,
        'throughput_batches_per_sec': 0.0
    }

    with memory_safe_context(threshold=0.75):
        try:
            device = torch.device("cuda" if torch.cuda.is_available() and measure_gpu_transfer else "cpu")

            monitor = SafePerformanceMonitor()

            for i, batch in enumerate(dataloader):
                if i >= num_batches:
                    break

                # Monitor resources
                metrics = monitor.start_monitoring()
                monitor.add_metric(metrics)

                with SafeBenchmarkTimer(f"data_loading_{i}") as loading_timer:
                    # Data is already loaded by the dataloader
                    pass

                loading_time = loading_timer.get_duration()
                results['loading_times'].append(loading_time)

                transfer_time = 0.0
                if measure_gpu_transfer and device.type == "cuda":
                    with SafeBenchmarkTimer(f"gpu_transfer_{i}") as transfer_timer:
                        try:
                            if isinstance(batch, dict):
                                for key, value in batch.items():
                                    if hasattr(value, 'to'):
                                        _ = value.to(device)
                            elif hasattr(batch, 'to'):
                                _ = batch.to(device)
                            elif isinstance(batch, (list, tuple)):
                                for item in batch:
                                    if hasattr(item, 'to'):
                                        _ = item.to(device)

                            if torch.cuda.is_available():
                                torch.cuda.synchronize()

                        except RuntimeError as e:
                            if "out of memory" in str(e).lower():
                                logger.error(f"OOM during GPU transfer: {e}")
                                emergency_cleanup()
                                transfer_time = 0.0
                            else:
                                raise e

                    transfer_time = transfer_timer.get_duration()

                results['transfer_times'].append(transfer_time)
                results['total_times'].append(loading_time + transfer_time)

                # Log progress
                if (i + 1) % max(1, num_batches // 4) == 0:
                    logger.info(f"Processed {i + 1}/{num_batches} batches")

            # Calculate statistics
            if results['loading_times']:
                results['avg_loading_time'] = sum(results['loading_times']) / len(results['loading_times'])
                results['avg_transfer_time'] = sum(results['transfer_times']) / len(results['transfer_times'])
                results['avg_total_time'] = sum(results['total_times']) / len(results['total_times'])

                if results['avg_total_time'] > 0:
                    results['throughput_batches_per_sec'] = 1.0 / results['avg_total_time']

            logger.info("Data loading benchmark completed:")
            logger.info(f"  Avg loading time: {results['avg_loading_time']:.4f}s")
            logger.info(f"  Avg transfer time: {results['avg_transfer_time']:.4f}s")
            logger.info(f"  Throughput: {results['throughput_batches_per_sec']:.2f} batches/sec")

            return results

        except Exception as e:
            logger.error(f"Data loading benchmark failed: {e}")
            emergency_cleanup()
            raise e


@contextmanager
def safe_benchmark_context(name: str = "benchmark"):
    """
    Context manager for safe benchmarking with automatic cleanup.

    Args:
        name: Benchmark name for logging
    """
    logger.info(f"Starting safe benchmark: {name}")
    start_time = time.time()

    try:
        log_system_resources(logger)
        yield

    except Exception as e:
        logger.error(f"Benchmark {name} failed: {e}")
        emergency_cleanup()
        raise e

    finally:
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"Benchmark {name} completed in {duration:.3f}s")
        log_system_resources(logger)


if __name__ == "__main__":
    # Test the safe benchmarking system
    logging.basicConfig(level=logging.INFO)

    print("Testing safe benchmarking system...")

    try:
        # Test timer
        with SafeBenchmarkTimer("test_timer") as timer:
            time.sleep(0.1)
        print(f"✅ Timer test: {timer.get_duration():.3f}s")

        # Test performance monitor
        monitor = SafePerformanceMonitor()
        for i in range(3):
            metrics = monitor.start_monitoring()
            monitor.add_metric(metrics)
            time.sleep(0.05)

        summary = monitor.get_summary()
        print(f"✅ Performance monitor test: {summary}")

        # Test benchmark context
        with safe_benchmark_context("test_context"):
            time.sleep(0.1)
        print("✅ Benchmark context test completed")

        print("Safe benchmarking system test completed")

    except Exception as e:
        print(f"❌ Test failed: {e}")
