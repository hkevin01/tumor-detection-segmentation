#!/usr/bin/env python3
"""
Lightweight VSCode-Safe Training Launcher

Prevents VSCode crashes during medical imaging training by:
1. Resource monitoring and limits
2. Process isolation
3. Memory management
4. Graceful degradation
"""

import os
import subprocess
import sys
import time
from pathlib import Path

import psutil


def get_system_info():
    """Get current system resource usage"""
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)
    return {
        'memory_percent': memory.percent,
        'memory_available_gb': memory.available / (1024**3),
        'cpu_percent': cpu_percent,
        'cpu_count': psutil.cpu_count()
    }

def is_vscode_safe():
    """Check if system resources allow safe training without VSCode crashes"""
    info = get_system_info()

    # Conservative limits to prevent VSCode crashes
    memory_safe = info['memory_percent'] < 70.0
    cpu_safe = info['cpu_percent'] < 75.0
    memory_available = info['memory_available_gb'] > 4.0

    return memory_safe and cpu_safe and memory_available, info

def create_safe_env():
    """Create environment with resource limits"""
    env = os.environ.copy()

    # Limit thread usage to prevent CPU overload
    cpu_limit = max(1, psutil.cpu_count() // 2)
    env.update({
        'OMP_NUM_THREADS': str(cpu_limit),
        'MKL_NUM_THREADS': str(cpu_limit),
        'NUMEXPR_NUM_THREADS': str(cpu_limit),
        'OPENBLAS_NUM_THREADS': str(cpu_limit),

        # PyTorch memory management
        'PYTORCH_CUDA_ALLOC_CONF': 'max_split_size_mb:256',

        # Python optimization
        'PYTHONHASHSEED': '0',
        'PYTHONUNBUFFERED': '1'
    })

    return env

def run_safe_training(epochs=2, max_batches=1):
    """Run training with VSCode crash prevention"""

    print("=== VSCode-Safe Training Launcher ===")

    # Check initial system state
    safe, info = is_vscode_safe()
    print("System Status:")
    print(f"  Memory: {info['memory_percent']:.1f}% used, {info['memory_available_gb']:.1f}GB available")
    print(f"  CPU: {info['cpu_percent']:.1f}% used, {info['cpu_count']} cores")
    print(f"  VSCode Safe: {'✓' if safe else '✗'}")

    if not safe:
        print("\n⚠️  System not safe for training - high resource usage detected")
        print("   Please close other applications or wait for system to cool down")
        return False

    # Prepare safe training command
    workspace = Path("/home/kevin/Projects/tumor-detection-segmentation")
    venv_python = workspace / "venv" / "bin" / "python"

    command = [
        str(venv_python),
        "src/training/train_enhanced.py",
        "--config", "config/recipes/unetr_multimodal.json",
        "--dataset-config", "config/datasets/msd_task01_brain.json",
        "--epochs", str(epochs),
        "--val-max-batches", str(max_batches),
        "--output-dir", f"logs/safe_training/test_{epochs}epochs"
    ]

    print(f"\n🚀 Starting safe training: {epochs} epochs, {max_batches} val batches")
    print("   This configuration is designed to prevent VSCode crashes")

    try:
        # Launch with resource limits
        env = create_safe_env()
        process = subprocess.Popen(
            command,
            cwd=str(workspace),
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            preexec_fn=lambda: os.nice(10)  # Lower priority
        )

        print(f"   Process ID: {process.pid}")
        print("   Monitoring resources...")

        # Monitor training
        last_check = 0
        for line in process.stdout:
            print(f"   {line.strip()}")

            # Check resources every 30 seconds
            if time.time() - last_check > 30:
                safe, current_info = is_vscode_safe()
                if not safe:
                    print("\n⚠️  Resources critical - terminating training")
                    print(f"   Memory: {current_info['memory_percent']:.1f}%")
                    print(f"   CPU: {current_info['cpu_percent']:.1f}%")
                    process.terminate()
                    break
                last_check = time.time()

        # Wait for completion
        return_code = process.wait()

        if return_code == 0:
            print("\n✅ Training completed successfully!")
            return True
        else:
            print(f"\n❌ Training failed with code {return_code}")
            return False

    except KeyboardInterrupt:
        print("\n🛑 Training interrupted by user")
        if 'process' in locals():
            process.terminate()
        return False
    except Exception as e:
        print(f"\n❌ Training error: {e}")
        return False

def main():
    """Main entry point"""

    if len(sys.argv) > 1:
        try:
            epochs = int(sys.argv[1])
        except ValueError:
            epochs = 2
    else:
        epochs = 2

    # Run safe training
    success = run_safe_training(epochs=epochs, max_batches=1)

    if success:
        print("\n🎉 Safe training completed without VSCode crashes!")
    else:
        print("\n💡 Training stopped to protect VSCode stability")

if __name__ == "__main__":
    main()
