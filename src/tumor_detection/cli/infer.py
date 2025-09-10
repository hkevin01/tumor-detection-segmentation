"""
Inference CLI wrapper for tumor detection package.

This module provides the command-line interface for running inference
on trained models.
"""

import sys
from pathlib import Path


def main():
    """Main entry point for inference CLI."""
    # Add the project root to sys.path to access existing inference scripts
    project_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(project_root))

    # Import and run the existing inference script
    from src.inference.inference import main as inference_main
    inference_main()


if __name__ == "__main__":
    main()
