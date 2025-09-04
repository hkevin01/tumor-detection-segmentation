#!/usr/bin/env python3
"""
Test script for the expanded training launcher.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_training_launcher():
    """Test the expanded training launcher with dry run."""

    print("Testing Expanded Training Launcher...")
    print("=" * 50)

    try:
        # Import the launcher
        from scripts.training.expanded_training_launcher import ExpandedTrainingLauncher

        # Create launcher instance
        launcher = ExpandedTrainingLauncher(project_root=str(project_root))

        # Get configurations
        configs = launcher.get_training_configurations()
        print(f"Found {len(configs)} training configurations:")

        for i, config in enumerate(configs, 1):
            print(f"  {i}. {config['name']} - {config['epochs']} epochs")
            print(f"     Description: {config['description']}")

        print("\n" + "=" * 50)
        print("Testing command generation (dry run)...")

        # Test command generation for first config
        if configs:
            test_config = configs[0]
            print(f"\nTesting configuration: {test_config['name']}")

            # Generate command
            cmd = launcher.build_training_command(test_config)
            print("Generated command:")
            print(f"  {cmd}")

            # Test dry run
            print("\nRunning dry run test...")
            success = launcher.run_training_session(test_config, dry_run=True)

            if success:
                print("✅ Dry run test PASSED!")
            else:
                print("❌ Dry run test FAILED!")
                return False

        print("\n" + "=" * 50)
        print("✅ ALL TESTS PASSED!")
        print("The training launcher is ready for use.")
        return True

    except Exception as e:
        print(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_training_launcher()
    sys.exit(0 if success else 1)
