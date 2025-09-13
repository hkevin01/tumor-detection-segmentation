#!/usr/bin/env python3
"""
Debug Requirements Traceability Detection

Test script to debug why requirements are not being detected.
"""

import re
from pathlib import Path

def test_detection():
    """Test requirement detection in files."""
    project_root = Path(__file__).parent

    # Test specific file
    test_file = project_root / "src" / "training" / "train_enhanced.py"

    if test_file.exists():
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()

        print(f"Testing file: {test_file}")
        print(f"File size: {len(content)} characters")

        # Test patterns
        functional_pattern = r'REQ-F-\d{3}'
        functional_matches = re.findall(functional_pattern, content)
        print(f"Functional matches: {functional_matches}")

        nf_pattern = r'REQ-NF-[A-Z]+-\d{3}'
        nf_matches = re.findall(nf_pattern, content)
        print(f"Non-functional matches: {nf_matches}")

        # Check for any 'REQ-' strings
        all_req_matches = re.findall(r'REQ-[A-Z]+-[A-Z0-9-]+', content)
        print(f"All REQ matches: {all_req_matches}")

        # Check first 1000 characters for REQ
        print(f"First 1000 chars contain 'REQ-F-001': {'REQ-F-001' in content[:1000]}")
        print(f"Content preview:")
        print(content[:500])

    else:
        print(f"File not found: {test_file}")

if __name__ == "__main__":
    test_detection()
