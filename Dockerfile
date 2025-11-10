# FrameForge - Dockerfile for Cloud Run GPU
# Base image with CUDA support for NVIDIA L4 GPU
FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    python3.10-venv \
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    libgomp1 \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create symlink for python and ensure pip is up to date
RUN ln -sf /usr/bin/python3 /usr/bin/python && \
    python3 -m pip install --upgrade pip setuptools wheel

# Copy requirements first for better caching
COPY app/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ /app/app/

# ✅ CRITICAL: Ensure static directory exists with index.html
RUN ls -la /app/app/static/index.html || echo "⚠️ WARNING: index.html not found!"

# Create directory for temporary files
RUN mkdir -p /app/temp

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV MODEL_NAME=Salesforce/blip-image-captioning-base
ENV TRANSFORMERS_CACHE=/tmp/hf_cache

# Expose port
EXPOSE 8080

# Run the application
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]