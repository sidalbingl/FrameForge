# 🧠 FrameForge – AI-Powered Video-to-Storyboard Generator
> Cloud Run Hackathon 2025 – GPU Category Submission  
> Region: `europe-west4` | GPU: NVIDIA L4 | Runtime: Cloud Run (Service)

---

## 1. Overview

**FrameForge** is a serverless, GPU-accelerated application that automatically converts short videos into storyboards.  
It extracts key frames, generates scene captions using vision-language models, and returns a structured visual narrative ready for creators, filmmakers, and analysts.

Built entirely on **Google Cloud Run with GPU**, FrameForge demonstrates how heavy multimodal AI workloads can run efficiently in a scalable, serverless environment.

---

## 2. Problem Statement

Video content analysis is resource-intensive.  
Manual frame selection and description take hours for filmmakers, educators, or content editors.  
Traditional AI pipelines for video understanding require dedicated servers or expensive GPU clusters.

---

## 3. Solution

FrameForge automates the video-to-storyboard process through a **GPU-powered inference pipeline** on Cloud Run:

1. User uploads a video (≤ 150 MB).
2. The video is split into key frames using **intelligent scene detection** or fixed-interval extraction.
3. Each frame is processed by **BLIP base model** running on Cloud Run GPU (NVIDIA L4).
4. (Optional) **Whisper** transcribes audio and aligns dialogue with frames.
5. **Gemini 1.5 Flash** analyzes the frames and generates a professional screenplay with:
   - Logline and synopsis
   - INT/EXT scene formatting
   - Visual style and themes
6. All assets are stored in **Google Cloud Storage (GCS)** and returned as signed URLs.

The result is a fast, comprehensive, fully serverless video-to-screenplay system.

---

## 4. Key Features

| Feature | Description |
|----------|-------------|
| 🎞️ **Video Frame Extraction** | Intelligent scene detection or fixed-interval extraction using FFmpeg/OpenCV/SceneDetect |
| 🧠 **GPU-Accelerated Captioning** | BLIP base model inference on NVIDIA L4 GPU |
| 🎬 **Narrative Analysis** | Gemini 1.5 Flash generates professional screenplay format output |
| 🎤 **Audio Transcription** | Whisper-powered dialogue extraction (optional) |
| ☁️ **Serverless Infrastructure** | Deployed on Google Cloud Run (Service) with GPU support |
| 💾 **Storage Integration** | Input/output handled via Google Cloud Storage |
| 🌐 **Simple Web UI** | Upload a video and visualize storyboard with screenplay |
| 📈 **Scalable Design** | Extendable to Cloud Run Jobs or Pub/Sub pipelines |

---

## 5. Target Users

- **Filmmakers & Creators:** Auto-generate storyboards from raw footage.  
- **Media Analysts:** Extract visual context and scene summaries.  
- **Educators & Researchers:** Demonstrate multimodal AI inference on GPUs.  
- **Developers:** Learn how to deploy ML models on Cloud Run GPU.

---

## 6. Technical Architecture

```text
[ Web UI / Client ]
        │ (HTTP POST /upload)
        ▼
[ Cloud Run GPU Service (FastAPI + PyTorch) ]
        │
        ├── Extract frames (OpenCV/FFmpeg)
        ├── Run caption model (BLIP-2 / LLaVA)
        ├── Generate storyboard JSON
        ▼
[ Google Cloud Storage ]
        │
        └── Stores input videos + frame images + results
        Region: europe-west4

        GPU: 1 × NVIDIA L4 (no-zonal-redundancy)

        Memory: 16 GB | Concurrency: 1 | Timeout: 900 s

        Build Tools: Cloud Build + Artifact Registry

        Optional Add-ons: Gemini API, Cloud Tasks / Jobs for longer workloads

---

## 7. Tech Stack

| Layer | Tools |
|-------|-------|
| Frontend | HTML / JS / Tailwind CSS |
| Backend | FastAPI + Uvicorn |
| AI / ML | PyTorch + Transformers (BLIP), Whisper, Gemini 1.5 Flash |
| GPU Runtime | Cloud Run + NVIDIA L4 |
| Storage | Google Cloud Storage |
| DevOps | Cloud Build + Artifact Registry |

---

## 8. Development Plan (6 Days)

| Day | Milestone | Description |
|-----|-----------|-------------|
| Day 1 | Environment Setup | Enable APIs, create bucket & repo, verify GPU quota |
| Day 2 | Local Prototype | Build FastAPI service, frame extraction & caption generation |
| Day 3 | Containerization | Write Dockerfile, build via Cloud Build, deploy to Cloud Run GPU |
| Day 4 | Web UI & Audio | HTML/JS interface + Whisper integration |
| Day 5 | Narrative Analysis | Integrate Gemini for screenplay generation |
| Day 6 | Demo & Docs | Testing, optimization, finalize documentation |


## 9. Success Criteria

✅ Runs on Cloud Run GPU (NVIDIA L4)
✅ Processes videos → storyboard with screenplay (< 90 s for 10s video)
✅ Uses Google Cloud Storage for all I/O
✅ Generates professional screenplay format output
✅ Audio transcription with dialogue alignment
✅ Clean documentation + architecture diagram

## 10. Future Enhancements

- Advanced scene classification (action, emotion, mood)
- Multi-language subtitle generation
- PDF/Word export for screenplay
- Batch processing via Cloud Run Jobs
- Real-time video streaming analysis
- Custom model fine-tuning for specific genres

## 11. Repository Structure
```
FrameForge/
 ├─ app/
 │   ├─ main.py          # FastAPI entrypoint
 │   ├─ inference.py     # Model loading + caption generation
 │   ├─ video.py         # Frame extraction logic
 │   ├─ storage.py       # GCS upload/download helpers
 │   ├─ audio.py         # Audio transcription with Whisper
 │   ├─ narrative.py     # Gemini screenplay generation
 │   ├─ requirements.txt
 │   └─ static/
 │       └─ index.html   # Web UI
 ├─ Dockerfile           # GPU-enabled Docker image
 ├─ Dockerfile.cpu       # CPU-only Docker image
 ├─ .env                 # Environment variables
 ├─ README.md
 ├─ architacture.md
 ├─ prd.md               # This file
 ├─ FRONTEND_BACKEND.md
 └─ BUILD.md
```

##  12. References

Google Cloud Run GPU Docs

Gemini & Gemma Models

Hugging Face BLIP-2

LLaVA: Large Language and Vision Assistant