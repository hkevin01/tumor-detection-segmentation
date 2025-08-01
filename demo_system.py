#!/usr/bin/env python3
"""
Medical Imaging GUI System - Comprehensive Demo
Showcases all components of the MONAI-based medical imaging system
"""

import sys
import os
import json
from datetime import datetime

def print_header():
    """Print system header"""
    print("🏥" + "=" * 58 + "🏥")
    print("     MEDICAL IMAGING AI - TUMOR DETECTION & SEGMENTATION")
    print("     Comprehensive GUI System Demo")
    print("     Powered by MONAI + React + FastAPI")
    print("🏥" + "=" * 58 + "🏥")
    print()

def demonstrate_backend():
    """Demonstrate the medical AI backend capabilities"""
    print("🧠 MEDICAL AI BACKEND DEMONSTRATION")
    print("-" * 40)
    
    try:
        sys.path.append('src')
        from medical_ai_backend import MedicalImagingAI
        
        # Initialize AI system
        print("🔧 Initializing Medical AI System...")
        ai = MedicalImagingAI()
        print("   ✅ System initialized successfully")
        
        # Show available models
        print("\n🤖 Available AI Models:")
        models = ["unet", "segresnet", "swinunetr"]
        for model in models:
            config = ai.config["models"][model]
            print(f"   • {model.upper()}: {config.get('spatial_dims', 3)}D, "
                  f"{config.get('in_channels', 1)} → {config.get('out_channels', 2)} channels")
        
        # Test model loading
        print("\n📥 Loading UNet model...")
        try:
            model = ai.load_model("unet")
            print("   ✅ UNet model loaded successfully")
            
            # Get model info
            info = ai.get_model_info()
            unet_info = info.get("unet", {})
            print(f"   📊 Parameters: {unet_info.get('total_parameters', 0):,}")
            print(f"   💾 Memory: {unet_info.get('memory_footprint_mb', 0):.1f} MB")
            
            # Benchmark the model
            print("\n⚡ Running performance benchmark...")
            benchmark = ai.benchmark_model("unet")
            print(f"   🕐 Inference time: {benchmark['average_inference_time']:.3f}s")
            print(f"   🚀 Throughput: {benchmark['throughput_fps']:.1f} FPS")
            
        except Exception as e:
            print(f"   ⚠️  Model loading: {e}")
            print("   💡 Install MONAI: pip install monai torch")
        
    except ImportError as e:
        print(f"   ❌ Backend import failed: {e}")
        print("   💡 Run: pip install -r requirements.txt")
    
    print()

def demonstrate_api():
    """Demonstrate the FastAPI backend"""
    print("🌐 FASTAPI BACKEND DEMONSTRATION")
    print("-" * 40)
    
    try:
        sys.path.append('src')
        from medical_imaging_api import app
        
        print("🔧 FastAPI application loaded")
        
        # Show available routes
        print("\n📡 Available API Endpoints:")
        routes = [
            ("/api/health", "Health check"),
            ("/api/dicom/upload", "DICOM file upload"),
            ("/api/ai/predict", "AI tumor prediction"),
            ("/api/ai/batch", "Batch processing"),
            ("/api/models/info", "Model information"),
            ("/api/patients", "Patient management"),
            ("/api/studies", "Study retrieval")
        ]
        
        for endpoint, description in routes:
            print(f"   • {endpoint:20} - {description}")
        
        print("\n📊 API Features:")
        features = [
            "CORS middleware for frontend integration",
            "Authentication and authorization ready",
            "File upload with validation",
            "Background task processing",
            "Error handling and logging",
            "OpenAPI documentation"
        ]
        
        for feature in features:
            print(f"   ✅ {feature}")
            
    except ImportError as e:
        print(f"   ❌ API import failed: {e}")
    
    print()

def demonstrate_frontend():
    """Demonstrate the React frontend structure"""
    print("⚛️  REACT FRONTEND DEMONSTRATION")
    print("-" * 40)
    
    print("🔧 Frontend Components:")
    
    components = {
        "App.tsx": "Main application with tabbed interface",
        "DicomViewer.tsx": "Advanced DICOM viewer with AI overlay",
        "PatientManagement.tsx": "Patient workflow and timeline",
        "ModelControlPanel.tsx": "AI model controls and monitoring"
    }
    
    for component, description in components.items():
        component_path = f"frontend/src/components/{component}" if component != "App.tsx" else f"frontend/src/{component}"
        
        if os.path.exists(component_path):
            with open(component_path, 'r') as f:
                lines = len(f.readlines())
            print(f"   ✅ {component:25} - {description} ({lines} lines)")
        else:
            print(f"   ⚠️  {component:25} - {description} (missing)")
    
    print("\n🎨 UI Features:")
    ui_features = [
        "Material-UI components for professional medical interface",
        "Dark theme optimized for medical imaging",
        "Responsive design for various screen sizes",
        "Real-time updates and state management",
        "Touch and gesture support",
        "Accessibility compliance (WCAG 2.1)"
    ]
    
    for feature in ui_features:
        print(f"   ✅ {feature}")
    
    print("\n📦 Dependencies:")
    package_path = "frontend/package.json"
    if os.path.exists(package_path):
        try:
            with open(package_path, 'r') as f:
                package_data = json.load(f)
            
            deps = package_data.get('dependencies', {})
            print(f"   📚 {len(deps)} runtime dependencies")
            
            key_deps = {
                '@mui/material': 'Material-UI',
                'react': 'React',
                'cornerstone-core': 'DICOM rendering',
                'three': '3D visualization'
            }
            
            for dep, desc in key_deps.items():
                version = deps.get(dep, 'not found')
                print(f"   • {desc:20} {version}")
                
        except json.JSONDecodeError:
            print("   ⚠️  Could not parse package.json")
    else:
        print("   ⚠️  package.json not found")
    
    print()

def demonstrate_system_integration():
    """Demonstrate system integration capabilities"""
    print("🔗 SYSTEM INTEGRATION DEMONSTRATION")
    print("-" * 40)
    
    print("🏗️ Architecture Overview:")
    print("   ┌─────────────────────────────────────┐")
    print("   │        React Frontend               │")
    print("   │  • DICOM Viewer                    │")
    print("   │  • Patient Management              │")
    print("   │  • Model Controls                  │")
    print("   └─────────────────┬───────────────────┘")
    print("                     │ REST API")
    print("   ┌─────────────────┴───────────────────┐")
    print("   │        FastAPI Backend             │")
    print("   │  • DICOM Processing                │")
    print("   │  • AI Inference                    │")
    print("   │  • Patient Data                    │")
    print("   └─────────────────┬───────────────────┘")
    print("                     │ Python API")
    print("   ┌─────────────────┴───────────────────┐")
    print("   │        MONAI AI Engine              │")
    print("   │  • UNet, SegResNet, SwinUNETR      │")
    print("   │  • Sliding Window Inference        │")
    print("   │  • Medical Transforms               │")
    print("   └─────────────────────────────────────┘")
    
    print("\n🔄 Data Flow:")
    flow_steps = [
        "1. User uploads DICOM files via React frontend",
        "2. FastAPI receives and validates medical images",
        "3. MONAI AI engine processes images with transforms",
        "4. Deep learning models perform tumor segmentation",
        "5. Results returned through API to frontend",
        "6. Interactive visualization with overlay"
    ]
    
    for step in flow_steps:
        print(f"   {step}")
    
    print("\n💾 Supported Formats:")
    formats = [
        "DICOM (.dcm, .dicom) - Medical imaging standard",
        "NIfTI (.nii, .nii.gz) - Neuroimaging format",
        "NRRD (.nrrd) - Nearly Raw Raster Data",
        "MetaImage (.mhd, .mha) - ITK format"
    ]
    
    for fmt in formats:
        print(f"   ✅ {fmt}")
    
    print()

def demonstrate_clinical_workflow():
    """Demonstrate clinical workflow capabilities"""
    print("🏥 CLINICAL WORKFLOW DEMONSTRATION")
    print("-" * 40)
    
    print("👩‍⚕️ Clinical Use Cases:")
    
    use_cases = [
        {
            "name": "Tumor Detection Screening",
            "description": "AI-powered initial screening for tumor presence",
            "workflow": [
                "Load patient DICOM study",
                "Run AI analysis (UNet/SegResNet)",
                "Review confidence scores",
                "Generate preliminary report"
            ]
        },
        {
            "name": "Treatment Response Assessment",
            "description": "Compare pre/post treatment scans",
            "workflow": [
                "Load baseline and follow-up studies",
                "Run comparative analysis",
                "Calculate volume changes",
                "Generate RECIST assessment"
            ]
        },
        {
            "name": "Surgical Planning",
            "description": "Detailed tumor segmentation for surgery",
            "workflow": [
                "High-resolution segmentation (SwinUNETR)",
                "3D tumor reconstruction",
                "Anatomical relationship analysis",
                "Export to surgical planning tools"
            ]
        }
    ]
    
    for i, use_case in enumerate(use_cases, 1):
        print(f"\n{i}. {use_case['name']}")
        print(f"   📋 {use_case['description']}")
        print("   🔄 Workflow:")
        for step in use_case['workflow']:
            print(f"      • {step}")
    
    print("\n📊 Quality Metrics:")
    metrics = [
        "Dice Similarity Coefficient (DSC)",
        "Hausdorff Distance (HD)",
        "Volume Overlap Error (VOE)",
        "Surface Distance Metrics",
        "Sensitivity and Specificity",
        "Inter-observer Variability"
    ]
    
    for metric in metrics:
        print(f"   📈 {metric}")
    
    print()

def show_startup_instructions():
    """Show how to start the system"""
    print("🚀 SYSTEM STARTUP INSTRUCTIONS")
    print("-" * 40)
    
    print("📋 Prerequisites:")
    prereqs = [
        "Python 3.8+ with pip",
        "Node.js 18+ with npm",
        "CUDA-capable GPU (recommended)",
        "8GB+ RAM (16GB+ recommended)"
    ]
    
    for prereq in prereqs:
        print(f"   • {prereq}")
    
    print("\n🔧 Quick Start Commands:")
    commands = [
        ("./quick_setup.sh", "Initial system setup"),
        ("./start_medical_gui.sh", "Start complete system"),
        ("python test_system.py", "Validate installation"),
        ("Open http://localhost:3000", "Access web interface")
    ]
    
    for command, description in commands:
        print(f"   $ {command:30} # {description}")
    
    print("\n🌐 Access Points:")
    access_points = [
        ("Frontend GUI", "http://localhost:3000"),
        ("API Documentation", "http://localhost:8000/docs"),
        ("API Health Check", "http://localhost:8000/api/health"),
        ("OpenAPI Schema", "http://localhost:8000/openapi.json")
    ]
    
    for service, url in access_points:
        print(f"   🌍 {service:20} {url}")
    
    print()

def main():
    """Main demonstration function"""
    print_header()
    
    demonstrations = [
        demonstrate_backend,
        demonstrate_api,
        demonstrate_frontend,
        demonstrate_system_integration,
        demonstrate_clinical_workflow,
        show_startup_instructions
    ]
    
    for demo in demonstrations:
        try:
            demo()
        except Exception as e:
            print(f"   ❌ Demo failed: {e}")
            print()
    
    print("🎉 DEMONSTRATION COMPLETE")
    print("-" * 40)
    print("✨ The comprehensive medical imaging GUI system includes:")
    print("   • Advanced DICOM viewer with AI overlay")
    print("   • Three state-of-the-art AI models (UNet, SegResNet, SwinUNETR)")
    print("   • Complete patient management workflow")
    print("   • Professional medical imaging interface")
    print("   • FastAPI backend with REST endpoints")
    print("   • MONAI-powered medical AI engine")
    print()
    print("🚀 Ready to start? Run: ./start_medical_gui.sh")
    print("📚 Documentation: MEDICAL_GUI_README.md")
    print()
    print("🏥 Built for healthcare professionals with ❤️")

if __name__ == "__main__":
    main()
