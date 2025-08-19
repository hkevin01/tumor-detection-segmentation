# Medical Imaging AI Platform

Advanced tumor detection and segmentation platform with interactive annotation, multi-modal fusion, and experiment tracking capabilities using MONAI, MLflow, and Docker.

> **🐳 Docker Deployment Ready**: Complete containerized deployment with web GUI, MLflow tracking, and MONAI Label integration. Launch everything with `./run.sh start`

## ✨ Key Features

- **🧠 Advanced AI Models**: Multi-modal UNETR, cascade detection, neural architecture search (DiNTS)
- **🎯 Interactive Annotation**: MONAI Label server with 3D Slicer integration and active learning
- **📊 Experiment Tracking**: MLflow integration with medical imaging metrics and model management
- **🔄 Multi-Modal Fusion**: Cross-attention mechanisms for T1/T1c/T2/FLAIR/CT/PET processing
- **� MONAI Dataset Integration**: Built-in support for Medical Segmentation Decathlon (MSD) datasets with auto-download
- **�🐳 Production Ready**: Complete Docker deployment with GPU acceleration and web GUI
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

# Download a MONAI dataset (example: Brain Tumor MSD Task01)
python scripts/data/pull_monai_dataset.py --dataset-id Task01_BrainTumour --root data/msd

# Train with MONAI dataset
python src/training/train_enhanced.py --config config/recipes/unetr_multimodal.json --dataset-config config/datasets/msd_task01_brain.json

# Or configure manually and train
# Edit config.json to set data paths and hyperparameters
python src/training/train_enhanced.py --config config/recipes/unetr_multimodal.json

# Run inference
python src/inference/inference.py
```

## 🐳 Docker Services

The platform includes these containerized services:

| Service | URL | Purpose |
|---------|-----|---------|
| **Web GUI** | <http://localhost:8000/gui> | Interactive dashboard and interface |
| **Main API** | <http://localhost:8000> | Core backend API and health checks |
| **MLflow UI** | <http://localhost:5001> | Experiment tracking and model management |
| **MONAI Label** | <http://localhost:8001> | Interactive annotation server |

### Docker Management

```bash
./run.sh start     # Start all services + open GUI
./run.sh stop      # Stop all services
./run.sh status    # Show service status
./run.sh logs      # View service logs
./run.sh cleanup   # Clean up Docker resources
./run.sh help      # Show all commands
```

## ⚙️ Configuration & Datasets

The platform includes comprehensive configuration management and built-in dataset support:

### MONAI Datasets (Recommended)

Download and use Medical Segmentation Decathlon (MSD) datasets with automatic MONAI integration:

```bash
# Download brain tumor dataset (Task01_BrainTumour)
python scripts/data/pull_monai_dataset.py --dataset-id Task01_BrainTumour --root data/msd

# Download liver tumor dataset (Task03_Liver)
python scripts/data/pull_monai_dataset.py --dataset-id Task03_Liver --root data/msd

# Train with pre-configured dataset recipes
python src/training/train_enhanced.py --config config/recipes/unetr_multimodal.json --dataset-config config/datasets/msd_task01_brain.json
```

**Available Dataset Configs**:

- `config/datasets/msd_task01_brain.json` - Multi-modal MRI brain tumor (T1/T1c/T2/FLAIR)
- `config/datasets/msd_task03_liver.json` - CT liver tumor segmentation

**Key Benefits**:

- **Auto-download**: MONAI handles dataset fetching, verification, and extraction
- **Standardized splits**: Reproducible train/validation splits
- **Smart caching**: CacheDataset/SmartCacheDataset for efficient loading
- **Transform presets**: Modality-specific preprocessing pipelines

### Training Configuration (`config.json`)

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

### Dataset Integration Options

**MONAI Datasets (Recommended)**:

- Medical Segmentation Decathlon (MSD) with auto-download
- Standardized transforms and caching strategies
- Built-in train/validation splits

**Hugging Face Datasets (Optional)**:

- Community-hosted medical imaging datasets
- BraTS variants, LiTS, LIDC-IDRI subsets
- Requires HF account and license acceptance for some datasets

**Custom Datasets**:

- BIDS-compatible layouts supported
- Flexible configuration for various modalities

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

- **MONAI**: Medical imaging AI framework with Label server and Decathlon dataset support
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
- **MONAI Tests** - MONAI dataset integration testing guide
- **Roadmap (Planning)** - See `docs/developer/roadmap.md` for planned work
- **Experiments & Baselines** - See `docs/developer/experiments.md` for reproducible runs

**Additional Resources**:

- API reference and training guides
- Model architecture descriptions
- Clinical workflow integration guides

## Scripts and Utilities

The project includes organized scripts for various tasks:

**Setup Scripts** (`scripts/setup/`):

- **Quick Setup**: `./scripts/setup/quick_setup.sh` - Complete environment setup
- **Enhanced GUI Setup**: `./scripts/setup/setup_enhanced_gui.sh` - GUI system setup
- **Git Setup**: `./scripts/setup/setup_git.sh` - Git workflow configuration
- **ROCm Setup**: `./scripts/setup/setup_rocm.sh` - AMD GPU/ROCm configuration

**Utility Scripts** (`scripts/utilities/`):

- **GUI Launcher**: `./scripts/utilities/run_gui.sh` - Start the complete GUI application
- **System Status**: `./scripts/utilities/system_status.sh` - Check system health
- **Git Status**: `./scripts/utilities/git_status.sh` - Quick Git commands and status

**Demo Scripts** (`scripts/demo/`):

- **System Demo**: `python scripts/demo/demo_system.py` - Comprehensive system demonstration
- **MONAI Integration Tests**: `python scripts/demo/test_monai_integration.py` - MONAI dataset testing suite

**Development Tools** (`tools/`):

- Project reorganization and maintenance scripts

## 🔬 Dataset Usage Examples

### Quick Start with MONAI Datasets

**Brain Tumor Segmentation (Multi-modal MRI)**:

```bash
# Download MSD Task01 (BraTS-like: T1, T1c, T2, FLAIR → tumor labels)
python scripts/data/pull_monai_dataset.py --dataset-id Task01_BrainTumour

# Train UNETR with multi-modal fusion
python src/training/train_enhanced.py \
  --config config/recipes/unetr_multimodal.json \
  --dataset-config config/datasets/msd_task01_brain.json \
  --amp
```

**Liver Tumor Segmentation (CT)**:

```bash
# Download MSD Task03 (CT → liver + tumor labels)
python scripts/data/pull_monai_dataset.py --dataset-id Task03_Liver

# Train with CT-specific transforms
python src/training/train_enhanced.py \
  --config config/recipes/unetr_multimodal.json \
  --dataset-config config/datasets/msd_task03_liver.json
```

**Dataset Features**:

- **Automatic Download**: MONAI handles fetching and verification
- **Smart Caching**: Efficient loading with CacheDataset/SmartCacheDataset
- **Modality-Aware Transforms**: Brain (4-channel MRI) vs CT (1-channel) preprocessing
- **Reproducible Splits**: Deterministic train/validation partitioning

## 🧪 Testing & Validation

### System Validation

```bash
# Test Docker setup
./test_docker.sh

# Validate all features
python test_system.py

# Comprehensive Docker validation
python validate_docker.py

# Test MONAI dataset integration
python scripts/demo/test_monai_integration.py
```

### MONAI Dataset Tests

The platform includes comprehensive tests for MONAI dataset integration:

```bash
# Run MONAI-specific tests
pytest -m cpu  # CPU-only tests (CI-compatible)

# Individual test suites
pytest tests/unit/test_transforms_presets.py      # Transform validation
pytest tests/integration/test_monai_msd_loader.py # Dataset loading tests

# Environment check
python test_monai_imports.py  # Verify dependencies
```

**MONAI Test Features**:

- **Fast & Lightweight**: Creates synthetic datasets (32x32x32 voxels) for testing
- **CI-Compatible**: CPU-only tests that run without GPU or large downloads
- **Comprehensive**: Validates transforms, dataset loading, and model compatibility
- **Production-Ready**: Includes UNet forward pass validation

### Automated Testing & CI/CD

The project includes comprehensive testing and a modern CI/CD pipeline:

```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/gui/           # GUI and frontend tests
pytest tests/integration/   # System integration tests
pytest tests/unit/          # Unit tests for individual components

# Code quality checks (run locally)
ruff check .                # Fast linting
black . --check --diff      # Format checking
mypy src                    # Type checking
```

**Test Structure**:

- `tests/gui/` - GUI backend and frontend integration tests
- `tests/integration/` - Full system integration and workflow tests
- `tests/unit/` - Unit tests for individual components

**CI/CD Pipeline Features**:

- **Code Quality**: Ruff, Black, and Mypy checks for modern Python development
- **Security**: Trivy vulnerability scanning for filesystem and container images
- **Supply Chain**: SBOM (Software Bill of Materials) generation with Syft
- **Testing**: Comprehensive test suites with coverage reporting
- **MONAI Integration**: Dedicated CPU-only MONAI dataset tests in CI
- **Artifacts**: Security reports and SBOMs uploaded to GitHub Security tab

### Inference and Visualization

- Enable test-time augmentation in the CLI by adding the `--tta` flag:

```bash
python src/inference/inference.py --config config/recipes/unetr_multimodal.json --model models/unetr/checkpoint.pt --tta
```

- The GUI backend exposes an overlay endpoint to preview labeled tumors for a study:

```text
GET /api/studies/{study_id}/overlay
```

This returns a PNG overlay combining the input image and the latest prediction mask.

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
✅ **MONAI Dataset Support** - Built-in MSD dataset integration with auto-download
✅ **MONAI Test Suite** - Comprehensive CPU-only tests for dataset integration
✅ **Multi-Modal AI Models** - Advanced fusion architectures implemented
✅ **Cascade Detection** - Two-stage detection and segmentation pipeline
✅ **GPU Acceleration** - CUDA and ROCm support with automatic detection
✅ **Modern CI/CD** - Ruff/Black/Mypy, SBOM generation, and security scanning
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
