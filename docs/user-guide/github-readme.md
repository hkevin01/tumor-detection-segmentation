# Tumor Detection & Segmentation System

🏥 **Professional medical imaging system with AI-powered tumor detection and comprehensive DICOM viewer integration**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![PyTorch](https://img.shields.io/badge/PyTorch-%23EE4C2C.svg?style=flat&logo=PyTorch&logoColor=white)](https://pytorch.org/)
[![MONAI](https://img.shields.io/badge/MONAI-medical%20imaging-green)](https://monai.io/)

## 🎯 Project Overview

A comprehensive medical imaging solution that combines state-of-the-art deep learning with professional clinical tools. Built for radiologists, researchers, and healthcare professionals who need reliable tumor detection and analysis capabilities.

### ✨ Key Features

- 🧠 **AI-Powered Detection**: MONAI-based deep learning for accurate tumor segmentation
- 🏥 **Professional DICOM Viewer**: Cornerstone3D integration with medical-grade tools
- 📊 **Clinical Dashboard**: Complete study management and patient workflow
- 🔬 **Research Ready**: Extensible framework for medical imaging research
- 🌐 **Web-Based Interface**: Modern React frontend with clinical-grade UX
- 📋 **Automated Reporting**: Clinical report generation with AI insights

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- Node.js 16 or higher
- CUDA-compatible GPU (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone git@github.com:hkevin01/tumor-detection-segmentation.git
   cd tumor-detection-segmentation
   ```

2. **Set up the enhanced system**
   ```bash
   chmod +x setup_enhanced_gui.sh
   ./setup_enhanced_gui.sh
   ```

3. **Launch the application**
   ```bash
   ./start_enhanced_gui.sh
   ```

4. **Access the interface**
   - 🖥️ **Clinical Interface**: http://localhost:3000
   - 📚 **API Documentation**: http://localhost:8000/docs

## 🏗️ Architecture

```
🏥 Medical Imaging System
├── 🧠 AI/ML Core (MONAI + PyTorch)
├── 🏥 DICOM Viewer (Cornerstone3D)
├── 🖥️ Web Interface (React + Material-UI)
├── ⚙️ Backend API (FastAPI)
└── 📊 Clinical Workflow Tools
```

## 📁 Project Structure

```
├── src/                    # Core AI/ML pipeline
│   ├── data/              # Data processing and datasets
│   ├── training/          # Model training framework
│   ├── evaluation/        # Performance evaluation
│   └── inference/         # Model inference engine
├── gui/                   # Web interface
│   ├── backend/          # FastAPI backend
│   └── frontend/         # React frontend with DICOM viewer
├── models/               # Trained model checkpoints
├── data/                 # Medical imaging datasets
└── docs/                 # Comprehensive documentation
```

## 🔬 Technologies

### AI/ML Stack
- **[MONAI](https://monai.io/)**: Medical imaging AI framework
- **[PyTorch](https://pytorch.org/)**: Deep learning backend
- **[NumPy](https://numpy.org/)**: Numerical computing
- **[scikit-learn](https://scikit-learn.org/)**: Machine learning utilities

### Medical Imaging
- **[Cornerstone3D](https://cornerstonejs.org/)**: Professional DICOM viewer
- **[DICOM](https://www.dicomstandard.org/)**: Medical imaging standard
- **[pydicom](https://pydicom.github.io/)**: DICOM file handling

### Web Technologies
- **[React](https://reactjs.org/)**: Frontend framework
- **[TypeScript](https://www.typescriptlang.org/)**: Type-safe development
- **[Material-UI](https://mui.com/)**: Professional UI components
- **[FastAPI](https://fastapi.tiangolo.com/)**: High-performance API framework

## 📖 Documentation

- 📚 **[Installation Guide](./INSTALLATION.md)**: Complete setup instructions
- 🔧 **[API Documentation](http://localhost:8000/docs)**: Interactive API reference
- 🏥 **[DICOM Viewer Guide](./gui/README_ENHANCED.md)**: Medical imaging viewer documentation
- 🧪 **[Development Guide](./CONTRIBUTING.md)**: Contributing and development setup

## 🏥 Clinical Features

### Professional DICOM Viewer
- Multi-planar reconstruction (MPR)
- Medical imaging tools (window/level, zoom, pan)
- Measurement and annotation capabilities
- AI detection overlay visualization

### Clinical Workflow
- Patient and study management
- DICOM file upload and processing
- Real-time AI analysis
- Automated clinical reporting
- Study comparison and review

### AI Analysis
- Tumor detection and segmentation
- Confidence scoring and visualization
- Interactive result examination
- Export capabilities for clinical use

## 🧪 Testing

Run the test suite:
```bash
python -m pytest tests/
```

For GUI testing:
```bash
cd gui/frontend && npm test
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

## 📞 Support

- 🐛 **Issues**: [GitHub Issues](https://github.com/hkevin01/tumor-detection-segmentation/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/hkevin01/tumor-detection-segmentation/discussions)
- 📧 **Contact**: [Project Maintainers](mailto:your-email@example.com)

## 🏆 Acknowledgments

- **[MONAI](https://monai.io/)** - Medical imaging AI framework
- **[Cornerstone3D](https://cornerstonejs.org/)** - Professional medical image viewer
- **[OHIF](https://ohif.org/)** - Open Health Imaging Foundation
- Medical imaging community and contributors

---

**🏥 Built for medical professionals, researchers, and healthcare innovation**

[⭐ Star this repository](https://github.com/hkevin01/tumor-detection-segmentation/stargazers) | [🍴 Fork it](https://github.com/hkevin01/tumor-detection-segmentation/fork) | [📋 Report Issues](https://github.com/hkevin01/tumor-detection-segmentation/issues)
