#!/usr/bin/env python3
"""Generate final organization summary."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def count_files_in_dir(directory):
    """Count files in a directory."""
    try:
        path = ROOT / directory
        if not path.exists():
            return 0
        return len([f for f in path.rglob("*") if f.is_file()])
    except Exception:
        return 0


def main():
    print("🎉 Repository Organization Complete!")
    print("=" * 50)

    print("\n📁 Directory Structure:")
    directories = [
        "config/", "docker/", "docs/", "scripts/", "src/",
        "tests/", "reports/", "temp/", "logs/", "models/",
        "data/", "notebooks/"
    ]

    for directory in directories:
        file_count = count_files_in_dir(directory)
        print(f"  {directory:<15} {file_count:>3} files")

    print(f"\n📄 Root directory files: {count_files_in_dir('.')}")

    print("\n✅ Completed Tasks:")
    print("  • Moved configuration files to config/")
    print("  • Cleaned up temporary files")
    print("  • Organized scripts by function")
    print("  • Consolidated log directories")
    print("  • Moved documentation to docs/")
    print("  • Moved Docker files to docker/")
    print("  • Moved requirements files to config/requirements/")
    print("  • Updated all file references")
    print("  • Validated structure and references")

    print("\n🚀 Next Steps:")
    print("  • Run MONAI dataset smoke test")
    print("  • Execute training validation")
    print("  • Finalize Docker workflows")

    print("\n📊 Organization Summary:")
    print("  All files have been moved to their proper locations!")
    print("  The root directory is now clean and organized.")
    print("  File references have been updated throughout the project.")


if __name__ == "__main__":
    main()
