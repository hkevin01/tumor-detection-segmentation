#!/usr/bin/env python3
"""
VSCode Crash Prevention System for Medical Imaging Training

This module provides resource management and process isolation to prevent
VSCode crashes during intensive medical imaging training operations.
"""

import logging
import os
import subprocess
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import psutil

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ResourceLimits:
    """Resource limits for training processes"""
    max_memory_percent: float = 60.0  # Max 60% of system memory
    max_cpu_percent: float = 80.0     # Max 80% CPU usage
    max_processes: int = 4            # Max concurrent training processes
    memory_check_interval: int = 10   # Check every 10 seconds

class CrashPrevention:
    """Main crash prevention system"""

    def __init__(self, limits: Optional[ResourceLimits] = None):
        self.limits = limits or ResourceLimits()
        self.running_processes: List[subprocess.Popen] = []
        self.monitoring_active = False

        # System info
        self.total_memory = psutil.virtual_memory().total
        self.cpu_count = psutil.cpu_count()

        logger.info(f"System: {self.cpu_count} CPUs, {self.total_memory / (1024**3):.1f}GB RAM")
        logger.info(f"Limits: {self.limits.max_memory_percent}% memory, {self.limits.max_cpu_percent}% CPU")

    def get_system_usage(self) -> Tuple[float, float]:
        """Get current system resource usage"""
        memory_percent = psutil.virtual_memory().percent
        cpu_percent = psutil.cpu_percent(interval=1)
        return memory_percent, cpu_percent

    def is_safe_to_launch(self) -> Tuple[bool, str]:
        """Check if it's safe to launch a new training process"""
        memory_percent, cpu_percent = self.get_system_usage()

        if memory_percent > self.limits.max_memory_percent:
            return False, f"Memory usage too high: {memory_percent:.1f}%"

        if cpu_percent > self.limits.max_cpu_percent:
            return False, f"CPU usage too high: {cpu_percent:.1f}%"

        if len(self.running_processes) >= self.limits.max_processes:
            return False, f"Too many processes running: {len(self.running_processes)}"

        return True, "Safe to launch"

    def create_resource_limited_env(self) -> Dict[str, str]:
        """Create environment variables for resource-limited execution"""
        env = os.environ.copy()

        # PyTorch settings for memory efficiency
        env.update({
            'OMP_NUM_THREADS': str(max(1, self.cpu_count // 2)),
            'MKL_NUM_THREADS': str(max(1, self.cpu_count // 2)),
            'NUMEXPR_NUM_THREADS': str(max(1, self.cpu_count // 2)),
            'OPENBLAS_NUM_THREADS': str(max(1, self.cpu_count // 2)),

            # CUDA/PyTorch memory management
            'PYTORCH_CUDA_ALLOC_CONF': 'max_split_size_mb:512',
            'CUDA_LAUNCH_BLOCKING': '1',

            # Python memory optimization
            'PYTHONHASHSEED': '0',
            'MALLOC_ARENA_MAX': '2',

            # Disable some VSCode integrations during training
            'PYTHONUNBUFFERED': '1',
            'TERM': 'xterm-256color'
        })

        return env

    def launch_training_safe(self, command: List[str], cwd: Optional[str] = None) -> Optional[subprocess.Popen]:
        """Launch training with resource monitoring and crash prevention"""

        # Check if safe to launch
        safe, reason = self.is_safe_to_launch()
        if not safe:
            logger.warning(f"Cannot launch training: {reason}")
            return None

        try:
            # Create resource-limited environment
            env = self.create_resource_limited_env()

            # Launch process with nice priority (lower priority)
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=lambda: os.nice(10)  # Lower priority
            )

            self.running_processes.append(process)
            logger.info(f"Launched training process {process.pid} with resource limits")

            return process

        except Exception as e:
            logger.error(f"Failed to launch training: {e}")
            return None

    def monitor_process(self, process: subprocess.Popen) -> None:
        """Monitor a training process for resource usage"""
        try:
            ps_process = psutil.Process(process.pid)

            while process.poll() is None:
                try:
                    # Get process resource usage
                    memory_info = ps_process.memory_info()
                    memory_percent = ps_process.memory_percent()
                    cpu_percent = ps_process.cpu_percent()

                    # Check system limits
                    sys_memory, sys_cpu = self.get_system_usage()

                    logger.info(f"Process {process.pid}: {memory_percent:.1f}% memory, {cpu_percent:.1f}% CPU")
                    logger.info(f"System: {sys_memory:.1f}% memory, {sys_cpu:.1f}% CPU")

                    # Emergency shutdown if limits exceeded
                    if sys_memory > 90 or sys_cpu > 95:
                        logger.warning("Emergency shutdown - system overloaded!")
                        self.graceful_shutdown(process)
                        break

                    time.sleep(self.limits.memory_check_interval)

                except psutil.NoSuchProcess:
                    break

        except Exception as e:
            logger.error(f"Error monitoring process {process.pid}: {e}")

    def graceful_shutdown(self, process: subprocess.Popen) -> None:
        """Gracefully shutdown a training process"""
        try:
            logger.info(f"Gracefully shutting down process {process.pid}")

            # Try SIGTERM first
            process.terminate()

            # Wait up to 30 seconds for graceful shutdown
            try:
                process.wait(timeout=30)
                logger.info(f"Process {process.pid} terminated gracefully")
            except subprocess.TimeoutExpired:
                # Force kill if needed
                logger.warning(f"Force killing process {process.pid}")
                process.kill()
                process.wait()

            # Remove from running processes
            if process in self.running_processes:
                self.running_processes.remove(process)

        except Exception as e:
            logger.error(f"Error shutting down process {process.pid}: {e}")

    def cleanup_all(self) -> None:
        """Cleanup all running training processes"""
        logger.info("Cleaning up all training processes...")

        for process in self.running_processes.copy():
            self.graceful_shutdown(process)

        self.running_processes.clear()
        logger.info("Cleanup complete")

    @contextmanager
    def safe_training_context(self):
        """Context manager for safe training execution"""
        try:
            yield self
        except KeyboardInterrupt:
            logger.info("Interrupt received, cleaning up...")
            self.cleanup_all()
            raise
        except Exception as e:
            logger.error(f"Error in training context: {e}")
            self.cleanup_all()
            raise
        finally:
            self.cleanup_all()

class VSCodeSafeTrainingLauncher:
    """Training launcher optimized for VSCode stability"""

    def __init__(self, workspace_dir: str):
        self.workspace_dir = Path(workspace_dir)
        self.crash_prevention = CrashPrevention()

        # Create safe output directory
        self.safe_output_dir = self.workspace_dir / "logs" / "safe_training"
        self.safe_output_dir.mkdir(parents=True, exist_ok=True)

    def launch_training_sequence(self, configs: List[Dict]) -> bool:
        """Launch training sequence with crash prevention"""

        with self.crash_prevention.safe_training_context():
            for i, config in enumerate(configs):
                logger.info(f"Starting training {i+1}/{len(configs)}: {config['name']}")

                # Wait for system to be ready
                while True:
                    safe, reason = self.crash_prevention.is_safe_to_launch()
                    if safe:
                        break
                    logger.info(f"Waiting for system: {reason}")
                    time.sleep(30)

                # Build command
                command = self.build_training_command(config)

                # Launch with monitoring
                process = self.crash_prevention.launch_training_safe(
                    command,
                    cwd=str(self.workspace_dir)
                )

                if process is None:
                    logger.error(f"Failed to launch training {config['name']}")
                    return False

                # Monitor process (this will block until completion)
                self.crash_prevention.monitor_process(process)

                # Wait between trainings
                if i < len(configs) - 1:
                    logger.info("Waiting 60 seconds before next training...")
                    time.sleep(60)

        return True

    def build_training_command(self, config: Dict) -> List[str]:
        """Build training command with safety parameters"""

        # Activate virtual environment
        venv_python = str(self.workspace_dir / "venv" / "bin" / "python")

        command = [
            venv_python,
            "src/training/train_enhanced.py",
            "--config", config["model_config"],
            "--dataset-config", config["dataset_config"],
            "--epochs", str(config["epochs"]),
            "--save-overlays",
            "--overlays-max", "2",  # Reduced for memory safety
            "--save-prob-maps",
            "--val-max-batches", "1",  # Reduced for memory safety
            "--output-dir", str(self.safe_output_dir / config["name"])
        ]

        return command

def main():
    """Main function for crash prevention testing"""

    # Test system
    crash_prev = CrashPrevention()

    print("=== VSCode Crash Prevention System ===")
    print(f"System: {crash_prev.cpu_count} CPUs, {crash_prev.total_memory / (1024**3):.1f}GB RAM")

    memory_percent, cpu_percent = crash_prev.get_system_usage()
    print(f"Current usage: {memory_percent:.1f}% memory, {cpu_percent:.1f}% CPU")

    safe, reason = crash_prev.is_safe_to_launch()
    print(f"Safe to launch: {safe} - {reason}")

    if len(sys.argv) > 1 and sys.argv[1] == "--test-training":
        # Test training sequence
        workspace_dir = "/home/kevin/Projects/tumor-detection-segmentation"
        launcher = VSCodeSafeTrainingLauncher(workspace_dir)

        # Safe training configuration
        safe_configs = [
            {
                "name": "safe_test_5epochs",
                "model_config": "config/recipes/unetr_multimodal.json",
                "dataset_config": "config/datasets/msd_task01_brain.json",
                "epochs": 2  # Very short for testing
            }
        ]

        success = launcher.launch_training_sequence(safe_configs)
        print(f"Training sequence completed: {success}")

if __name__ == "__main__":
    main()
