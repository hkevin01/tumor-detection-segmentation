#!/usr/bin/env python3
"""Complete smoke test workflow: validation, dataset download, and training."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def run_command(cmd, description, check=True):
    """Run a command and handle errors."""
    print(f"\n🔄 {description}")
    print(f"Command: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd, check=check, capture_output=True, text=True
        )
        if result.stdout:
            print(f"✅ Output:\n{result.stdout}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stdout:
            print(f"STDOUT:\n{e.stdout}")
        if e.stderr:
            print(f"STDERR:\n{e.stderr}")
        return False


def check_docker_prereqs():
    """Check if Docker is available and working."""
    print("\n🔍 Checking Docker prerequisites...")

    # Check if Docker is available
    if not run_command(["docker", "--version"], "Check Docker installation"):
        return False

    # Check if Docker daemon is running
    if not run_command(["docker", "info"], "Check Docker daemon", check=False):
        print("❌ Docker daemon is not running")
        return False

    print("✅ Docker prerequisites OK")
    return True


def download_sample_dataset():
    """Download a small MONAI dataset for testing."""
    print("\n📥 Downloading sample MONAI dataset...")

    # Use Task01_BrainTumour as it's relatively small
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "data" / "pull_monai_dataset.py"),
        "--dataset-id", "Task01_BrainTumour",
        "--root", "data/msd",
        "--sections", "training"  # Only training section for smoke test
    ]

    return run_command(cmd, "Download Task01_BrainTumour dataset")


def run_smoke_training():
    """Run a quick 2-epoch training."""
    print("\n🏃 Running smoke training (2 epochs)...")

    # First try host-based training if MONAI is available
    try:
        import importlib.util

        # Check if MONAI and torch are available
        monai_spec = importlib.util.find_spec("monai")
        torch_spec = importlib.util.find_spec("torch")

        if monai_spec and torch_spec:
            print("✅ MONAI and PyTorch available on host, running directly...")
            cmd = [
                sys.executable,
                str(ROOT / "src" / "training" / "train_enhanced.py"),
                "--epochs", "2",
                "--save-overlays"
            ]

            return run_command(cmd, "Host-based smoke training")
        else:
            raise ImportError("MONAI or PyTorch not available")

    except ImportError:
        print("⚠️  MONAI/PyTorch not available on host, trying Docker...")

        # Try Docker-based training
        launcher = ROOT / "scripts" / "tools" / "smoke_train_launcher.sh"
        if launcher.exists():
            cmd = [str(launcher), "run"]
            return run_command(cmd, "Docker-based smoke training")
        else:
            print("❌ Smoke training launcher not found")
            return False


def update_task_status():
    """Update the task status to completed."""
    print("\n📝 Updating task status...")

    task_manager = ROOT / "scripts" / "organization" / "task_manager.py"
    if task_manager.exists():
        cmd = [
            sys.executable, str(task_manager),
            "set-status", "final_validation", "run_smoke_train", "completed"
        ]
        return run_command(cmd, "Update task status")
    else:
        print("⚠️  Task manager not found, skipping status update")
        return True


def main():
    """Run the complete smoke test workflow."""
    print("🚀 Starting Complete Smoke Test Workflow")
    print("=" * 50)

    success = True

    # Step 1: Check Docker prerequisites
    if not check_docker_prereqs():
        print("\n⚠️  Docker not available, will try host-based approach only")

    # Step 2: Download sample dataset
    if not download_sample_dataset():
        print("\n❌ Dataset download failed, continuing anyway...")
        success = False

    # Step 3: Run smoke training
    if not run_smoke_training():
        print("\n❌ Smoke training failed")
        success = False
    else:
        print("\n✅ Smoke training completed successfully!")

    # Step 4: Update task status
    if success:
        update_task_status()
        print("\n🎉 Complete smoke test workflow finished successfully!")
    else:
        print("\n⚠️  Smoke test completed with some issues")

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
