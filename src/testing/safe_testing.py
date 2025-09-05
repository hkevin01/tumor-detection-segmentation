#!/usr/bin/env python3
"""
Enhanced Testing Framework with Crash Prevention
===============================================

This module provides crash-safe testing utilities for medical imaging
workflows with comprehensive error handling and resource management.

Features:
- Memory-safe test execution
- GPU-aware testing
- Automatic cleanup on failures
- Test isolation and recovery
- Resource monitoring during tests
"""

import gc
import logging
import traceback
from contextlib import contextmanager
from typing import Any, Callable, Dict, List

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False

try:
    from src.utils.crash_prevention import (
        emergency_cleanup,
        gpu_safe_context,
        log_system_resources,
        memory_safe_context,
        safe_execution,
    )
    CRASH_PREVENTION_AVAILABLE = True
except ImportError:
    CRASH_PREVENTION_AVAILABLE = False
    # Fallback implementations
    @contextmanager
    def memory_safe_context(*args, **kwargs):
        yield None
    @contextmanager
    def gpu_safe_context(*args, **kwargs):
        yield None
    def safe_execution(*args, **kwargs):
        def decorator(func):
            return func
        return decorator
    def emergency_cleanup():
        gc.collect()
    def log_system_resources(logger=None):
        pass

logger = logging.getLogger(__name__)


class SafeTestRunner:
    """Safe test runner with crash prevention and resource monitoring."""

    def __init__(self, cleanup_between_tests: bool = True):
        self.cleanup_between_tests = cleanup_between_tests
        self.test_results = []
        self.current_test = None

    @safe_execution(max_retries=1)
    def run_test_safe(
        self,
        test_func: Callable,
        test_name: str = None,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run a single test with crash prevention.

        Args:
            test_func: Test function to run
            test_name: Name for the test
            *args: Test function arguments
            **kwargs: Test function keyword arguments

        Returns:
            Test result dictionary
        """
        if test_name is None:
            test_name = getattr(test_func, '__name__', 'unknown_test')

        self.current_test = test_name

        result = {
            'test_name': test_name,
            'status': 'failed',
            'error': None,
            'traceback': None,
            'duration': 0.0,
            'memory_peak': None,
            'gpu_memory_peak': None
        }

        logger.info(f"Starting test: {test_name}")

        with memory_safe_context(threshold=0.75):
            with gpu_safe_context(threshold=0.80):
                try:
                    log_system_resources(logger)

                    import time
                    start_time = time.perf_counter()

                    # Run the test
                    test_func(*args, **kwargs)

                    end_time = time.perf_counter()
                    result['duration'] = end_time - start_time
                    result['status'] = 'passed'

                    logger.info(f"Test {test_name} PASSED in {result['duration']:.3f}s")

                except AssertionError as e:
                    result['error'] = str(e)
                    result['traceback'] = traceback.format_exc()
                    logger.error(f"Test {test_name} FAILED: {e}")

                except Exception as e:
                    result['error'] = str(e)
                    result['traceback'] = traceback.format_exc()

                    if "out of memory" in str(e).lower():
                        logger.error(f"Test {test_name} OOM: {e}")
                        emergency_cleanup()
                    else:
                        logger.error(f"Test {test_name} ERROR: {e}")

                finally:
                    if self.cleanup_between_tests:
                        self._cleanup_after_test()

                    log_system_resources(logger)

        self.test_results.append(result)
        return result

    def _cleanup_after_test(self):
        """Cleanup resources after test execution."""
        try:
            # Clear CUDA cache if available
            if TORCH_AVAILABLE and torch.cuda.is_available():
                torch.cuda.empty_cache()

            # Force garbage collection
            gc.collect()

            logger.debug("Test cleanup completed")

        except Exception as e:
            logger.warning(f"Test cleanup failed: {e}")

    def run_test_suite_safe(
        self,
        test_functions: List[Callable],
        suite_name: str = "test_suite"
    ) -> Dict[str, Any]:
        """
        Run a suite of tests with crash prevention.

        Args:
            test_functions: List of test functions
            suite_name: Name for the test suite

        Returns:
            Test suite results
        """
        logger.info(f"Starting test suite: {suite_name} ({len(test_functions)} tests)")

        suite_results = {
            'suite_name': suite_name,
            'total_tests': len(test_functions),
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'total_duration': 0.0,
            'test_results': []
        }

        start_time = time.perf_counter()

        for i, test_func in enumerate(test_functions):
            test_name = f"{suite_name}::{getattr(test_func, '__name__', f'test_{i}')}"

            try:
                result = self.run_test_safe(test_func, test_name)
                suite_results['test_results'].append(result)

                if result['status'] == 'passed':
                    suite_results['passed'] += 1
                else:
                    if 'AssertionError' in str(result.get('error', '')):
                        suite_results['failed'] += 1
                    else:
                        suite_results['errors'] += 1

            except Exception as e:
                logger.error(f"Failed to run test {test_name}: {e}")
                suite_results['errors'] += 1
                emergency_cleanup()

        end_time = time.perf_counter()
        suite_results['total_duration'] = end_time - start_time

        # Log summary
        logger.info(f"Test suite {suite_name} completed:")
        logger.info(f"  Total: {suite_results['total_tests']}")
        logger.info(f"  Passed: {suite_results['passed']}")
        logger.info(f"  Failed: {suite_results['failed']}")
        logger.info(f"  Errors: {suite_results['errors']}")
        logger.info(f"  Duration: {suite_results['total_duration']:.3f}s")

        return suite_results

    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all test results."""
        total_tests = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['status'] == 'passed')
        failed = total_tests - passed

        return {
            'total_tests': total_tests,
            'passed': passed,
            'failed': failed,
            'success_rate': passed / total_tests if total_tests > 0 else 0.0,
            'total_duration': sum(r['duration'] for r in self.test_results)
        }


@contextmanager
def safe_test_environment(
    test_name: str = "test",
    memory_threshold: float = 0.75,
    gpu_threshold: float = 0.80
):
    """
    Context manager for safe test environment with automatic cleanup.

    Args:
        test_name: Name for logging
        memory_threshold: Memory usage threshold
        gpu_threshold: GPU memory threshold
    """
    logger.info(f"Setting up safe test environment: {test_name}")

    with memory_safe_context(threshold=memory_threshold):
        with gpu_safe_context(threshold=gpu_threshold):
            try:
                log_system_resources(logger)
                yield

            except Exception as e:
                logger.error(f"Test environment {test_name} failed: {e}")
                emergency_cleanup()
                raise e

            finally:
                # Cleanup
                if TORCH_AVAILABLE and torch.cuda.is_available():
                    torch.cuda.empty_cache()
                gc.collect()

                logger.info(f"Test environment {test_name} cleaned up")
                log_system_resources(logger)


def safe_assert_shapes_equal(tensor1: Any, tensor2: Any, message: str = ""):
    """Safely assert tensor shapes are equal with detailed error info."""
    try:
        if hasattr(tensor1, 'shape') and hasattr(tensor2, 'shape'):
            shape1 = tuple(tensor1.shape)
            shape2 = tuple(tensor2.shape)

            if shape1 != shape2:
                error_msg = f"Shape mismatch: {shape1} != {shape2}"
                if message:
                    error_msg = f"{message}: {error_msg}"
                raise AssertionError(error_msg)

        else:
            raise AssertionError(f"Cannot compare shapes: {type(tensor1)} vs {type(tensor2)}")

    except Exception as e:
        emergency_cleanup()
        raise e


def safe_assert_tensor_close(
    tensor1: Any,
    tensor2: Any,
    rtol: float = 1e-5,
    atol: float = 1e-8,
    message: str = ""
):
    """Safely assert tensors are close with memory management."""
    try:
        if not TORCH_AVAILABLE:
            raise ImportError("PyTorch not available")

        if not (hasattr(tensor1, 'shape') and hasattr(tensor2, 'shape')):
            raise AssertionError("Inputs must be tensor-like objects")

        # Check shapes first
        safe_assert_shapes_equal(tensor1, tensor2, "Shape check before value comparison")

        # Convert to torch tensors if needed
        if not isinstance(tensor1, torch.Tensor):
            tensor1 = torch.tensor(tensor1)
        if not isinstance(tensor2, torch.Tensor):
            tensor2 = torch.tensor(tensor2)

        # Check if close
        if not torch.allclose(tensor1, tensor2, rtol=rtol, atol=atol):
            max_diff = torch.max(torch.abs(tensor1 - tensor2)).item()
            error_msg = f"Tensors not close (max_diff={max_diff:.6e})"
            if message:
                error_msg = f"{message}: {error_msg}"
            raise AssertionError(error_msg)

    except Exception as e:
        emergency_cleanup()
        raise e


@safe_execution(max_retries=1)
def run_memory_stress_test(
    test_func: Callable,
    memory_sizes: List[int] = None,
    test_name: str = "memory_stress_test"
) -> Dict[str, Any]:
    """
    Run memory stress test with automatic scaling.

    Args:
        test_func: Function to test with different memory sizes
        memory_sizes: List of memory sizes to test (MB)
        test_name: Name for the test

    Returns:
        Stress test results
    """
    if memory_sizes is None:
        memory_sizes = [64, 128, 256, 512, 1024]

    logger.info(f"Starting memory stress test: {test_name}")

    results = {
        'test_name': test_name,
        'tested_sizes': [],
        'successful_sizes': [],
        'failed_sizes': [],
        'max_successful_size': 0,
        'errors': []
    }

    for size_mb in memory_sizes:
        logger.info(f"Testing memory size: {size_mb}MB")

        with safe_test_environment(f"{test_name}_{size_mb}MB"):
            try:
                test_func(size_mb)
                results['successful_sizes'].append(size_mb)
                results['max_successful_size'] = size_mb
                logger.info(f"✅ Memory test {size_mb}MB: PASSED")

            except Exception as e:
                results['failed_sizes'].append(size_mb)
                results['errors'].append({
                    'size_mb': size_mb,
                    'error': str(e)
                })

                if "out of memory" in str(e).lower():
                    logger.warning(f"❌ Memory test {size_mb}MB: OOM (expected)")
                    break  # Stop testing larger sizes
                else:
                    logger.error(f"❌ Memory test {size_mb}MB: ERROR - {e}")

            finally:
                results['tested_sizes'].append(size_mb)
                emergency_cleanup()

    logger.info("Memory stress test completed:")
    logger.info(f"  Max successful size: {results['max_successful_size']}MB")
    logger.info(f"  Successful: {len(results['successful_sizes'])}")
    logger.info(f"  Failed: {len(results['failed_sizes'])}")

    return results


if __name__ == "__main__":
    # Test the safe testing framework
    logging.basicConfig(level=logging.INFO)

    print("Testing safe testing framework...")

    def dummy_test_pass():
        """Dummy test that passes."""
        assert 1 + 1 == 2

    def dummy_test_fail():
        """Dummy test that fails."""
        assert 1 + 1 == 3

    def dummy_test_error():
        """Dummy test that raises error."""
        raise ValueError("Test error")

    try:
        runner = SafeTestRunner()

        # Test individual tests
        result1 = runner.run_test_safe(dummy_test_pass, "test_pass")
        print(f"✅ Test pass result: {result1['status']}")

        result2 = runner.run_test_safe(dummy_test_fail, "test_fail")
        print(f"✅ Test fail result: {result2['status']}")

        result3 = runner.run_test_safe(dummy_test_error, "test_error")
        print(f"✅ Test error result: {result3['status']}")

        # Test suite
        suite_results = runner.run_test_suite_safe(
            [dummy_test_pass, dummy_test_fail, dummy_test_error],
            "dummy_suite"
        )
        print(f"✅ Suite results: {suite_results['passed']}/{suite_results['total_tests']} passed")

        # Test environment context
        with safe_test_environment("test_context"):
            assert True
        print("✅ Test environment context completed")

        print("Safe testing framework test completed")

    except Exception as e:
        print(f"❌ Test failed: {e}")
