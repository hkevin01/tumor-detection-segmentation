# Medical Imaging AI - Tumor Detection and Segmentation
# Multi-stage Docker build for development and production

# Base image - Use Python 3.11 slim for lighter build
FROM python:3.11-slim as base

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    wget \
    curl \
    unzip \
    build-essential \
    cmake \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgl1-mesa-dev \
    libgtk-3-0 \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install -r requirements.txt

# Development stage
FROM base as development

# Install development tools
RUN python -m pip install \
    jupyter \
    jupyterlab \
    ipython \
    pytest-xdist \
    pre-commit \
    black \
    flake8 \
    mypy \
    isort

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/models /app/logs /app/reports

# Set permissions
RUN chmod +x /app/scripts/*.sh 2>/dev/null || true

# Expose ports for development
EXPOSE 8000 8888 6006

# Default command for development
CMD ["bash"]

# Production stage
FROM base as production

# Copy only necessary files
COPY src/ ./src/
COPY config/ ./config/
COPY scripts/ ./scripts/
COPY pyproject.toml ./
COPY README.md ./

# Create necessary directories
RUN mkdir -p /app/data /app/models /app/logs /app/reports

# Set permissions
RUN chmod +x /app/scripts/*.sh 2>/dev/null || true

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port for API
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command for production
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Testing stage
FROM development as testing

# Copy test files
COPY tests/ ./tests/

# Install additional test dependencies
RUN python -m pip install \
    pytest-html \
    pytest-cov \
    pytest-benchmark \
    pytest-mock

# Run tests by default
CMD ["python", "-m", "pytest", "tests/", "-v", "--tb=short"]
