#!/usr/bin/env python3
"""Remove remaining duplicates in nested directories."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def clean_nested_duplicates():
    """Remove duplicates in nested project directories."""
    print("Cleaning nested duplicates...")

    # Remove duplicates in notebooks/tumor-detection-segmentation/
    nested_dir = ROOT / "notebooks" / "tumor-detection-segmentation"
    if nested_dir.exists():
        duplicates = [
            nested_dir / "config.json",
            nested_dir / "requirements.txt"
        ]

        for dup in duplicates:
            if dup.exists():
                print(f"REMOVE: {dup.relative_to(ROOT)}")
                dup.unlink()
            else:
                print(f"SKIP: {dup.relative_to(ROOT)} (not found)")

    print("Nested cleanup complete!")

if __name__ == "__main__":
    clean_nested_duplicates()
