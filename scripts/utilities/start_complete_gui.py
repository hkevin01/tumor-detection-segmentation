#!/usr/bin/env python3
"""
Complete GUI startup script for Tumor Detection System.

This script starts both the FastAPI backend and React frontend servers,
providing a complete clinical interface for the tumor detection system.
"""

import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

class GuiLauncher:
    """Complete GUI launcher for backend and frontend."""
    
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.processes = []
        
    def check_dependencies(self):
        """Check if required dependencies are installed."""
        print("🔍 Checking dependencies...")
        
        # Check Python dependencies
        python_packages = [
            ("fastapi", "pip install fastapi"),
            ("uvicorn", "pip install uvicorn[standard]"),
        ]
        
        missing_python = []
        for package, install_cmd in python_packages:
            try:
                __import__(package)
            except ImportError:
                missing_python.append((package, install_cmd))
        
        if missing_python:
            print("❌ Missing Python dependencies:")
            for package, install_cmd in missing_python:
                print(f"   - {package}: {install_cmd}")
            return False
        
        # Check Node.js
        try:
            result = subprocess.run(['node', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Node.js: {result.stdout.strip()}")
            else:
                print("❌ Node.js not found. Please install Node.js 16+")
                return False
        except FileNotFoundError:
            print("❌ Node.js not found. Please install Node.js 16+")
            return False
        
        # Check npm
        try:
            subprocess.run(['npm', '--version'], 
                          capture_output=True, check=True)
            print("✅ npm available")
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("❌ npm not found. Please install npm")
            return False
        
        print("✅ All dependencies available")
        return True
    
    def setup_frontend_dependencies(self):
        """Install frontend dependencies if needed."""
        frontend_dir = project_root / "gui" / "frontend"
        node_modules = frontend_dir / "node_modules"
        
        if not node_modules.exists():
            print("📦 Installing frontend dependencies...")
            try:
                subprocess.run(
                    ['npm', 'install'], 
                    cwd=frontend_dir,
                    check=True
                )
                print("✅ Frontend dependencies installed")
                return True
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to install frontend dependencies: {e}")
                return False
        else:
            print("✅ Frontend dependencies already installed")
            return True
    
    def start_backend(self):
        """Start the FastAPI backend server."""
        print("🚀 Starting backend server...")
        
        try:
            # Start backend process
            self.backend_process = subprocess.Popen(
                [sys.executable, str(project_root / "start_gui.py")],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes.append(self.backend_process)
            
            # Wait a moment for server to start
            time.sleep(3)
            
            if self.backend_process.poll() is None:
                print("✅ Backend server started on http://localhost:8000")
                return True
            else:
                stdout, stderr = self.backend_process.communicate()
                print(f"❌ Backend failed to start:")
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start backend: {e}")
            return False
    
    def start_frontend(self):
        """Start the React frontend server."""
        print("🚀 Starting frontend server...")
        
        frontend_dir = project_root / "gui" / "frontend"
        
        try:
            # Start frontend process
            self.frontend_process = subprocess.Popen(
                ['npm', 'start'],
                cwd=frontend_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.processes.append(self.frontend_process)
            
            # Wait for frontend to start
            time.sleep(10)
            
            if self.frontend_process.poll() is None:
                print("✅ Frontend server started on http://localhost:3000")
                return True
            else:
                stdout, stderr = self.frontend_process.communicate()
                print(f"❌ Frontend failed to start:")
                print(f"STDOUT: {stdout}")
                print(f"STDERR: {stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start frontend: {e}")
            return False
    
    def monitor_processes(self):
        """Monitor running processes."""
        print("\n📊 Monitoring servers...")
        print("   Backend API: http://localhost:8000")
        print("   Frontend UI: http://localhost:3000")
        print("   API Docs: http://localhost:8000/docs")
        print("\n   Press Ctrl+C to stop all servers\n")
        
        try:
            while True:
                # Check if processes are still running
                if self.backend_process and self.backend_process.poll() is not None:
                    print("❌ Backend process stopped unexpectedly")
                    break
                
                if self.frontend_process and self.frontend_process.poll() is not None:
                    print("❌ Frontend process stopped unexpectedly")
                    break
                
                time.sleep(2)
                
        except KeyboardInterrupt:
            print("\n🛑 Stopping servers...")
            self.cleanup()
    
    def cleanup(self):
        """Clean up all processes."""
        for process in self.processes:
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                except Exception as e:
                    print(f"Error stopping process: {e}")
        
        print("✅ All servers stopped")
    
    def launch(self):
        """Launch the complete GUI system."""
        print("🏥 Tumor Detection Complete GUI Launcher")
        print("=" * 50)
        
        # Check dependencies
        if not self.check_dependencies():
            print("\n❌ Dependency check failed.")
            return False
        
        # Setup frontend dependencies
        if not self.setup_frontend_dependencies():
            print("\n❌ Frontend setup failed.")
            return False
        
        # Start backend
        if not self.start_backend():
            print("\n❌ Backend startup failed.")
            return False
        
        # Start frontend
        if not self.start_frontend():
            print("\n❌ Frontend startup failed.")
            self.cleanup()
            return False
        
        # Monitor processes
        self.monitor_processes()
        
        return True


def main():
    """Main entry point."""
    launcher = GuiLauncher()
    
    # Setup signal handlers
    def signal_handler(sig, frame):
        print("\n🛑 Received shutdown signal...")
        launcher.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        success = launcher.launch()
        if not success:
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        launcher.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()
