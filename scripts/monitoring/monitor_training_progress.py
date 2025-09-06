#!/usr/bin/env python3
"""Training Progress Monitor"""
import time
import json
from pathlib import Path

def monitor_training():
    """Monitor training progress"""
    print("📊 Training Progress Monitor")
    print("=" * 40)
    
    # Check for MLflow runs
    mlflow_dir = Path("mlruns")
    if mlflow_dir.exists():
        print("✅ MLflow tracking active")
    else:
        print("⚠️ MLflow not found")
    
    # Check for model checkpoints
    models_dir = Path("models")
    if models_dir.exists():
        checkpoints = list(models_dir.rglob("*.pt"))
        print(f"📁 Found {len(checkpoints)} model checkpoints")
    else:
        print("📁 No model checkpoints found")
    
    print("🔄 Use Ctrl+C to stop monitoring")

if __name__ == "__main__":
    monitor_training()
