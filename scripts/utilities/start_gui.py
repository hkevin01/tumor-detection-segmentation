#!/usr/bin/env python3
"""
Startup script for the Tumor Detection GUI Backend.

This script starts the FastAPI server for the clinical interface.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))


def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = [
        ("fastapi", "pip install fastapi"),
        ("uvicorn", "pip install uvicorn[standard]"),
        ("sqlalchemy", "pip install sqlalchemy"),
        ("pydantic", "pip install pydantic"),
    ]
    
    missing_packages = []
    
    for package, install_cmd in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append((package, install_cmd))
    
    if missing_packages:
        print("❌ Missing required dependencies:")
        for package, install_cmd in missing_packages:
            print(f"   - {package}: {install_cmd}")
        print("\nInstall all GUI dependencies with:")
        print("   pip install -r requirements.txt")
        return False
    
    return True


def check_configuration():
    """Check if configuration file exists and is valid."""
    config_path = project_root / "config.json"
    
    if not config_path.exists():
        print(f"❌ Configuration file not found: {config_path}")
        print("   Please create config.json in the project root")
        return False
    
    try:
        import json
        with open(config_path, encoding='utf-8') as f:
            config = json.load(f)
        
        # Check for GUI configuration
        if "gui" not in config:
            print("⚠️  No GUI configuration found in config.json")
            print("   Using default settings")
        
        return True
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in config.json: {e}")
        return False
    except (IOError, OSError) as e:
        print(f"❌ Error reading config.json: {e}")
        return False


def setup_directories():
    """Create necessary directories."""
    directories = [
        project_root / "uploads",
        project_root / "logs",
        project_root / "reports",
        project_root / "models"
    ]
    
    for directory in directories:
        directory.mkdir(exist_ok=True)
    
    print("✅ Directories created/verified")


def main():
    """Main startup function."""
    print("🏥 Tumor Detection GUI Backend Startup")
    print("=" * 50)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed. Please install missing packages.")
        sys.exit(1)
    
    print("✅ Dependencies check passed")
    
    # Check configuration
    if not check_configuration():
        print("\n❌ Configuration check failed.")
        sys.exit(1)
    
    print("✅ Configuration check passed")
    
    # Setup directories
    setup_directories()
    
    # Import and start the server
    try:
        from gui.backend.main import main as start_server
        print("\n🚀 Starting Tumor Detection API server...")
        print("   Press Ctrl+C to stop the server")
        start_server()
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except ImportError as e:
        print(f"\n❌ Import error: {e}")
        print("   Make sure all dependencies are installed")
        sys.exit(1)
    except (RuntimeError, OSError) as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)
