#!/usr/bin/env python3
"""
Training Progress Monitor
========================

Comprehensive monitoring for the expanded training sequence.
"""

import subprocess
from pathlib import Path
from datetime import datetime


def check_training_status():
    """Check current training process status."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "train_enhanced.py"],
            capture_output=True,
            text=True
        )
        
        if result.stdout.strip():
            # Get detailed process info
            ps_result = subprocess.run(
                ["ps", "aux"] + [line.strip() for line in result.stdout.strip().split('\n')],
                capture_output=True,
                text=True
            )
            return True, ps_result.stdout
        return False, None
    except Exception as e:
        return False, str(e)


def check_outputs():
    """Check for training outputs."""
    project_root = Path(".")
    
    outputs = {
        "mlruns": list(project_root.glob("mlruns")),
        "checkpoints": list(project_root.glob("models/checkpoints/*.pth")),
        "logs": list(project_root.glob("logs/**/*.log")),
        "cache": list(project_root.glob("cache/**")),
    }
    
    return {k: [str(p) for p in v] for k, v in outputs.items()}


def get_system_stats():
    """Get system resource usage."""
    try:
        # Memory usage
        mem_result = subprocess.run(
            ["free", "-h"],
            capture_output=True,
            text=True
        )
        
        # CPU load
        uptime_result = subprocess.run(
            ["uptime"],
            capture_output=True,
            text=True
        )
        
        return {
            "memory": mem_result.stdout,
            "uptime": uptime_result.stdout.strip()
        }
    except Exception as e:
        return {"error": str(e)}


def main():
    """Monitor training progress."""
    print("🔍 Training Progress Monitor")
    print("=" * 50)
    print(f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check training status
    is_running, process_info = check_training_status()
    
    if is_running:
        print("✅ Training is ACTIVE")
        print("Process details:")
        print(process_info)
    else:
        print("❌ No training processes found")
        print("Process check result:", process_info)
    
    print()
    
    # Check outputs
    outputs = check_outputs()
    print("📁 Output Status:")
    for category, files in outputs.items():
        if files:
            print(f"  ✅ {category}: {len(files)} items")
            for f in files[:3]:  # Show first 3
                print(f"     - {f}")
            if len(files) > 3:
                print(f"     ... and {len(files) - 3} more")
        else:
            print(f"  ⭕ {category}: None found")
    
    print()
    
    # System stats
    stats = get_system_stats()
    print("💻 System Status:")
    if "error" not in stats:
        print("Memory usage:")
        print(stats["memory"])
        print(f"Load: {stats['uptime']}")
    else:
        print(f"Error getting stats: {stats['error']}")
    
    print()
    print("=" * 50)
    
    # Training sequence status
    print("🎯 TRAINING SEQUENCE STATUS")
    print("Current stage: 5-epoch baseline training")
    print("Next stages: 10-epoch extended → 25-epoch production")
    print("Expected total time: ~30-60 minutes per 5-epoch session")
    
    return is_running


if __name__ == "__main__":
    main()
