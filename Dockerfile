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
# Install numpy first to prevent NumPy 2.x from being installed by other packages
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir "numpy<2.0,>=1.26.4" && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code (avoid cache files)
COPY app/*.py /app/app/
COPY app/static/ /app/app/static/

# Verify static files and check for screenplay button
RUN ls -la /app/app/static/index.html && \
    echo "Static files copied successfully" && \
    grep -q "View Full Screenplay" /app/app/static/index.html && \
    echo "✓ Screenplay button found in index.html" || \
    echo "✗ WARNING: Screenplay button NOT found in index.html!"

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
# Use timeout=0 to disable timeout for model loading
# Cloud Run will handle the startup timeout separately
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080} --timeout-keep-alive 300"]