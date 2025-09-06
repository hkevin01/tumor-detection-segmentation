#!/usr/bin/env python3
"""Training Status Summary"""
from pathlib import Path
import json

def training_status():
    """Get training status summary"""
    print("📈 Training Status Summary")
    print("=" * 40)
    
    # Check outputs
    output_dirs = [
        "outputs/training",
        "reports/inference_exports",
        "logs/training"
    ]
    
    for output_dir in output_dirs:
        path = Path(output_dir)
        if path.exists():
            files = list(path.rglob("*"))
            print(f"📁 {output_dir}: {len(files)} files")
        else:
            print(f"📁 {output_dir}: not found")

if __name__ == "__main__":
    training_status()
