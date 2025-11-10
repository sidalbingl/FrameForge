# 🐳 Docker Build Instructions

## Quick Start

### For Local Development (Windows/Mac - CPU Only)

Use the lightweight CPU Dockerfile:

```powershell
# PowerShell (Windows)
docker build -f Dockerfile.cpu -t frameforge:latest .
docker run -p 8080:8080 frameforge:latest
```

```bash
# Bash (Mac/Linux)
docker build -f Dockerfile.cpu -t frameforge:latest .
docker run -p 8080:8080 frameforge:latest
```

### For Cloud Run GPU Deployment

Use the GPU Dockerfile:

```bash
docker build -t frameforge:gpu .
```

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

## Build Options

| Dockerfile | Base Image | Size | Use Case |
|-----------|------------|------|----------|
| `Dockerfile.cpu` | `python:3.10-slim` | ~500MB | Local development (Windows/Mac) |
| `Dockerfile` | `nvidia/cuda:12.1.0` | ~5GB+ | Cloud Run GPU deployment |

## Verification

After building, verify the image:

```bash
docker images frameforge
```

You should see your image listed. Then test it:

```bash
docker run -p 8080:8080 frameforge:latest
```

Visit `http://localhost:8080` in your browser to see the API health check.

