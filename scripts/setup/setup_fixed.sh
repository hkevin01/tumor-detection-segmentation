#!/bin/bash

# Fixed Setup Script for Medical Imaging AI
echo "🏥 Medical Imaging AI - Fixed Installation Setup"
echo "=============================================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install core dependencies first
echo "🧠 Installing core ML dependencies..."
pip install torch torchvision numpy matplotlib pandas scikit-learn scipy tqdm

# Install MONAI and medical imaging libraries
echo "🏥 Installing medical imaging libraries..."
pip install monai nibabel pydicom SimpleITK dicom2nifti itk

# Install web framework dependencies
echo "🌐 Installing web framework dependencies..."
pip install fastapi uvicorn[standard] sqlalchemy python-multipart python-dotenv

# Install data processing libraries
echo "📊 Installing data processing libraries..."
pip install pydantic aiofiles Pillow opencv-python-headless

# Install visualization libraries
echo "📈 Installing visualization libraries..."
pip install vtk tensorboard torchmetrics albumentations

# Install development tools
echo "🔧 Installing development tools..."
pip install pytest pytest-asyncio black flake8 jupyter jupyterlab ipywidgets

# Install additional utilities
echo "🛠️  Installing additional utilities..."
pip install requests click python-dateutil pytz cryptography structlog

# Performance optimization
echo "⚡ Installing performance libraries..."
pip install numba psutil

# Optional: Install DICOM handling libraries (Python-based alternatives)
echo "🩻 Installing DICOM handling libraries..."
pip install pynetdicom highdicom

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "🚀 Next steps:"
echo "   1. Activate virtual environment: source venv/bin/activate"
echo "   2. Run the application: ./scripts/utilities/run_gui.sh"
echo "   3. Or start backend only: python src/medical_imaging_api.py"
echo ""
echo "📚 Note: Cornerstone3D DICOM viewing is handled by the React frontend"
echo "    The Python backend uses pydicom and SimpleITK for DICOM processing"
echo ""
echo "🏥 Medical Imaging AI is ready to use!"
