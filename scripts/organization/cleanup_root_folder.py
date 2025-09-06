#!/usr/bin/env python3
"""
Root Folder Cleanup Script
=========================

Moves files from root folder to appropriate subfolders and ensures
all scripts and links continue to work properly.

Author: Tumor Detection Segmentation Team
Phase: Root Organization
"""

import logging
import os
import shutil
from pathlib import Path
from typing import Dict, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_file_moves() -> Dict[str, str]:
    """Define file moves from root to appropriate subfolders"""
    return {
        # Log files to logs/
        "logs/clinical/clinical_demo_20250905_234239.log": "logs/clinical/",
        "logs/clinical/clinical_integration.log": "logs/clinical/",
        "logs/clinical/clinical_operator_20250906_001225.log": "logs/clinical/",
        "logs/clinical/clinical_operator_20250906_001254.log": "logs/clinical/",
        "logs/clinical/clinical_operator_20250906_001312.log": "logs/clinical/",
        "logs/training/real_training_20250905_234413.log": "logs/training/",

        # Test scripts to tests/
        "tests/system/test_crash_prevention_enhanced.py": "tests/system/",
        "tests/system/test_crash_prevention_simple.py": "tests/system/",
        "tests/system/test_crash_prevention_system.py": "tests/system/",
        "tests/training/test_training_launcher.py": "tests/training/",
        "tests/training/simple_train_test.py": "tests/training/",

        # Script files to scripts/
        "scripts/training/launch_expanded_training.py": "scripts/training/",
        "scripts/monitoring/monitor_and_launch.py": "scripts/monitoring/",
        "scripts/organization/move_root_files.py": "scripts/organization/",

        # Shell scripts to scripts/
        "scripts/deployment/deploy_clinical_platform.sh": "scripts/deployment/",
        "scripts/clinical/run_clinical_operator.sh": "scripts/clinical/",

        # Documentation files to docs/
        "docs/status/CRASH_PREVENTION_COMPLETE.md": "docs/status/",
        "docs/status/CRASH_PREVENTION_COMPLETION_REPORT.md": "docs/status/",
        "docs/status/FINAL_TASK_COMPLETION.md": "docs/status/",
        "docs/status/IMMEDIATE_EXECUTION_PLAN.md": "docs/status/",

        # Configuration files to config/
        "config/organization/organization_tasks.json": "config/organization/",
        "config/requirements/requirements-dev.txt": "config/requirements/",
    }


def get_files_to_keep_in_root() -> List[str]:
    """Files that should remain in root folder"""
    return [
        ".dockerignore",
        ".env",
        ".gitignore",
        ".pre-commit-config.yaml",
        ".ruff.toml",
        "LICENSE",
        "Makefile",
        "README.md",
        "pyproject.toml",
        "requirements.txt",
        "run.sh",
        "setup.py"
    ]


def move_file_safely(src: Path, dest_dir: Path, filename: str):
    """Move file safely, creating destination directory if needed"""
    src_file = src / filename
    if not src_file.exists():
        logger.warning(f"⚠️ Source file not found: {src_file}")
        return False

    # Create destination directory
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / filename

    # Check if destination already exists
    if dest_file.exists():
        logger.warning(f"⚠️ Destination already exists: {dest_file}")
        return False

    # Move the file
    try:
        shutil.move(str(src_file), str(dest_file))
        logger.info(f"✅ Moved: {filename} → {dest_dir}")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to move {filename}: {e}")
        return False


def update_script_references(root_dir: Path, moves: Dict[str, str]):
    """Update references in scripts to moved files"""
    logger.info("🔄 Updating script references...")

    # Update references in scripts
    script_dirs = [
        root_dir / "scripts",
        root_dir / "tests",
        root_dir / "src"
    ]

    for script_dir in script_dirs:
        if not script_dir.exists():
            continue

        for script_file in script_dir.rglob("*.py"):
            try:
                with open(script_file, 'r') as f:
                    content = f.read()

                updated = False
                for old_path, new_dir in moves.items():
                    # Update direct file references
                    if old_path in content:
                        new_path = new_dir + old_path
                        content = content.replace(old_path, new_path)
                        updated = True

                if updated:
                    with open(script_file, 'w') as f:
                        f.write(content)
                    logger.info(f"🔄 Updated references in: {script_file}")

            except Exception as e:
                logger.warning(f"⚠️ Could not update {script_file}: {e}")


def cleanup_empty_directories(root_dir: Path):
    """Remove empty directories after moving files"""
    logger.info("🧹 Cleaning up empty directories...")

    for item in root_dir.iterdir():
        if item.is_dir() and item.name not in ['.git', '.venv', '.pytest_cache', '.mypy_cache', '__pycache__']:
            try:
                if not any(item.iterdir()):
                    item.rmdir()
                    logger.info(f"🗑️ Removed empty directory: {item.name}")
            except:
                pass  # Directory not empty or other issues


def main():
    logger.info("🧹 ROOT FOLDER CLEANUP")
    logger.info("=" * 50)

    root_dir = Path("/home/kevin/Projects/tumor-detection-segmentation")
    moves = get_file_moves()
    keep_files = get_files_to_keep_in_root()

    # Count files to move
    total_moves = 0
    successful_moves = 0

    logger.info("📁 Moving files to appropriate subfolders...")

    for filename, dest_subdir in moves.items():
        dest_dir = root_dir / dest_subdir
        if move_file_safely(root_dir, dest_dir, filename):
            successful_moves += 1
        total_moves += 1

    # Update script references
    update_script_references(root_dir, moves)

    # Clean up empty directories
    cleanup_empty_directories(root_dir)

    # Verify root folder only has essential files
    logger.info("🔍 Verifying root folder cleanup...")
    root_files = [f.name for f in root_dir.iterdir() if f.is_file()]
    unexpected_files = [f for f in root_files if f not in keep_files and not f.startswith('.')]

    if unexpected_files:
        logger.warning("⚠️ Unexpected files still in root:")
        for f in unexpected_files:
            logger.warning(f"   {f}")
    else:
        logger.info("✅ Root folder contains only essential files")

    # Final summary
    logger.info("=" * 50)
    logger.info("🏁 ROOT CLEANUP COMPLETE")
    logger.info("=" * 50)
    logger.info(f"📊 Files moved: {successful_moves}/{total_moves}")
    logger.info(f"📁 Root files remaining: {len(root_files)}")

    if successful_moves == total_moves:
        logger.info("🎉 All files moved successfully!")
    else:
        logger.warning(f"⚠️ {total_moves - successful_moves} files could not be moved")

    # Show current root structure
    logger.info("\n📂 Current root folder structure:")
    for item in sorted(root_dir.iterdir()):
        if item.is_file():
            logger.info(f"   📄 {item.name}")
        elif item.is_dir() and not item.name.startswith('.'):
            logger.info(f"   📁 {item.name}/")


if __name__ == "__main__":
    main()
