# Tumor Detection GUI System

A clinical web interface for AI-powered tumor detection and segmentation, built with FastAPI backend and React frontend.

## 🏥 Overview

This GUI system provides medical professionals with an intuitive web interface to:
- Upload and manage DICOM medical images
- Run AI-powered tumor detection analysis
- View and interpret AI results with confidence scores
- Generate clinical reports
- Manage patient studies and history

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+ (for frontend development)
- pip or conda package manager

### Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the Backend Server**
   ```bash
   python start_gui.py
   ```

3. **Access the Interface**
   - Open your browser and go to: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Interactive API: http://localhost:8000/redoc

## 📋 Features

### ✅ Implemented (Backend)
- FastAPI web server with automatic documentation
- DICOM file upload and validation
- RESTful API endpoints for clinical workflow
- In-memory data storage for development
- Patient and study management
- AI model integration framework
- Clinical report generation
- Health monitoring and logging

### 🔄 In Development (Frontend)
- React-based clinical interface
- DICOM image viewer integration
- Real-time AI processing status
- Interactive tumor visualization
- Clinical reporting dashboard

### 📅 Planned Features
- Database integration (PostgreSQL)
- User authentication and authorization
- Multi-tenant support for hospitals
- Advanced AI model management
- PACS integration
- Audit logging and compliance

## 🔧 API Endpoints

### Core Endpoints
- `GET /` - API status and information
- `GET /api/health` - Health check
- `POST /api/upload` - Upload DICOM files
- `GET /api/studies` - List medical studies
- `POST /api/predict` - Run AI tumor detection
- `POST /api/reports` - Generate clinical reports
- `GET /api/models` - List available AI models
- `GET /api/patients` - Patient management

### Example Usage

**Upload a DICOM file:**
```bash
curl -X POST "http://localhost:8000/api/upload" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@path/to/scan.dcm"
```

**Run tumor detection:**
```bash
curl -X POST "http://localhost:8000/api/predict" \
  -H "Content-Type: application/json" \
  -d '{"study_id": "study_001", "model_id": "unet_v1"}'
```

## 🏗️ Architecture

```
gui/
├── backend/               # FastAPI backend
│   ├── main.py           # Main application
│   ├── models.py         # Data models
│   └── api/
│       └── routes.py     # API endpoints
├── frontend/             # React frontend (planned)
│   ├── src/
│   ├── public/
│   └── package.json
└── shared/               # Shared utilities
```

### Backend Components

1. **FastAPI Application** (`main.py`)
   - Web server setup and configuration
   - CORS middleware for frontend integration
   - Static file serving
   - Route registration

2. **Data Models** (`models.py`)
   - Patient, Study, and Report models
   - Database abstraction layer
   - In-memory storage for development

3. **API Routes** (`api/routes.py`)
   - RESTful endpoints for clinical workflow
   - File upload handling
   - AI integration points
   - Report generation

## 🔧 Configuration

The system uses `config.json` for configuration. Key GUI settings:

```json
{
  "gui": {
    "host": "localhost",
    "port": 8000,
    "cors_origins": ["http://localhost:3000"],
    "max_upload_size": 104857600,
    "upload_directory": "./uploads"
  },
  "security": {
    "secret_key": "your-secret-key",
    "algorithm": "HS256",
    "access_token_expire_minutes": 1440
  },
  "dicom": {
    "supported_modalities": ["CT", "MR", "PT"],
    "max_series_size": 1000
  }
}
```

## 🧪 Development

### Running in Development Mode
```bash
# Start with auto-reload
python start_gui.py

# Or run directly
cd gui/backend
python main.py
```

### Testing
```bash
# Test the API
curl http://localhost:8000/api/health

# View API documentation
open http://localhost:8000/docs
```

### Adding New Features

1. **Add API Endpoint**
   - Define route in `api/routes.py`
   - Add data validation models
   - Implement business logic

2. **Add Data Model**
   - Define model in `models.py`
   - Add to storage layer
   - Update API responses

3. **Configure Settings**
   - Add configuration in `config.json`
   - Update validation in application

## 📊 Integration with AI Pipeline

The GUI integrates with the existing tumor detection pipeline:

```python
# Integration example (TODO: implement)
from inference.inference import TumorPredictor

predictor = TumorPredictor(
    model_path="./models/unet_v1.pth",
    config_path="config.json"
)

result = predictor.predict_single("path/to/dicom/file.dcm")
```

## 🔒 Security Features

- File type validation for uploads
- Path traversal protection
- CORS configuration
- Input sanitization
- Error handling without information disclosure

## 📝 Clinical Workflow

1. **Upload DICOM Study**
   - Medical technician uploads patient scan
   - System validates file format and metadata
   - Study is registered in the system

2. **AI Analysis**
   - Radiologist initiates AI processing
   - System runs tumor detection algorithm
   - Results are stored with confidence metrics

3. **Review Results**
   - AI findings are overlaid on medical images
   - Radiologist reviews and validates results
   - Manual adjustments can be made if needed

4. **Generate Report**
   - Clinical report is generated from AI findings
   - Report includes recommendations and follow-up
   - PDF export for medical records

## 🐛 Troubleshooting

### Common Issues

**"FastAPI not available" error:**
```bash
pip install fastapi uvicorn python-multipart
```

**"Import utils.utils could not be resolved":**
- Ensure you're running from the project root
- Check that src/ directory is in Python path

**"Permission denied" on uploads:**
```bash
mkdir -p uploads
chmod 755 uploads
```

**Configuration errors:**
- Verify config.json exists and is valid JSON
- Check file permissions for configuration file

### Logging
- Logs are stored in `./logs/` directory
- Use `tail -f logs/app.log` to monitor in real-time
- Adjust log level in configuration

## 🚀 Production Deployment

### Docker Deployment (Planned)
```bash
# Build container
docker build -t tumor-detection-gui .

# Run container
docker run -p 8000:8000 tumor-detection-gui
```

### Environment Variables
```bash
export TUMOR_DETECTION_CONFIG=/path/to/config.json
export TUMOR_DETECTION_LOG_LEVEL=INFO
export TUMOR_DETECTION_SECRET_KEY=your-production-secret
```

### Database Setup (Planned)
```bash
# PostgreSQL setup
pip install psycopg2-binary
export DATABASE_URL=postgresql://user:pass@localhost/tumor_detection
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

### Code Style
- Follow PEP 8 for Python code
- Use type hints where possible
- Add docstrings for public methods
- Keep line length under 80 characters

## 📄 License

This project is part of the tumor detection and segmentation system. Please refer to the main project license.

## 🆘 Support

For technical support or questions:
1. Check the troubleshooting section above
2. Review API documentation at `/docs`
3. Check application logs in `./logs/`
4. Create an issue in the project repository

---

**Status**: ✅ Backend Functional | 🔄 Frontend In Development | 📅 Database Integration Planned
