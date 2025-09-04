#!/usr/bin/env python3
"""
Expanded Training Launcher for Medical Imaging AI
=================================================

Launches longer training sessions after smoke test validation.
Supports multiple training configurations with different epochs and hyperparameters.
"""

import argparse
import logging
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ExpandedTrainingLauncher:
    """Manages expanded training sessions for medical imaging models."""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.venv_activate = self.project_root / ".venv" / "bin" / "activate"

    def get_training_configurations(self) -> List[Dict]:
        """Define expanded training configurations."""
        return [
            {
                "name": "5-epoch-baseline",
                "description": "5-epoch baseline training for initial model validation",
                "epochs": 5,
                "config": "config/recipes/unetr_multimodal.json",
                "dataset_config": "config/datasets/msd_task01_brain.json",
                "save_overlays": True,
                "overlays_max": 5,
                "val_max_batches": 3,
                "save_prob_maps": True
            },
            {
                "name": "10-epoch-extended",
                "description": "10-epoch extended training for better convergence",
                "epochs": 10,
                "config": "config/recipes/unetr_multimodal.json",
                "dataset_config": "config/datasets/msd_task01_brain.json",
                "save_overlays": True,
                "overlays_max": 8,
                "val_max_batches": 5,
                "save_prob_maps": True
            },
            {
                "name": "25-epoch-production",
                "description": "25-epoch production training for final model",
                "epochs": 25,
                "config": "config/recipes/unetr_multimodal.json",
                "dataset_config": "config/datasets/msd_task01_brain.json",
                "save_overlays": True,
                "overlays_max": 10,
                "val_max_batches": 10,
                "save_prob_maps": True
            }
        ]

    def build_training_command(self, config: Dict) -> str:
        """Build training command from configuration."""
        venv_python = self.project_root / ".venv" / "bin" / "python"

        # Build the command parts
        cmd_parts = [
            f"cd {self.project_root}",
            f"PYTHONPATH={self.project_root} {venv_python} src/training/train_enhanced.py"
        ]

        # Add configuration arguments
        cmd_args = [
            "--config", config["config"],
            "--dataset-config", config["dataset_config"],
            "--epochs", str(config["epochs"])
        ]

        # Add optional arguments
        if config.get("save_overlays", False):
            cmd_args.append("--save-overlays")
            if "overlays_max" in config:
                cmd_args.extend(["--overlays-max",
                                str(config["overlays_max"])])

        if config.get("save_prob_maps", False):
            cmd_args.append("--save-prob-maps")

        if "val_max_batches" in config:
            cmd_args.extend(["--val-max-batches",
                            str(config["val_max_batches"])])

        # Join the command parts
        cmd_parts[1] += " " + " ".join(cmd_args)
        return " && ".join(cmd_parts)

    def run_training_session(self, config: Dict, dry_run: bool = False) -> bool:
        """Run a single training session."""
        logger.info(f"Starting training session: {config['name']}")
        logger.info(f"Description: {config['description']}")
        logger.info(f"Epochs: {config['epochs']}")

        cmd_str = self.build_training_command(config)

        if dry_run:
            logger.info(f"DRY RUN - Would execute: {cmd_str}")
            return True

        try:
            logger.info(f"Executing: {cmd_str}")
            result = subprocess.run(
                cmd_str,
                shell=True,
                cwd=self.project_root,
                capture_output=False,
                text=True
            )

            if result.returncode == 0:
                logger.info(f"Training session '{config['name']}' completed successfully")
                return True
            else:
                logger.error(f"Training session '{config['name']}' failed with return code {result.returncode}")
                return False

        except Exception as e:
            logger.error(f"Error running training session '{config['name']}': {e}")
            return False

    def run_all_sessions(self, dry_run: bool = False, start_from: Optional[str] = None) -> None:
        """Run all training sessions in sequence."""
        configs = self.get_training_configurations()

        # Filter configurations if start_from is specified
        if start_from:
            start_idx = None
            for i, config in enumerate(configs):
                if config["name"] == start_from:
                    start_idx = i
                    break

            if start_idx is not None:
                configs = configs[start_idx:]
                logger.info(f"Starting from configuration: {start_from}")
            else:
                logger.error(f"Configuration '{start_from}' not found")
                return

        successful_sessions = 0
        total_sessions = len(configs)

        for i, config in enumerate(configs, 1):
            logger.info(f"=== Training Session {i}/{total_sessions} ===")

            if self.run_training_session(config, dry_run):
                successful_sessions += 1
            else:
                logger.error("Training session failed. Stopping execution.")
                break

            # Add delay between sessions (except for the last one)
            if i < total_sessions and not dry_run:
                logger.info("Waiting 30 seconds before next session...")
                time.sleep(30)

        logger.info(f"Training execution summary: {successful_sessions}/{total_sessions} sessions completed successfully")

    def list_configurations(self) -> None:
        """List all available training configurations."""
        configs = self.get_training_configurations()

        print("Available Training Configurations:")
        print("=" * 50)

        for config in configs:
            print(f"Name: {config['name']}")
            print(f"Description: {config['description']}")
            print(f"Epochs: {config['epochs']}")
            print(f"Overlays: {config.get('overlays_max', 'N/A')}")
            print(f"Val Batches: {config.get('val_max_batches', 'N/A')}")
            print("-" * 30)

def main():
    parser = argparse.ArgumentParser(description="Expanded Training Launcher for Medical Imaging AI")
    parser.add_argument("--project-root",
                       default="/home/kevin/Projects/tumor-detection-segmentation",
                       help="Project root directory")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show commands without executing them")
    parser.add_argument("--list", action="store_true",
                       help="List available training configurations")
    parser.add_argument("--start-from", type=str,
                       help="Start from a specific configuration")
    parser.add_argument("--session", type=str,
                       help="Run only a specific training session")

    args = parser.parse_args()

    launcher = ExpandedTrainingLauncher(args.project_root)

    if args.list:
        launcher.list_configurations()
        return

    if args.session:
        # Run single session
        configs = launcher.get_training_configurations()
        config = next((c for c in configs if c["name"] == args.session), None)

        if config:
            launcher.run_training_session(config, args.dry_run)
        else:
            logger.error(f"Configuration '{args.session}' not found")
            launcher.list_configurations()
    else:
        # Run all sessions
        launcher.run_all_sessions(args.dry_run, args.start_from)

if __name__ == "__main__":
    main()
