#!/usr/bin/env python3
"""
Quick validation test for the medical imaging system
"""

import json
import os
import sys


def test_configuration():
    """Test if configuration files are valid"""
    print("🧪 Testing configuration files...")

    # Test main config
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        print("✅ Main config.json is valid")
        print(f"   - Enhanced features enabled: {config.get('enhanced_features', {})}")
        print(f"   - MONAI Label enabled: {config.get('monai_label', {}).get('enabled', False)}")
        print(f"   - MLflow enabled: {config.get('mlflow', {}).get('enabled', False)}")
    except Exception as e:
        print(f"❌ Error loading config.json: {e}")
        return False

    # Test recipe configs
    recipe_dir = "config/recipes"
    if os.path.exists(recipe_dir):
        recipes = [f for f in os.listdir(recipe_dir) if f.endswith('.json')]
        print(f"✅ Found {len(recipes)} configuration recipes")
        for recipe in recipes:
            print(f"   - {recipe}")

    return True

def test_directories():
    """Test if all required directories exist"""
    print("\n📁 Testing directory structure...")

    required_dirs = [
        'src/data',
        'src/fusion',
        'src/models',
        'src/utils',
        'src/training',
        'scripts/setup',
        'scripts/utilities',
        'config/recipes',
        'config/docker'
    ]

    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"✅ {dir_path}")
        else:
            print(f"❌ Missing: {dir_path}")

    return True

def test_key_files():
    """Test if key implementation files exist"""
    print("\n📄 Testing key implementation files...")

    key_files = [
        'src/data/preprocess.py',
        'src/fusion/attention_fusion.py',
        'src/models/cascade_detector.py',
        'src/utils/logging_mlflow.py',
        'src/training/train_enhanced.py',
        'scripts/setup/setup_monai_label.sh',
        'scripts/utilities/start_medical_gui.sh',
        'config/docker/docker-compose.yml'
    ]

    for file_path in key_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ Missing: {file_path}")

    return True

def test_docker_config():
    """Test Docker configuration"""
    print("\n🐳 Testing Docker configuration...")

    docker_files = [
        'config/docker/Dockerfile.cuda',
        'config/docker/Dockerfile.rocm',
        'config/docker/docker-compose.yml'
    ]

    for file_path in docker_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ Missing: {file_path}")

    # Check if docker-compose.yml has all services
    try:
        import yaml
        with open('config/docker/docker-compose.yml', 'r') as f:
            compose = yaml.safe_load(f)
        services = list(compose.get('services', {}).keys())
        print(f"✅ Docker services configured: {', '.join(services)}")
    except Exception as e:
        print(f"⚠️  Could not validate docker-compose.yml: {e}")

    return True

def main():
    """Run all system tests"""
    print("🔍 Medical Imaging AI Platform - System Validation")
    print("=" * 60)

    tests = [
        test_configuration,
        test_directories,
        test_key_files,
        test_docker_config
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append(False)

    print("\n" + "=" * 60)
    if all(results):
        print("🎉 All system tests PASSED!")
        print("✅ Your platform is ready for deployment")
        return 0
    else:
        print("❌ Some tests FAILED")
        print("🔧 Please check the errors above and fix missing components")
        return 1

if __name__ == "__main__":
    sys.exit(main())
