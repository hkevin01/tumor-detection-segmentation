#!/usr/bin/env python3
"""
Launch expanded training sessions in sequence.
"""

import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Launch all training sessions in sequence."""

    print("🚀 Starting Expanded Training Session Launcher")
    print("=" * 60)

    try:
        from scripts.training.expanded_training_launcher import ExpandedTrainingLauncher

        # Create launcher instance
        launcher = ExpandedTrainingLauncher(project_root=str(project_root))

        print("Available Training Configurations:")
        configs = launcher.get_training_configurations()

        for i, config in enumerate(configs, 1):
            print(f"  {i}. {config['name']} ({config['epochs']} epochs)")
            print(f"     {config['description']}")

        print("\n" + "=" * 60)
        print("🎯 Starting Training Session Sequence...")

        # Run all sessions in order
        successful_sessions = 0
        total_sessions = len(configs)

        for i, config in enumerate(configs, 1):
            print(f"\n📊 SESSION {i}/{total_sessions}: {config['name']}")
            print("-" * 40)

            start_time = time.time()
            success = launcher.run_training_session(config, dry_run=False)
            end_time = time.time()

            elapsed = end_time - start_time
            elapsed_min = elapsed / 60

            if success:
                successful_sessions += 1
                print(f"✅ Session completed successfully in {elapsed_min:.1f} minutes")
            else:
                print(f"❌ Session failed after {elapsed_min:.1f} minutes")
                print("Stopping training sequence due to failure.")
                break

        print("\n" + "=" * 60)
        print("📈 TRAINING SEQUENCE SUMMARY")
        print(f"Sessions completed: {successful_sessions}/{total_sessions}")

        if successful_sessions == total_sessions:
            print("🎉 ALL TRAINING SESSIONS COMPLETED SUCCESSFULLY!")
        else:
            print(f"⚠️  Sequence stopped at session {successful_sessions + 1}")

        return successful_sessions == total_sessions

    except KeyboardInterrupt:
        print("\n⏹️  Training sequence interrupted by user")
        return False
    except Exception as e:
        print(f"❌ Training sequence failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
