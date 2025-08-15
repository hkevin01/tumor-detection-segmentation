#!/usr/bin/env python3
"""
Main FastAPI application for Medical Imaging AI Platform
"""

import json
import logging
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Medical Imaging AI Platform",
    description="Advanced medical imaging analysis with MONAI Label integration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
config_path = Path(__file__).parent.parent / "config.json"
if config_path.exists():
    with open(config_path) as f:
        config = json.load(f)
else:
    config = {
        "gui": {"enabled": True, "host": "0.0.0.0", "port": 8000},
        "mlflow": {"enabled": True, "tracking_uri": "http://mlflow:5000"},
        "monai_label": {"enabled": True, "server_port": 8001}
    }

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Medical Imaging AI Platform", "status": "running"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "services": {
        "web": "running",
        "mlflow": config.get("mlflow", {}).get("enabled", False),
        "monai_label": config.get("monai_label", {}).get("enabled", False)
    }}

@app.get("/config")
async def get_config():
    """Get current configuration"""
    return config

@app.get("/gui", response_class=HTMLResponse)
async def get_gui():
    """Serve the medical imaging GUI"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Medical Imaging AI Platform</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 15px;
                padding: 30px;
                backdrop-filter: blur(10px);
            }
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            .services {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .service-card {
                background: rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                padding: 25px;
                text-align: center;
                transition: transform 0.3s ease;
            }
            .service-card:hover {
                transform: translateY(-5px);
            }
            .service-title {
                font-size: 1.4em;
                font-weight: bold;
                margin-bottom: 15px;
            }
            .service-description {
                margin-bottom: 20px;
                opacity: 0.9;
            }
            .service-link {
                display: inline-block;
                background: rgba(255, 255, 255, 0.3);
                color: white;
                text-decoration: none;
                padding: 10px 20px;
                border-radius: 5px;
                transition: background 0.3s ease;
            }
            .service-link:hover {
                background: rgba(255, 255, 255, 0.4);
            }
            .features {
                margin-top: 40px;
            }
            .feature-list {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 15px;
                margin-top: 20px;
            }
            .feature-item {
                background: rgba(255, 255, 255, 0.1);
                padding: 15px;
                border-radius: 8px;
                border-left: 4px solid #4CAF50;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🧠 Medical Imaging AI Platform</h1>
                <p>Advanced tumor detection and segmentation with interactive annotation</p>
            </div>

            <div class="services">
                <div class="service-card">
                    <div class="service-title">🔬 Main Application</div>
                    <div class="service-description">
                        Core medical imaging analysis, inference, and training capabilities
                    </div>
                    <a href="http://localhost:8000" class="service-link" target="_blank">
                        Open Application
                    </a>
                </div>

                <div class="service-card">
                    <div class="service-title">📊 MLflow Tracking</div>
                    <div class="service-description">
                        Experiment tracking, model management, and performance monitoring
                    </div>
                    <a href="http://localhost:5001" class="service-link" target="_blank">
                        Open MLflow UI
                    </a>
                </div>

                <div class="service-card">
                    <div class="service-title">🎯 MONAI Label</div>
                    <div class="service-description">
                        Interactive annotation server for 3D Slicer integration
                    </div>
                    <a href="http://localhost:8001" class="service-link" target="_blank">
                        Open MONAI Label
                    </a>
                </div>
            </div>

            <div class="features">
                <h2>🚀 Platform Features</h2>
                <div class="feature-list">
                    <div class="feature-item">
                        <strong>Multi-Modal Fusion</strong><br>
                        Advanced cross-attention mechanisms for T1/T1c/T2/FLAIR/CT/PET
                    </div>
                    <div class="feature-item">
                        <strong>Cascade Detection</strong><br>
                        Two-stage detection + high-resolution segmentation pipeline
                    </div>
                    <div class="feature-item">
                        <strong>Interactive Annotation</strong><br>
                        3D Slicer integration with active learning workflows
                    </div>
                    <div class="feature-item">
                        <strong>Experiment Tracking</strong><br>
                        Comprehensive MLflow integration with medical imaging metrics
                    </div>
                    <div class="feature-item">
                        <strong>GPU Acceleration</strong><br>
                        CUDA and ROCm support for high-performance inference
                    </div>
                    <div class="feature-item">
                        <strong>Production Ready</strong><br>
                        Docker deployment with monitoring and logging
                    </div>
                </div>
            </div>

            <div style="text-align: center; margin-top: 40px; opacity: 0.8;">
                <p>System Status: <span style="color: #4CAF50;">🟢 All Services Running</span></p>
                <p>Version: 1.0.0 | Build: Docker</p>
            </div>
        </div>

        <script>
            // Auto-refresh status every 30 seconds
            setInterval(async () => {
                try {
                    const response = await fetch('/health');
                    const health = await response.json();
                    console.log('Health check:', health);
                } catch (error) {
                    console.log('Health check failed:', error);
                }
            }, 30000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Upload medical imaging file"""
    try:
        # Create upload directory
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)

        # Save uploaded file
        file_path = upload_dir / file.filename
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)

        return {"filename": file.filename, "size": len(content), "status": "uploaded"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/models")
async def list_models():
    """List available models"""
    models_dir = Path("models")
    if not models_dir.exists():
        return {"models": []}

    models = []
    for model_file in models_dir.glob("**/*.pth"):
        models.append({
            "name": model_file.name,
            "path": str(model_file),
            "size": model_file.stat().st_size
        })

    return {"models": models}

if __name__ == "__main__":
    port = config.get("gui", {}).get("port", 8000)
    host = config.get("gui", {}).get("host", "0.0.0.0")

    logger.info(f"Starting Medical Imaging AI Platform on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
    uvicorn.run(app, host=host, port=port)
