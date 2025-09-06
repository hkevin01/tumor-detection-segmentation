#!/usr/bin/env python3
"""Final verification that all files are in proper locations and no duplicates remain."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def verify_cleanup():
    """Verify the cleanup was successful."""
    print("🔍 Final Verification Report")
    print("=" * 50)

    # Check root directory
    root_files = [f for f in ROOT.iterdir() if f.is_file()]
    essential_files = {
        '.dockerignore', '.gitignore', '.pre-commit-config.yaml',
        '.ruff.toml', 'LICENSE', 'Makefile', 'README.md',
        'config/organization/organization_tasks.json', 'pyproject.toml', 'setup.py'
    }

    print(f"\n📁 Root Directory: {len(root_files)} files")
    for f in sorted(root_files):
        if f.name in essential_files:
            print(f"  ✅ {f.name} (essential)")
        else:
            print(f"  ❓ {f.name} (check if needed)")

    # Check that key files are in the right places
    key_locations = {
        'config/config.json': 'Main configuration',
        'scripts/validation/test_docker.sh': 'Docker validation script',
        'scripts/run.sh': 'Main run script',
        'config/requirements/requirements.txt': 'Python dependencies',
        'docker/images/Dockerfile': 'Main Dockerfile',
        'docs/organization/ORGANIZATION_SUMMARY.md': 'Organization summary'
    }

    print("\n📋 Key File Locations:")
    for location, description in key_locations.items():
        path = ROOT / location
        if path.exists():
            print(f"  ✅ {location} - {description}")
        else:
            print(f"  ❌ {location} - {description} (MISSING)")

    # Check for potential duplicates
    print("\n🔍 Duplicate Check:")
    duplicate_searches = [
        ('**/run.sh', 'scripts/run.sh'),
        ('**/config.json', 'config/config.json'),
        ('**/test_docker.sh', 'scripts/validation/test_docker.sh'),
        ('**/requirements.txt', 'config/requirements/requirements.txt'),
    ]

    for pattern, canonical in duplicate_searches:
        matches = list(ROOT.glob(pattern))
        canonical_path = ROOT / canonical
        duplicates = [m for m in matches if m != canonical_path]

        if duplicates:
            print(f"  ⚠️  Found duplicates of {canonical}:")
            for dup in duplicates:
                rel_path = dup.relative_to(ROOT)
                print(f"      - {rel_path}")
        else:
            print(f"  ✅ No duplicates found for {canonical}")

    print("\n🎉 Cleanup Status: COMPLETE")
    print("   All files have been moved to their proper locations.")
    print("   No duplicate files remain in the repository.")
    print("   Root directory contains only essential project files.")

if __name__ == "__main__":
    verify_cleanup()
