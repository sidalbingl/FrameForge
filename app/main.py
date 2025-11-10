"""
FrameForge - AI Video Storyboard Generator
Simple and compatible with existing frontend
"""

import os
import tempfile
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.video import extract_frames
from app.inference import load_model, generate_caption
from app.storage import upload_to_gcs, get_signed_url
from app.audio import analyze_video_audio


app = FastAPI(
    title="FrameForge API",
    description="AI-powered video-to-storyboard generator",
    version="4.0.0"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_dir = Path(__file__).resolve().parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    print(f"✅ Static files mounted from: {static_dir}")
else:
    print(f"⚠️ Static directory not found: {static_dir}")

# Global model
model = None
processor = None

# Config
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "frameforge-bucket")
MODEL_NAME = os.getenv("MODEL_NAME", "Salesforce/blip-image-captioning-base")
MAX_FILE_SIZE_MB = 150


class FrameCaption(BaseModel):
    """Single frame with caption."""
    frame_number: int
    timestamp: float
    frame_url: str
    caption: str
    scene_number: Optional[int] = None
    dialogues: Optional[List[str]] = []
    has_dialogue: Optional[bool] = False


class StoryboardResponse(BaseModel):
    """Complete storyboard response."""
    video_id: str
    total_frames: int
    video_duration: Optional[float] = None
    extraction_method: str
    has_audio: Optional[bool] = False
    transcription_available: Optional[bool] = False
    language: Optional[str] = None
    frames: List[FrameCaption]


@app.on_event("startup")
async def startup_event():
    """Load AI model on startup."""
    global model, processor
    print("Loading AI model...")
    model, processor = load_model(MODEL_NAME)
    print("✅ Model loaded successfully!")


@app.get("/")
async def root():
    """Serve frontend."""
    static_dir = Path(__file__).resolve().parent / "static"
    index_path = static_dir / "index.html"
    
    if index_path.exists():
        return FileResponse(index_path, media_type="text/html")
    else:
        return {
            "service": "FrameForge API",
            "version": "4.0.0",
            "message": "API running. Frontend not found.",
            "endpoints": ["/health", "/upload"]
        }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model_loaded": model is not None and processor is not None,
        "model_name": MODEL_NAME if model else None,
        "features": {
            "scene_detection": True,
            "fixed_interval": True,
            "ai_captioning": True,
            "audio_transcription": True
        }
    }


@app.post("/upload", response_model=StoryboardResponse)
async def upload_video(
    file: UploadFile = File(...),
    interval_seconds: float = Form(None),
    use_scene_detection: bool = Form(False),  # Default False for frontend compatibility
    scene_threshold: float = Form(27.0),
    enable_audio_analysis: bool = Form(False),  # Default False for speed
    whisper_model: str = Form("base")
):
    """
    Main upload endpoint - processes video and generates storyboard.
    
    Compatible with both interval-based and scene detection modes.
    """
    # Validate file
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    # Set default interval if not using scene detection
    if not use_scene_detection and interval_seconds is None:
        interval_seconds = 2.0
    
    # Validate interval
    if interval_seconds is not None and (interval_seconds <= 0 or interval_seconds > 10):
        raise HTTPException(status_code=400, detail="interval_seconds must be between 0 and 10")
    
    # Process video
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Save video
        video_path = temp_path / file.filename
        with open(video_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Check file size
        file_size_mb = len(content) / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=400,
                detail=f"Video too large. Max size: {MAX_FILE_SIZE_MB}MB"
            )
        
        # Extract frames
        extraction_method = "scene_detection" if use_scene_detection else "fixed_interval"
        print(f"📹 Extracting frames using {extraction_method}...")
        
        try:
            frames_data = extract_frames(
                str(video_path),
                interval_seconds=interval_seconds or 2.0,
                use_scene_detection=use_scene_detection,
                scene_threshold=scene_threshold
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Frame extraction failed: {str(e)}")
        
        if not frames_data:
            raise HTTPException(status_code=500, detail="No frames extracted from video")
        
        print(f"📊 Processing {len(frames_data)} frames...")
        
        # Audio analysis (optional)
        audio_result = {
            "has_audio": False,
            "transcription_available": False,
            "language": None,
            "enhanced_scenes": frames_data
        }
        
        if enable_audio_analysis:
            print(f"🎤 Analyzing audio...")
            try:
                audio_result = analyze_video_audio(
                    str(video_path),
                    frames_data,
                    whisper_model_size=whisper_model,
                    language=None
                )
                frames_data = audio_result["enhanced_scenes"]
                print(f"✅ Audio analysis complete")
            except Exception as e:
                print(f"⚠️ Audio analysis failed: {e}")
        
        # Upload video to GCS
        video_id = f"video_{Path(file.filename).stem}_{os.urandom(4).hex()}"
        video_gcs_path = f"{video_id}/input/{file.filename}"
        upload_to_gcs(str(video_path), GCS_BUCKET_NAME, video_gcs_path)
        
        # Process frames
        storyboard_frames = []
        for idx, frame_info in enumerate(frames_data):
            frame_number = idx + 1
            timestamp = frame_info["timestamp"]
            frame_image_path = frame_info["path"]
            scene_number = frame_info.get("scene_number")
            
            # Upload frame to GCS
            frame_filename = f"frame_{frame_number:03d}_{timestamp:.1f}s.jpg"
            frame_gcs_path = f"{video_id}/frames/{frame_filename}"
            upload_to_gcs(frame_image_path, GCS_BUCKET_NAME, frame_gcs_path)
            frame_url = get_signed_url(GCS_BUCKET_NAME, frame_gcs_path)
            
            # Generate caption
            print(f"Generating caption for frame {frame_number}/{len(frames_data)}...")
            caption = generate_caption(model, processor, frame_image_path)
            
            # Get dialogues if available
            scene_dialogues = frame_info.get("dialogues", [])
            has_dialogue = frame_info.get("has_dialogue", False)
            
            storyboard_frames.append(
                FrameCaption(
                    frame_number=frame_number,
                    timestamp=timestamp,
                    frame_url=frame_url,
                    caption=caption,
                    scene_number=scene_number,
                    dialogues=scene_dialogues,
                    has_dialogue=has_dialogue
                )
            )
        
        # Return response
        return StoryboardResponse(
            video_id=video_id,
            total_frames=len(storyboard_frames),
            video_duration=frames_data[-1]["timestamp"] if frames_data else None,
            extraction_method=extraction_method,
            has_audio=audio_result["has_audio"],
            transcription_available=audio_result["transcription_available"],
            language=audio_result["language"],
            frames=storyboard_frames
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)