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

1. User uploads a short video (≤ 10 s).
2. The video is split into key frames using OpenCV/FFmpeg.
3. Each frame is processed by a lightweight **Vision-Language Model (VLM)** (e.g., BLIP-2 or LLaVA-7B) running on Cloud Run GPU (NVIDIA L4).
4. Captions are aggregated into a JSON storyboard structure.
5. All assets are stored in **Google Cloud Storage (GCS)** and returned as signed URLs.
6. (Optional) Gemini or Gemma text model refines captions for stylistic consistency.

The result is a fast, low-cost, fully serverless video summarization system.

---

## 4. Key Features

| Feature | Description |
|----------|-------------|
| 🎞️ Video Frame Extraction | Uses FFmpeg/OpenCV to sample frames every 2 s |
| 🧠 GPU-Accelerated Captioning | BLIP-2 / LLaVA inference on NVIDIA L4 GPU |
| ☁️ Serverless Infrastructure | Deployed on Google Cloud Run (Service) |
| 💾 Storage Integration | Input/output handled via Google Cloud Storage |
| 🌐 Simple Web UI | Upload a video and visualize storyboard JSON |
| 🔥 Warm-Up Endpoint | `/warmup` preloads model to avoid cold-start delay |
| 📈 Scalable Design | Extendable to Cloud Run Jobs or Pub/Sub pipelines |

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

        Optional Add-ons: Gemini API (text refinement), Cloud Tasks / Jobs for longer workloads 
## 7. Tech Stack
Layer	Tools
Frontend	HTML / JS / Tailwind (lightweight demo UI)
Backend	FastAPI + Uvicorn
AI / ML	PyTorch + Transformers (BLIP-2 or LLaVA)
GPU Runtime	Cloud Run + NVIDIA L4
Storage	Google Cloud Storage
DevOps	Cloud Build + Artifact Registry

## 8. Development Plan (6 Days)
Day	Milestone	Description
Day 1	Environment Setup	Enable APIs, create bucket & repo, verify GPU quota
Day 2	Local Prototype	Build FastAPI service, frame extraction & single-image caption
Day 3	Containerization	Write Dockerfile, build via Cloud Build, deploy to Cloud Run GPU
Day 4	Web UI	Minimal HTML/JS interface for upload & storyboard display
Day 5	Optimization	Warm-up endpoint, memory tuning, error handling
Day 6	Demo & Docs	Record 3 min video, finalize README & architecture diagram


##  9. Success Criteria

✅ Runs on Cloud Run GPU (NVIDIA L4)
✅ Processes a 10 s video → storyboard (< 90 s total latency)
✅ Uses Google Cloud Storage for all I/O
✅ Public demo URL available
✅ Clean documentation + architecture diagram

##  10. Future Enhancements

Scene-change detection & timeline labeling

Emotion / action classification per frame

Gemini integration for narrative consistency

PDF storyboard export

Batch processing via Cloud Run Jobs

##  11. Repository Structure
frameforge/
 ├─ app/
 │   ├─ main.py          # FastAPI entrypoint
 │   ├─ inference.py     # Model loading + caption generation
 │   ├─ video.py         # Frame extraction logic
 │   ├─ storage.py       # GCS upload/download helpers
 │   └─ requirements.txt
 ├─ Dockerfile
 ├─ web/                 # Simple frontend
 ├─ README.md
 └─ PRD.md               # This file

##  12. References

Google Cloud Run GPU Docs

Gemini & Gemma Models

Hugging Face BLIP-2

LLaVA: Large Language and Vision Assistant