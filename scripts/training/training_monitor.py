#!/usr/bin/env python3
"""
Training Monitor for Medical Imaging AI
=======================================

Monitors training progress and provides real-time updates.
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Optional, List
import subprocess

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrainingMonitor:
    """Monitors medical imaging AI training progress."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.logs_dir = self.project_root / "logs"
        self.models_dir = self.project_root / "models"

    def check_smoke_test_status(self) -> Dict:
        """Check if smoke test is running or completed."""
        try:
            # Check for running processes
            result = subprocess.run(
                ["pgrep", "-f", "train_enhanced.py"],
                capture_output=True,
                text=True
            )

            is_running = len(result.stdout.strip()) > 0

            # Check for recent log files
            log_files = []
            if self.logs_dir.exists():
                log_files = list(self.logs_dir.glob("*.log"))
                log_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            # Check for model checkpoints
            checkpoint_files = []
            if self.models_dir.exists():
                checkpoint_files = list(self.models_dir.glob("**/*.pth"))
                checkpoint_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            return {
                "is_running": is_running,
                "recent_logs": [str(f) for f in log_files[:5]],
                "recent_checkpoints": [str(f) for f in checkpoint_files[:3]],
                "timestamp": time.time()
            }

        except Exception as e:
            logger.error(f"Error checking smoke test status: {e}")
            return {
                "is_running": False,
                "recent_logs": [],
                "recent_checkpoints": [],
                "error": str(e),
                "timestamp": time.time()
            }

    def wait_for_smoke_test_completion(self,
                                      timeout_minutes: int = 30) -> bool:
        """Wait for smoke test to complete."""
        logger.info("Monitoring smoke test progress...")

        start_time = time.time()
        timeout_seconds = timeout_minutes * 60

        while True:
            status = self.check_smoke_test_status()

            if not status["is_running"]:
                logger.info("Smoke test appears to have completed")
                return True

            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                logger.warning(f"Timeout after {timeout_minutes} minutes")
                return False

            remaining = timeout_seconds - elapsed
            logger.info(f"Smoke test still running... "
                       f"({remaining/60:.1f} minutes remaining)")

            time.sleep(30)  # Check every 30 seconds

    def get_training_summary(self) -> Dict:
        """Get summary of training environment and status."""
        status = self.check_smoke_test_status()

        # Check virtual environment
        venv_path = self.project_root / ".venv"
        venv_active = venv_path.exists()

        # Check key files
        training_script = self.project_root / "src/training/train_enhanced.py"
        config_file = self.project_root / "config/recipes/unetr_multimodal.json"
        dataset_config = self.project_root / "config/datasets/msd_task01_brain.json"

        return {
            "environment": {
                "virtual_env": venv_active,
                "training_script": training_script.exists(),
                "config_files": {
                    "model_config": config_file.exists(),
                    "dataset_config": dataset_config.exists()
                }
            },
            "training_status": status,
            "ready_for_expansion": not status["is_running"] and venv_active
        }

    def print_status_report(self) -> None:
        """Print comprehensive status report."""
        summary = self.get_training_summary()

        print("=" * 60)
        print("MEDICAL IMAGING AI TRAINING STATUS REPORT")
        print("=" * 60)

        print("\n🔧 ENVIRONMENT STATUS:")
        env = summary["environment"]
        print(f"  Virtual Environment: {'✅' if env['virtual_env'] else '❌'}")
        print(f"  Training Script: {'✅' if env['training_script'] else '❌'}")
        print(f"  Model Config: {'✅' if env['config_files']['model_config'] else '❌'}")
        print(f"  Dataset Config: {'✅' if env['config_files']['dataset_config'] else '❌'}")

        print("\n🚀 TRAINING STATUS:")
        status = summary["training_status"]
        if status["is_running"]:
            print("  Status: 🟡 SMOKE TEST RUNNING")
        else:
            print("  Status: ✅ READY FOR EXPANDED TRAINING")

        if status["recent_logs"]:
            print(f"  Recent Logs: {len(status['recent_logs'])} files")
            for log in status["recent_logs"][:2]:
                print(f"    - {log}")

        if status["recent_checkpoints"]:
            print(f"  Model Checkpoints: {len(status['recent_checkpoints'])} files")
            for checkpoint in status["recent_checkpoints"][:2]:
                print(f"    - {checkpoint}")

        print(f"\n📊 EXPANSION READINESS:")
        ready = summary["ready_for_expansion"]
        print(f"  Ready for Expanded Training: {'✅' if ready else '⏳ WAITING'}")

        if ready:
            print("\n🎯 NEXT STEPS:")
            print("  1. Run 5-epoch baseline training")
            print("  2. Run 10-epoch extended training")
            print("  3. Run 25-epoch production training")
            print("\n  Use: python scripts/training/expanded_training_launcher.py")

        print("=" * 60)


def main():
    """Main monitoring function."""
    import argparse

    parser = argparse.ArgumentParser(description="Training Monitor")
    parser.add_argument("--project-root",
                       default="/home/kevin/Projects/tumor-detection-segmentation",
                       help="Project root directory")
    parser.add_argument("--wait", action="store_true",
                       help="Wait for smoke test completion")
    parser.add_argument("--timeout", type=int, default=30,
                       help="Timeout in minutes for waiting")

    args = parser.parse_args()

    monitor = TrainingMonitor(args.project_root)

    if args.wait:
        if monitor.wait_for_smoke_test_completion(args.timeout):
            print("\n✅ Smoke test completed! Ready for expanded training.")
        else:
            print("\n⏰ Timeout reached. Check training status manually.")

    monitor.print_status_report()


if __name__ == "__main__":
    main()
