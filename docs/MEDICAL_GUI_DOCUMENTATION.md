# Medical Imaging GUI - Comprehensive System Documentation

## 🏥 Overview

This is a complete medical imaging GUI system for tumor detection and segmentation using MONAI (Medical Open Network for AI). The system provides a professional-grade interface for radiologists and medical professionals to analyze medical images with AI assistance.

## 🎯 Key Features

### Core Medical Imaging Components

#### 1. **Advanced DICOM Viewer**
- **Multi-planar Reconstruction**: Axial, sagittal, and coronal views
- **Window/Level Adjustment**: Optimal tissue contrast for different anatomies
- **Interactive Tools**: Zoom, pan, measurement, and annotation tools
- **Cine Mode**: Automated slice navigation through volumes
- **Overlay Support**: Segmentation masks with adjustable opacity
- **DICOM Metadata Display**: Complete patient and study information

#### 2. **AI-Powered Tumor Detection**
- **Real-time Inference**: Live tumor detection and segmentation
- **Multiple AI Models**: UNet, SegResNet, and SwinUNETR architectures
- **Confidence Scoring**: AI confidence levels for clinical decision support
- **Interactive Editing**: Manual refinement of AI segmentations
- **Export Capabilities**: DICOM-SEG and NIfTI format exports

#### 3. **Patient Management System**
- **Comprehensive Patient Records**: Demographics, medical history, and studies
- **Study Browser**: Organized view of all patient imaging studies
- **Timeline Visualization**: Treatment history and imaging progression
- **Longitudinal Analysis**: Automated comparison between studies
- **Clinical Reporting**: Structured report generation

#### 4. **Model Control Panel**
- **Model Management**: Load, unload, and configure AI models
- **Performance Monitoring**: Real-time GPU utilization and memory usage
- **Batch Processing**: Queue multiple studies for analysis
- **Benchmarking Tools**: Performance testing and optimization
- **Parameter Tuning**: Advanced inference configuration

### MONAI-Based AI Backend

#### 1. **Deep Learning Pipeline**
```python
# Supported Model Architectures:
- UNet: Fast and reliable 3D segmentation
- SegResNet: High accuracy with efficient inference  
- SwinUNETR: State-of-the-art transformer-based architecture

# Evaluation Metrics:
- DiceMetric: Overlap-based similarity measure
- HausdorffDistanceMetric: Boundary accuracy assessment
- SurfaceDistanceMetric: Surface-to-surface distance evaluation

# Data Processing:
- Compose transforms for preprocessing pipelines
- CacheDataset for efficient data loading
- Sliding window inference for large 3D volumes
```

#### 2. **Advanced Features**
- **Automated Preprocessing**: DICOM to tensor conversion with normalization
- **Multi-GPU Support**: Distributed inference for faster processing
- **Memory Optimization**: Intelligent batch sizing and caching
- **Error Handling**: Robust pipeline with graceful failure recovery

## 🚀 Installation & Setup

### Prerequisites
- **Python 3.8+** with pip
- **Node.js 18+** with npm
- **CUDA-capable GPU** (recommended for AI inference)
- **8GB+ RAM** (16GB+ recommended)
- **Docker** (optional, for containerized deployment)

### Quick Start

1. **Clone and Setup**
   ```bash
   git clone https://github.com/your-repo/tumor-detection-segmentation.git
   cd tumor-detection-segmentation
   chmod +x start_medical_gui.sh
   ./start_medical_gui.sh
   ```

2. **Manual Installation**
   ```bash
   # Backend setup
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   
   # Frontend setup
   cd frontend
   npm install
   npm run dev
   
   # Start backend
   cd ../src
   python medical_imaging_api.py
   ```

3. **Access the Application**
   - **Frontend GUI**: http://localhost:3000
   - **Backend API**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or use individual containers
docker build -t medical-imaging-backend -f Dockerfile.backend .
docker build -t medical-imaging-frontend -f Dockerfile.frontend ./frontend

docker run -p 8000:8000 medical-imaging-backend
docker run -p 3000:3000 medical-imaging-frontend
```

## 💻 User Interface Guide

### Main Dashboard

The medical imaging GUI consists of several integrated components:

#### 1. **DICOM Viewer Interface**
- **Central Viewport**: Main image display with rendering controls
- **Study Navigator**: Thumbnail view of all slices
- **Tools Panel**: Zoom, pan, window/level, and measurement tools
- **Overlay Controls**: Segmentation display and opacity settings

#### 2. **Patient Management Panel**
- **Patient Browser**: Search and select patients
- **Study Timeline**: Chronological view of imaging studies
- **Comparison Tools**: Side-by-side study comparison
- **Report Generation**: Clinical report creation and export

#### 3. **AI Control Center**
- **Model Selection**: Choose between available AI models
- **Inference Parameters**: Adjust detection sensitivity and processing options
- **Batch Queue**: Monitor and manage bulk processing jobs
- **Performance Metrics**: Real-time system performance monitoring

### Workflow Examples

#### 1. **Single Study Analysis**
```
1. Upload DICOM → 2. Select AI Model → 3. Run Analysis → 
4. Review Results → 5. Export Findings
```

#### 2. **Longitudinal Comparison**
```
1. Load Patient → 2. Select Studies → 3. Run Comparison → 
4. Review Changes → 5. Generate Report
```

#### 3. **Batch Processing**
```
1. Queue Studies → 2. Configure Parameters → 3. Start Batch → 
4. Monitor Progress → 5. Review Results
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# API Configuration
API_HOST=localhost
API_PORT=8000
FRONTEND_PORT=3000

# AI Model Settings
DEFAULT_MODEL=unet
INFERENCE_DEVICE=cuda
MAX_BATCH_SIZE=4
INFERENCE_TIMEOUT=300

# Data Directories
DATA_DIR=./data
LOG_DIR=./logs
TEMP_DIR=./temp

# Security (change in production)
SECRET_KEY=your-secret-key-here
API_KEY=your-api-key-here

# DICOM Settings
DICOM_MAX_FILE_SIZE=100MB
ALLOWED_MODALITIES=MR,CT,PET

# Performance Settings
ENABLE_CACHING=true
CACHE_SIZE=1000
WORKER_PROCESSES=4
```

### Model Configuration

Customize AI model parameters in `src/medical_ai_backend.py`:

```python
config = {
    "models": {
        "unet": {
            "spatial_dims": 3,
            "in_channels": 1,
            "out_channels": 2,
            "channels": (16, 32, 64, 128, 256),
            "strides": (2, 2, 2, 2),
            "num_res_units": 2,
            "dropout": 0.1
        }
    },
    "inference": {
        "roi_size": (96, 96, 96),
        "sw_batch_size": 4,
        "overlap": 0.5,
        "mode": "gaussian"
    }
}
```

## 📊 API Reference

### Core Endpoints

#### Upload DICOM
```http
POST /api/dicom/upload
Content-Type: multipart/form-data

Response:
{
  "dicom_id": "uuid",
  "filename": "study.dcm",
  "metadata": {...},
  "message": "Success"
}
```

#### Run AI Prediction
```http
POST /api/ai/predict
Content-Type: application/json

{
  "dicom_id": "uuid",
  "model_name": "unet",
  "inference_params": {
    "roi_size": [96, 96, 96],
    "sw_batch_size": 4,
    "overlap": 0.5
  }
}
```

#### Compare Studies
```http
GET /api/compare/{dicom_id1}/{dicom_id2}

Response:
{
  "comparison_id": "uuid",
  "study1": {...},
  "study2": {...},
  "changes": {
    "volume_change_mm3": -88.8,
    "volume_change_percent": -7.1,
    "response_assessment": "Partial Response"
  }
}
```

### WebSocket Events

Real-time updates for long-running operations:

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws');

// Listen for inference progress
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.type === 'inference_progress') {
    updateProgressBar(data.progress);
  }
};
```

## 🧪 Testing & Validation

### Unit Tests
```bash
# Run backend tests
python -m pytest tests/

# Run frontend tests
cd frontend && npm test
```

### Integration Tests
```bash
# Test complete workflow
python tests/test_integration.py
```

### Performance Benchmarks
```bash
# Benchmark AI models
python src/benchmark_models.py

# Load testing
python tests/load_test_api.py
```

## 🚀 Deployment

### Production Setup

#### 1. **Environment Configuration**
```bash
# Production environment variables
export NODE_ENV=production
export PYTHONPATH=/app/src
export CUDA_VISIBLE_DEVICES=0,1

# Security settings
export SECRET_KEY=$(openssl rand -hex 32)
export API_KEY=$(openssl rand -hex 16)
```

#### 2. **Database Setup**
```sql
-- PostgreSQL setup for production
CREATE DATABASE medical_imaging;
CREATE USER medical_app WITH ENCRYPTED PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE medical_imaging TO medical_app;
```

#### 3. **Nginx Configuration**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 100M;
    }
}
```

### Monitoring & Logging

#### 1. **Application Monitoring**
```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

INFERENCE_COUNTER = Counter('inference_total', 'Total inferences')
INFERENCE_DURATION = Histogram('inference_duration_seconds', 'Inference duration')
GPU_MEMORY_USAGE = Gauge('gpu_memory_usage_bytes', 'GPU memory usage')
```

#### 2. **Log Configuration**
```python
LOGGING_CONFIG = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'medical_imaging.log',
            'formatter': 'detailed'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        }
    },
    'loggers': {
        'medical_imaging': {
            'handlers': ['file', 'console'],
            'level': 'INFO'
        }
    }
}
```

## 🔒 Security Considerations

### Data Protection
- **HIPAA Compliance**: Patient data encryption at rest and in transit
- **Access Control**: Role-based permissions for different user types
- **Audit Logging**: Complete audit trail of all system actions
- **Data Anonymization**: Automatic PHI removal for research use

### Network Security
- **HTTPS/TLS**: Encrypted communication for all API endpoints
- **API Authentication**: JWT tokens with refresh mechanisms
- **Rate Limiting**: Protection against DoS attacks
- **Input Validation**: Comprehensive input sanitization

## 📈 Performance Optimization

### AI Model Optimization
- **Model Quantization**: Reduce model size for faster inference
- **Mixed Precision**: Use FP16 for better GPU performance
- **Model Pruning**: Remove unnecessary parameters
- **Batch Optimization**: Dynamic batch sizing based on GPU memory

### System Performance
- **Caching Strategy**: Redis for session and result caching
- **Database Optimization**: Indexed queries and connection pooling
- **CDN Integration**: Static asset delivery optimization
- **Load Balancing**: Multiple backend instances for scalability

## 🤝 Contributing

### Development Setup
```bash
# Fork the repository
git clone https://github.com/your-username/tumor-detection-segmentation.git

# Create feature branch
git checkout -b feature/new-feature

# Install development dependencies
pip install -r requirements-dev.txt
cd frontend && npm install --include=dev

# Run tests
python -m pytest
npm test
```

### Code Standards
- **Python**: Follow PEP 8, use black formatter
- **TypeScript**: Use ESLint and Prettier
- **Documentation**: Comprehensive docstrings and comments
- **Testing**: Maintain >80% code coverage

## 📞 Support & Documentation

### Resources
- **API Documentation**: http://localhost:8000/docs
- **User Manual**: `docs/user_manual.pdf`
- **Developer Guide**: `docs/developer_guide.md`
- **Troubleshooting**: `docs/troubleshooting.md`

### Community
- **Issues**: GitHub Issues for bug reports
- **Discussions**: GitHub Discussions for questions
- **Contributions**: Pull requests welcome

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **MONAI Team**: For the excellent medical imaging framework
- **FastAPI**: For the high-performance web framework
- **React/Material-UI**: For the modern frontend components
- **Medical Imaging Community**: For continued feedback and support
