"""
Simplified training script moved to src/training/train.py

This file is kept for backward compatibility.
Please use the modular training system in src/training/
"""

import sys
from pathlib import Path

# Add proper import path
sys.path.append(str(Path(__file__).parent))

try:
    from training.train import main
    
    if __name__ == "__main__":
        print("Note: This script has been moved to src/training/train.py")
        print("Using the new modular training system...")
        main()
        
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure all dependencies are installed:")
    print("  pip install -r requirements.txt")
    print("")
    print("Or run the training script directly:")
    print("  python src/training/train.py")