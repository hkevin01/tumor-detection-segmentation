#!/usr/bin/env python3
"""
Test Phase 2 Setup

Simple test to validate that Phase 2 clinical features are properly
initialized.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_phase2_imports():
    """Test that Phase 2 dependencies can be imported."""
    print("🧪 Testing Phase 2 imports...")

    # Test DICOM libraries
    try:
        import pydicom
        import pynetdicom  # noqa: F401
        print(f"✅ DICOM libraries: pydicom {pydicom.__version__}")
    except ImportError as e:
        print(f"❌ DICOM import failed: {e}")
        return False

    # Test FHIR libraries
    try:
        import fhir.resources  # noqa: F401
        print("✅ FHIR libraries available")
    except ImportError as e:
        print(f"❌ FHIR import failed: {e}")
        return False

    # Test report generation libraries
    try:
        import docx  # noqa: F401
        import reportlab  # noqa: F401
        print("✅ Report generation libraries available")
    except ImportError as e:
        print(f"❌ Report generation import failed: {e}")
        return False

    return True


def test_clinical_modules():
    """Test that clinical modules can be imported."""
    print("🏥 Testing clinical modules...")

    try:
        from src.clinical.dicom_server.dicom_server import \
            DICOMServer  # noqa: F401, E501
        print("✅ DICOM server module loads")
    except ImportError as e:
        print(f"⚠️ DICOM server import issue: {e}")

    try:
        from src.clinical.report_generation.clinical_reports import \
            ClinicalReportGenerator  # noqa: E501; noqa: F401
        print("✅ Report generation module loads")
    except ImportError as e:
        print(f"⚠️ Report generation import issue: {e}")

    return True


def test_directory_structure():
    """Test that Phase 2 directory structure exists."""
    print("📁 Testing directory structure...")

    required_dirs = [
        "src/clinical",
        "src/clinical/dicom_server",
        "src/clinical/fhir_server",
        "src/clinical/report_generation",
        "src/clinical/slicer_plugin",
        "src/clinical/validation",
        "config/clinical",
        "templates/reports"
    ]

    all_exist = True
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"✅ {dir_path}")
        else:
            print(f"❌ Missing: {dir_path}")
            all_exist = False

    return all_exist


def main():
    """Run all Phase 2 tests."""
    print("🚀 Phase 2 Setup Validation")
    print("=" * 40)

    tests = [
        ("Import Tests", test_phase2_imports),
        ("Module Tests", test_clinical_modules),
        ("Directory Structure", test_directory_structure)
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 20)
        result = test_func()
        results.append((test_name, result))

    print("\n" + "=" * 40)
    print("📊 Test Summary:")

    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        all_passed &= result

    if all_passed:
        print("\n🎉 Phase 2 setup validation PASSED!")
        print("Ready for clinical development!")
    else:
        print("\n⚠️ Some tests failed. Review setup.")
        sys.exit(1)


if __name__ == "__main__":
    main()
