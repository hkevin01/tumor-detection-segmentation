# Docker Configuration

This directory contains all Docker-related files for the tumor detection segmentation project.

## Files Overview

### Dockerfiles
- `Dockerfile` - Main production Dockerfile
- `Dockerfile.cuda` - CUDA-enabled Dockerfile for NVIDIA GPUs
- `Dockerfile.phase4` - Phase 4 enhanced Dockerfile with advanced integrations
- `Dockerfile.simple` - Simplified Dockerfile for development

### Docker Compose Files
- `docker-compose.yml` - Main development and production setup
- `docker-compose.cpu.yml` - CPU-only configuration
- `docker-compose.phase4.yml` - Phase 4 advanced configuration

### Configuration Files
- `.dockerignore` - Docker ignore patterns
- `requirements-docker.txt` - Docker-specific Python requirements

### Scripts
- `docker-manager` - Docker management utility

## Usage

### Quick Start
```bash
# From project root directory
docker-compose -f docker/docker-compose.yml up -d
```

### Development Environment
```bash
# Start development environment
docker-compose -f docker/docker-compose.yml up tumor-detection-dev

# Start with GPU support
docker-compose -f docker/docker-compose.yml up tumor-detection-dev
```

### Production Deployment
```bash
# Build and run production container
docker-compose -f docker/docker-compose.yml up tumor-detection-prod
```

### Testing Environment
```bash
# Run tests in container
docker-compose -f docker/docker-compose.yml up tumor-detection-test
```

### Jupyter Notebook
```bash
# Start Jupyter environment
docker-compose -f docker/docker-compose.yml up jupyter
```

## Environment Variables

The Docker setup supports the following environment variables:
- `CUDA_VISIBLE_DEVICES` - GPU device selection
- `PYTHONPATH` - Python path configuration
- `MODEL_CACHE_DIR` - Model cache directory
- `DATA_DIR` - Data directory path

## Volumes

The following volumes are configured:
- `tumor_data` - Training/validation data
- `tumor_models` - Model weights and checkpoints
- `tumor_logs` - Application logs
- `tumor_reports` - Test reports and outputs
- `tumor_notebooks` - Jupyter notebooks

## Building Custom Images

```bash
# Build specific target
docker build -f docker/Dockerfile -t tumor-detection:latest .

# Build with CUDA support
docker build -f docker/Dockerfile.cuda -t tumor-detection:cuda .

# Build development image
docker build -f docker/Dockerfile --target development -t tumor-detection:dev .
```

## Troubleshooting

### GPU Issues
- Ensure NVIDIA Docker is installed for GPU support
- Check CUDA compatibility with your GPU drivers
- Use `docker/Dockerfile.cuda` for GPU-enabled builds

### Port Conflicts
- Default ports: 8000 (API), 8888 (Jupyter), 8501 (Streamlit)
- Modify ports in docker-compose files if needed

### Volume Permissions
- Ensure proper permissions on mounted directories
- Use `chown` if encountering permission issues

## Development Workflow

1. Make code changes in the project root
2. Rebuild containers: `docker-compose -f docker/docker-compose.yml build`
3. Restart services: `docker-compose -f docker/docker-compose.yml up -d`
4. Check logs: `docker-compose -f docker/docker-compose.yml logs -f`
