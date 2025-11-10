# 🎬 FrameForge - AI-Powered Video-to-Storyboard Generator

FrameForge is a serverless, GPU-accelerated application that automatically converts short videos into storyboards. It extracts key frames, generates scene captions using vision-language models, and returns a structured visual narrative.

Built for **Google Cloud Run with GPU** (NVIDIA L4), demonstrating how heavy multimodal AI workloads can run efficiently in a scalable, serverless environment.

## 🚀 Features

- 🎞️ **Video Frame Extraction** - Extracts frames every 2 seconds using OpenCV/FFmpeg
- 🧠 **GPU-Accelerated Captioning** - BLIP-2 inference on NVIDIA L4 GPU
- ☁️ **Serverless Infrastructure** - Deployed on Google Cloud Run (Service)
- 💾 **Storage Integration** - Input/output handled via Google Cloud Storage
- 🌐 **Simple Web UI** - Upload a video and visualize storyboard JSON
- 🔥 **Warm-Up Endpoint** - Preloads model to avoid cold-start delay

## 📁 Project Structure

```
frameforge/
 ├─ app/
 │   ├─ main.py          # FastAPI entrypoint
 │   ├─ inference.py     # Model loading + caption generation
 │   ├─ video.py         # Frame extraction logic
 │   ├─ storage.py       # GCS upload/download helpers
 │   └─ requirements.txt
 ├─ Dockerfile
 ├─ web/
 │   └─ index.html       # Simple HTML/JS UI
 ├─ README.md
 └─ PRD.md
```

## 🛠️ Setup & Installation

### Prerequisites

- Python 3.10+
- Docker (for containerization)
- Google Cloud SDK (for GCS and Cloud Run deployment)
- FFmpeg (for video processing)
- NVIDIA GPU (optional, for local GPU testing)

### Local Development (CPU)

1. **Clone the repository and navigate to the project:**

```bash
cd frameforge
```

2. **Create a virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**

```bash
pip install -r app/requirements.txt
```

4. **Set up Google Cloud Storage (optional for local dev):**

```bash
# Set your GCS bucket name
export GCS_BUCKET_NAME="your-bucket-name"

# Authenticate with Google Cloud
gcloud auth application-default login
```

5. **Run the FastAPI server:**

```bash
cd app
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

6. **Open the web UI:**

Open `web/index.html` in your browser, or serve it with a simple HTTP server:

```bash
cd web
python -m http.server 8000
```

Then navigate to `http://localhost:8000`

### Docker Build & Run (Local)

**For Local Development (CPU-only, recommended for Windows/Mac):**

1. **Build the CPU-only Docker image (much faster, smaller):**

```bash
docker build -f Dockerfile.cpu -t frameforge:latest .
```

2. **Run the container:**

```bash
docker run -p 8080:8080 frameforge:latest
```

**For GPU Support (Linux with NVIDIA Docker runtime):**

1. **Build the GPU Docker image:**

```bash
docker build -t frameforge:gpu .
```

2. **Run with GPU:**

```bash
docker run --gpus all -p 8080:8080 \
  -e GCS_BUCKET_NAME="your-bucket-name" \
  frameforge:gpu
```

**Note:** The GPU Dockerfile (`Dockerfile`) uses a CUDA base image (~5GB+) and requires NVIDIA Docker runtime. For local testing on Windows/Mac, use `Dockerfile.cpu` instead (Python base image, ~500MB).

## ☁️ Deploy to Cloud Run GPU

### Prerequisites

- Google Cloud Project with billing enabled
- Cloud Run API enabled
- GPU quota for NVIDIA L4 in your region (europe-west4)
- Artifact Registry repository

### Deployment Steps

1. **Create a GCS bucket:**

```bash
gsutil mb -p YOUR_PROJECT_ID -l europe-west4 gs://frameforge-bucket
```

2. **Build and push the Docker image:**

```bash
# Set your project ID and region
export PROJECT_ID="your-project-id"
export REGION="europe-west4"
export REPO="frameforge-repo"
export IMAGE="frameforge:latest"

# Create Artifact Registry repository
gcloud artifacts repositories create $REPO \
  --repository-format=docker \
  --location=$REGION

# Build and push
gcloud builds submit --tag gcr.io/$PROJECT_ID/$IMAGE

# Or using Artifact Registry:
gcloud builds submit --tag $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$IMAGE
```

3. **Deploy to Cloud Run:**

```bash
gcloud run deploy frameforge \
  --image $REGION-docker.pkg.dev/$PROJECT_ID/$REPO/$IMAGE \
  --platform managed \
  --region $REGION \
  --allow-unauthenticated \
  --memory 16Gi \
  --cpu 4 \
  --timeout 900 \
  --max-instances 1 \
  --set-env-vars GCS_BUCKET_NAME=frameforge-bucket,MODEL_NAME=Salesforce/blip2-opt-2.7b \
  --add-cloudsql-instances=PROJECT_ID:REGION:INSTANCE \
  --gpu-type nvidia-l4 \
  --gpu-count 1
```

**Note:** Cloud Run GPU support requires specific configuration. Ensure your project has GPU quota enabled.

## 📡 API Endpoints

### `GET /`
Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "service": "FrameForge",
  "version": "1.0.0"
}
```

### `GET /warmup`
Warm-up endpoint to preload model.

**Response:**
```json
{
  "status": "ready",
  "model": "Salesforce/blip2-opt-2.7b",
  "message": "Model is loaded and ready for inference"
}
```

### `POST /upload`
Upload a video and generate storyboard.

**Parameters:**
- `file`: Video file (multipart/form-data)
- `interval_seconds`: Frame extraction interval (default: 2.0)

**Response:**
```json
{
  "video_id": "video_abc123_xyz",
  "total_frames": 5,
  "frames": [
    {
      "frame_number": 1,
      "timestamp": 0.0,
      "frame_url": "https://storage.googleapis.com/...",
      "caption": "A person walking in a park"
    },
    ...
  ]
}
```

### `GET /health`
Detailed health check.

## 🔧 Configuration

Environment variables:

- `GCS_BUCKET_NAME`: Google Cloud Storage bucket name
- `MODEL_NAME`: Hugging Face model identifier (default: `Salesforce/blip2-opt-2.7b`)
- `PORT`: Server port (default: 8080)
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to GCP service account JSON

## 🧪 Testing

Test with a sample video:

```bash
curl -X POST "http://localhost:8080/upload" \
  -F "file=@sample_video.mp4" \
  -F "interval_seconds=2.0"
```

## 📝 Notes

- **Model Selection**: The default model is BLIP-2 OPT-2.7B, which is lightweight and suitable for Cloud Run. For better quality, you can use larger models like LLaVA-7B, but they require more memory.
- **Local Development**: The code includes stub implementations for GCS and model loading, so you can test locally without full setup.
- **GPU Requirements**: Cloud Run GPU requires NVIDIA L4 with specific configuration. Check [Cloud Run GPU documentation](https://cloud.google.com/run/docs/using/gpus) for details.

## 🐛 Troubleshooting

1. **Model not loading**: Ensure you have enough memory (16GB recommended for BLIP-2).
2. **GCS errors**: Verify your bucket exists and credentials are set correctly.
3. **FFmpeg errors**: Ensure FFmpeg is installed in the container or system.
4. **GPU not detected**: Check Docker GPU runtime configuration for local testing.

## 📚 References

- [Google Cloud Run GPU Docs](https://cloud.google.com/run/docs/using/gpus)
- [BLIP-2 Model](https://huggingface.co/Salesforce/blip2-opt-2.7b)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 📄 License

This project is created for hackathon purposes.

## 🙏 Acknowledgments

Built for Cloud Run Hackathon 2025 - GPU Category Submission.

build:
 gcloud builds submit --tag europe-west4-docker.pkg.dev/frameforge-477214/frameforge-repo/frameforge-gpu:v9 .

deploy:
frameforge-repo/frameforge-gpu:v9 --region europe-west4 --gpu=1 --gpu-type=nvidia-l4 --memory=16Gi --cpu=4 --port=8080 --concurrency=1 --allow-unauthenticated --update-env-vars GCS_BUCKET_NAME=frameforge-bucket