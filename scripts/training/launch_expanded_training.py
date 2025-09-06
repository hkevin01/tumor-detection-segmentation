#!/usr/bin/env python3
"""
Expanded Training Launcher with Hyperparameter Sweeps
====================================================

Comprehensive training launcher supporting hyperparameter sweeps,
multiple models, and clinical workflow i        # Final summary
        logger.info("=" * 60)
        logger.info("🏁 Hyperparameter Sweep Complete")
        logger.info("=" * 60)ration.

Author: Tumor Detection Segmentation Team
Phase: Clinical Production Training
"""

import argparse
import itertools
import json
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'training_launcher_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ExpandedTrainingLauncher:
    """Advanced training launcher with hyperparameter sweep capabilities"""

    def __init__(self):
        self.start_time = datetime.now()
        self.experiments = []
        self.failed_experiments = []

    def parse_grid_parameter(self, param_str: str) -> Dict[str, List[Union[str, int, float, bool]]]:
        """Parse grid parameter string into parameter grid"""
        grid = {}

        # Split by space to get individual parameter=value1,value2 pairs
        param_pairs = param_str.split()

        for pair in param_pairs:
            if '=' not in pair:
                continue

            param, values_str = pair.split('=', 1)
            values = []

            for value_str in values_str.split(','):
                value_str = value_str.strip()

                # Try to convert to appropriate type
                if value_str.lower() in ['true', 'false']:
                    values.append(value_str.lower() == 'true')
                elif value_str.isdigit():
                    values.append(int(value_str))
                elif self.is_float(value_str):
                    values.append(float(value_str))
                else:
                    values.append(value_str)

            grid[param] = values

        return grid

    def is_float(self, value: str) -> bool:
        """Check if string represents a float"""
        try:
            float(value)
            return True
        except ValueError:
            return False

    def generate_parameter_combinations(self, grid: Dict) -> List[Dict]:
        """Generate all parameter combinations from grid"""
        if not grid:
            return [{}]

        # Get parameter names and their value lists
        param_names = list(grid.keys())
        param_values = [grid[name] for name in param_names]

        # Generate all combinations
        combinations = []
        for combination in itertools.product(*param_values):
            param_dict = dict(zip(param_names, combination))
            combinations.append(param_dict)

        return combinations

    def build_training_command(self, base_config: str, dataset_config: str,
                             params: Dict, experiment_name: str,
                             run_name: str, epochs: int) -> List[str]:
        """Build training command with parameters"""
        cmd = [
            'python', 'src/training/train_enhanced.py',
            '--config', base_config,
            '--dataset-config', dataset_config,
            '--epochs', str(epochs),
            '--experiment-name', experiment_name,
            '--run-name', run_name
        ]

        # Add parameter overrides
        for param, value in params.items():
            if param == 'roi':
                # Handle ROI as special case - convert to spatial size
                if isinstance(value, (int, str)):
                    roi_size = str(value)
                    cmd.extend(['--spatial-size', roi_size, roi_size, roi_size])
            elif param == 'cache':
                cmd.extend(['--cache-rate', '1.0' if value == 'cache' else '0.8'])
            elif param == 'amp' and value:
                cmd.append('--amp')
            elif param == 'tta' and value:
                cmd.append('--tta')
            elif param == 'batch_size':
                cmd.extend(['--batch-size', str(value)])
            elif param == 'learning_rate':
                cmd.extend(['--learning-rate', str(value)])
            elif param == 'save_overlays' and value:
                cmd.extend(['--save-overlays', '--overlays-max', '3'])
            else:
                # Generic parameter handling
                cmd.extend([f'--{param.replace("_", "-")}', str(value)])

        # Add tags for tracking
        tags = []
        for param, value in params.items():
            tags.append(f'{param}={value}')

        if tags:
            cmd.extend(['--tags', ','.join(tags)])

        return cmd

    def run_experiment(self, cmd: List[str], run_name: str, timeout: int = 3600) -> bool:
        """Run a single training experiment"""
        logger.info(f"🚀 Starting experiment: {run_name}")
        logger.info(f"   Command: {' '.join(cmd)}")

        try:
            # Create experiment log file
            log_file = Path(f'logs/experiments/{run_name}.log')
            log_file.parent.mkdir(parents=True, exist_ok=True)

            # Run training with timeout
            with open(log_file, 'w') as f:
                process = subprocess.Popen(
                    cmd,
                    stdout=f,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True
                )

                try:
                    return_code = process.wait(timeout=timeout)

                    if return_code == 0:
                        logger.info(f"✅ Experiment {run_name} completed successfully")
                        return True
                    else:
                        logger.error(f"❌ Experiment {run_name} failed with return code {return_code}")
                        return False

                except subprocess.TimeoutExpired:
                    process.kill()
                    logger.error(f"❌ Experiment {run_name} timed out after {timeout}s")
                    return False

        except Exception as e:
            logger.error(f"❌ Experiment {run_name} failed with error: {e}")
            return False

    def run_sweep(self, config: str, dataset_config: str, grid_str: str,
                  epochs: int, experiment_name: str, dry_run: bool = False,
                  max_concurrent: int = 1, timeout: int = 3600) -> bool:
        """Run hyperparameter sweep"""
        logger.info("🔍 Hyperparameter Sweep Configuration")
        logger.info("=" * 60)

        # Parse parameter grid
        grid = self.parse_grid_parameter(grid_str)
        logger.info(f"📊 Parameter grid: {grid}")

        # Generate combinations
        combinations = self.generate_parameter_combinations(grid)
        logger.info(f"🎯 Total experiments: {len(combinations)}")

        if dry_run:
            logger.info("🎭 Dry run mode - showing experiments without execution")
            for i, params in enumerate(combinations):
                run_name = f"sweep-{i+1:03d}"
                cmd = self.build_training_command(
                    config, dataset_config, params, experiment_name, run_name, epochs
                )
                logger.info(f"   Experiment {i+1}: {' '.join(cmd)}")
            return True

        # Run experiments
        logger.info("🚀 Starting hyperparameter sweep...")
        successful_experiments = 0

        for i, params in enumerate(combinations):
            run_name = f"sweep-{i+1:03d}-{'-'.join(f'{k}={v}' for k, v in params.items())}"
            run_name = run_name.replace('/', '_').replace(' ', '_')  # Sanitize name

            cmd = self.build_training_command(
                config, dataset_config, params, experiment_name, run_name, epochs
            )

            success = self.run_experiment(cmd, run_name, timeout)

            if success:
                successful_experiments += 1
                self.experiments.append({
                    'run_name': run_name,
                    'params': params,
                    'status': 'success'
                })
            else:
                self.failed_experiments.append({
                    'run_name': run_name,
                    'params': params,
                    'status': 'failed'
                })

            # Progress update
            progress = ((i + 1) / len(combinations)) * 100
            logger.info(f"📈 Progress: {i+1}/{len(combinations)} ({progress:.1f}%)")

        # Final summary
        logger.info("=" * 60)
        logger.info("� Hyperparameter Sweep Complete")
        logger.info("=" * 60)
        logger.info(f"✅ Successful experiments: {successful_experiments}/{len(combinations)}")
        logger.info(f"❌ Failed experiments: {len(self.failed_experiments)}")
        logger.info(f"⏱️ Total duration: {datetime.now() - self.start_time}")

        # Save results summary
        self.save_sweep_results(experiment_name)

        return successful_experiments > 0

    def save_sweep_results(self, experiment_name: str):
        """Save sweep results to file"""
        results = {
            'experiment_name': experiment_name,
            'start_time': self.start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'duration': str(datetime.now() - self.start_time),
            'total_experiments': len(self.experiments) + len(self.failed_experiments),
            'successful_experiments': len(self.experiments),
            'failed_experiments': len(self.failed_experiments),
            'experiments': self.experiments,
            'failed': self.failed_experiments
        }

        results_file = Path(f'reports/sweeps/{experiment_name}_sweep_results.json')
        results_file.parent.mkdir(parents=True, exist_ok=True)

        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"📊 Sweep results saved: {results_file}")

    def run_single_training(self, config: str, dataset_config: str,
                           epochs: int, experiment_name: str, run_name: str,
                           params: Optional[Dict] = None) -> bool:
        """Run single training experiment"""
        logger.info("🎯 Single Training Experiment")
        logger.info("=" * 60)

        if params is None:
            params = {}

        cmd = self.build_training_command(
            config, dataset_config, params, experiment_name, run_name, epochs
        )

        success = self.run_experiment(cmd, run_name)

        if success:
            logger.info("✅ Training completed successfully")
            logger.info("📊 Check MLflow UI for results: http://localhost:5001")
        else:
            logger.error("❌ Training failed")

        return success


def main():
    """Main function for training launcher"""
    parser = argparse.ArgumentParser(description='Expanded Training Launcher')

    # Required arguments
    parser.add_argument('--config', required=True,
                       help='Model configuration file')
    parser.add_argument('--dataset-config', required=True,
                       help='Dataset configuration file')

    # Training parameters
    parser.add_argument('--epochs', type=int, default=50,
                       help='Number of training epochs')
    parser.add_argument('--experiment-name', default='clinical-training',
                       help='MLflow experiment name')
    parser.add_argument('--run-name',
                       help='MLflow run name (auto-generated if not specified)')

    # Hyperparameter sweep
    parser.add_argument('--grid',
                       help='Hyperparameter grid (e.g., "roi=96,128 cache=smart,cache amp=true")')

    # Execution control
    parser.add_argument('--dry-run', action='store_true',
                       help='Show commands without executing')
    parser.add_argument('--max-concurrent', type=int, default=1,
                       help='Maximum concurrent experiments')
    parser.add_argument('--timeout', type=int, default=3600,
                       help='Timeout per experiment in seconds')

    args = parser.parse_args()

    # Validate configuration files
    if not Path(args.config).exists():
        logger.error(f"❌ Model config not found: {args.config}")
        return False

    if not Path(args.dataset_config).exists():
        logger.error(f"❌ Dataset config not found: {args.dataset_config}")
        return False

    # Create launcher
    launcher = ExpandedTrainingLauncher()

    # Generate run name if not specified
    if not args.run_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if args.grid:
            args.run_name = f"sweep_{timestamp}"
        else:
            args.run_name = f"single_{timestamp}"

    logger.info("🚀 Expanded Training Launcher")
    logger.info(f"📁 Model config: {args.config}")
    logger.info(f"📁 Dataset config: {args.dataset_config}")
    logger.info(f"🎯 Experiment: {args.experiment_name}")
    logger.info(f"🏷️ Run name: {args.run_name}")

    # Run sweep or single experiment
    if args.grid:
        logger.info(f"🔍 Hyperparameter grid: {args.grid}")
        success = launcher.run_sweep(
            args.config, args.dataset_config, args.grid,
            args.epochs, args.experiment_name, args.dry_run,
            args.max_concurrent, args.timeout
        )
    else:
        logger.info("🎯 Single experiment mode")
        success = launcher.run_single_training(
            args.config, args.dataset_config, args.epochs,
            args.experiment_name, args.run_name
        )

    if success:
        logger.info("🎉 Training launcher completed successfully!")
        logger.info("📊 Check results at: http://localhost:5001")
    else:
        logger.error("❌ Training launcher failed")

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
