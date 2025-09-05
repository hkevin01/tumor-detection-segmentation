#!/usr/bin/env python3
"""
VSCode Crash Prevention System
Automatically optimizes system settings to prevent crashes during medical imaging workflows
"""

import json
import os
import subprocess
import sys
from pathlib import Path


class VSCodeCrashPrevention:
    def __init__(self):
        self.project_root = Path.cwd()
        self.vscode_settings_dir = self.project_root / ".vscode"
        self.vscode_settings_file = self.vscode_settings_dir / "settings.json"
        self.crash_logs_dir = Path("logs/crash_prevention")
        self.crash_logs_dir.mkdir(parents=True, exist_ok=True)

    def install_monitoring_dependencies(self):
        """Install required packages for monitoring"""
        print("📦 Installing monitoring dependencies...")

        dependencies = [
            "psutil>=5.9.0",
            "GPUtil>=1.4.0",
            "memory-profiler>=0.60.0",
            "line-profiler>=4.0.0",
            "pympler>=0.9"
        ]

        try:
            for dep in dependencies:
                print(f"  Installing {dep}...")
                subprocess.run([sys.executable, "-m", "pip", "install", dep],
                             check=True, capture_output=True)
            print("✅ All monitoring dependencies installed")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies: {e}")
            return False

    def optimize_vscode_settings(self):
        """Optimize VSCode settings to prevent crashes"""
        print("⚙️  Optimizing VSCode settings...")

        # Create .vscode directory if it doesn't exist
        self.vscode_settings_dir.mkdir(exist_ok=True)

        # Load existing settings or create new
        settings = {}
        if self.vscode_settings_file.exists():
            try:
                with open(self.vscode_settings_file, 'r') as f:
                    settings = json.load(f)
                print("  📄 Loaded existing VSCode settings")
            except json.JSONDecodeError:
                print("  ⚠️  Corrupted settings file, creating new one")
                settings = {}

        # Memory and performance optimizations
        crash_prevention_settings = {
            # Memory management
            "files.watcherExclude": {
                "**/logs/**": True,
                "**/data/**": True,
                "**/models/**": True,
                "**/reports/**": True,
                "**/.venv/**": True,
                "**/venv/**": True,
                "**/__pycache__/**": True,
                "**/*.pyc": True,
                "**/.git/**": True,
                "**/node_modules/**": True,
                "**/temp/**": True,
                "**/tmp/**": True
            },

            # File handling optimizations
            "files.maxMemoryForLargeFilesMB": 512,
            "search.maxResults": 10000,
            "search.smartCase": True,
            "search.followSymlinks": False,

            # Python-specific optimizations
            "python.analysis.memory.keepLibraryAst": False,
            "python.analysis.indexing": False,
            "python.analysis.packageIndexDepths": [
                {
                    "name": "",
                    "depth": 1
                }
            ],
            "python.analysis.autoImportCompletions": False,
            "python.analysis.completeFunctionParens": False,

            # Jupyter notebook optimizations
            "jupyter.enableCellCodeLens": False,
            "jupyter.askForKernelRestart": False,
            "jupyter.alwaysTrustNotebooks": True,
            "jupyter.widgetScriptSources": ["jsdelivr.com", "unpkg.com"],
            "jupyter.outputScrolling": True,
            "jupyter.enableScrollingForCellOutputs": True,
            "jupyter.maxOutputSize": 400,
            "jupyter.textOutputLimit": 30000,

            # Git optimizations
            "git.enabled": True,
            "git.autoRepositoryDetection": False,
            "git.decorations.enabled": False,
            "git.autoStash": False,

            # Extension optimizations
            "extensions.autoUpdate": False,
            "extensions.autoCheckUpdates": False,

            # Editor optimizations
            "editor.wordWrap": "on",
            "editor.minimap.enabled": False,
            "editor.suggest.showWords": False,
            "editor.suggest.showSnippets": False,
            "editor.quickSuggestions": {
                "other": False,
                "comments": False,
                "strings": False
            },

            # Terminal optimizations
            "terminal.integrated.scrollback": 1000,
            "terminal.integrated.fastScrollSensitivity": 5,

            # Medical imaging specific
            "python.defaultInterpreterPath": "./.venv/bin/python",
            "python.terminal.activateEnvironment": True,
            "python.envFile": "${workspaceFolder}/.env",

            # Crash prevention warnings
            "window.title": "🧠 Tumor Detection - ${activeEditorShort}",
            "workbench.colorTheme": "Default Light+",  # Lighter theme uses less resources
        }

        # Merge with existing settings
        settings.update(crash_prevention_settings)

        # Save optimized settings
        try:
            with open(self.vscode_settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            print("✅ VSCode settings optimized for crash prevention")
            return True
        except Exception as e:
            print(f"❌ Failed to save VSCode settings: {e}")
            return False

    def create_memory_optimized_configs(self):
        """Create memory-optimized configuration files"""
        print("📝 Creating memory-optimized configs...")

        # Low-memory training config
        low_memory_config = {
            "model": {
                "name": "UNETR",
                "img_size": [64, 64, 64],  # Reduced from 96x96x96
                "feature_size": 16,        # Reduced from 32
                "hidden_size": 512,        # Reduced from 768
                "mlp_dim": 2048,          # Reduced from 3072
                "num_heads": 8,           # Reduced from 12
                "pos_embed": "conv",
                "norm_name": "instance",
                "dropout_rate": 0.0
            },
            "training": {
                "batch_size": 1,           # Force batch size 1
                "val_batch_size": 1,
                "cache_mode": "none",      # Disable caching
                "num_workers": 1,          # Reduce workers
                "pin_memory": False,       # Disable pin memory
                "persistent_workers": False
            },
            "memory_optimization": {
                "gradient_checkpointing": True,
                "mixed_precision": True,
                "gradient_accumulation_steps": 4,
                "empty_cache_frequency": 10
            }
        }

        config_dir = Path("config/memory_optimized")
        config_dir.mkdir(parents=True, exist_ok=True)

        with open(config_dir / "low_memory_unetr.json", 'w') as f:
            json.dump(low_memory_config, f, indent=2)

        # CPU-only fallback config
        cpu_config = low_memory_config.copy()
        cpu_config["model"]["img_size"] = [32, 32, 32]  # Even smaller for CPU
        cpu_config["training"]["batch_size"] = 1
        cpu_config["training"]["use_cuda"] = False

        with open(config_dir / "cpu_fallback.json", 'w') as f:
            json.dump(cpu_config, f, indent=2)

        print("✅ Memory-optimized configs created")
        return True

    def setup_memory_monitoring_scripts(self):
        """Create memory monitoring wrapper scripts"""
        print("🔧 Setting up memory monitoring scripts...")

        scripts_dir = Path("scripts/monitoring")
        scripts_dir.mkdir(parents=True, exist_ok=True)

        # Training wrapper with monitoring
        training_wrapper = '''#!/bin/bash
# Memory-monitored training wrapper

echo "🧠 Starting memory-monitored training..."

# Start monitoring in background
python scripts/monitoring/vscode_crash_monitor.py --action start &
MONITOR_PID=$!

# Cleanup function
cleanup() {
    echo "🛑 Stopping monitoring..."
    kill $MONITOR_PID 2>/dev/null
    # Force garbage collection
    python -c "import gc; gc.collect()"
    # Clear CUDA cache if available
    python -c "try: import torch; torch.cuda.empty_cache(); except: pass"
}

# Set trap for cleanup
trap cleanup EXIT INT TERM

# Set memory limits
ulimit -v 8388608  # 8GB virtual memory limit

# Set environment variables for memory optimization
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128
export CUDA_VISIBLE_DEVICES=0
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

# Run training with memory monitoring
echo "🚀 Starting training..."
python "$@"

# Cleanup
cleanup
'''

        wrapper_script = scripts_dir / "monitored_train.sh"
        with open(wrapper_script, 'w') as f:
            f.write(training_wrapper)

        # Make executable
        os.chmod(wrapper_script, 0o755)

        # Emergency stop script
        emergency_stop = '''#!/bin/bash
# Emergency stop script for runaway processes

echo "🚨 EMERGENCY STOP TRIGGERED"

# Kill all Python training processes
pkill -f "train_enhanced.py"
pkill -f "train.py"

# Kill high-memory Python processes
ps aux | grep python | awk '$6 > 1000000 {print $2}' | xargs kill -9 2>/dev/null

# Clear GPU memory
python -c "
try:
    import torch
    torch.cuda.empty_cache()
    print('✅ GPU cache cleared')
except:
    print('ℹ️  No GPU cache to clear')
"

# Force garbage collection
python -c "import gc; gc.collect(); print('✅ Garbage collection completed')"

echo "✅ Emergency stop completed"
'''

        emergency_script = scripts_dir / "emergency_stop.sh"
        with open(emergency_script, 'w') as f:
            f.write(emergency_stop)

        os.chmod(emergency_script, 0o755)

        print("✅ Memory monitoring scripts created")
        return True

    def setup_environment_file(self):
        """Create optimized environment file"""
        print("🌍 Setting up optimized environment...")

        env_content = '''# VSCode Crash Prevention Environment Variables

# Memory optimization
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:128
CUDA_LAUNCH_BLOCKING=1

# Threading optimization
OMP_NUM_THREADS=1
MKL_NUM_THREADS=1
NUMEXPR_NUM_THREADS=1

# Python optimization
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1

# Jupyter optimization
JUPYTER_MEMORY_LIMIT=2G

# VSCode optimization
VSCODE_CRASH_PREVENTION=enabled
'''

        with open(".env", 'w') as f:
            f.write(env_content)

        print("✅ Environment file created")
        return True

    def create_launch_configs(self):
        """Create VSCode launch configurations for safe debugging"""
        print("🚀 Creating safe launch configurations...")

        launch_config = {
            "version": "0.2.0",
            "configurations": [
                {
                    "name": "🧠 Safe Training (Low Memory)",
                    "type": "python",
                    "request": "launch",
                    "program": "${workspaceFolder}/src/training/train_enhanced.py",
                    "args": [
                        "--config", "config/memory_optimized/low_memory_unetr.json",
                        "--dataset-config", "config/datasets/msd_task01_brain.json",
                        "--epochs", "1",
                        "--amp",
                        "--output-dir", "logs/safe_training"
                    ],
                    "console": "integratedTerminal",
                    "env": {
                        "PYTORCH_CUDA_ALLOC_CONF": "max_split_size_mb:128",
                        "OMP_NUM_THREADS": "1",
                        "MKL_NUM_THREADS": "1"
                    },
                    "envFile": "${workspaceFolder}/.env"
                },
                {
                    "name": "🖥️ CPU-Only Training",
                    "type": "python",
                    "request": "launch",
                    "program": "${workspaceFolder}/src/training/train_enhanced.py",
                    "args": [
                        "--config", "config/memory_optimized/cpu_fallback.json",
                        "--dataset-config", "config/datasets/msd_task01_brain.json",
                        "--epochs", "1",
                        "--no-cuda",
                        "--output-dir", "logs/cpu_training"
                    ],
                    "console": "integratedTerminal",
                    "env": {
                        "CUDA_VISIBLE_DEVICES": "",
                        "OMP_NUM_THREADS": "2"
                    }
                },
                {
                    "name": "🔍 Memory Monitor",
                    "type": "python",
                    "request": "launch",
                    "program": "${workspaceFolder}/scripts/monitoring/vscode_crash_monitor.py",
                    "args": ["--action", "start"],
                    "console": "integratedTerminal"
                }
            ]
        }

        launch_file = self.vscode_settings_dir / "launch.json"
        with open(launch_file, 'w') as f:
            json.dump(launch_config, f, indent=2)

        print("✅ Safe launch configurations created")
        return True

    def create_tasks(self):
        """Create VSCode tasks for monitoring and cleanup"""
        print("⚡ Creating monitoring and cleanup tasks...")

        tasks_config = {
            "version": "2.0.0",
            "tasks": [
                {
                    "label": "🔍 Start Memory Monitor",
                    "type": "shell",
                    "command": "python",
                    "args": ["scripts/monitoring/vscode_crash_monitor.py", "--action", "start"],
                    "group": "build",
                    "presentation": {
                        "echo": True,
                        "reveal": "always",
                        "focus": False,
                        "panel": "new"
                    },
                    "isBackground": True
                },
                {
                    "label": "📊 Memory Report",
                    "type": "shell",
                    "command": "python",
                    "args": ["scripts/monitoring/vscode_crash_monitor.py", "--action", "report"],
                    "group": "test"
                },
                {
                    "label": "🚨 Emergency Cleanup",
                    "type": "shell",
                    "command": "bash",
                    "args": ["scripts/monitoring/emergency_stop.sh"],
                    "group": "build"
                },
                {
                    "label": "🧠 Safe Training (Monitored)",
                    "type": "shell",
                    "command": "bash",
                    "args": [
                        "scripts/monitoring/monitored_train.sh",
                        "src/training/train_enhanced.py",
                        "--config", "config/memory_optimized/low_memory_unetr.json",
                        "--dataset-config", "config/datasets/msd_task01_brain.json",
                        "--epochs", "2"
                    ],
                    "group": "build",
                    "presentation": {
                        "echo": True,
                        "reveal": "always",
                        "panel": "new"
                    }
                }
            ]
        }

        tasks_file = self.vscode_settings_dir / "tasks.json"
        with open(tasks_file, 'w') as f:
            json.dump(tasks_config, f, indent=2)

        print("✅ Monitoring and cleanup tasks created")
        return True

    def run_full_setup(self):
        """Run complete crash prevention setup"""
        print("🚀 Setting up VSCode crash prevention system...")
        print("=" * 60)

        success_count = 0
        total_steps = 7

        steps = [
            ("Installing monitoring dependencies", self.install_monitoring_dependencies),
            ("Optimizing VSCode settings", self.optimize_vscode_settings),
            ("Creating memory-optimized configs", self.create_memory_optimized_configs),
            ("Setting up monitoring scripts", self.setup_memory_monitoring_scripts),
            ("Creating environment file", self.setup_environment_file),
            ("Creating launch configurations", self.create_launch_configs),
            ("Creating tasks", self.create_tasks)
        ]

        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            if step_func():
                success_count += 1
                print(f"✅ {step_name} completed")
            else:
                print(f"❌ {step_name} failed")

        print("\n" + "=" * 60)
        print(f"🎯 Setup completed: {success_count}/{total_steps} steps successful")

        if success_count == total_steps:
            print("\n🎉 VSCode crash prevention system fully installed!")
            print("\n📝 Next steps:")
            print("  1. Restart VSCode to apply settings")
            print("  2. Use 'Safe Training (Low Memory)' launch config")
            print("  3. Run 'Start Memory Monitor' task before training")
            print("  4. Use 'Emergency Cleanup' task if needed")
            print("\n⚡ Quick start commands:")
            print("  • Ctrl+Shift+P → 'Tasks: Run Task' → 'Start Memory Monitor'")
            print("  • F5 → Select 'Safe Training (Low Memory)'")
            print("  • Ctrl+Shift+P → 'Tasks: Run Task' → 'Emergency Cleanup'")
        else:
            print("\n⚠️  Some setup steps failed. Check the errors above.")

        return success_count == total_steps

def main():
    prevention_system = VSCodeCrashPrevention()
    prevention_system.run_full_setup()

if __name__ == "__main__":
    main()
