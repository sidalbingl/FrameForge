"""
FrameForge - AI Video Storyboard Generator
Simple and compatible with existing frontend
"""

import os
import tempfile
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException, Form

# Load environment variables from .env file
load_dotenv()
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.video import extract_frames
from app.inference import load_model, generate_caption
from app.storage import upload_to_gcs, get_signed_url
from app.narrative import (
    initialize_gemini,
    generate_screenplay_from_captions,
    upload_video_to_gemini,
    generate_screenplay_from_video,
    cleanup_gemini_file
)


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
    print(f"[OK] Static files mounted from: {static_dir}")
else:
    print(f"[WARN] Static directory not found: {static_dir}")

# Global model
model = None
processor = None
is_blip2 = False  # Track if we're using BLIP-2

# Config
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "frameforge-bucket")
MODEL_NAME = os.getenv("MODEL_NAME", "Salesforce/blip-image-captioning-base")  # BLIP base with text conditioning
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
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


class ScreenplayData(BaseModel):
    """Screenplay narrative analysis."""
    screenplay_full: str
    logline: Optional[str] = None
    synopsis: Optional[str] = None
    screenplay: Optional[str] = None
    scenes_breakdown: Optional[str] = None
    visual_style: Optional[str] = None
    themes: Optional[str] = None
    model_used: Optional[str] = None


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
    screenplay: Optional[ScreenplayData] = None


@app.on_event("startup")
async def startup_event():
    """Load AI model on startup."""
    global model, processor, is_blip2
    try:
        print("Loading AI model...")
        print(f"Model: {MODEL_NAME}")
        model, processor, is_blip2 = load_model(MODEL_NAME)
        print(f"[OK] Model loaded successfully! (BLIP-2: {is_blip2})")
    except Exception as e:
        print(f"[ERROR] ERROR: Failed to load model during startup: {e}")
        import traceback
        print(traceback.format_exc())
        print("[WARN] WARNING: Application will start but caption generation will fail!")
        # Don't raise - let the app start, model will be loaded lazily on first request
        model = None
        processor = None
        is_blip2 = False

    # Initialize Gemini API
    if GOOGLE_API_KEY:
        try:
            print("Initializing Gemini API...")
            if initialize_gemini(GOOGLE_API_KEY):
                print("[OK] Gemini API initialized successfully!")
            else:
                print("[WARN] Gemini API initialization failed")
        except Exception as e:
            print(f"[WARN] Gemini initialization error: {e}")
    else:
        print("[WARN] GOOGLE_API_KEY not set - narrative analysis disabled")


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
    global model, processor
    model_status = "loaded" if (model is not None and processor is not None) else "not_loaded"
    gemini_status = "available" if GOOGLE_API_KEY else "not_configured"
    return {
        "status": "healthy",
        "model_loaded": model is not None and processor is not None,
        "model_status": model_status,
        "model_name": MODEL_NAME,
        "gemini_status": gemini_status,
        "features": {
            "scene_detection": True,
            "fixed_interval": True,
            "ai_captioning": model_status == "loaded",
            "narrative_analysis": gemini_status == "available"
        }
    }


@app.post("/upload", response_model=StoryboardResponse)
async def upload_video(
    file: UploadFile = File(...),
    interval_seconds: float = Form(None),
    use_scene_detection: bool = Form(True),  # Default True - use intelligent scene detection
    scene_threshold: float = Form(27.0),
    enable_narrative_analysis: bool = Form(True),  # Enable screenplay generation by default
    narrative_method: str = Form("captions")  # "captions" or "video" (captions is faster/cheaper)
):
    """
    Main upload endpoint - processes video and generates storyboard.

    Features:
    - Intelligent scene detection or fixed interval frame extraction
    - AI-powered frame captioning with BLIP
    - Narrative analysis with Gemini AI
    """
    global model, processor, is_blip2  # Declare global variables at function start

    try:
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
            print(f"[VIDEO] Extracting frames using {extraction_method}...")
            
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
            
            print(f"[STATS] Processing {len(frames_data)} frames...")

            # Upload video to GCS
            video_id = f"video_{Path(file.filename).stem}_{os.urandom(4).hex()}"
            video_gcs_path = f"{video_id}/input/{file.filename}"
            try:
                video_upload_success = upload_to_gcs(str(video_path), GCS_BUCKET_NAME, video_gcs_path)
                if not video_upload_success:
                    print(f"[WARN] Warning: Video upload to GCS failed, continuing anyway")
            except Exception as e:
                print(f"[WARN] Warning: Video upload error: {e}, continuing anyway")
            
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
                try:
                    frame_upload_success = upload_to_gcs(frame_image_path, GCS_BUCKET_NAME, frame_gcs_path)
                    if not frame_upload_success:
                        print(f"[WARN] Warning: Frame {frame_number} upload failed, using fallback URL")
                except Exception as e:
                    print(f"[WARN] Warning: Frame {frame_number} upload error: {e}, using fallback URL")
                
                # Get signed URL (with fallback)
                try:
                    frame_url = get_signed_url(GCS_BUCKET_NAME, frame_gcs_path)
                except Exception as e:
                    print(f"[WARN] Warning: Failed to get signed URL: {e}, using public URL")
                    frame_url = f"https://storage.googleapis.com/{GCS_BUCKET_NAME}/{frame_gcs_path}"

                # Generate caption - lazy load model if not loaded
                if model is None or processor is None:
                    print("[WARN] Model not loaded, loading now...")
                    try:
                        model, processor, is_blip2 = load_model(MODEL_NAME)
                        print(f"[OK] Model loaded successfully! (BLIP-2: {is_blip2})")
                    except Exception as e:
                        print(f"[ERROR] Failed to load model: {e}")
                        import traceback
                        print(traceback.format_exc())
                        raise HTTPException(status_code=500, detail=f"AI model failed to load: {str(e)}")

                print(f"Generating caption for frame {frame_number}/{len(frames_data)}...")
                try:
                    # Generate caption without prompt - BLIP creates natural descriptions
                    caption = generate_caption(
                        model,
                        processor,
                        frame_image_path,
                        is_blip2=is_blip2  # Pass BLIP-2 flag
                    )
                    if not caption or len(caption.strip()) == 0:
                        caption = "Scene from the video"
                except Exception as e:
                    print(f"[WARN] Caption generation failed for frame {frame_number}: {e}")
                    import traceback
                    print(traceback.format_exc())
                    caption = "Scene from the video"  # Fallback caption
                
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

            # Generate narrative analysis / screenplay
            screenplay_data = None
            if enable_narrative_analysis and GOOGLE_API_KEY:
                print("[ACTION] Generating narrative analysis...")
                try:
                    # Prepare frame data for narrative analysis
                    narrative_frames = []
                    for frame in storyboard_frames:
                        narrative_frames.append({
                            "frame_number": frame.frame_number,
                            "timestamp": frame.timestamp,
                            "caption": frame.caption,
                            "scene_number": frame.scene_number,
                            "has_dialogue": frame.has_dialogue,
                            "dialogues": frame.dialogues
                        })

                    video_metadata = {
                        "duration": frames_data[-1]["timestamp"] if frames_data else None,
                        "total_frames": len(storyboard_frames)
                    }

                    if narrative_method == "video":
                        # Upload video to Gemini and analyze (slower, more accurate)
                        print("[UPLOAD] Using video analysis method...")
                        gemini_video = upload_video_to_gemini(str(video_path), video_id)
                        if gemini_video:
                            screenplay_result = generate_screenplay_from_video(
                                gemini_video,
                                narrative_frames
                            )
                            cleanup_gemini_file(gemini_video)
                        else:
                            screenplay_result = {"error": "Video upload failed"}
                    else:
                        # Use captions only (faster, cheaper)
                        print("[NOTE] Using captions analysis method...")
                        screenplay_result = generate_screenplay_from_captions(
                            narrative_frames,
                            video_metadata
                        )

                    if "error" not in screenplay_result:
                        screenplay_data = ScreenplayData(**screenplay_result)
                        print("[OK] Narrative analysis complete!")
                    else:
                        print(f"[WARN] Narrative analysis failed: {screenplay_result['error']}")

                except Exception as e:
                    print(f"[WARN] Narrative analysis error: {e}")
                    import traceback
                    print(traceback.format_exc())
            elif enable_narrative_analysis and not GOOGLE_API_KEY:
                print("[WARN] Narrative analysis requested but GOOGLE_API_KEY not set")

            # Return response
            return StoryboardResponse(
                video_id=video_id,
                total_frames=len(storyboard_frames),
                video_duration=frames_data[-1]["timestamp"] if frames_data else None,
                extraction_method=extraction_method,
                has_audio=False,
                transcription_available=False,
                language=None,
                frames=storyboard_frames,
                screenplay=screenplay_data
            )
    except HTTPException:
        # Re-raise HTTP exceptions (they have proper status codes)
        raise
    except Exception as e:
        # Catch any unexpected errors and return 500
        print(f"[ERROR] Unexpected error in /upload endpoint: {e}")
        import traceback
        print(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)