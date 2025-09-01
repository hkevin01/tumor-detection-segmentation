# 🐳 Docker Setup Guide - Tumor Detection & Segmentation

## Quick Start with Docker

The project now runs entirely in Docker containers. No virtual environment needed!

### Prerequisites

- **Docker** (version 20.10+)
- **Docker Compose** (version 2.0+)
- **NVIDIA Docker** (for GPU support)

### 🚀 Getting Started

1. **Clone and navigate to project:**
   ```bash
   cd /home/kevin/Projects/tumor-detection-segmentation
   ```

2. **Start development environment:**
   ```bash
   ./docker-manager.sh dev
   ```

3. **Access the development container:**
   ```bash
   ./docker-manager.sh exec
   ```

### 🛠️ Available Commands

The `docker-manager.sh` script provides all necessary commands:

```bash
# Build all Docker images
./docker-manager.sh build

# Development environment
./docker-manager.sh dev

# Run tests in container
./docker-manager.sh test

# Start Jupyter Lab
./docker-manager.sh jupyter

# Production environment
./docker-manager.sh prod

# Full stack (with DB, Cache, MLOps)
./docker-manager.sh stack

# View logs
./docker-manager.sh logs

# Stop all services
./docker-manager.sh stop

# Cleanup everything
./docker-manager.sh clean

# Show help
./docker-manager.sh help
```

### 🧪 Running Tests

Tests now run in isolated Docker containers:

```bash
# Run all tests
./docker-manager.sh test

# Run specific tests in dev container
./docker-manager.sh exec tumor-detection-dev python -m pytest tests/integration/ -v

# Run tests with coverage
./docker-manager.sh exec tumor-detection-dev python -m pytest tests/ --cov=src --cov-report=html
```

### 💻 Development Workflow

1. **Start development container:**
   ```bash
   ./docker-manager.sh dev
   ```

2. **Access container shell:**
   ```bash
   ./docker-manager.sh exec
   ```

3. **Inside container, run your commands:**
   ```bash
   # Run tests
   python -m pytest tests/ -v

   # Start FastAPI development server
   uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

   # Run training
   python -m src.training.train --config config/training.yaml

   # Run inference
   python -m src.inference.inference --model models/best_model.pth --input data/test_image.nii.gz
   ```

### 📊 Jupyter Development

Start Jupyter Lab in a separate container:

```bash
./docker-manager.sh jupyter
```

Access at: http://localhost:8889

### 🌐 Service URLs

When running, access these services:

- **FastAPI (Development):** http://localhost:8000
- **FastAPI (Production):** http://localhost:8080
- **Jupyter Lab:** http://localhost:8889
- **TensorBoard:** http://localhost:6006
- **MLFlow:** http://localhost:5000
- **PostgreSQL:** localhost:5432
- **Redis:** localhost:6379

### 📁 Data Management

Data is persisted in Docker volumes:

```bash
# Backup all data
./docker-manager.sh backup

# Restore from backup
./docker-manager.sh restore /path/to/backup

# Check volume status
docker volume ls | grep tumor
```

### 🏗️ Docker Architecture

The project uses multi-stage Docker builds:

- **base:** Common dependencies and CUDA support
- **development:** Full development environment with tools
- **production:** Minimal production image
- **testing:** Testing environment with test dependencies

### 🔧 Environment Configuration

Copy and customize the environment file:

# Create environment file inside docker/
```bash
cp docker/.env.example docker/.env
# Edit docker/.env with your specific configuration or use docker-compose env_file
```

### 🐛 Troubleshooting

**Container not starting:**
```bash
# Check logs
./docker-manager.sh logs tumor-detection-dev

# Rebuild images
./docker-manager.sh build
```

**GPU not available:**
```bash
# Check NVIDIA Docker installation
docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi

# Verify GPU in container
./docker-manager.sh exec tumor-detection-dev nvidia-smi
```

**Permission issues:**
```bash
# Fix file permissions
sudo chown -R $USER:$USER .
```

### 📦 Container Management

**View running containers:**
```bash
./docker-manager.sh status
```

**Clean up resources:**
```bash
./docker-manager.sh clean
```

**Access container directly:**
```bash
docker-compose exec tumor-detection-dev bash
```

### 🔒 Production Deployment

For production deployment:

```bash
# Start production stack
./docker-manager.sh prod

# With full infrastructure
./docker-manager.sh stack
```

The production container runs as a non-root user for security.

### 💡 Benefits of Docker Setup

✅ **Consistent Environment:** Same environment across development, testing, and production
✅ **Isolated Dependencies:** No conflicts with system packages
✅ **GPU Support:** NVIDIA CUDA ready out of the box
✅ **Scalable:** Easy to scale horizontally
✅ **Reproducible:** Exact same setup for all team members
✅ **Easy Cleanup:** Remove everything with one command

---

🎉 **Virtual environment removed!** Everything now runs in Docker containers.

For detailed documentation, see the individual files:
- `Dockerfile` - Container definitions
- `docker-compose.yml` - Service orchestration
- `docker-manager.sh` - Management commands
- `.env.example` - Environment configuration
