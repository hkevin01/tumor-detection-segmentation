# 🐳 Docker Deployment Guide

## Medical Imaging AI Platform - Complete Docker Setup

This guide provides step-by-step instructions for running the Medical Imaging AI Platform in Docker containers with GUI access.

### 🚀 Quick Start

```bash
# Test Docker setup
./test_docker.sh

# Start all services with GUI
./run.sh start

# View service status
./run.sh status

# Stop all services
./run.sh stop
```

### 📋 Available Services

| Service | URL | Description |
|---------|-----|-------------|
| **Main Application** | http://localhost:8000 | Core medical imaging API and backend |
| **Web GUI** | http://localhost:8000/gui | Interactive web interface |
| **MLflow UI** | http://localhost:5001 | Experiment tracking and model management |
| **MONAI Label** | http://localhost:8001 | Interactive annotation server |

### 🔧 Run Script Commands

```bash
./run.sh start      # Start all services and open GUI
./run.sh stop       # Stop all services
./run.sh restart    # Restart all services
./run.sh status     # Show service status
./run.sh logs       # Show service logs (Ctrl+C to exit)
./run.sh build      # Build Docker images
./run.sh gui        # Open web GUI in browser
./run.sh cleanup    # Stop services and clean up Docker resources
./run.sh help       # Show help message
```

### 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web GUI       │    │  MLflow UI      │    │  MONAI Label    │
│  Port: 8000/gui │    │  Port: 5001     │    │  Port: 8001     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────────────────────────────────────┐
         │            Medical AI Backend                    │
         │              Port: 8000                         │
         └─────────────────────────────────────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
    ┌─────────┐            ┌─────────┐            ┌─────────┐
    │  Redis  │            │PostgreSQL│            │ Volumes │
    │ Port:6379│            │Port: 5432│            │ Storage │
    └─────────┘            └─────────┘            └─────────┘
```

### 🎮 GPU Support

**NVIDIA GPU (CUDA)**:
- Automatically detected by the run script
- Uses `Dockerfile.cuda` for GPU acceleration
- Requires `nvidia-docker` or Docker with GPU support

**AMD GPU (ROCm)**:
- Modify docker-compose.yml to use `Dockerfile.rocm`
- Ensure ROCm drivers are installed

**CPU Only**:
- Falls back automatically if no GPU support detected
- All features remain available (slower performance)

### 📁 Docker Volumes

The setup uses persistent volumes for:

- **model_data**: Trained models and checkpoints
- **logs_data**: Application and training logs
- **mlflow_artifacts**: MLflow experiment artifacts
- **monai_data**: MONAI Label annotation data
- **redis_data**: Redis cache
- **postgres_data**: PostgreSQL database

### 🔍 Service Details

#### Main Application (Port 8000)
- FastAPI backend with medical imaging APIs
- Serves web GUI at `/gui` endpoint
- Health checks at `/health` endpoint
- File upload and inference capabilities

#### MLflow UI (Port 5001)
- Experiment tracking and comparison
- Model registry and versioning
- Metrics visualization and logging
- Artifact storage and retrieval

#### MONAI Label (Port 8001)
- Interactive annotation server
- 3D Slicer integration
- Active learning workflows
- Custom model training strategies

### 🛠️ Customization

#### Environment Variables

```bash
# GPU configuration
CUDA_VISIBLE_DEVICES=0

# MLflow settings
MLFLOW_TRACKING_URI=http://mlflow:5000
MLFLOW_BACKEND_STORE_URI=postgresql://mlflow:mlflow@postgres:5432/mlflow

# MONAI Label settings
MONAI_LABEL_HOST=0.0.0.0
MONAI_LABEL_PORT=8001

# Database settings
DATABASE_URL=postgresql://mlflow:mlflow@postgres:5432/mlflow
REDIS_URL=redis://redis:6379
```

#### Port Configuration

To change default ports, edit `config/docker/docker-compose.yml`:

```yaml
services:
  web:
    ports:
      - "8080:8000"  # Change 8000 to 8080
```

### 🐛 Troubleshooting

#### Service Won't Start
```bash
# Check service logs
./run.sh logs

# Check service status
docker-compose -f config/docker/docker-compose.yml ps

# Restart individual service
docker-compose -f config/docker/docker-compose.yml restart web
```

#### Port Already in Use
```bash
# Find process using port
sudo netstat -tulpn | grep :8000

# Kill process if needed
sudo kill -9 <PID>
```

#### GPU Not Detected
```bash
# Check NVIDIA Docker
docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi

# Install nvidia-docker if needed
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
```

#### Memory Issues
```bash
# Increase Docker memory limit in Docker Desktop
# Or add memory limits to docker-compose.yml:
services:
  web:
    deploy:
      resources:
        limits:
          memory: 8G
```

### 📊 Monitoring

#### Health Checks
All services include health checks:
- Web: `http://localhost:8000/health`
- MLflow: `http://localhost:5001`
- MONAI Label: `http://localhost:8001/info/`

#### Log Monitoring
```bash
# Follow all logs
./run.sh logs

# Follow specific service
docker-compose -f config/docker/docker-compose.yml logs -f web

# View recent logs
docker-compose -f config/docker/docker-compose.yml logs --tail=100 web
```

### 🔐 Security

#### Default Credentials
- PostgreSQL: `mlflow:mlflow`
- Change passwords in production deployment

#### Network Security
- All services run on isolated Docker network
- Only necessary ports exposed to host
- Internal service communication encrypted

### 🚀 Production Deployment

#### SSL/TLS
Add nginx reverse proxy with SSL:

```yaml
nginx:
  image: nginx:alpine
  ports:
    - "443:443"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
    - ./ssl:/etc/nginx/ssl
```

#### Scaling
Use Docker Swarm or Kubernetes for scaling:

```bash
# Docker Swarm
docker swarm init
docker stack deploy -c docker-compose.yml medical-ai

# Kubernetes
kubectl apply -f k8s/
```

### 📋 Maintenance

#### Updates
```bash
# Pull latest images
docker-compose -f config/docker/docker-compose.yml pull

# Rebuild with latest code
./run.sh build

# Restart services
./run.sh restart
```

#### Backup
```bash
# Backup volumes
docker run --rm -v medical-ai-platform_model_data:/data -v $(pwd):/backup alpine tar czf /backup/models.tar.gz /data

# Backup database
docker exec medical-ai-platform_postgres_1 pg_dump -U mlflow mlflow > backup.sql
```

---

## 🎉 Ready to Deploy!

Your Medical Imaging AI Platform is now fully containerized and ready for deployment. Simply run:

```bash
./run.sh start
```

And access the GUI at: **http://localhost:8000/gui**
