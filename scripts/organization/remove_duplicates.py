#!/usr/bin/env python3
"""Remove duplicate files that were left behind during organization."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Define duplicates to remove (keeping the canonical version)
DUPLICATES_TO_REMOVE = [
    # Keep scripts/validation/test_docker.sh, remove others
    "scripts/test_docker.sh",
    "scripts/docker/test_docker.sh",
    "tests/docker/test_docker.sh",

    # Other potential duplicates found during file search
]


def remove_duplicate(file_path):
    """Remove a duplicate file if it exists."""
    full_path = ROOT / file_path
    if full_path.exists():
        print(f"REMOVE: {file_path}")
        full_path.unlink()
    else:
        print(f"SKIP: {file_path} (not found)")


def main():
    """Remove duplicate files."""
    print("Removing duplicate files...")

    # First, let's scan for potential duplicates
    duplicate_patterns = [
        "scripts/test_docker.sh",
        "scripts/docker/test_docker.sh",
        "tests/docker/test_docker.sh"
    ]

    canonical_validation = ROOT / "scripts/validation/test_docker.sh"

    print("Canonical file: scripts/validation/test_docker.sh")
    print(f"Canonical exists: {canonical_validation.exists()}")

    for duplicate in duplicate_patterns:
        dup_path = ROOT / duplicate
        if dup_path.exists():
            # Check if it's the same as canonical or empty
            if dup_path.stat().st_size == 0:
                print(f"REMOVE empty duplicate: {duplicate}")
                dup_path.unlink()
            else:
                print(f"WARN: Non-empty duplicate found: {duplicate}")
                # Don't auto-remove non-empty files
        else:
            print(f"SKIP: {duplicate} (not found)")

    print("Duplicate cleanup complete!")


if __name__ == "__main__":
    main()
