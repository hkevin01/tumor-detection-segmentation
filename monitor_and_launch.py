#!/usr/bin/env python3
"""
Monitor training progress and launch expanded sessions.
"""

import subprocess
import sys
import time
from pathlib import Path


def check_smoke_test_status():
    """Check if the smoke test is still running."""
    try:
        # Check for running python processes with train_enhanced.py
        result = subprocess.run(
            ["pgrep", "-f", "train_enhanced.py"],
            capture_output=True,
            text=True
        )
        return len(result.stdout.strip()) > 0
    except Exception:
        return False

def monitor_and_launch():
    """Monitor smoke test and launch expanded training when ready."""

    print("🔍 Monitoring smoke test progress...")
    print("Waiting for 1-epoch smoke test to complete before launching expanded training...")

    # Wait for smoke test to complete
    while check_smoke_test_status():
        print("⏳ Smoke test still running... waiting 30 seconds")
        time.sleep(30)

    print("✅ Smoke test completed! Launching expanded training sessions...")

    # Launch expanded training
    project_root = Path(__file__).parent
    launcher_script = project_root / "launch_expanded_training.py"

    if launcher_script.exists():
        print("🚀 Starting expanded training sequence...")
        subprocess.run([sys.executable, str(launcher_script)])
    else:
        print("❌ Training launcher not found!")

if __name__ == "__main__":
    monitor_and_launch()
