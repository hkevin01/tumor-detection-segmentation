#!/usr/bin/env python3
"""Final cleanup: move remaining root files to proper locations."""

import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Remaining files to move
REMAINING_MOVES = {
    # Documentation files still in root
    "CONTRIBUTING.md": "docs/",
    "DEPLOYMENT.md": "docs/deployment/",
    "IMPLEMENTATION_COMPLETE.md": "docs/",
    "VERIFICATION_STATUS.md": "docs/verification/",
    "VERIFICATION_SUCCESS.md": "docs/verification/",

    # Shell scripts still in root
    "cleanup_root.sh": "scripts/cleanup/",
    "cleanup_root_organized.sh": "scripts/cleanup/",
    "commands.sh": "scripts/utilities/",
    "demo_complete_workflow.sh": "scripts/demo/",
    "demo_enhanced_workflow.sh": "scripts/demo/",
    "run.sh": "scripts/",
    "setup_fixed.sh": "scripts/setup/",
    "test_docker.sh": "scripts/validation/",
    "verify_monai_venv.sh": "scripts/validation/",

    # Python files still in root
    "run_tests.py": "scripts/testing/",
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
    "verify_monai_checklist.py": "scripts/validation/",

    # Docker files still in root
    "Dockerfile": "docker/images/",
    "Dockerfile.cuda": "docker/images/",
    "Dockerfile.phase4": "docker/images/",
    "Dockerfile.simple": "docker/images/",
    "docker-compose.cpu.yml": "docker/compose/",
    "docker-compose.phase4.yml": "docker/compose/",
    "docker-compose.yml": "docker/compose/",
}


def force_move_file(src, dst_dir):
    """Force move file, replacing if exists."""
    src_path = ROOT / src
    if not src_path.exists():
        print(f"SKIP: {src} (not found)")
        return

    dst_path = ROOT / dst_dir
    os.makedirs(dst_path, exist_ok=True)

    final_path = dst_path / src
    if final_path.exists():
        print(f"REPLACE: {src} -> {dst_dir}")
        final_path.unlink()
    else:
        print(f"MOVE: {src} -> {dst_dir}")

    shutil.move(str(src_path), str(final_path))


def main():
    print("Force moving remaining files from root...")

    for src_file, dst_dir in REMAINING_MOVES.items():
        force_move_file(src_file, dst_dir)

    print("Force cleanup complete!")


if __name__ == "__main__":
    main()
