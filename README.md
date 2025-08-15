# Medical Imaging AI Platform

Advanced tumor detection and segmentation platform with interactive annotation, multi-modal fusion, and experiment tracking capabilities using MONAI, MLflow, and Docker.

> **🐳 Docker Deployment Ready**: Complete containerized deployment with web GUI, MLflow tracking, and MONAI Label integration. Launch everything with `./run.sh start`

## ✨ Key Features

- **🧠 Advanced AI Models**: Multi-modal UNETR, cascade detection, neural architecture search (DiNTS)
- **🎯 Interactive Annotation**: MONAI Label server with 3D Slicer integration and active learning
- **📊 Experiment Tracking**: MLflow integration with medical imaging metrics and model management
- **🔄 Multi-Modal Fusion**: Cross-attention mechanisms for T1/T1c/T2/FLAIR/CT/PET processing
- **🐳 Production Ready**: Complete Docker deployment with GPU acceleration and web GUI
- **🎨 Web Interface**: Beautiful dashboard at `http://localhost:8000/gui` for all services
- **⚡ GPU Accelerated**: CUDA and ROCm support with automatic CPU fallback

## Project Structure

```text
├── src/                    # Main source code
│   ├── data/              # Data handling and preprocessing
│   ├── training/          # Model training scripts
│   ├── evaluation/        # Model evaluation and metrics
│   ├── inference/         # Inference and prediction
│   ├── reporting/         # Clinical report generation
│   ├── fusion/            # Multi-modal data fusion
│   ├── patient_analysis/  # Patient longitudinal analysis
│   └── utils/             # Utility functions
├── tests/                 # Organized test suites
│   ├── gui/              # GUI and frontend tests
│   └── integration/      # System integration tests
├── scripts/               # Organized utility scripts
│   ├── setup/            # Installation and setup scripts
│   ├── utilities/        # Runtime utilities and GUI launchers
│   └── demo/             # Demo and showcase scripts
├── docs/                  # Structured documentation
│   ├── user-guide/       # User-facing documentation
│   ├── developer/        # Developer documentation
│   └── api/              # API documentation
├── config/                # Configuration management
│   └── docker/           # Docker and containerization configs
├── tools/                 # Development and maintenance tools
├── data/                  # Datasets (not tracked in git)
├── models/                # Trained model checkpoints
├── notebooks/             # Jupyter notebooks for experiments
├── frontend/, gui/        # Frontend components
└── config.json           # Main configuration parameters
```

## 🚀 Quick Start

### Option 1: Docker Deployment (Recommended)

Complete platform with all services in containers:

```bash
# Clone the repository
git clone https://github.com/hkevin01/tumor-detection-segmentation.git
cd tumor-detection-segmentation

# Test Docker setup
./test_docker.sh

# Start all services with web GUI
./run.sh start

# Access the platform:
# - Web GUI: http://localhost:8000/gui
# - MLflow UI: http://localhost:5001
# - MONAI Label: http://localhost:8001
```

### Option 2: Local Development

For development and customization:

```bash
# Setup environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure
# Edit config.json to set data paths and hyperparameters

# Train a model
python src/training/train_enhanced.py --config config/recipes/unetr_multimodal.json

# Run inference
python src/inference/inference.py
```

## 🐳 Docker Services

The platform includes these containerized services:

| Service | URL | Purpose |
|---------|-----|---------|
| **Web GUI** | http://localhost:8000/gui | Interactive dashboard and interface |
| **Main API** | http://localhost:8000 | Core backend API and health checks |
| **MLflow UI** | http://localhost:5001 | Experiment tracking and model management |
| **MONAI Label** | http://localhost:8001 | Interactive annotation server |

### Docker Management

```bash
./run.sh start     # Start all services + open GUI
./run.sh stop      # Stop all services
./run.sh status    # Show service status
./run.sh logs      # View service logs
./run.sh cleanup   # Clean up Docker resources
./run.sh help      # Show all commands
```

## ⚙️ Configuration

The platform includes comprehensive configuration management:

### Main Configuration (`config.json`)

Key settings include:

- **Enhanced Features**: Multi-modal fusion, cascade detection, MONAI Label integration, MLflow tracking
- **Model Architecture**: UNETR, SegResNet, DiNTS neural architecture search
- **Training**: Batch size, learning rate, AMP, distributed training
- **Data Processing**: Modality-specific normalization, curriculum augmentation
- **Services**: MLflow tracking URI, MONAI Label server settings
- **Deployment**: Docker configuration, GPU settings, monitoring

### Configuration Recipes

Pre-configured scenarios in `config/recipes/`:

- `unetr_multimodal.json` - Multi-modal UNETR with cross-attention fusion
- `cascade_detection.json` - Two-stage detection + segmentation pipeline
- `dints_nas.json` - Neural architecture search configuration

### GPU Support

- **NVIDIA GPUs**: CUDA support with automatic detection
- **AMD GPUs**: ROCm support (use `Dockerfile.rocm`)
- **CPU Only**: Automatic fallback for systems without GPU acceleration

## 🏗️ Architecture & Implementation

### AI Models & Algorithms

**Multi-Modal Fusion**:
- Cross-attention mechanisms for T1/T1c/T2/FLAIR/CT/PET
- Early and late fusion strategies
- Adaptive fusion with modality attention gates

**Cascade Detection Pipeline**:
- RetinaUNet3D for initial detection
- High-resolution UNETR for refined segmentation
- Two-stage workflow with post-processing

**Neural Architecture Search**:
- DiNTS (Differentiable Neural Architecture Search)
- Automated model optimization
- Performance-aware architecture selection

### Interactive Annotation

**MONAI Label Integration**:
- 3D Slicer compatibility
- Active learning strategies (random, epistemic, custom)
- Real-time model updates
- Interactive refinement workflows

### Experiment Management

**MLflow Tracking**:
- Medical imaging specific metrics (Dice, IoU, HD95)
- Segmentation overlay visualization
- Model versioning and artifacts
- Comprehensive experiment comparison

### Data Processing

**Enhanced Preprocessing**:
- Modality-specific normalization
- Curriculum augmentation strategies
- Cross-site harmonization
- Advanced data augmentation pipelines

## 📚 Dependencies

Core frameworks and libraries:

- **MONAI**: Medical imaging AI framework with Label server
- **PyTorch**: Deep learning backend with CUDA/ROCm support
- **MLflow**: Experiment tracking and model management
- **FastAPI**: Web API framework for backend services
- **Docker**: Containerization and deployment
- **PostgreSQL**: Database backend for MLflow
- **Redis**: Caching and session management

See `requirements.txt` and `requirements-docker.txt` for complete dependency lists.

## 📖 Documentation

Comprehensive documentation is organized in the `docs/` directory:

**User Documentation** (`docs/user-guide/`):
- **Medical GUI Guide** - Complete interface documentation
- **Setup Guide** - Installation and configuration instructions
- **GitHub Integration** - Repository and collaboration guide

**Developer Documentation** (`docs/developer/`):
- **Implementation Guide** - Technical implementation details
- **Git Workflow** - Development workflow and best practices
- **GUI Development Status** - Frontend/backend development progress
- **DICOM Viewer** - Medical imaging viewer documentation
- **Development Steps** - Project development roadmap

**Additional Resources**:
- API reference and training guides
- Model architecture descriptions
- Clinical workflow integration guides

## Scripts and Utilities

The project includes organized scripts for various tasks:

**Setup Scripts** (`scripts/setup/`):
- **Quick Setup**: `./scripts/setu./scripts/setup/quick_setup.sh` - Complete environment setup
- **Enhanced GUI Setup**: `./scripts/setup/setup_enhanced_gui.sh` - GUI system setup
- **Git Setup**: `./scripts/setup/setup_git.sh` - Git workflow configuration
- **ROCm Setup**: `./scripts/setup/setup_rocm.sh` - AMD GPU/ROCm configuration

**Utility Scripts** (`scripts/utilities/`):
- **GUI Launcher**: `./scripts/utilitie./scripts/utilities/run_gui.sh` - Start the complete GUI application
- **System Status**: `./scripts/utilities/system_status.sh` - Check system health
- **Git Status**: `./scripts/utilitie./scripts/utilities/git_status.sh` - Quick Git commands and status

**Demo Scripts** (`scripts/demo/`):
- **System Demo**: `python scripts/demo/demo_system.py` - Comprehensive system demonstration

**Development Tools** (`tools/`):
- Project reorganization and maintenance scripts

## 🧪 Testing & Validation

### System Validation

```bash
# Test Docker setup
./test_docker.sh

# Validate all features
python test_system.py

# Comprehensive Docker validation
python validate_docker.py
```

### Automated Testing

The project includes organized test suites:

```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/gui/           # GUI and frontend tests
pytest tests/integration/   # System integration tests
```

**Test Structure**:
- `tests/gui/` - GUI backend and frontend integration tests
- `tests/integration/` - Full system integration and workflow tests
- `tests/unit/` - Unit tests for individual components

### Health Monitoring

All Docker services include health checks:
- Web API: `http://localhost:8000/health`
- MLflow: `http://localhost:5001`
- MONAI Label: `http://localhost:8001/info/`

## 🚀 Deployment & Production

### Docker Deployment

The platform is production-ready with:

- **Multi-service Architecture**: Web, MLflow, MONAI Label, Redis, PostgreSQL
- **GPU Acceleration**: CUDA/ROCm support with automatic CPU fallback
- **Persistent Storage**: Docker volumes for models, experiments, and data
- **Health Monitoring**: Automated health checks and service monitoring
- **Scalability**: Ready for multi-node deployment and load balancing

### Deployment Guides

- `DOCKER_GUIDE.md` - Complete Docker deployment instructions
- `DEPLOYMENT.md` - General deployment and configuration guide
- `DOCKER_COMPLETE.md` - Implementation status and architecture overview

### Production Features

- **Web GUI**: Interactive dashboard at `http://localhost:8000/gui`
- **API Endpoints**: RESTful API with OpenAPI documentation
- **Experiment Tracking**: MLflow with PostgreSQL backend
- **Interactive Annotation**: MONAI Label server for clinical workflows
- **Monitoring**: Service health checks and resource monitoring

## 📊 Current Status

✅ **Complete Docker Deployment** - All services containerized and orchestrated
✅ **Web GUI Interface** - Beautiful dashboard for all platform interactions
✅ **MLflow Integration** - Full experiment tracking and model management
✅ **MONAI Label Server** - Interactive annotation with 3D Slicer compatibility
✅ **Multi-Modal AI Models** - Advanced fusion architectures implemented
✅ **Cascade Detection** - Two-stage detection and segmentation pipeline
✅ **GPU Acceleration** - CUDA and ROCm support with automatic detection
✅ **Production Ready** - Health checks, monitoring, and persistent storage

## 🛠️ Development

For developers contributing to the platform:

### Local Development Setup

```bash
# Clone and setup development environment
git clone https://github.com/hkevin01/tumor-detection-segmentation.git
cd tumor-detection-segmentation
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run in development mode
python src/main.py
```

### Docker Development

```bash
# Build and test locally
./run.sh build
./run.sh start

# View logs for debugging
./run.sh logs

# Clean up for fresh start
./run.sh cleanup
```

## 📞 Support & Documentation

- **Quick Start**: `./run.sh help` for all available commands
- **Docker Setup**: `./test_docker.sh` to validate Docker configuration
- **System Status**: `python test_system.py` for comprehensive validation
- **Complete Guides**: See `DOCKER_GUIDE.md` and `DEPLOYMENT.md`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
