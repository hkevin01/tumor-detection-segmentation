"""
FastAPI backend for tumor detection GUI application.

This module provides a web API interface for the tumor detection and 
segmentation system, enabling clinical integration through a modern web interface.
"""

import sys
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

try:
    from fastapi import FastAPI, HTTPException, UploadFile, File
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles
    import uvicorn
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

import asyncio
from datetime import datetime
import logging

from utils.utils import load_config, setup_logging, get_device

# Initialize logging
logger = setup_logging(log_dir="./logs", log_level="INFO")

class TumorDetectionAPI:
    """Main API class for the tumor detection web interface."""
    
    def __init__(self, config_path: str = "config.json"):
        """Initialize the API with configuration."""
        if not FASTAPI_AVAILABLE:
            raise ImportError(
                "FastAPI not available. Install with: "
                "pip install fastapi uvicorn python-multipart"
            )
        
        # Load configuration
        self.config = load_config(config_path)
        self.gui_config = self.config.get("gui", {})
        
        # Initialize FastAPI app
        self.app = FastAPI(
            title="Tumor Detection & Segmentation API",
            description="Clinical interface for AI-powered tumor detection",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # Setup CORS
        self._setup_cors()
        
        # Setup routes
        self._setup_routes()
        
        # Setup static files
        self._setup_static_files()
        
        logger.info("Tumor Detection API initialized successfully")
    
    def _setup_cors(self):
        """Configure CORS settings."""
        origins = self.gui_config.get("cors_origins", ["http://localhost:3000"])
        
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    def _setup_static_files(self):
        """Setup static file serving."""
        # Serve uploaded files
        uploads_dir = Path("./uploads")
        uploads_dir.mkdir(exist_ok=True)
        self.app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), 
                      name="uploads")
        
        # Serve frontend build (in production)
        frontend_build = Path("./gui/frontend/build")
        if frontend_build.exists():
            self.app.mount("/", StaticFiles(directory=str(frontend_build), 
                          html=True), name="frontend")
    
    def _setup_routes(self):
        """Setup API routes."""
        
        @self.app.get("/")
        async def root():
            """Root endpoint."""
            return {
                "message": "Tumor Detection & Segmentation API",
                "version": "1.0.0",
                "status": "running",
                "timestamp": datetime.now().isoformat()
            }
        
        # Include API routes
        try:
            from api.routes import get_router
            api_router = get_router()
            self.app.include_router(api_router, prefix="/api")
            logger.info("API routes included successfully")
        except ImportError as e:
            logger.warning(f"Could not import API routes: {e}")
            # Add basic fallback routes
            self._setup_fallback_routes()
    
    def _setup_fallback_routes(self):
        """Setup basic fallback routes when full API is not available."""
        
        @self.app.get("/api/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "device": get_device(),
                "timestamp": datetime.now().isoformat()
            }
        
        @self.app.post("/api/upload")
        async def upload_file(file: UploadFile = File(...)):
            """Basic file upload endpoint."""
            try:
                if not file.filename.lower().endswith(('.dcm', '.dicom')):
                    raise HTTPException(
                        status_code=400,
                        detail="Only DICOM files (.dcm, .dicom) are supported"
                    )
                
                uploads_dir = Path("./uploads")
                uploads_dir.mkdir(exist_ok=True)
                
                file_path = uploads_dir / file.filename
                with open(file_path, "wb") as buffer:
                    content = await file.read()
                    buffer.write(content)
                
                logger.info(f"File uploaded: {file_path}")
                
                return {
                    "message": "File uploaded successfully",
                    "filename": file.filename,
                    "file_path": str(file_path),
                    "size": len(content),
                    "upload_time": datetime.now().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Upload failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))


def create_app(config_path: str = "config.json") -> FastAPI:
    """Factory function to create FastAPI app."""
    api = TumorDetectionAPI(config_path)
    return api.app


def main():
    """Main function to run the API server."""
    if not FASTAPI_AVAILABLE:
        print("Error: FastAPI not available.")
        print("Install with: pip install fastapi uvicorn python-multipart")
        return
    
    # Load configuration
    try:
        config = load_config("config.json")
        gui_config = config.get("gui", {})
    except Exception as e:
        print(f"Failed to load configuration: {e}")
        gui_config = {"host": "localhost", "port": 8000}
    
    # Create app
    app = create_app()
    
    # Run server
    host = gui_config.get("host", "localhost")
    port = gui_config.get("port", 8000)
    
    print(f"Starting Tumor Detection API server...")
    print(f"Server will be available at: http://{host}:{port}")
    print(f"API documentation: http://{host}:{port}/docs")
    
    uvicorn.run(
        "main:create_app",
        host=host,
        port=port,
        reload=True,
        factory=True
    )


if __name__ == "__main__":
    main()
