#!/usr/bin/env python3
"""
Test script for the GUI backend to verify integration.
"""

import sys
from pathlib import Path
import json

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


def test_imports():
    """Test that all required modules can be imported."""
    print("Testing imports...")
    
    try:
        # Test utils import
        from utils.utils import load_config, setup_logging, get_device
        print("✅ Utils import successful")
    except ImportError as e:
        print(f"❌ Utils import failed: {e}")
        return False
    
    try:
        # Test backend models
        from gui.backend.models import get_storage, StudyStatus
        print("✅ Backend models import successful")
    except ImportError as e:
        print(f"❌ Backend models import failed: {e}")
        return False
    
    try:
        # Test API routes (might fail without FastAPI)
        from gui.backend.api.routes import get_router
        print("✅ API routes import successful")
    except ImportError as e:
        print(f"⚠️  API routes import failed (expected if FastAPI not installed): {e}")
    
    try:
        # Test main app
        from gui.backend.main import create_app
        print("✅ Main app import successful")
    except ImportError as e:
        print(f"⚠️  Main app import failed (expected if FastAPI not installed): {e}")
    
    return True


def test_storage():
    """Test the in-memory storage system."""
    print("\nTesting storage system...")
    
    try:
        from gui.backend.models import get_storage, StudyStatus
        storage = get_storage()
        
        # Test patient creation
        patient_data = {
            "name": "Test Patient",
            "medical_record_number": "TEST001"
        }
        patient_id = storage.add_patient(patient_data)
        print(f"✅ Patient created with ID: {patient_id}")
        
        # Test study creation
        study_data = {
            "patient_id": patient_id,
            "modality": "CT",
            "description": "Test study"
        }
        study_id = storage.add_study(study_data)
        print(f"✅ Study created with ID: {study_id}")
        
        # Test status update
        storage.update_study_status(study_id, StudyStatus.PROCESSING)
        print("✅ Study status updated")
        
        # Test retrieval
        studies = storage.get_studies()
        print(f"✅ Retrieved {len(studies)} studies")
        
        models = storage.get_models()
        print(f"✅ Retrieved {len(models)} AI models")
        
        return True
        
    except Exception as e:
        print(f"❌ Storage test failed: {e}")
        return False


def test_configuration():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    config_path = project_root / "config.json"
    
    if not config_path.exists():
        print("❌ config.json not found")
        return False
    
    try:
        with open(config_path, encoding='utf-8') as f:
            config = json.load(f)
        
        # Check for required sections
        required_sections = ["gui", "model", "training"]
        missing_sections = [s for s in required_sections if s not in config]
        
        if missing_sections:
            print(f"⚠️  Missing config sections: {missing_sections}")
        else:
            print("✅ All required config sections present")
        
        # Check GUI config
        gui_config = config.get("gui", {})
        print(f"✅ GUI config: host={gui_config.get('host', 'localhost')}, port={gui_config.get('port', 8000)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


def test_utils():
    """Test utility functions."""
    print("\nTesting utility functions...")
    
    try:
        from utils.utils import load_config, setup_logging, get_device
        
        # Test config loading
        config = load_config("config.json")
        print(f"✅ Config loaded: {len(config)} sections")
        
        # Test device detection
        device = get_device()
        print(f"✅ Device detected: {device}")
        
        # Test logging setup
        logger = setup_logging(log_dir="./logs", log_level="INFO")
        logger.info("Test log message")
        print("✅ Logging setup successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Utils test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 GUI Backend Integration Tests")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_configuration,
        test_utils,
        test_storage
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
            print()
    
    print("=" * 40)
    print(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed! GUI backend is ready.")
        return True
    else:
        print("❌ Some tests failed. Check the output above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
