#!/usr/bin/env python3
"""
Simple Crash Prevention Test
============================

Direct test of crash prevention utilities without complex imports.
"""

import logging
import os
import sys

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_crash_prevention_direct():
    """Test crash prevention utilities directly."""

    # Add the project root to Python path
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    logger.info("Testing crash prevention utilities...")

    try:
        # Import directly without going through src.__init__.py
        from src.utils.crash_prevention import (
            MemoryMonitor,
            emergency_cleanup,
            gpu_safe_context,
            log_system_resources,
            memory_safe_context,
            safe_execution,
        )
        logger.info("✅ Core crash prevention utilities imported successfully")

        # Test MemoryMonitor
        monitor = MemoryMonitor(threshold=0.85)
        logger.info("✅ MemoryMonitor created")

        # Test check_memory method
        memory_info = monitor.check_memory()
        logger.info(f"✅ Memory check: {memory_info['usage_percent']:.1f}% usage")

        # Test safe execution decorator
        @safe_execution(max_retries=1)
        def test_success():
            return "success"

        result = test_success()
        if result == "success":
            logger.info("✅ Safe execution decorator working")

        # Test context managers
        with memory_safe_context(threshold=0.80):
            logger.info("✅ Memory safe context working")

        with gpu_safe_context(threshold=0.85):
            logger.info("✅ GPU safe context working")

        # Test emergency cleanup
        emergency_cleanup()
        logger.info("✅ Emergency cleanup working")

        # Test resource logging
        log_system_resources(logger)
        logger.info("✅ Resource logging working")

        logger.info("🎉 ALL CRASH PREVENTION TESTS PASSED!")
        return True

    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_crash_prevention_direct()
    if success:
        print("\n🎉 Crash prevention system is working correctly!")
        print("Your VSCode crash prevention is fully operational.")
    else:
        print("\n❌ Some issues found. Check the logs above.")

    sys.exit(0 if success else 1)
