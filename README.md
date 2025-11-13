# 🎬 FrameForge - AI-Powered Video-to-Storyboard Generator

FrameForge is a serverless, GPU-accelerated application that automatically converts videos into professional storyboards with screenplay format output. It extracts key frames, generates scene captions using vision-language models, analyzes narrative structure, and returns a comprehensive screenplay-style breakdown.

Built for **Google Cloud Run with GPU** (NVIDIA L4), demonstrating how heavy multimodal AI workloads can run efficiently in a scalable, serverless environment.

## 🚀 Features

### Core Features
- 🎞️ **Video Frame Extraction** - Intelligent scene detection or fixed-interval extraction
- 🧠 **GPU-Accelerated Captioning** - BLIP image captioning on NVIDIA L4 GPU
- 🎬 **Narrative Analysis** - Gemini Flash generates screenplay format output with:
  - **Logline** - One-sentence story summary
  - **Synopsis** - Detailed narrative breakdown
  - **Screenplay Format** - Professional INT/EXT scene formatting
  - **Scene Breakdown** - Timestamped scene analysis
  - **Visual Style** - Cinematography and mood analysis
  - **Themes** - Story themes and messages
- 🎤 **Audio Transcription** - Whisper-powered dialogue extraction (optional)
- ☁️ **Serverless Infrastructure** - Deployed on Google Cloud Run (Service)
- 💾 **Storage Integration** - Input/output handled via Google Cloud Storage
- 🌐 **Simple Web UI** - Upload a video and visualize storyboard JSON
- 🔥 **Warm-Up Endpoint** - Preloads model to avoid cold-start delay

### NEW: Screenplay Generation
The system now analyzes videos contextually and generates professional screenplay format output, perfect for:
- Film production planning
- Video content analysis
- Storyboard creation
- Script development
- Educational purposes

## 📁 Project Structure

```
FrameForge/
 ├─ app/
 │   ├─ main.py          # FastAPI entrypoint
 │   ├─ inference.py     # Model loading + caption generation
 │   ├─ video.py         # Frame extraction logic
 │   ├─ storage.py       # GCS upload/download helpers
 │   ├─ audio.py         # Audio transcription with Whisper
 │   ├─ narrative.py     # Gemini Pro screenplay generation
 │   ├─ requirements.txt
 │   └─ static/
 │       └─ index.html   # Web UI
 ├─ Dockerfile           # GPU-enabled Docker image (Cloud Run)
 ├─ Dockerfile.cpu       # CPU-only Docker image (local dev)
 ├─ .env                 # Environment variables
 ├─ README.md
 ├─ architacture.md
 ├─ prd.md
 ├─ FRONTEND_BACKEND.md
 └─ BUILD.md
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

4. **Set up environment variables:**

Create a `.env` file from the example:

Edit `.env` and add your API keys:

```bash
# Get your Google API Key from: https://makersuite.google.com/app/apikey
GOOGLE_API_KEY=your_google_api_key_here

# Optional: Google Cloud Storage
GCS_BUCKET_NAME=your-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json
```

**Note:** Narrative analysis requires a Google API key. Without it, the system will still work but only provide frame captions.

5. **Set up Google Cloud Storage (optional for local dev):**

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

Navigate to `http://localhost:8080` in your browser. The FastAPI backend serves the frontend automatically from `app/static/index.html`.

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
Upload a video and generate storyboard with screenplay analysis.

**Parameters:**
- `file`: Video file (multipart/form-data)
- `interval_seconds`: Frame extraction interval (default: 2.0)
- `use_scene_detection`: Use intelligent scene detection instead of fixed interval (default: false)
- `scene_threshold`: Scene detection threshold (default: 27.0)
- `enable_audio_analysis`: Extract and transcribe audio (default: false)
- `whisper_model`: Whisper model size for audio (default: "base")
- `enable_narrative_analysis`: Generate screenplay format output (default: true)
- `narrative_method`: "captions" (fast) or "video" (slow, more accurate) (default: "captions")

**Response:**
```json
{
  "video_id": "video_abc123_xyz",
  "total_frames": 5,
  "video_duration": 10.5,
  "extraction_method": "fixed_interval",
  "has_audio": false,
  "frames": [
    {
      "frame_number": 1,
      "timestamp": 0.0,
      "frame_url": "https://storage.googleapis.com/...",
      "caption": "A person walking in a park",
      "scene_number": 1,
      "has_dialogue": false,
      "dialogues": []
    }
  ],
  "screenplay": {
    "screenplay_full": "...",
    "logline": "One-sentence story summary",
    "synopsis": "Detailed narrative breakdown...",
    "screenplay": "FADE IN:\n\nINT. PARK - DAY...",
    "scenes_breakdown": "- Scene 1 (0:00-5:00): ...",
    "visual_style": "Natural lighting, handheld camera...",
    "themes": "Human connection, nature...",
    "model_used": "gemini-1.5-flash"
  }
}
```

### `GET /health`
Detailed health check.

## 🔧 Configuration

Environment variables:

- `GOOGLE_API_KEY`: **🆕 Required for narrative analysis** - Get from [Google AI Studio](https://makersuite.google.com/app/apikey)
- `GCS_BUCKET_NAME`: Google Cloud Storage bucket name
- `MODEL_NAME`: Hugging Face model identifier (default: `Salesforce/blip-image-captioning-base`)
- `PORT`: Server port (default: 8080)
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to GCP service account JSON

## 🧪 Testing

### Basic Upload (Frame Captions Only)
```bash
curl -X POST "http://localhost:8080/upload" \
  -F "file=@sample_video.mp4" \
  -F "interval_seconds=2.0"
```

### Full Analysis with Screenplay Generation
```bash
curl -X POST "http://localhost:8080/upload" \
  -F "file=@sample_video.mp4" \
  -F "interval_seconds=2.0" \
  -F "enable_narrative_analysis=true" \
  -F "narrative_method=captions"
```

### Scene Detection + Audio + Screenplay
```bash
curl -X POST "http://localhost:8080/upload" \
  -F "file=@sample_video.mp4" \
  -F "use_scene_detection=true" \
  -F "scene_threshold=27.0" \
  -F "enable_audio_analysis=true" \
  -F "whisper_model=base" \
  -F "enable_narrative_analysis=true"
```

## 📝 Notes

- **Narrative Analysis**: Uses Google Gemini 1.5 Flash to generate professional screenplay format output from frame captions
  - **"captions" method**: Fast, cheaper, uses only extracted frame captions (recommended)
  - **"video" method**: Slower, more accurate, uploads full video to Gemini for analysis
- **Model Selection**: The default caption model is BLIP base (`Salesforce/blip-image-captioning-base`). Lightweight and fast for GPU inference.
- **GPU Requirements**: Cloud Run GPU requires NVIDIA L4 with specific configuration. Check [Cloud Run GPU documentation](https://cloud.google.com/run/docs/using/gpus) for details.
- **API Keys**: Get your Google API key from [Google AI Studio](https://makersuite.google.com/app/apikey) - free tier available!

## 🐛 Troubleshooting

1. **Model not loading**: Ensure you have enough memory (8GB+ recommended for BLIP).
2. **GCS errors**: Verify your bucket exists and credentials are set correctly.
3. **FFmpeg errors**: Ensure FFmpeg is installed in the container or system.
4. **GPU not detected**: Check Docker GPU runtime configuration for local testing.
5. **🆕 Narrative analysis failing**:
   - Verify `GOOGLE_API_KEY` is set correctly
   - Check [Google AI Studio quota](https://makersuite.google.com/app/apikey)
   - Try using `narrative_method=captions` for faster processing

## 📚 References

- [Google Cloud Run GPU Docs](https://cloud.google.com/run/docs/using/gpus)
- [Google Gemini Pro API](https://ai.google.dev/docs)
- [BLIP Model](https://huggingface.co/Salesforce/blip-image-captioning-base)
- [OpenAI Whisper](https://github.com/openai/whisper)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## 📄 License

This project is created for hackathon purposes.

## 🙏 Acknowledgments

Built for Cloud Run Hackathon 2025 - GPU Category Submission.
