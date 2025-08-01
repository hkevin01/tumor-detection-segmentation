# Multi-stage Docker build for Tumor Detection System

# Stage 1: Build frontend
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend
COPY gui/frontend/package*.json ./
RUN npm ci --only=production

COPY gui/frontend/ ./
RUN npm run build

# Stage 2: Python backend
FROM python:3.9-slim AS backend

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY gui/backend/ ./gui/backend/
COPY config.json .

# Copy built frontend from previous stage
COPY --from=frontend-builder /app/frontend/build ./gui/frontend/build

# Create necessary directories
RUN mkdir -p data models temp/dicom reports logs

# Set environment variables
ENV PYTHONPATH=/app
ENV NODE_ENV=production

# Expose ports
EXPOSE 8000 3000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command
CMD ["python", "gui/backend/main.py"]
