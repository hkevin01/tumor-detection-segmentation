#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Performance Tracking for Medical Image Segmentation Benchmarking

This module provides comprehensive performance tracking capabilities including
resource monitoring, training profiling, and performance analysis for medical
image segmentation models.

Key Features:
- GPU and CPU resource monitoring
- Memory usage tracking
- Training time profiling
- Inference performance analysis
- Resource utilization reports
- Performance bottleneck identification
"""

import json
import logging
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch not available. GPU monitoring will be limited.")

try:
    import pynvml
    NVIDIA_ML_AVAILABLE = True
except ImportError:
    NVIDIA_ML_AVAILABLE = False
    logging.warning("pynvml not available. NVIDIA GPU monitoring will be limited.")


@dataclass
class ResourceSnapshot:
    """Single snapshot of resource utilization."""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    gpu_memory_mb: Optional[float] = None
    gpu_utilization: Optional[float] = None
    gpu_temperature: Optional[float] = None


@dataclass
class TrainingProfile:
    """Training performance profile."""
    model_name: str
    epoch_times: List[float] = field(default_factory=list)
    batch_times: List[float] = field(default_factory=list)
    forward_times: List[float] = field(default_factory=list)
    backward_times: List[float] = field(default_factory=list)
    optimizer_times: List[float] = field(default_factory=list)
    data_loading_times: List[float] = field(default_factory=list)

    def get_statistics(self) -> Dict[str, Dict[str, float]]:
        """Get timing statistics."""
        import numpy as np

        stats = {}

        timing_data = {
            'epoch_times': self.epoch_times,
            'batch_times': self.batch_times,
            'forward_times': self.forward_times,
            'backward_times': self.backward_times,
            'optimizer_times': self.optimizer_times,
            'data_loading_times': self.data_loading_times
        }

        for name, times in timing_data.items():
            if times:
                stats[name] = {
                    'mean': float(np.mean(times)),
                    'std': float(np.std(times)),
                    'min': float(np.min(times)),
                    'max': float(np.max(times)),
                    'total': float(np.sum(times))
                }
            else:
                stats[name] = {
                    'mean': 0.0, 'std': 0.0, 'min': 0.0, 'max': 0.0, 'total': 0.0
                }

        return stats


@dataclass
class PerformanceReport:
    """Comprehensive performance report."""
    model_name: str
    resource_snapshots: List[ResourceSnapshot] = field(default_factory=list)
    training_profile: Optional[TrainingProfile] = None
    inference_stats: Dict[str, float] = field(default_factory=dict)
    total_runtime: float = 0.0
    peak_memory_mb: float = 0.0
    average_cpu_percent: float = 0.0
    average_gpu_utilization: Optional[float] = None

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        import numpy as np

        summary = {
            'model_name': self.model_name,
            'total_runtime': self.total_runtime,
            'peak_memory_mb': self.peak_memory_mb,
            'average_cpu_percent': self.average_cpu_percent
        }

        if self.resource_snapshots:
            cpu_usage = [s.cpu_percent for s in self.resource_snapshots]
            memory_usage = [s.memory_mb for s in self.resource_snapshots]

            summary.update({
                'cpu_usage_stats': {
                    'mean': float(np.mean(cpu_usage)),
                    'max': float(np.max(cpu_usage)),
                    'std': float(np.std(cpu_usage))
                },
                'memory_usage_stats': {
                    'mean': float(np.mean(memory_usage)),
                    'max': float(np.max(memory_usage)),
                    'std': float(np.std(memory_usage))
                }
            })

            # GPU statistics if available
            gpu_utils = [s.gpu_utilization for s in self.resource_snapshots
                        if s.gpu_utilization is not None]
            if gpu_utils:
                summary['gpu_utilization_stats'] = {
                    'mean': float(np.mean(gpu_utils)),
                    'max': float(np.max(gpu_utils)),
                    'std': float(np.std(gpu_utils))
                }

        if self.training_profile:
            summary['training_profile'] = self.training_profile.get_statistics()

        if self.inference_stats:
            summary['inference_stats'] = self.inference_stats

        return summary


class ResourceMonitor:
    """Monitor system resource utilization during model training/inference."""

    def __init__(self, monitoring_interval: float = 1.0):
        self.monitoring_interval = monitoring_interval
        self.snapshots: List[ResourceSnapshot] = []
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None

        # Initialize NVIDIA ML if available
        self.gpu_available = False
        if NVIDIA_ML_AVAILABLE:
            try:
                pynvml.nvmlInit()
                self.gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                self.gpu_available = True
            except Exception as e:
                logging.warning(f"Failed to initialize NVIDIA ML: {e}")

    def start_monitoring(self) -> None:
        """Start resource monitoring in background thread."""
        if self.monitoring:
            return

        self.monitoring = True
        self.snapshots.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_monitoring(self) -> List[ResourceSnapshot]:
        """Stop resource monitoring and return snapshots."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)

        return self.snapshots.copy()

    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self.monitoring:
            snapshot = self._take_snapshot()
            self.snapshots.append(snapshot)
            time.sleep(self.monitoring_interval)

    def _take_snapshot(self) -> ResourceSnapshot:
        """Take a single resource snapshot."""
        # CPU and memory
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        memory_mb = memory.used / (1024 ** 2)
        memory_percent = memory.percent

        # GPU metrics if available
        gpu_memory_mb = None
        gpu_utilization = None
        gpu_temperature = None

        if self.gpu_available:
            try:
                # GPU memory
                gpu_memory_info = pynvml.nvmlDeviceGetMemoryInfo(self.gpu_handle)
                gpu_memory_mb = gpu_memory_info.used / (1024 ** 2)

                # GPU utilization
                gpu_util = pynvml.nvmlDeviceGetUtilizationRates(self.gpu_handle)
                gpu_utilization = gpu_util.gpu

                # GPU temperature
                gpu_temperature = pynvml.nvmlDeviceGetTemperature(
                    self.gpu_handle, pynvml.NVML_TEMPERATURE_GPU
                )

            except Exception as e:
                logging.debug(f"Error reading GPU metrics: {e}")

        # PyTorch GPU memory if available
        elif TORCH_AVAILABLE and torch.cuda.is_available():
            try:
                gpu_memory_mb = torch.cuda.memory_allocated() / (1024 ** 2)
            except Exception:
                pass

        return ResourceSnapshot(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            memory_percent=memory_percent,
            gpu_memory_mb=gpu_memory_mb,
            gpu_utilization=gpu_utilization,
            gpu_temperature=gpu_temperature
        )

    def get_peak_memory(self) -> float:
        """Get peak memory usage in MB."""
        if not self.snapshots:
            return 0.0

        return max(snapshot.memory_mb for snapshot in self.snapshots)

    def get_average_cpu_usage(self) -> float:
        """Get average CPU usage percentage."""
        if not self.snapshots:
            return 0.0

        import numpy as np
        return float(np.mean([snapshot.cpu_percent for snapshot in self.snapshots]))

    def get_average_gpu_utilization(self) -> Optional[float]:
        """Get average GPU utilization percentage."""
        gpu_utils = [s.gpu_utilization for s in self.snapshots
                    if s.gpu_utilization is not None]

        if not gpu_utils:
            return None

        import numpy as np
        return float(np.mean(gpu_utils))


class TrainingProfiler:
    """Profile training performance with detailed timing information."""

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.profile = TrainingProfile(model_name=model_name)
        self.current_timers: Dict[str, float] = {}

    def start_timer(self, timer_name: str) -> None:
        """Start a timer."""
        self.current_timers[timer_name] = time.time()

    def end_timer(self, timer_name: str) -> float:
        """End a timer and record the duration."""
        if timer_name not in self.current_timers:
            return 0.0

        duration = time.time() - self.current_timers[timer_name]
        del self.current_timers[timer_name]

        # Record timing based on timer name
        if timer_name == 'epoch':
            self.profile.epoch_times.append(duration)
        elif timer_name == 'batch':
            self.profile.batch_times.append(duration)
        elif timer_name == 'forward':
            self.profile.forward_times.append(duration)
        elif timer_name == 'backward':
            self.profile.backward_times.append(duration)
        elif timer_name == 'optimizer':
            self.profile.optimizer_times.append(duration)
        elif timer_name == 'data_loading':
            self.profile.data_loading_times.append(duration)

        return duration

    def get_profile(self) -> TrainingProfile:
        """Get the training profile."""
        return self.profile


class PerformanceTracker:
    """Main performance tracking orchestrator."""

    def __init__(
        self,
        model_name: str,
        monitoring_interval: float = 1.0,
        enable_profiling: bool = True
    ):
        self.model_name = model_name
        self.enable_profiling = enable_profiling

        # Initialize components
        self.resource_monitor = ResourceMonitor(monitoring_interval)
        self.profiler = TrainingProfiler(model_name) if enable_profiling else None

        # Tracking state
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None

    def start_tracking(self) -> None:
        """Start performance tracking."""
        self.start_time = time.time()
        self.resource_monitor.start_monitoring()

    def stop_tracking(self) -> PerformanceReport:
        """Stop tracking and generate performance report."""
        self.end_time = time.time()

        # Stop resource monitoring
        resource_snapshots = self.resource_monitor.stop_monitoring()

        # Calculate total runtime
        total_runtime = (self.end_time - self.start_time) if self.start_time else 0.0

        # Get resource statistics
        peak_memory = self.resource_monitor.get_peak_memory()
        avg_cpu = self.resource_monitor.get_average_cpu_usage()
        avg_gpu = self.resource_monitor.get_average_gpu_utilization()

        # Create report
        report = PerformanceReport(
            model_name=self.model_name,
            resource_snapshots=resource_snapshots,
            training_profile=self.profiler.get_profile() if self.profiler else None,
            total_runtime=total_runtime,
            peak_memory_mb=peak_memory,
            average_cpu_percent=avg_cpu,
            average_gpu_utilization=avg_gpu
        )

        return report

    def profile_inference(
        self,
        model: Any,
        data_loader: Any,
        device: str = "cpu",
        num_samples: int = 100
    ) -> Dict[str, float]:
        """Profile inference performance."""
        if not TORCH_AVAILABLE:
            return {}

        model.eval()
        inference_times = []

        with torch.no_grad():
            sample_count = 0
            for data, _ in data_loader:
                if sample_count >= num_samples:
                    break

                data = data.to(device)

                # Warm-up runs
                for _ in range(3):
                    _ = model(data)

                # Timed inference
                if device.startswith("cuda"):
                    torch.cuda.synchronize()

                start_time = time.time()
                _ = model(data)

                if device.startswith("cuda"):
                    torch.cuda.synchronize()

                end_time = time.time()
                inference_times.append((end_time - start_time) * 1000)  # Convert to ms

                sample_count += data.shape[0]

        if not inference_times:
            return {}

        import numpy as np
        stats = {
            'mean_inference_time_ms': float(np.mean(inference_times)),
            'std_inference_time_ms': float(np.std(inference_times)),
            'min_inference_time_ms': float(np.min(inference_times)),
            'max_inference_time_ms': float(np.max(inference_times)),
            'throughput_samples_per_sec': 1000.0 / np.mean(inference_times)
        }

        return stats

    def get_profiler(self) -> Optional[TrainingProfiler]:
        """Get the training profiler."""
        return self.profiler


def create_performance_report(
    model_name: str,
    tracking_results: List[PerformanceReport],
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """Create comprehensive performance report from multiple tracking runs."""

    if not tracking_results:
        return {}

    import numpy as np

    # Aggregate statistics
    report = {
        'model_name': model_name,
        'num_runs': len(tracking_results),
        'runtime_statistics': {},
        'resource_statistics': {},
        'training_statistics': {},
        'inference_statistics': {}
    }

    # Runtime statistics
    runtimes = [r.total_runtime for r in tracking_results]
    report['runtime_statistics'] = {
        'mean_runtime': float(np.mean(runtimes)),
        'std_runtime': float(np.std(runtimes)),
        'min_runtime': float(np.min(runtimes)),
        'max_runtime': float(np.max(runtimes))
    }

    # Resource statistics
    peak_memories = [r.peak_memory_mb for r in tracking_results]
    avg_cpus = [r.average_cpu_percent for r in tracking_results]

    report['resource_statistics'] = {
        'peak_memory_stats': {
            'mean': float(np.mean(peak_memories)),
            'std': float(np.std(peak_memories)),
            'max': float(np.max(peak_memories))
        },
        'cpu_usage_stats': {
            'mean': float(np.mean(avg_cpus)),
            'std': float(np.std(avg_cpus)),
            'max': float(np.max(avg_cpus))
        }
    }

    # GPU statistics if available
    gpu_utils = [r.average_gpu_utilization for r in tracking_results
                if r.average_gpu_utilization is not None]
    if gpu_utils:
        report['resource_statistics']['gpu_utilization_stats'] = {
            'mean': float(np.mean(gpu_utils)),
            'std': float(np.std(gpu_utils)),
            'max': float(np.max(gpu_utils))
        }

    # Training profile statistics
    training_profiles = [r.training_profile for r in tracking_results
                        if r.training_profile is not None]
    if training_profiles:
        # Aggregate training statistics
        all_epoch_times = []
        all_batch_times = []

        for profile in training_profiles:
            all_epoch_times.extend(profile.epoch_times)
            all_batch_times.extend(profile.batch_times)

        if all_epoch_times:
            report['training_statistics']['epoch_time_stats'] = {
                'mean': float(np.mean(all_epoch_times)),
                'std': float(np.std(all_epoch_times)),
                'min': float(np.min(all_epoch_times)),
                'max': float(np.max(all_epoch_times))
            }

        if all_batch_times:
            report['training_statistics']['batch_time_stats'] = {
                'mean': float(np.mean(all_batch_times)),
                'std': float(np.std(all_batch_times)),
                'min': float(np.min(all_batch_times)),
                'max': float(np.max(all_batch_times))
            }

    # Inference statistics
    inference_stats_list = [r.inference_stats for r in tracking_results
                           if r.inference_stats]
    if inference_stats_list:
        # Aggregate inference statistics
        inference_times = []
        throughputs = []

        for stats in inference_stats_list:
            if 'mean_inference_time_ms' in stats:
                inference_times.append(stats['mean_inference_time_ms'])
            if 'throughput_samples_per_sec' in stats:
                throughputs.append(stats['throughput_samples_per_sec'])

        if inference_times:
            report['inference_statistics']['inference_time_stats'] = {
                'mean': float(np.mean(inference_times)),
                'std': float(np.std(inference_times)),
                'min': float(np.min(inference_times)),
                'max': float(np.max(inference_times))
            }

        if throughputs:
            report['inference_statistics']['throughput_stats'] = {
                'mean': float(np.mean(throughputs)),
                'std': float(np.std(throughputs)),
                'min': float(np.min(throughputs)),
                'max': float(np.max(throughputs))
            }

    # Save report if path provided
    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)

    return report


# Example usage and testing
if __name__ == "__main__":
    print("Testing Performance Tracking...")

    # Test resource monitor
    print("Testing ResourceMonitor...")
    monitor = ResourceMonitor(monitoring_interval=0.1)
    monitor.start_monitoring()

    # Simulate some work
    time.sleep(1.0)

    snapshots = monitor.stop_monitoring()
    print(f"Collected {len(snapshots)} resource snapshots")

    if snapshots:
        print(f"Peak memory: {monitor.get_peak_memory():.2f} MB")
        print(f"Average CPU: {monitor.get_average_cpu_usage():.2f}%")

    # Test training profiler
    print("\nTesting TrainingProfiler...")
    profiler = TrainingProfiler("test_model")

    profiler.start_timer('epoch')
    time.sleep(0.1)
    epoch_time = profiler.end_timer('epoch')
    print(f"Epoch time: {epoch_time:.3f}s")

    # Test performance tracker
    print("\nTesting PerformanceTracker...")
    tracker = PerformanceTracker("test_model", monitoring_interval=0.1)
    tracker.start_tracking()

    # Simulate training
    time.sleep(0.5)

    report = tracker.stop_tracking()
    print(f"Generated performance report for {report.model_name}")
    print(f"Total runtime: {report.total_runtime:.3f}s")
    print(f"Peak memory: {report.peak_memory_mb:.2f} MB")

    print("\nPerformance tracking tests completed successfully!")
    print("\nPerformance tracking tests completed successfully!")
