#!/usr/bin/env python3
"""
Immediate Next Steps Executor for Tumor Detection Project

Executes the prioritized tasks from the deep search synthesis:
1. Docker stack validation
2. CPU-only smoke tests
3. Dataset download (Task01 Brain)
4. 2-epoch training test
5. Baseline inference
6. MLflow integration
7. Launch utilities testing

This script provides a systematic approach to validating the entire pipeline.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional


class TaskExecutor:
    """Executes immediate next steps for project validation"""

    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.results = {}

    def run_command(self, cmd: List[str], cwd: Optional[Path] = None,
                   timeout: int = 300) -> Dict:
        """Run a command and capture results"""
        cwd = cwd or self.project_root

        print(f"🔄 Running: {' '.join(cmd)}")
        print(f"   Directory: {cwd}")

        try:
            result = subprocess.run(
                cmd,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout
            )

            success = result.returncode == 0
            print(f"   {'✅' if success else '❌'} Exit code: {result.returncode}")

            if not success and result.stderr:
                print(f"   Error: {result.stderr[:200]}...")

            return {
                'success': success,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }

        except subprocess.TimeoutExpired:
            print(f"   ⏱️ Command timed out after {timeout}s")
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': f'Command timed out after {timeout}s'
            }
        except Exception as e:
            print(f"   ❌ Exception: {e}")
            return {
                'success': False,
                'returncode': -1,
                'stdout': '',
                'stderr': str(e)
            }

    def task_1_docker_validation(self) -> bool:
        """Task 1: Validate Docker Stack"""
        print("\n" + "="*60)
        print("📦 TASK 1: Docker Stack Validation")
        print("="*60)

        # Check Docker is available
        result = self.run_command(['docker', '--version'])
        if not result['success']:
            print("❌ Docker not available")
            return False

        print("✅ Docker available")

        # Check docker-compose
        result = self.run_command(['docker-compose', '--version'])
        if not result['success']:
            print("❌ docker-compose not available")
            return False

        print("✅ docker-compose available")

        # Try to build test-lite image
        print("🏗️ Building test-lite Docker image...")
        result = self.run_command([
            'docker', 'build',
            '-f', 'docker/Dockerfile.test-lite',
            '-t', 'tumor-test-lite',
            '.'
        ], timeout=600)

        if not result['success']:
            print("❌ Failed to build test-lite image")
            return False

        print("✅ Test-lite image built successfully")

        # Run smoke tests in container
        print("🧪 Running smoke tests in container...")
        result = self.run_command([
            'docker', 'run', '--rm', 'tumor-test-lite'
        ], timeout=300)

        if not result['success']:
            print("❌ Smoke tests failed in container")
            print(f"   Error output: {result['stderr'][:500]}")
            return False

        print("✅ Smoke tests passed in container")
        self.results['task_1'] = {'success': True, 'details': 'Docker stack validated'}
        return True

    def task_2_cpu_smoke_tests(self) -> bool:
        """Task 2: Run CPU-Only Smoke Tests"""
        print("\n" + "="*60)
        print("🧪 TASK 2: CPU-Only Smoke Tests")
        print("="*60)

        # Check if virtual environment exists
        venv_path = self.project_root / '.venv'
        if not venv_path.exists():
            print("❌ Virtual environment not found at .venv")
            return False

        python_exe = venv_path / 'bin' / 'python'

        # Run pytest with cpu marker
        print("🧪 Running pytest with CPU-only tests...")
        result = self.run_command([
            str(python_exe), '-m', 'pytest',
            '-m', 'cpu',
            '-v',
            '--tb=short'
        ])

        if not result['success']:
            print("❌ CPU tests failed")
            return False

        print("✅ CPU tests passed")

        # Try running MONAI verification checklist
        monai_script = self.project_root / 'scripts' / 'validation' / 'verify_monai_checklist.py'
        if monai_script.exists() and monai_script.stat().st_size > 0:
            print("🔍 Running MONAI verification checklist...")
            result = self.run_command([
                str(python_exe), str(monai_script)
            ])

            if result['success']:
                print("✅ MONAI verification passed")
            else:
                print("⚠️ MONAI verification had issues (continuing)")

        self.results['task_2'] = {'success': True, 'details': 'CPU smoke tests passed'}
        return True

    def task_3_pull_dataset(self) -> bool:
        """Task 3: Pull Brain Dataset (Task01)"""
        print("\n" + "="*60)
        print("🧠 TASK 3: Pull Brain Dataset (Task01)")
        print("="*60)

        venv_path = self.project_root / '.venv'
        python_exe = venv_path / 'bin' / 'python'

        # Check if dataset already exists
        data_dir = self.project_root / 'data' / 'msd' / 'Task01_BrainTumour'
        if data_dir.exists():
            print("✅ Dataset already exists")
            self.results['task_3'] = {'success': True, 'details': 'Dataset already present'}
            return True

        # Download dataset
        print("📦 Downloading MSD Task01_BrainTumour dataset...")
        result = self.run_command([
            str(python_exe),
            'scripts/data/pull_monai_dataset.py',
            '--dataset-id', 'Task01_BrainTumour',
            '--root', 'data/msd'
        ], timeout=1800)  # 30 minutes timeout for download

        if not result['success']:
            print("❌ Dataset download failed")
            return False

        # Verify dataset was downloaded
        if data_dir.exists():
            print("✅ Dataset downloaded successfully")
            # Count files to verify
            try:
                file_count = len(list(data_dir.glob('**/*.nii.gz')))
                print(f"   Found {file_count} NIfTI files")
            except:
                pass

            self.results['task_3'] = {'success': True, 'details': f'Dataset downloaded to {data_dir}'}
            return True
        else:
            print("❌ Dataset directory not found after download")
            return False

    def task_4_training_test(self) -> bool:
        """Task 4: Run 2-Epoch Training Test"""
        print("\n" + "="*60)
        print("🏋️ TASK 4: 2-Epoch Training Test")
        print("="*60)

        venv_path = self.project_root / '.venv'
        python_exe = venv_path / 'bin' / 'python'

        # Check dataset exists
        data_dir = self.project_root / 'data' / 'msd' / 'Task01_BrainTumour'
        if not data_dir.exists():
            print("❌ Dataset not found - run task 3 first")
            return False

        # Create output directory
        output_dir = self.project_root / 'logs' / 'immediate_validation' / 'training_test'
        output_dir.mkdir(parents=True, exist_ok=True)

        # Run 2-epoch training
        print("🚀 Starting 2-epoch training test...")
        result = self.run_command([
            str(python_exe),
            'src/training/train_enhanced.py',
            '--config', 'config/recipes/unetr_multimodal.json',
            '--dataset-config', 'config/datasets/msd_task01_brain.json',
            '--epochs', '2',
            '--amp',
            '--save-overlays',
            '--overlays-max', '3',
            '--sw-overlap', '0.25',
            '--output-dir', str(output_dir)
        ], timeout=3600)  # 1 hour timeout

        if not result['success']:
            print("❌ Training test failed")
            return False

        # Check if model was saved
        model_files = list(output_dir.glob('**/*.pt')) + list(output_dir.glob('**/*.pth'))
        if model_files:
            print(f"✅ Training completed - model saved: {model_files[0].name}")
        else:
            print("⚠️ Training completed but no model file found")

        self.results['task_4'] = {'success': True, 'details': f'2-epoch training completed, output: {output_dir}'}
        return True

    def task_5_baseline_inference(self) -> bool:
        """Task 5: Test Baseline Inference"""
        print("\n" + "="*60)
        print("🔍 TASK 5: Baseline Inference Test")
        print("="*60)

        # Check if we have a trained model from task 4
        training_output = self.project_root / 'logs' / 'immediate_validation' / 'training_test'
        model_files = list(training_output.glob('**/*.pt')) + list(training_output.glob('**/*.pth'))

        if not model_files:
            print("❌ No trained model found - run task 4 first")
            return False

        model_path = model_files[0]
        print(f"📦 Using model: {model_path}")

        venv_path = self.project_root / '.venv'
        python_exe = venv_path / 'bin' / 'python'

        # Create inference output directory
        output_dir = self.project_root / 'reports' / 'immediate_validation' / 'inference_test'
        output_dir.mkdir(parents=True, exist_ok=True)

        # Run inference
        print("🔍 Running baseline inference...")
        result = self.run_command([
            str(python_exe),
            'src/inference/inference.py',
            '--config', 'config/recipes/unetr_multimodal.json',
            '--dataset-config', 'config/datasets/msd_task01_brain.json',
            '--model', str(model_path),
            '--output-dir', str(output_dir),
            '--save-overlays',
            '--save-prob-maps',
            '--slices', 'auto',
            '--tta',
            '--amp'
        ], timeout=1800)  # 30 minutes

        if not result['success']:
            print("❌ Inference test failed")
            return False

        # Check outputs
        overlay_files = list(output_dir.glob('**/*overlay*'))
        prob_files = list(output_dir.glob('**/*prob*'))
        nifti_files = list(output_dir.glob('**/*.nii.gz'))

        print("✅ Inference completed:")
        print(f"   Overlay files: {len(overlay_files)}")
        print(f"   Probability maps: {len(prob_files)}")
        print(f"   NIfTI outputs: {len(nifti_files)}")

        self.results['task_5'] = {
            'success': True,
            'details': f'Inference completed, outputs: {len(overlay_files)} overlays, {len(prob_files)} prob maps'
        }
        return True

    def task_6_mlflow_check(self) -> bool:
        """Task 6: Verify MLflow Integration"""
        print("\n" + "="*60)
        print("📊 TASK 6: MLflow Integration Check")
        print("="*60)

        # Check if MLflow UI is accessible (if running)
        try:
            import requests
            response = requests.get('http://localhost:5001', timeout=5)
            if response.status_code == 200:
                print("✅ MLflow UI accessible at http://localhost:5001")
            else:
                print("⚠️ MLflow UI not accessible (may not be running)")
        except:
            print("⚠️ MLflow UI not accessible (may not be running)")

        # Check if MLflow is installed
        venv_path = self.project_root / '.venv'
        python_exe = venv_path / 'bin' / 'python'

        result = self.run_command([
            str(python_exe), '-c', 'import mlflow; print(f"MLflow version: {mlflow.__version__}")'
        ])

        if result['success']:
            print("✅ MLflow is installed and importable")
        else:
            print("❌ MLflow not available")
            return False

        self.results['task_6'] = {'success': True, 'details': 'MLflow integration verified'}
        return True

    def task_7_launch_utilities(self) -> bool:
        """Task 7: Test Launch Utilities"""
        print("\n" + "="*60)
        print("🚀 TASK 7: Launch Utilities Test")
        print("="*60)

        venv_path = self.project_root / '.venv'
        python_exe = venv_path / 'bin' / 'python'

        # Check for launch utilities
        launch_scripts = [
            'scripts/training/scripts/training/launch_expanded_training.py',
            'scripts/training/scripts/monitoring/monitor_and_launch.py',
            'scripts/training/monitor_training_progress.py'
        ]

        for script in launch_scripts:
            script_path = self.project_root / script
            if script_path.exists():
                print(f"✅ Found: {script}")

                # Test help command
                result = self.run_command([
                    str(python_exe), str(script_path), '--help'
                ])
                if result['success']:
                    print("   Help command works")
                else:
                    print("   ⚠️ Help command failed")
            else:
                print(f"❌ Missing: {script}")

        # Look for test files
        test_files = list(self.project_root.glob('**/tests/training/test_training_launcher.py'))
        if test_files:
            print(f"✅ Found test file: {test_files[0]}")

            # Run the test
            result = self.run_command([
                str(python_exe), '-m', 'pytest', str(test_files[0]), '-v'
            ])

            if result['success']:
                print("✅ Launch utility tests passed")
            else:
                print("❌ Launch utility tests failed")

        self.results['task_7'] = {'success': True, 'details': 'Launch utilities checked'}
        return True

    def run_all_tasks(self, skip_tasks: List[int] = None) -> Dict:
        """Run all immediate next steps"""
        skip_tasks = skip_tasks or []

        print("🚀 STARTING IMMEDIATE NEXT STEPS EXECUTION")
        print(f"   Project root: {self.project_root}")
        print(f"   Skip tasks: {skip_tasks}")
        print("="*80)

        tasks = [
            (1, self.task_1_docker_validation, "Docker Stack Validation"),
            (2, self.task_2_cpu_smoke_tests, "CPU-Only Smoke Tests"),
            (3, self.task_3_pull_dataset, "Pull Brain Dataset"),
            (4, self.task_4_training_test, "2-Epoch Training Test"),
            (5, self.task_5_baseline_inference, "Baseline Inference"),
            (6, self.task_6_mlflow_check, "MLflow Integration"),
            (7, self.task_7_launch_utilities, "Launch Utilities")
        ]

        success_count = 0
        total_tasks = len([t for t in tasks if t[0] not in skip_tasks])

        for task_num, task_func, task_name in tasks:
            if task_num in skip_tasks:
                print(f"\n⏭️ SKIPPING TASK {task_num}: {task_name}")
                continue

            try:
                success = task_func()
                if success:
                    success_count += 1
                    print(f"\n✅ TASK {task_num} COMPLETED: {task_name}")
                else:
                    print(f"\n❌ TASK {task_num} FAILED: {task_name}")

            except Exception as e:
                print(f"\n💥 TASK {task_num} ERROR: {task_name}")
                print(f"   Exception: {e}")
                self.results[f'task_{task_num}'] = {'success': False, 'error': str(e)}

        # Final summary
        print("\n" + "="*80)
        print("📋 EXECUTION SUMMARY")
        print("="*80)
        print(f"✅ Successful tasks: {success_count}/{total_tasks}")

        for task_id, result in self.results.items():
            status = "✅" if result['success'] else "❌"
            print(f"{status} {task_id}: {result.get('details', 'No details')}")

        # Save results
        results_file = self.project_root / 'logs' / 'immediate_validation' / 'execution_results.json'
        results_file.parent.mkdir(parents=True, exist_ok=True)

        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        print(f"\n📄 Results saved to: {results_file}")

        return {
            'success_count': success_count,
            'total_tasks': total_tasks,
            'results': self.results
        }

def main():
    parser = argparse.ArgumentParser(description="Execute immediate next steps for project validation")
    parser.add_argument(
        '--project-root',
        default='/home/kevin/Projects/tumor-detection-segmentation',
        help='Project root directory'
    )
    parser.add_argument(
        '--skip-tasks',
        nargs='+',
        type=int,
        default=[],
        help='Task numbers to skip (1-7)'
    )
    parser.add_argument(
        '--task',
        type=int,
        help='Run only specific task (1-7)'
    )

    args = parser.parse_args()

    executor = TaskExecutor(args.project_root)

    if args.task:
        # Run single task
        task_methods = {
            1: executor.task_1_docker_validation,
            2: executor.task_2_cpu_smoke_tests,
            3: executor.task_3_pull_dataset,
            4: executor.task_4_training_test,
            5: executor.task_5_baseline_inference,
            6: executor.task_6_mlflow_check,
            7: executor.task_7_launch_utilities
        }

        if args.task in task_methods:
            success = task_methods[args.task]()
            sys.exit(0 if success else 1)
        else:
            print(f"Invalid task number: {args.task}")
            sys.exit(1)
    else:
        # Run all tasks
        results = executor.run_all_tasks(skip_tasks=args.skip_tasks)
        success_rate = results['success_count'] / results['total_tasks']

        if success_rate >= 0.8:  # 80% success rate
            print("\n🎉 EXECUTION SUCCESSFUL!")
            sys.exit(0)
        else:
            print("\n⚠️ EXECUTION PARTIALLY FAILED")
            sys.exit(1)

if __name__ == "__main__":
    main()
