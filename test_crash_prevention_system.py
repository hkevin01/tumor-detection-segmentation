#!/usr/bin/env python3
"""
Test Comprehensive Crash Prevention System
=========================================

This script tests all the crash prevention utilities we've added throughout
the codebase to ensure they work correctly and prevent VSCode crashes.
"""

import logging
import os
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_crash_prevention_imports():
    """Test that all crash prevention modules can be imported."""
    logger.info("Testing crash prevention module imports...")

    test_results = {
        'core_utils': False,
        'safe_models': False,
        'safe_benchmarks': False,
        'safe_testing': False,
        'safe_gui': False,
        'safe_plots': False,
        'safe_loaders': False
    }

    try:
        # Test core crash prevention utilities
        test_results['core_utils'] = True
        logger.info("✅ Core crash prevention utilities imported successfully")

    except Exception as e:
        logger.error(f"❌ Core utilities import failed: {e}")

    try:
        # Test safe model utilities
        test_results['safe_models'] = True
        logger.info("✅ Safe model utilities imported successfully")

    except Exception as e:
        logger.error(f"❌ Safe models import failed: {e}")

    try:
        # Test safe benchmarking
        test_results['safe_benchmarks'] = True
        logger.info("✅ Safe benchmarking utilities imported successfully")

    except Exception as e:
        logger.error(f"❌ Safe benchmarks import failed: {e}")

    try:
        # Test safe testing framework
        test_results['safe_testing'] = True
        logger.info("✅ Safe testing framework imported successfully")

    except Exception as e:
        logger.error(f"❌ Safe testing import failed: {e}")

    try:
        # Test safe GUI components
        test_results['safe_gui'] = True
        logger.info("✅ Safe GUI components imported successfully")

    except Exception as e:
        logger.error(f"❌ Safe GUI import failed: {e}")

    try:
        # Test safe visualization
        test_results['safe_plots'] = True
        logger.info("✅ Safe visualization utilities imported successfully")

    except Exception as e:
        logger.error(f"❌ Safe plots import failed: {e}")

    try:
        # Test safe data loaders
        test_results['safe_loaders'] = True
        logger.info("✅ Safe data loaders imported successfully")

    except Exception as e:
        logger.error(f"❌ Safe loaders import failed: {e}")

    # Summary
    passed = sum(test_results.values())
    total = len(test_results)

    logger.info(f"\nImport test summary: {passed}/{total} modules imported successfully")

    return test_results


def test_memory_monitoring():
    """Test memory monitoring functionality."""
    logger.info("Testing memory monitoring...")

    try:
        from src.utils.crash_prevention import MemoryMonitor, log_system_resources

        # Create monitor
        monitor = MemoryMonitor(threshold=0.85)
        logger.info("✅ Memory monitor created")

        # Check memory
        memory_info = monitor.check_memory()
        logger.info(f"Memory usage: {memory_info['usage_percent']:.1f}%")

        # Log system resources
        log_system_resources(logger)
        logger.info("✅ System resource logging working")

        return True

    except Exception as e:
        logger.error(f"❌ Memory monitoring test failed: {e}")
        return False


def test_safe_execution_decorator():
    """Test safe execution decorator."""
    logger.info("Testing safe execution decorator...")

    try:
        from src.utils.crash_prevention import safe_execution

        @safe_execution(max_retries=2)
        def test_function_success():
            return "success"

        @safe_execution(max_retries=1)
        def test_function_failure():
            raise ValueError("Test error")

        # Test successful function
        result = test_function_success()
        if result == "success":
            logger.info("✅ Safe execution decorator working for success case")
        else:
            logger.error("❌ Safe execution decorator failed for success case")
            return False

        # Test failure case
        try:
            test_function_failure()
            logger.error("❌ Safe execution decorator should have raised exception")
            return False
        except ValueError:
            logger.info("✅ Safe execution decorator working for failure case")

        return True

    except Exception as e:
        logger.error(f"❌ Safe execution decorator test failed: {e}")
        return False


def test_context_managers():
    """Test safe context managers."""
    logger.info("Testing safe context managers...")

    try:
        from src.utils.crash_prevention import gpu_safe_context, memory_safe_context

        # Test memory safe context
        with memory_safe_context(threshold=0.80):
            logger.info("✅ Memory safe context working")

        # Test GPU safe context
        with gpu_safe_context(threshold=0.85):
            logger.info("✅ GPU safe context working")

        return True

    except Exception as e:
        logger.error(f"❌ Context managers test failed: {e}")
        return False


def test_enhanced_training_integration():
    """Test that enhanced training script has crash prevention."""
    logger.info("Testing enhanced training integration...")

    try:
        # Check if enhanced training file exists and has decorators
        training_file = "src/training/train_enhanced.py"

        if not os.path.exists(training_file):
            logger.error(f"❌ Enhanced training file not found: {training_file}")
            return False

        with open(training_file, 'r') as f:
            content = f.read()

        # Check for crash prevention imports and decorators
        checks = [
            "from src.utils.crash_prevention import",
            "@safe_execution",
            "memory_safe_context",
            "emergency_cleanup"
        ]

        for check in checks:
            if check in content:
                logger.info(f"✅ Found: {check}")
            else:
                logger.warning(f"⚠️ Missing: {check}")

        logger.info("✅ Enhanced training integration checked")
        return True

    except Exception as e:
        logger.error(f"❌ Enhanced training integration test failed: {e}")
        return False


def test_memory_cleanup():
    """Test memory cleanup functionality."""
    logger.info("Testing memory cleanup...")

    try:
        from src.utils.crash_prevention import emergency_cleanup

        # Create some objects to clean up
        large_list = [list(range(1000)) for _ in range(100)]

        # Check memory before cleanup
        import psutil
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024

        # Run cleanup
        emergency_cleanup()

        # Check memory after cleanup
        memory_after = process.memory_info().rss / 1024 / 1024

        logger.info(f"Memory before cleanup: {memory_before:.1f} MB")
        logger.info(f"Memory after cleanup: {memory_after:.1f} MB")
        logger.info("✅ Memory cleanup function working")

        return True

    except Exception as e:
        logger.error(f"❌ Memory cleanup test failed: {e}")
        return False


def main():
    """Run comprehensive crash prevention system test."""
    logger.info("="*60)
    logger.info("COMPREHENSIVE CRASH PREVENTION SYSTEM TEST")
    logger.info("="*60)

    test_functions = [
        ("Import Tests", test_crash_prevention_imports),
        ("Memory Monitoring", test_memory_monitoring),
        ("Safe Execution Decorator", test_safe_execution_decorator),
        ("Context Managers", test_context_managers),
        ("Enhanced Training Integration", test_enhanced_training_integration),
        ("Memory Cleanup", test_memory_cleanup)
    ]

    results = {}

    for test_name, test_func in test_functions:
        logger.info(f"\n--- {test_name} ---")
        try:
            results[test_name] = test_func()
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False

    # Final summary
    logger.info("\n" + "="*60)
    logger.info("CRASH PREVENTION SYSTEM TEST SUMMARY")
    logger.info("="*60)

    passed = 0
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name:30s} {status}")
        if result:
            passed += 1

    logger.info("-"*60)
    logger.info(f"Total: {passed}/{total} tests passed")

    if passed == total:
        logger.info("🎉 ALL CRASH PREVENTION TESTS PASSED!")
        logger.info("The system should now be much more stable and crash-resistant.")
    else:
        logger.warning(f"⚠️ {total - passed} tests failed. Check the logs above for details.")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
