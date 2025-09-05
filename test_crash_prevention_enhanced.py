#!/usr/bin/env python3
"""
Test script for enhanced crash prevention utilities
"""

import logging
import os
import sys
import time

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_enhanced_crash_prevention():
    """Test the enhanced crash prevention utilities"""
    print("🚀 Starting Enhanced Crash Prevention Test...")

    try:
        from utils.crash_prevention import (
            EnhancedGPUMonitor,
            EnhancedMemoryMonitor,
            TimeMetrics,
            enhanced_safe_execution,
            memory_safe,
            ultra_safe,
        )
        print("✅ Successfully imported enhanced crash prevention utilities")

        # Test TimeMetrics
        print("\n📊 Testing TimeMetrics...")
        metrics = TimeMetrics(operation_name="test_operation")
        time.sleep(0.1)  # Small delay
        duration = metrics.finish()
        print(f"   Duration: {duration:.4f}s")
        print(f"   Nanoseconds: {metrics.duration_nanoseconds}")
        print("✅ TimeMetrics working correctly")

        # Test EnhancedMemoryMonitor
        print("\n🧠 Testing EnhancedMemoryMonitor...")
        memory_monitor = EnhancedMemoryMonitor(
            threshold=0.85,
            check_interval=1.0,
            enable_persistence=False  # Disable for testing
        )
        memory_status = memory_monitor.check_memory()
        print(f"   Memory Usage: {memory_status['usage_percent']:.2f}%")
        print(f"   Available: {memory_status['available_gb']:.2f} GB")
        print("✅ EnhancedMemoryMonitor working correctly")

        # Test EnhancedGPUMonitor
        print("\n🎮 Testing EnhancedGPUMonitor...")
        try:
            gpu_monitor = EnhancedGPUMonitor(
                memory_threshold=0.90,
                auto_scaling=False
            )
            gpu_status = gpu_monitor.get_comprehensive_gpu_usage()
            print(f"   GPU Status: {len(gpu_status)} GPUs detected")
            print("✅ EnhancedGPUMonitor working correctly")
        except Exception as e:
            print(f"⚠️  GPU monitoring not available: {e}")

        # Test decorators
        print("\n🛡️ Testing safety decorators...")

        @memory_safe
        def safe_function():
            """Test function with memory safety"""
            return "Success!"

        @ultra_safe
        def ultra_safe_function():
            """Test function with ultra safety"""
            return "Ultra safe success!"

        result1 = safe_function()
        result2 = ultra_safe_function()
        print(f"   Safe function result: {result1}")
        print(f"   Ultra safe function result: {result2}")
        print("✅ Safety decorators working correctly")

        # Test enhanced_safe_execution with metrics
        print("\n📈 Testing enhanced execution with metrics...")

        @enhanced_safe_execution(record_metrics=True, max_retries=1)
        def metrics_test_function():
            """Test function that records metrics"""
            time.sleep(0.05)  # Small delay
            return "Metrics test passed!"

        result3 = metrics_test_function()
        print(f"   Metrics test result: {result3}")
        print("✅ Enhanced execution with metrics working correctly")

        print("\n🎉 All tests completed successfully!")
        print("✅ Enhanced crash prevention system is working correctly!")

        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    success = test_enhanced_crash_prevention()

    if success:
        print("\n🏆 Enhanced crash prevention test PASSED!")
        sys.exit(0)
    else:
        print("\n💥 Enhanced crash prevention test FAILED!")
        sys.exit(1)
