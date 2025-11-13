# 🐳 FrameForge - Build & Deployment Guide

## Quick Start

### For Local Development (Windows/Mac - CPU Only)

Use the lightweight CPU Dockerfile for local testing:

```powershell
# PowerShell (Windows)
docker build -f Dockerfile.cpu -t frameforge:latest .
docker run -p 8080:8080 -e GOOGLE_API_KEY=your_key frameforge:latest
```

```bash
# Bash (Mac/Linux)
docker build -f Dockerfile.cpu -t frameforge:latest .
docker run -p 8080:8080 -e GOOGLE_API_KEY=your_key frameforge:latest
```

**Note:** Frontend will be available at `http://localhost:8080`

### For Cloud Run GPU Deployment

Build and push to Artifact Registry:

```bash
# Set project variables
export PROJECT_ID="frameforge-477214"
export REGION="europe-west4"
export REPO="frameforge-repo"
export IMAGE="frameforge-gpu"

# Build with Cloud Build (recommended)
gcloud builds submit --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${IMAGE}:latest .

# Or build locally (slower)
docker build -t ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${IMAGE}:latest .
docker push ${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/${IMAGE}:latest
```

## Deploy to Cloud Run

```bash
gcloud run deploy frameforge-gpu \
  --image europe-west4-docker.pkg.dev/frameforge-477214/frameforge-repo/frameforge-gpu:latest \
  --region europe-west4 \
  --gpu=1 \
  --gpu-type=nvidia-l4 \
  --memory=16Gi \
  --cpu=4 \
  --port=8080 \
  --concurrency=1 \
  --timeout=900 \
  --allow-unauthenticated \
  --set-env-vars GCS_BUCKET_NAME=frameforge-bucket,GOOGLE_API_KEY=your_gemini_api_key,MODEL_NAME=Salesforce/blip-image-captioning-base
```

**Important:** Replace `your_gemini_api_key` with your actual Google API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

---

## Common Issues

### Issue 1: "Cannot find path" (Windows)

**Problem:** Path encoding issues with special characters (like Turkish characters in "Masaüstü")

**Solution:** Navigate to the directory first, then build:

```powershell
cd "D:\Masaüstü\FrameForge"
docker build -f Dockerfile.cpu -t frameforge:latest .
```

### Issue 2: Docker Desktop not running

**Problem:** `error during connect: Head "http://%2F%2F.%2Fpipe%2FdockerDesktopLinuxEngine/_ping"`

**Solution:** 
1. Start Docker Desktop
2. Wait for it to fully start (whale icon in system tray should be steady)
3. Try the build command again

### Issue 3: CUDA base image too large/slow

**Problem:** The `nvidia/cuda` base image is very large (~5GB+) and takes a long time to download

**Solution:** Use `Dockerfile.cpu` for local development:

```bash
docker build -f Dockerfile.cpu -t frameforge:latest .
```

### Issue 4: Build fails on Windows

**Problem:** Line ending issues or path problems

**Solution:** 
1. Ensure you're using Git Bash or PowerShell (not CMD)
2. Make sure Docker Desktop is using WSL 2 backend
3. Check Docker Desktop settings → General → Use WSL 2 based engine

### Issue 5: GPU quota exceeded on Cloud Run

**Problem:** `ERROR: Quota exceeded for total allowable count of GPUs per project per region`

**Solutions:**
1. **Request quota increase:**
   - Go to [GCP Quotas page](https://console.cloud.google.com/iam-admin/quotas?project=frameforge-477214)
   - Filter for "GPUs" or "Cloud Run GPU"
   - Request increase (explain use case)
   - Wait 24-48 hours

2. **Use different region:**
   ```bash
   # Try us-central1 or other GPU-enabled regions
   gcloud run deploy frameforge-gpu \
     --region us-central1 \
     --gpu=1 --gpu-type=nvidia-l4 ...
   ```

3. **Delete old revisions:**
   ```bash
   # List all revisions
   gcloud run revisions list --service frameforge-gpu --region europe-west4

   # Delete old revisions
   gcloud run revisions delete <revision-name> --region europe-west4
   ```

---

## Build Options

| Dockerfile | Base Image | Size | Use Case |
|-----------|------------|------|----------|
| `Dockerfile.cpu` | `python:3.10-slim` | ~500MB | Local development (Windows/Mac) |
| `Dockerfile` | `nvidia/cuda:12.1.0-runtime-ubuntu22.04` | ~5GB+ | Cloud Run GPU deployment |

**Key Differences:**
- `Dockerfile.cpu`: No CUDA, lighter, faster build
- `Dockerfile`: CUDA 12.1, GPU support, optimized for L4

## Verification

### 1. Verify Docker Image

```bash
# List images
docker images frameforge

# Expected output:
# REPOSITORY   TAG      IMAGE ID       CREATED         SIZE
# frameforge   latest   abc123def456   2 minutes ago   X GB
```

### 2. Test Locally

```bash
# Run container
docker run -p 8080:8080 \
  -e GOOGLE_API_KEY=your_key \
  frameforge:latest

# In another terminal, test health endpoint
curl http://localhost:8080/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_name": "Salesforce/blip-image-captioning-base",
  "gemini_status": "available",
  "features": {
    "scene_detection": true,
    "ai_captioning": true,
    "audio_transcription": true,
    "narrative_analysis": true
  }
}
```

### 3. Test Frontend

Visit `http://localhost:8080` in your browser. You should see the FrameForge web interface.

---

## Environment Variables

Required and optional environment variables:

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GOOGLE_API_KEY` | Yes* | - | Gemini API key for narrative analysis |
| `GCS_BUCKET_NAME` | Yes** | `frameforge-bucket` | Google Cloud Storage bucket |
| `MODEL_NAME` | No | `Salesforce/blip-image-captioning-base` | HuggingFace model ID |
| `PORT` | No | `8080` | Server port |
| `TRANSFORMERS_CACHE` | No | `/tmp/hf_cache` | Model cache directory |

\* Required for narrative analysis feature
\** Required for production deployment

---

## Performance Tips

1. **Pre-download models:**
   ```dockerfile
   # Add to Dockerfile to cache models during build
   RUN python -c "from transformers import AutoProcessor, BlipForConditionalGeneration; \
       BlipForConditionalGeneration.from_pretrained('Salesforce/blip-image-captioning-base'); \
       AutoProcessor.from_pretrained('Salesforce/blip-image-captioning-base')"
   ```

2. **Use Cloud Build for faster builds:**
   - Cloud Build uses powerful machines
   - Automatically pushes to Artifact Registry
   - Better caching

3. **Optimize Docker layers:**
   - Install dependencies before copying code
   - Use `.dockerignore` to exclude unnecessary files

---

## Troubleshooting Cloud Run Deployment

### Check logs
```bash
# View recent logs
gcloud run services logs read frameforge-gpu --region europe-west4 --limit 50

# Follow logs in real-time
gcloud run services logs tail frameforge-gpu --region europe-west4
```

### Check service status
```bash
# Get service details
gcloud run services describe frameforge-gpu --region europe-west4

# List all revisions
gcloud run revisions list --service frameforge-gpu --region europe-west4
```

### Update environment variables
```bash
# Update without redeploying
gcloud run services update frameforge-gpu \
  --region europe-west4 \
  --update-env-vars GOOGLE_API_KEY=new_key
```

