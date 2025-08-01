#!/usr/bin/env python3
"""
Medical Imaging GUI System Test
Quick validation of all components
"""

import sys
import os

def test_backend():
    """Test the medical AI backend"""
    print("🧠 Testing Medical AI Backend...")
    try:
        sys.path.append('src')
        from medical_ai_backend import MedicalImagingAI
        
        ai = MedicalImagingAI()
        print("   ✅ Medical AI backend initialized")
        
        # Test model info
        info = ai.get_model_info()
        print(f"   📊 {len(info)} models available")
        
        return True
    except Exception as e:
        print(f"   ❌ Backend test failed: {e}")
        return False

def test_api():
    """Test the FastAPI backend"""
    print("🌐 Testing FastAPI Backend...")
    try:
        sys.path.append('src')
        from medical_imaging_api import app
        print("   ✅ FastAPI backend loaded")
        
        # Check if app has the expected routes
        routes = [route.path for route in app.routes]
        print(f"   📡 {len(routes)} API routes available")
        
        return True
    except Exception as e:
        print(f"   ❌ API test failed: {e}")
        return False

def test_frontend():
    """Test frontend structure"""
    print("⚛️  Testing Frontend Structure...")
    try:
        frontend_files = [
            'frontend/package.json',
            'frontend/src/App.tsx',
            'frontend/src/components/DicomViewer.tsx',
            'frontend/src/components/PatientManagement.tsx',
            'frontend/src/components/ModelControlPanel.tsx'
        ]
        
        missing_files = []
        for file in frontend_files:
            if not os.path.exists(file):
                missing_files.append(file)
        
        if missing_files:
            print(f"   ⚠️  Missing files: {missing_files}")
            return False
        else:
            print("   ✅ All frontend components present")
            return True
            
    except Exception as e:
        print(f"   ❌ Frontend test failed: {e}")
        return False

def test_dependencies():
    """Test key dependencies"""
    print("📦 Testing Dependencies...")
    
    dependencies = {
        'torch': 'PyTorch',
        'numpy': 'NumPy',
        'fastapi': 'FastAPI',
    }
    
    optional_deps = {
        'monai': 'MONAI (Medical AI)',
        'SimpleITK': 'SimpleITK (Medical Imaging)',
        'pydicom': 'PyDICOM (DICOM Processing)'
    }
    
    all_good = True
    
    for dep, name in dependencies.items():
        try:
            __import__(dep)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} (required)")
            all_good = False
    
    for dep, name in optional_deps.items():
        try:
            __import__(dep)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ⚠️  {name} (optional, but recommended)")
    
    return all_good

def main():
    """Run all tests"""
    print("🏥 Medical Imaging AI - System Validation")
    print("=" * 50)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Backend", test_backend),
        ("API", test_api),
        ("Frontend", test_frontend)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   💥 {test_name} test crashed: {e}")
            results.append((test_name, False))
        print()
    
    # Summary
    print("📋 Test Summary:")
    print("-" * 30)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("\n🎉 All systems ready! Run './start_medical_gui.sh' to launch")
    else:
        print("\n⚠️  Some issues detected. Check dependencies and run:")
        print("   pip install -r requirements.txt")
        print("   cd frontend && npm install")

if __name__ == "__main__":
    main()
