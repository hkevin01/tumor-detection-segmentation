#!/usr/bin/env python3
"""
Test runner script for the tumor detection and segmentation project.

This script provides convenient ways to run different types of tests
based on the markers and categories available in the project.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> tuple[int, str]:
    """Run a command and return the exit code and output."""
    print(f"\n🧪 {description}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode, result.stdout
    except Exception as e:
        print(f"Error running command: {e}")
        return 1, str(e)


def main():
    """Main test runner function."""
    print("🔬 Tumor Detection & Segmentation Test Runner")
    print("=" * 60)

    # Define test commands
    test_commands = {
        "1": {
            "cmd": ["python", "-m", "pytest", "--collect-only", "-q"],
            "desc": "Show all available tests (collection only)"
        },
        "2": {
            "cmd": ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
            "desc": "Run all tests with verbose output"
        },
        "3": {
            "cmd": ["python", "-m", "pytest", "-m", "unit", "-v"],
            "desc": "Run only unit tests"
        },
        "4": {
            "cmd": ["python", "-m", "pytest", "-m", "cpu", "-v"],
            "desc": "Run only CPU tests (no GPU required)"
        },
        "5": {
            "cmd": ["python", "-m", "pytest", "-m", "integration", "-v"],
            "desc": "Run only integration tests"
        },
        "6": {
            "cmd": ["python", "-m", "pytest", "-m", "not slow", "-v"],
            "desc": "Run fast tests (exclude slow tests)"
        },
        "7": {
            "cmd": ["python", "-m", "pytest", "-m", "cpu and not slow", "-v"],
            "desc": "Run fast CPU tests"
        },
        "8": {
            "cmd": ["python", "-m", "pytest", "--markers"],
            "desc": "Show all available test markers"
        },
        "9": {
            "cmd": ["python", "-m", "pytest", "tests/unit/", "-v"],
            "desc": "Run tests in unit directory"
        },
        "10": {
            "cmd": ["python", "-m", "pytest", "tests/integration/", "-v"],
            "desc": "Run tests in integration directory"
        }
    }

    if len(sys.argv) > 1:
        # Run specific test command
        choice = sys.argv[1]
        if choice in test_commands:
            cmd_info = test_commands[choice]
            run_command(cmd_info["cmd"], cmd_info["desc"])
        else:
            print(f"❌ Invalid choice: {choice}")
            print("Available options:")
            for key, value in test_commands.items():
                print(f"  {key}: {value['desc']}")
    else:
        # Interactive mode
        print("\nAvailable test options:")
        for key, value in test_commands.items():
            print(f"  {key}: {value['desc']}")

        print("\nExamples:")
        print("  python run_tests.py 1  # Show all tests")
        print("  python run_tests.py 3  # Run unit tests")
        print("  python run_tests.py 7  # Run fast CPU tests")

        choice = input("\nEnter your choice (1-10): ").strip()

        if choice in test_commands:
            cmd_info = test_commands[choice]
            returncode, output = run_command(cmd_info["cmd"], cmd_info["desc"])

            if returncode == 0:
                print("\n✅ Tests completed successfully!")
            else:
                print(f"\n❌ Tests failed with exit code: {returncode}")
        else:
            print(f"❌ Invalid choice: {choice}")


if __name__ == "__main__":
    main()
