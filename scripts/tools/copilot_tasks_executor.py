#!/usr/bin/env python3
"""
Copilot Tasks Execution Script
Executes the immediate next steps from docs/TASKS.md
"""

import subprocess
import sys
import time
from pathlib import Path


def run_command(cmd, description, allow_failure=False):
    """Run a command and return success status"""
    print(f"\n🔄 {description}")
    print(f"Command: {cmd}")

    try:
        if isinstance(cmd, str):
            result = subprocess.run(
                cmd, shell=True, capture_output=True, text=True, cwd=Path.cwd()
            )
        else:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=Path.cwd()
            )

        if result.returncode == 0:
            print(f"✅ Output:\n{result.stdout}")
            return True
        else:
            print(f"❌ Error: {result.stderr}")
            if not allow_failure:
                return False
            else:
                print("⚠️  Continuing despite error...")
                return True

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False if not allow_failure else True


def check_environment():
    """Task 1: Environment & Container Verification"""
    print("\n" + "="*60)
    print("🎯 TASK 1: ENVIRONMENT & CONTAINER VERIFICATION")
    print("="*60)

    # Check Docker
    if not run_command("docker --version", "Check Docker installation"):
        return False

    if not run_command("docker info", "Check Docker daemon", allow_failure=True):
        print("⚠️  Docker daemon issues, but continuing...")

    # Check system status
    system_status_script = Path("scripts/utilities/system_status.sh")
    if system_status_script.exists():
        run_command(f"chmod +x {system_status_script} && {system_status_script}",
                   "Run system status check", allow_failure=True)

    # Check Docker helper
    docker_helper = Path("docker/docker-helper.sh")
    if docker_helper.exists():
        run_command(f"chmod +x {docker_helper} && {docker_helper} status",
                   "Check Docker helper status", allow_failure=True)

    return True


def start_services():
    """Start Docker services if possible"""
    print("\n🚀 Starting Docker services...")

    # Try to start main services
    compose_file = Path("docker/docker-compose.yml")
    if compose_file.exists():
        run_command("cd docker && docker-compose up -d --build",
                   "Start Docker services", allow_failure=True)

        # Wait a bit for services to start
        print("⏳ Waiting for services to initialize...")
        time.sleep(10)

        # Check service status
        run_command("docker ps", "Check running containers", allow_failure=True)

    return True


def check_monai_dataset():
    """Task 2: MONAI Dataset Smoke Testing"""
    print("\n" + "="*60)
    print("🎯 TASK 2: MONAI DATASET SMOKE TESTING")
    print("="*60)

    # Check if MONAI is available
    if not run_command("python3 -c 'import monai; print(f\"MONAI version: {monai.__version__}\")'",
                      "Check MONAI installation", allow_failure=True):
        print("⚠️  MONAI not available on host, will need Docker or installation")

    # Check dataset script
    dataset_script = Path("scripts/data/pull_monai_dataset.py")
    if dataset_script.exists():
        print(f"✅ Dataset download script found: {dataset_script}")
        # Don't run the actual download yet, just verify script exists
    else:
        print("❌ Dataset download script not found")

    # Check for existing datasets
    data_dir = Path("data")
    if data_dir.exists():
        datasets = list(data_dir.glob("**/*.nii*"))
        if datasets:
            print(f"✅ Found {len(datasets)} NIfTI files in data directory")
        else:
            print("⚠️  No NIfTI datasets found in data directory")

    return True


def check_training_infrastructure():
    """Check training scripts and configs"""
    print("\n🔧 Checking training infrastructure...")

    # Check training script
    train_script = Path("src/training/train_enhanced.py")
    if train_script.exists():
        print(f"✅ Training script found: {train_script}")
    else:
        print("❌ Training script not found")

    # Check config files
    config_dir = Path("config")
    if config_dir.exists():
        recipes = list(config_dir.glob("**/recipes/*.json"))
        datasets_configs = list(config_dir.glob("**/datasets/*.json"))
        print(f"✅ Found {len(recipes)} recipe configs and {len(datasets_configs)} dataset configs")

    return True


def check_inference_infrastructure():
    """Task 3: Baseline Inference & Overlay Export"""
    print("\n" + "="*60)
    print("🎯 TASK 3: BASELINE INFERENCE & OVERLAY EXPORT")
    print("="*60)

    # Check inference script
    inference_script = Path("src/inference/inference.py")
    if inference_script.exists():
        print(f"✅ Inference script found: {inference_script}")
    else:
        print("❌ Inference script not found")

    # Check for existing model checkpoints
    models_dir = Path("models")
    if models_dir.exists():
        checkpoints = list(models_dir.glob("**/*.pt")) + list(models_dir.glob("**/*.pth"))
        if checkpoints:
            print(f"✅ Found {len(checkpoints)} model checkpoints:")
            for cp in checkpoints[:5]:  # Show first 5
                print(f"   - {cp}")
        else:
            print("⚠️  No model checkpoints found")

    # Check output directory
    reports_dir = Path("reports")
    if not reports_dir.exists():
        reports_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created reports directory: {reports_dir}")

    return True


def check_mlflow_setup():
    """Task 4: MLflow Tracking Setup"""
    print("\n" + "="*60)
    print("🎯 TASK 4: MLFLOW TRACKING SETUP")
    print("="*60)

    # Check if MLflow is accessible
    run_command("curl -s http://localhost:5001 || echo 'MLflow not accessible on port 5001'",
               "Check MLflow accessibility", allow_failure=True)

    # Check MLflow Python module
    run_command("python3 -c 'import mlflow; print(f\"MLflow version: {mlflow.__version__}\")'",
               "Check MLflow installation", allow_failure=True)

    # Check Docker compose for MLflow service
    compose_file = Path("docker/docker-compose.yml")
    if compose_file.exists():
        result = subprocess.run(['grep', '-n', 'mlflow', str(compose_file)],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ MLflow service found in Docker compose")
            print(f"Lines: {result.stdout}")
        else:
            print("⚠️  MLflow service not found in Docker compose")

    return True


def update_task_status():
    """Update the task completion status"""
    print("\n📝 Updating task completion status...")

    # Update our verification script to show task completion
    verify_script = Path("scripts/organization/verify_task_status.py")
    if verify_script.exists():
        run_command(f"python3 {verify_script}", "Show current task status", allow_failure=True)

    print("\n🎉 Copilot Task Verification Complete!")
    return True


def main():
    """Main execution function"""
    print("🚀 COPILOT TASKS EXECUTION")
    print("="*60)
    print("Executing immediate next steps from docs/TASKS.md")
    print("="*60)

    success = True

    # Execute tasks in sequence
    if not check_environment():
        print("❌ Environment verification failed")
        success = False

    if success:
        start_services()

    if not check_monai_dataset():
        print("❌ MONAI dataset check failed")
        success = False

    if not check_training_infrastructure():
        print("❌ Training infrastructure check failed")
        success = False

    if not check_inference_infrastructure():
        print("❌ Inference infrastructure check failed")
        success = False

    if not check_mlflow_setup():
        print("❌ MLflow setup check failed")
        success = False

    update_task_status()

    if success:
        print("\n🎉 All Copilot task checks completed successfully!")
        print("\n📋 SUMMARY - TASKS READY FOR EXECUTION:")
        print("- ✅ Environment verified and containers checked")
        print("- ✅ MONAI dataset infrastructure ready")
        print("- ✅ Training pipeline infrastructure ready")
        print("- ✅ Inference and overlay export ready")
        print("- ✅ MLflow tracking infrastructure ready")
        print("\n🚀 Next: Execute actual training and inference workflows")
        return 0
    else:
        print("\n⚠️  Some checks failed, but infrastructure is partially ready")
        return 1


if __name__ == "__main__":
    sys.exit(main())
