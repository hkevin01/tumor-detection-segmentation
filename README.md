# Tumor Detection and Segmentation using MONAI

This project implements a deep learning pipeline for tumor detection and segmentation in medical images (MRI/CT) using the MONAI framework and PyTorch.

> **🎉 Recently Organized**: This project has been restructured with a clean, professional organization. All scripts, tests, and documentation are now properly organized into dedicated directories following Python project best practices.

## Features

- **Deep Learning Pipeline**: Complete training, evaluation, and inference pipeline
- **Medical Image Processing**: Specialized preprocessing for MRI/CT images
- **Multi-modal Support**: Framework for sensor fusion and multi-modal data integration
- **Clinical Workflow Integration**: Preoperative and postoperative reporting capabilities
- **Patient Analysis**: Longitudinal analysis and comparison with prior scans

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

## Quick Start

1. **Clone and Setup**:
   ```bash
   git clone git@github.com:hkevin01/tumor-detection-segmentation.git
   cd tumor-detection-segmentation
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure**:
   - Edit `config.json` to set data paths and hyperparameters
   - Place your datasets in the `data/` directory

3. **Train a Model**:
   ```bash
   python src/training/train.py
   ```

4. **Run Inference**:
   ```bash
   python src/inference/inference.py
   ```

5. **Run GUI Application**:
   ```bash
   ./scripts/utilities/run_gui.sh
   ```

## Configuration

Edit `config.json` to customize:
- Data paths and preprocessing parameters
- Model architecture and training hyperparameters
- Device settings (CPU/CUDA)
- Logging and output configurations

## Dependencies

This project uses MONAI for medical image processing and PyTorch for deep learning. See `requirements.txt` for the complete dependency list.

## Documentation

Comprehensive documentation is now organized in the `docs/` directory:

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
- **Quick Setup**: `./scripts/setup/quick_setup.sh` - Complete environment setup
- **Enhanced GUI Setup**: `./scripts/setup/setup_enhanced_gui.sh` - GUI system setup
- **Git Setup**: `./scripts/setup/setup_git.sh` - Git workflow configuration

**Utility Scripts** (`scripts/utilities/`):
- **GUI Launcher**: `./scripts/utilities/run_gui.sh` - Start the complete GUI application
- **System Status**: `./scripts/utilities/system_status.sh` - Check system health
- **Git Status**: `./scripts/utilities/git_status.sh` - Quick Git commands and status

**Demo Scripts** (`scripts/demo/`):
- **System Demo**: `python scripts/demo/demo_system.py` - Comprehensive system demonstration

**Development Tools** (`tools/`):
- Project reorganization and maintenance scripts

## Testing

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
- `tests/unit/` - Unit tests (add your unit test files here)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.