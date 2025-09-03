#!/usr/bin/env python3
"""Move files from root directory to proper subfolders."""

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Define target directories and ensure they exist
MOVES = {
    # Python files to scripts/
    "debug_datalist.py": "scripts/debug/",
    "diagnose_tests.py": "scripts/debug/",
    "reorganization_summary.py": "scripts/organization/",
    "run_tests.py": "scripts/testing/",
    "task_manager.py": "scripts/organization/",
    "test_enhanced_inference.py": "scripts/testing/",
    "test_imports.py": "scripts/testing/",
    "test_imports_quick.py": "scripts/testing/",
    "test_monai_imports.py": "scripts/testing/",
    "test_overlay_quality.py": "scripts/testing/",
    "test_overlay_system.py": "scripts/testing/",
    "test_system.py": "scripts/testing/",
    "test_viz_system.py": "scripts/testing/",
    "test_warnings.py": "scripts/testing/",
    "validate_docker.py": "scripts/validation/",
    "validate_monai_integration.py": "scripts/validation/",
    "validate_prompt_pack.py": "scripts/validation/",
    "validate_test_structure.py": "scripts/validation/",
    "verify_monai_checklist.py": "scripts/validation/",

    # Shell scripts to scripts/
    "cleanup_root.sh": "scripts/cleanup/",
    "cleanup_root_organized.sh": "scripts/cleanup/",
    "commands.sh": "scripts/utilities/",
    "demo_complete_workflow.sh": "scripts/demo/",
    "demo_enhanced_workflow.sh": "scripts/demo/",
    "docker-entrypoint.sh": "docker/scripts/",
    "docker-manager.sh": "docker/scripts/",
    "move_files.sh": "scripts/organization/",
    "organize_files.sh": "scripts/organization/",
    "organize_root.sh": "scripts/organization/",
    "run.sh": "scripts/",
    "scripts.sh": "scripts/utilities/",
    "setup_fixed.sh": "scripts/setup/",
    "test_docker.sh": "scripts/validation/",
    "verify_monai_venv.sh": "scripts/validation/",

    # Documentation files to docs/
    "CONTRIBUTING.md": "docs/",
    "DEPLOYMENT.md": "docs/deployment/",
    "DOCKER_COMPLETE.md": "docs/docker/",
    "DOCKER_GUIDE.md": "docs/docker/",
    "DOCKER_SETUP.md": "docs/docker/",
    "ENHANCED_TRAINING_SUMMARY.md": "docs/training/",
    "IMPLEMENTATION_COMPLETE.md": "docs/",
    "INSTALLATION_FIX.md": "docs/installation/",
    "MONAI_IMPLEMENTATION_STATUS.md": "docs/monai/",
    "MONAI_TESTS_COMPLETE.md": "docs/monai/",
    "ORGANIZATION_SUMMARY.md": "docs/organization/",
    "PHASE_3_SUMMARY.md": "docs/phases/",
    "ROOT_ORGANIZATION_COMPLETE.md": "docs/organization/",
    "SWIG_WARNING_SUPPRESSION.md": "docs/troubleshooting/",
    "TRANSITION_COMPLETE.md": "docs/phases/",
    "VERIFICATION_STATUS.md": "docs/verification/",
    "VERIFICATION_SUCCESS.md": "docs/verification/",

    # Config files to config/
    "config.json": "DELETE",  # Empty file, already have proper one in config/
    ".env.example": "DELETE",  # Empty file, already have proper one in config/
    "mypy.ini": "DELETE",     # Empty file, already have proper one in config/
    "pytest.ini": "DELETE",   # Empty file, already have proper one in config/

    # Docker files to docker/
    "Dockerfile": "docker/images/",
    "Dockerfile.cuda": "docker/images/",
    "Dockerfile.phase4": "docker/images/",
    "Dockerfile.simple": "docker/images/",
    "docker-compose.cpu.yml": "docker/compose/",
    "docker-compose.phase4.yml": "docker/compose/",
    "docker-compose.yml": "docker/compose/",

    # Requirements files to config/
    "requirements-dev.txt": "config/requirements/",
    "requirements-docker.txt": "config/requirements/",
    "requirements-fixed.txt": "config/requirements/",
    "requirements-integrations.txt": "config/requirements/",
    "requirements.txt": "config/requirements/",

    # Temp files to temp/ or DELETE
    "test.tmp": "DELETE",
    "test2.pyc": "DELETE",
    ".coverage": "reports/",
}


def ensure_dir_exists(dir_path):
    """Create directory if it doesn't exist."""
    os.makedirs(dir_path, exist_ok=True)


def move_file(src, dst_dir):
    """Move file to destination directory."""
    src_path = ROOT / src
    if not src_path.exists():
        print(f"SKIP: {src} (not found)")
        return

    if dst_dir == "DELETE":
        print(f"DELETE: {src}")
        src_path.unlink()
        return

    dst_path = ROOT / dst_dir
    ensure_dir_exists(dst_path)

    final_path = dst_path / src
    if final_path.exists():
        print(f"SKIP: {src} -> {dst_dir} (already exists)")
        return

    print(f"MOVE: {src} -> {dst_dir}")
    shutil.move(str(src_path), str(final_path))


def main():
    print("Moving files from root to proper subfolders...")

    for src_file, dst_dir in MOVES.items():
        move_file(src_file, dst_dir)

    # Also move test directories
    test_dirs = ["test_temp", "test_viz"]
    for test_dir in test_dirs:
        test_path = ROOT / test_dir
        if test_path.exists():
            print(f"MOVE: {test_dir}/ -> temp/")
            ensure_dir_exists(ROOT / "temp")
            shutil.move(str(test_path), str(ROOT / "temp" / test_dir))

    print("File organization complete!")


if __name__ == "__main__":
    main()
