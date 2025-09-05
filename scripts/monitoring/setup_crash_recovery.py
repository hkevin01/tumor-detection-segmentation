#!/usr/bin/env python3
"""
VSCode Crash Recovery System
Automatically recovers from crashes and saves work
"""

import os
from pathlib import Path


class CrashRecoverySystem:
    def __init__(self):
        self.project_root = Path.cwd()
        self.recovery_dir = Path("recovery")
        self.recovery_dir.mkdir(exist_ok=True)

        # Setup auto-save
        self.auto_save_interval = 30  # seconds
        self.auto_save_thread = None
        self.running = False

    def setup_auto_save(self):
        """Setup automatic saving of important files"""
        print("💾 Setting up auto-save system...")

        important_files = [
            "src/**/*.py",
            "config/**/*.json",
            "notebooks/**/*.ipynb",
            ".vscode/settings.json",
            ".vscode/launch.json",
            ".vscode/tasks.json"
        ]

        # Create auto-save script
        auto_save_script = f'''#!/bin/bash
# Auto-save important files every {self.auto_save_interval} seconds

RECOVERY_DIR="{self.recovery_dir}"
PROJECT_ROOT="{self.project_root}"

while true; do
    timestamp=$(date '+%Y%m%d_%H%M%S')
    backup_dir="$RECOVERY_DIR/auto_backup_$timestamp"

    # Create backup directory
    mkdir -p "$backup_dir"

    # Copy important files
    find "$PROJECT_ROOT" -name "*.py" -path "*/src/*" -exec cp --parents {{}} "$backup_dir" \\;
    find "$PROJECT_ROOT" -name "*.json" -path "*/config/*" -exec cp --parents {{}} "$backup_dir" \\;
    find "$PROJECT_ROOT" -name "*.ipynb" -path "*/notebooks/*" -exec cp --parents {{}} "$backup_dir" \\;

    # Copy VSCode settings
    if [ -d "$PROJECT_ROOT/.vscode" ]; then
        cp -r "$PROJECT_ROOT/.vscode" "$backup_dir/"
    fi

    # Keep only last 10 backups
    ls -dt "$RECOVERY_DIR"/auto_backup_* | tail -n +11 | xargs rm -rf

    sleep {self.auto_save_interval}
done
'''

        script_path = self.recovery_dir / "auto_save.sh"
        with open(script_path, 'w') as f:
            f.write(auto_save_script)

        os.chmod(script_path, 0o755)
        print("✅ Auto-save script created")
        return True

    def create_crash_detection(self):
        """Create crash detection system"""
        print("🔍 Setting up crash detection...")

        crash_detector = '''#!/usr/bin/env python3
import psutil
import time
import json
import os
from datetime import datetime
from pathlib import Path

def detect_vscode_crash():
    """Monitor VSCode processes and detect crashes"""
    recovery_dir = Path("recovery")
    recovery_dir.mkdir(exist_ok=True)

    last_vscode_count = 0
    crash_count = 0

    while True:
        try:
            # Count VSCode processes
            vscode_procs = [p for p in psutil.process_iter(['name'])
                           if 'code' in p.info['name'].lower()]
            current_count = len(vscode_procs)

            # Detect sudden drop in VSCode processes (potential crash)
            if last_vscode_count > 0 and current_count == 0:
                crash_count += 1
                crash_info = {
                    'timestamp': datetime.now().isoformat(),
                    'crash_number': crash_count,
                    'previous_process_count': last_vscode_count,
                    'system_memory_percent': psutil.virtual_memory().percent,
                    'system_cpu_percent': psutil.cpu_percent()
                }

                # Save crash info
                crash_file = recovery_dir / f"crash_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(crash_file, 'w') as f:
                    json.dump(crash_info, f, indent=2)

                print(f"🚨 VSCode crash detected! Crash #{crash_count}")
                print(f"   Memory: {crash_info['system_memory_percent']:.1f}%")
                print(f"   CPU: {crash_info['system_cpu_percent']:.1f}%")

                # Trigger recovery
                os.system("python recovery/recovery_assistant.py")

            last_vscode_count = current_count
            time.sleep(5)

        except Exception as e:
            print(f"Crash detection error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    detect_vscode_crash()
'''

        detector_path = self.recovery_dir / "crash_detector.py"
        with open(detector_path, 'w') as f:
            f.write(crash_detector)

        print("✅ Crash detector created")
        return True

    def create_recovery_assistant(self):
        """Create recovery assistant that helps after crashes"""
        print("🛠️ Setting up recovery assistant...")

        recovery_assistant = '''#!/usr/bin/env python3
"""
Recovery Assistant - Helps recover from VSCode crashes
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

def main():
    print("\\n🔧 VSCode Recovery Assistant")
    print("=" * 50)

    recovery_dir = Path("recovery")
    project_root = Path.cwd()

    # Check for recent backups
    backups = list(recovery_dir.glob("auto_backup_*"))
    backups.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    if not backups:
        print("❌ No backups found")
        return

    print(f"✅ Found {len(backups)} backup(s)")

    # Show most recent backup
    latest_backup = backups[0]
    backup_time = datetime.fromtimestamp(latest_backup.stat().st_mtime)
    print(f"📅 Latest backup: {backup_time.strftime('%Y-%m-%d %H:%M:%S')}")

    # Recovery options
    print("\\n🔧 Recovery Options:")
    print("1. Restore latest backup")
    print("2. List all backups")
    print("3. Check system status")
    print("4. Clear GPU memory")
    print("5. Exit")

    try:
        choice = input("\\nSelect option (1-5): ")

        if choice == "1":
            restore_backup(latest_backup, project_root)
        elif choice == "2":
            list_backups(backups)
        elif choice == "3":
            check_system_status()
        elif choice == "4":
            clear_gpu_memory()
        elif choice == "5":
            print("👋 Goodbye!")
        else:
            print("❌ Invalid choice")

    except KeyboardInterrupt:
        print("\\n👋 Recovery cancelled")

def restore_backup(backup_path, project_root):
    """Restore from backup"""
    print(f"\\n🔄 Restoring from {backup_path.name}...")

    try:
        # Restore source files
        src_backup = backup_path / "src"
        if src_backup.exists():
            print("  📁 Restoring source files...")
            shutil.copytree(src_backup, project_root / "src", dirs_exist_ok=True)

        # Restore config files
        config_backup = backup_path / "config"
        if config_backup.exists():
            print("  ⚙️  Restoring config files...")
            shutil.copytree(config_backup, project_root / "config", dirs_exist_ok=True)

        # Restore VSCode settings
        vscode_backup = backup_path / ".vscode"
        if vscode_backup.exists():
            print("  🎨 Restoring VSCode settings...")
            shutil.copytree(vscode_backup, project_root / ".vscode", dirs_exist_ok=True)

        print("✅ Backup restored successfully!")

    except Exception as e:
        print(f"❌ Restore failed: {e}")

def list_backups(backups):
    """List all available backups"""
    print("\\n📋 Available Backups:")
    for i, backup in enumerate(backups[:10], 1):  # Show latest 10
        backup_time = datetime.fromtimestamp(backup.stat().st_mtime)
        size_mb = sum(f.stat().st_size for f in backup.rglob('*') if f.is_file()) / 1024**2
        print(f"  {i}. {backup.name} - {backup_time.strftime('%m/%d %H:%M')} ({size_mb:.1f}MB)")

def check_system_status():
    """Check current system status"""
    print("\\n📊 System Status:")
    try:
        import psutil

        # Memory
        memory = psutil.virtual_memory()
        print(f"  💾 Memory: {memory.percent:.1f}% used ({memory.used/1024**3:.1f}GB / {memory.total/1024**3:.1f}GB)")

        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"  🖥️  CPU: {cpu_percent:.1f}%")

        # Disk
        disk = psutil.disk_usage('/')
        print(f"  💿 Disk: {disk.percent:.1f}% used ({disk.used/1024**3:.1f}GB / {disk.total/1024**3:.1f}GB)")

        # Processes
        vscode_procs = [p for p in psutil.process_iter(['name']) if 'code' in p.info['name'].lower()]
        python_procs = [p for p in psutil.process_iter(['name']) if 'python' in p.info['name'].lower()]
        print(f"  🔧 VSCode processes: {len(vscode_procs)}")
        print(f"  🐍 Python processes: {len(python_procs)}")

    except ImportError:
        print("  ❌ psutil not available for system monitoring")

def clear_gpu_memory():
    """Clear GPU memory"""
    print("\\n🧹 Clearing GPU memory...")
    try:
        import subprocess
        result = subprocess.run([
            sys.executable, "-c",
            "try: import torch; torch.cuda.empty_cache(); print('✅ GPU cache cleared'); except: print('❌ No GPU or PyTorch')"
        ], capture_output=True, text=True)
        print(result.stdout)
    except Exception as e:
        print(f"❌ Failed to clear GPU memory: {e}")

if __name__ == "__main__":
    main()
'''

        assistant_path = self.recovery_dir / "recovery_assistant.py"
        with open(assistant_path, 'w') as f:
            f.write(recovery_assistant)

        print("✅ Recovery assistant created")
        return True

    def setup_full_recovery_system(self):
        """Setup complete recovery system"""
        print("🚀 Setting up crash recovery system...")
        print("=" * 50)

        steps = [
            ("Setting up auto-save", self.setup_auto_save),
            ("Creating crash detection", self.create_crash_detection),
            ("Setting up recovery assistant", self.create_recovery_assistant)
        ]

        success_count = 0
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            if step_func():
                success_count += 1
                print(f"✅ {step_name} completed")
            else:
                print(f"❌ {step_name} failed")

        print("\n" + "=" * 50)
        print(f"🎯 Recovery system setup: {success_count}/{len(steps)} steps successful")

        if success_count == len(steps):
            print("\n🎉 Crash recovery system fully installed!")
            print("\n📝 Usage:")
            print("  • Auto-save runs every 30 seconds")
            print("  • Crash detector monitors VSCode processes")
            print("  • Recovery assistant helps after crashes")
            print("\n⚡ Manual commands:")
            print("  • Start auto-save: ./recovery/auto_save.sh &")
            print("  • Start crash detector: python recovery/crash_detector.py &")
            print("  • Run recovery: python recovery/recovery_assistant.py")

        return success_count == len(steps)

def main():
    recovery_system = CrashRecoverySystem()
    recovery_system.setup_full_recovery_system()

if __name__ == "__main__":
    main()
