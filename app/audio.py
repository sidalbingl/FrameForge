"""
FrameForge - Audio Analysis Module
Extracts audio from video, transcribes speech, and analyzes dialogue.
"""

import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional

# Try to import Whisper for speech recognition
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("Warning: whisper not available. Audio transcription disabled.")


def check_ffmpeg() -> bool:
    """Check if FFmpeg is available in the system."""
    try:
        subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def extract_audio_from_video(
    video_path: str,
    output_audio_path: str = None,
    audio_format: str = "wav"
) -> Optional[str]:
    """
    Extract audio track from video file using FFmpeg.
    
    Args:
        video_path: Path to input video file
        output_audio_path: Path for output audio file (auto-generated if None)
        audio_format: Audio format (wav, mp3, m4a)
        
    Returns:
        Path to extracted audio file or None if failed
    """
    if not check_ffmpeg():
        print("❌ FFmpeg not available for audio extraction")
        return None
    
    video_path_obj = Path(video_path)
    
    # Auto-generate output path if not provided
    if output_audio_path is None:
        output_audio_path = str(video_path_obj.parent / f"{video_path_obj.stem}_audio.{audio_format}")
    
    # FFmpeg command to extract audio
    # -vn: no video, -acodec: audio codec
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vn",  # No video
        "-acodec", "pcm_s16le" if audio_format == "wav" else "libmp3lame",
        "-ar", "16000",  # 16kHz sample rate (optimal for Whisper)
        "-ac", "1",  # Mono channel
        "-y",  # Overwrite output file
        output_audio_path
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ Audio extracted to: {output_audio_path}")
        return output_audio_path
    
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg audio extraction failed: {e.stderr}")
        return None


def transcribe_audio(
    audio_path: str,
    model_size: str = "base",
    language: str = None
) -> Optional[Dict[str, Any]]:
    """
    Transcribe audio file using OpenAI Whisper.
    
    Args:
        audio_path: Path to audio file
        model_size: Whisper model size (tiny, base, small, medium, large)
        language: Language code (None for auto-detection, "tr" for Turkish, "en" for English)
        
    Returns:
        Dict with transcription results or None if failed
        {
            "text": "full transcription",
            "segments": [{"start": 0.0, "end": 5.2, "text": "hello"}],
            "language": "en"
        }
    """
    if not WHISPER_AVAILABLE:
        print("❌ Whisper not available for transcription")
        return None
    
    if not os.path.exists(audio_path):
        print(f"❌ Audio file not found: {audio_path}")
        return None
    
    try:
        print(f"🎤 Loading Whisper model ({model_size})...")
        model = whisper.load_model(model_size)
        
        print(f"🎤 Transcribing audio...")
        result = model.transcribe(
            audio_path,
            language=language,
            verbose=False
        )
        
        print(f"✅ Transcription complete! Language: {result['language']}")
        return result
    
    except Exception as e:
        print(f"❌ Transcription failed: {e}")
        return None


def extract_dialogue_segments(
    transcription_result: Dict[str, Any],
    min_duration: float = 1.0
) -> List[Dict[str, Any]]:
    """
    Extract meaningful dialogue segments from transcription.
    
    Args:
        transcription_result: Result from transcribe_audio()
        min_duration: Minimum segment duration in seconds
        
    Returns:
        List of dialogue segments with timestamps
    """
    if not transcription_result or "segments" not in transcription_result:
        return []
    
    dialogues = []
    
    for segment in transcription_result["segments"]:
        duration = segment["end"] - segment["start"]
        
        # Filter out very short segments (usually noise)
        if duration >= min_duration:
            dialogues.append({
                "start": segment["start"],
                "end": segment["end"],
                "duration": duration,
                "text": segment["text"].strip()
            })
    
    return dialogues


def match_dialogue_to_scenes(
    scenes: List[Dict[str, Any]],
    dialogues: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Match dialogue segments to video scenes based on timestamps.
    
    Args:
        scenes: List of scene dicts with 'timestamp' field
        dialogues: List of dialogue dicts with 'start' and 'end' fields
        
    Returns:
        List of scenes with matched dialogues added
    """
    enhanced_scenes = []
    
    for scene in scenes:
        scene_time = scene["timestamp"]
        scene_dialogues = []
        
        # Find dialogues that occur during or near this scene
        for dialogue in dialogues:
            # Check if dialogue overlaps with scene timeframe
            # We use a window of ±5 seconds around the scene timestamp
            if (dialogue["start"] <= scene_time + 5 and 
                dialogue["end"] >= scene_time - 5):
                scene_dialogues.append(dialogue["text"])
        
        # Add dialogues to scene
        enhanced_scene = scene.copy()
        if scene_dialogues:
            enhanced_scene["dialogues"] = scene_dialogues
            enhanced_scene["has_dialogue"] = True
        else:
            enhanced_scene["dialogues"] = []
            enhanced_scene["has_dialogue"] = False
        
        enhanced_scenes.append(enhanced_scene)
    
    return enhanced_scenes


def analyze_video_audio(
    video_path: str,
    scenes: List[Dict[str, Any]],
    whisper_model_size: str = "base",
    language: str = None
) -> Dict[str, Any]:
    """
    Complete audio analysis pipeline for video.
    
    Args:
        video_path: Path to video file
        scenes: List of detected scenes
        whisper_model_size: Whisper model size (tiny, base, small, medium, large)
        language: Language code for transcription (None for auto)
        
    Returns:
        Dict containing:
        {
            "has_audio": bool,
            "transcription_available": bool,
            "full_transcript": str,
            "language": str,
            "dialogue_segments": list,
            "enhanced_scenes": list  # scenes with matched dialogues
        }
    """
    result = {
        "has_audio": False,
        "transcription_available": False,
        "full_transcript": "",
        "language": None,
        "dialogue_segments": [],
        "enhanced_scenes": scenes
    }
    
    # Step 1: Extract audio
    audio_path = extract_audio_from_video(video_path)
    if not audio_path:
        print("⚠️ Could not extract audio, continuing without transcription")
        return result
    
    result["has_audio"] = True
    
    # Step 2: Transcribe audio
    transcription = transcribe_audio(
        audio_path,
        model_size=whisper_model_size,
        language=language
    )
    
    if not transcription:
        print("⚠️ Transcription failed, continuing without dialogue")
        # Clean up audio file
        try:
            os.remove(audio_path)
        except:
            pass
        return result
    
    result["transcription_available"] = True
    result["full_transcript"] = transcription.get("text", "")
    result["language"] = transcription.get("language", "unknown")
    
    # Step 3: Extract dialogue segments
    dialogues = extract_dialogue_segments(transcription)
    result["dialogue_segments"] = dialogues
    
    print(f"✅ Found {len(dialogues)} dialogue segments")
    
    # Step 4: Match dialogues to scenes
    enhanced_scenes = match_dialogue_to_scenes(scenes, dialogues)
    result["enhanced_scenes"] = enhanced_scenes
    
    # Count scenes with dialogue
    scenes_with_dialogue = sum(1 for s in enhanced_scenes if s.get("has_dialogue", False))
    print(f"✅ Matched dialogues to {scenes_with_dialogue}/{len(scenes)} scenes")
    
    # Clean up audio file
    try:
        os.remove(audio_path)
        print(f"🗑️ Cleaned up temporary audio file")
    except Exception as e:
        print(f"⚠️ Could not delete audio file: {e}")
    
    return result


# Model size recommendations based on use case
WHISPER_MODEL_RECOMMENDATIONS = {
    "fastest": "tiny",      # ~1GB RAM, fastest but less accurate
    "balanced": "base",     # ~1GB RAM, good balance (recommended)
    "accurate": "small",    # ~2GB RAM, better accuracy
    "best": "medium",       # ~5GB RAM, high accuracy
    "max": "large"          # ~10GB RAM, maximum accuracy (slow)
}


def get_recommended_whisper_model(video_duration: float) -> str:
    """
    Get recommended Whisper model size based on video duration.
    
    Args:
        video_duration: Video duration in seconds
        
    Returns:
        Recommended model size
    """
    if video_duration < 60:
        return "base"  # Short videos: fast processing
    elif video_duration < 180:
        return "base"  # Medium videos: balanced
    else:
        return "small"  # Long videos: better accuracy