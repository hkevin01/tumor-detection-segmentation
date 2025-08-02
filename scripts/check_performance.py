#!/usr/bin/env python3
"""Script to check for performance regressions in benchmark results."""

import json
import sys
from pathlib import Path
import numpy as np

def load_benchmark_results(file_path):
    """Load benchmark results from a JSON file."""
    with open(file_path, 'r') as f:
        return json.load(f)

def check_performance_regression(current_results, baseline_results, threshold=0.1):
    """
    Compare current results against baseline.
    
    Args:
        current_results: Current benchmark results
        baseline_results: Baseline benchmark results
        threshold: Maximum allowed performance degradation (10% by default)
        
    Returns:
        tuple: (has_regression, details)
    """
    regressions = []
    
    for test_name, current in current_results.items():
        if test_name in baseline_results:
            baseline = baseline_results[test_name]
            
            # Compare mean execution times
            current_mean = current.get('stats', {}).get('mean', 0)
            baseline_mean = baseline.get('stats', {}).get('mean', 0)
            
            if baseline_mean > 0:
                regression = (current_mean - baseline_mean) / baseline_mean
                
                if regression > threshold:
                    regressions.append({
                        'test': test_name,
                        'regression': regression * 100,
                        'current_time': current_mean,
                        'baseline_time': baseline_mean
                    })
    
    return bool(regressions), regressions

def main():
    """Main function to check performance regressions."""
    # Load current results
    current_file = Path('.pytest_benchmark/current.json')
    if not current_file.exists():
        print("No current benchmark results found")
        sys.exit(1)
    
    # Load baseline results
    baseline_file = Path('.pytest_benchmark/baseline.json')
    if not baseline_file.exists():
        print("No baseline benchmark results found")
        sys.exit(1)
    
    current_results = load_benchmark_results(current_file)
    baseline_results = load_benchmark_results(baseline_file)
    
    has_regression, regressions = check_performance_regression(
        current_results,
        baseline_results
    )
    
    if has_regression:
        print("⚠️ Performance regressions detected:")
        for reg in regressions:
            print(f"""
Test: {reg['test']}
Regression: {reg['regression']:.2f}%
Current Time: {reg['current_time']:.4f}s
Baseline Time: {reg['baseline_time']:.4f}s
""")
        sys.exit(1)
    else:
        print("✅ No performance regressions detected")
        sys.exit(0)

if __name__ == '__main__':
    main()
