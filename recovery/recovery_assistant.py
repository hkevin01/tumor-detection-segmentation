#!/usr/bin/env python3
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
    print("\n🔧 VSCode Recovery Assistant")
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
    print("\n🔧 Recovery Options:")
    print("1. Restore latest backup")
    print("2. List all backups")
    print("3. Check system status")
    print("4. Clear GPU memory")
    print("5. Exit")
    
    try:
        choice = input("\nSelect option (1-5): ")
        
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
        print("\n👋 Recovery cancelled")

def restore_backup(backup_path, project_root):
    """Restore from backup"""
    print(f"\n🔄 Restoring from {backup_path.name}...")
    
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
    print("\n📋 Available Backups:")
    for i, backup in enumerate(backups[:10], 1):  # Show latest 10
        backup_time = datetime.fromtimestamp(backup.stat().st_mtime)
        size_mb = sum(f.stat().st_size for f in backup.rglob('*') if f.is_file()) / 1024**2
        print(f"  {i}. {backup.name} - {backup_time.strftime('%m/%d %H:%M')} ({size_mb:.1f}MB)")

def check_system_status():
    """Check current system status"""
    print("\n📊 System Status:")
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
    print("\n🧹 Clearing GPU memory...")
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
