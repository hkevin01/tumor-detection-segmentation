#!/usr/bin/env python3
"""
Diagnostic script to understand pytest test selection issues.
"""

import subprocess
from pathlib import Path


def run_pytest_with_explanation(args: list[str], description: str) -> None:
    """Run pytest command and explain the results."""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"Command: python -m pytest {' '.join(args)}")
    print('='*60)

    try:
        result = subprocess.run(
            ["python", "-m", "pytest"] + args,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )

        print("STDOUT:")
        print(result.stdout)

        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)

        print(f"\nExit code: {result.returncode}")

        # Analyze the output
        if "deselected" in result.stdout and "0 selected" in result.stdout:
            print("\n❌ ISSUE DETECTED: Tests were deselected!")
            print("This usually means:")
            print("  - The marker selection didn't match any tests")
            print("  - Tests are being skipped due to missing dependencies")
            print("  - Configuration conflicts")

        elif "collected" in result.stdout:
            print("\n✅ Tests were successfully collected!")

    except Exception as e:
        print(f"Error: {e}")


def main():
    """Main diagnostic function."""
    print("🔬 Pytest Diagnostic Tool")
    print("This will help diagnose why tests are being deselected.")

    # Test different scenarios
    scenarios = [
        (["--collect-only", "-q"], "Collecting all tests"),
        (["-m", "cpu", "--collect-only", "-q"], "Collecting CPU tests"),
        (["-m", "unit", "--collect-only", "-q"], "Collecting unit tests"),
        (["-m", "integration", "--collect-only", "-q"], "Collecting integration tests"),
        (["-m", "nonexistent", "--collect-only", "-q"], "Testing nonexistent marker (should show deselection)"),
        (["--markers"], "Showing all available markers"),
        (["tests/", "--collect-only", "-q"], "Collecting from tests directory"),
    ]

    for args, description in scenarios:
        run_pytest_with_explanation(args, description)
        print("\n" + "─" * 60)


if __name__ == "__main__":
    main()
