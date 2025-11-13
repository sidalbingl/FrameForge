"""
Video processing module for FrameForge.
Handles frame extraction with both scene detection and fixed interval modes.
"""

import os
import subprocess
from pathlib import Path
from typing import List, Dict
import tempfile
import shutil


def extract_frames(
    video_path: str,
    interval_seconds: float = 2.0,
    use_scene_detection: bool = False,
    scene_threshold: float = 27.0
) -> List[Dict]:
    """
    Extract frames from video using either scene detection or fixed interval.
    
    Args:
        video_path: Path to input video
        interval_seconds: Extract frame every N seconds (for fixed interval mode)
        use_scene_detection: Use scene detection instead of fixed interval
        scene_threshold: Sensitivity for scene detection (15-35, lower = more scenes)
        
    Returns:
        List of dicts with keys: timestamp, path, scene_number
    """
    video_path = Path(video_path)
    output_dir = video_path.parent / "frames"
    output_dir.mkdir(exist_ok=True)
    
    # Clean any existing frames to avoid confusion
    for old_frame in output_dir.glob("*.jpg"):
        try:
            old_frame.unlink()
        except:
            pass
    
    if use_scene_detection:
        return extract_frames_scene_detection(video_path, output_dir, scene_threshold)
    else:
        return extract_frames_fixed_interval(video_path, output_dir, interval_seconds)


def extract_frames_fixed_interval(
    video_path: Path,
    output_dir: Path,
    interval_seconds: float
) -> List[Dict]:
    """
    Extract frames at fixed time intervals.
    Uses a two-pass approach: extract all frames to temp, then select by time.
    """
    print(f"Extracting frames every {interval_seconds} seconds...")
    
    # Get video duration first
    duration = get_video_duration(str(video_path))
    if duration <= 0:
        raise RuntimeError("Could not determine video duration")
    
    # Calculate target frame times
    target_times = []
    current_time = 0.0
    while current_time < duration:
        target_times.append(current_time)
        current_time += interval_seconds
    
    print(f"Video duration: {duration:.2f}s, extracting {len(target_times)} frames")
    
    # Extract frames one by one using -ss (seek) flag
    # This is more reliable than using fps filter with complex patterns
    frames = []
    for idx, timestamp in enumerate(target_times):
        frame_num = idx + 1
        output_file = output_dir / f"frame_{frame_num:04d}.jpg"
        
        # FFmpeg command to extract single frame at specific time
        cmd = [
            "ffmpeg",
            "-ss", f"{timestamp:.3f}",  # Seek to timestamp
            "-i", str(video_path),
            "-vframes", "1",  # Extract only 1 frame
            "-q:v", "2",      # High quality
            str(output_file),
            "-y",             # Overwrite
            "-loglevel", "error"
        ]
        
        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
            
            if output_file.exists():
                frames.append({
                    "timestamp": timestamp,
                    "path": str(output_file),
                    "scene_number": frame_num
                })
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"Warning: Failed to extract frame at {timestamp}s")
            continue
    
    if not frames:
        raise RuntimeError("No frames were extracted")
    
    print(f"✅ Extracted {len(frames)} frames successfully")
    return frames


def extract_frames_scene_detection(
    video_path: Path,
    output_dir: Path,
    threshold: float
) -> List[Dict]:
    """
    Extract frames using PySceneDetect for accurate scene change detection.
    More reliable than FFmpeg select filter.
    """
    print(f"[SCENE] Using intelligent scene detection (threshold={threshold})...")

    try:
        # Import scenedetect
        try:
            from scenedetect import VideoManager, SceneManager
            from scenedetect.detectors import ContentDetector
        except ImportError:
            print("[SCENE] PySceneDetect not available, using FFmpeg method...")
            return extract_frames_scene_detection_ffmpeg(video_path, output_dir, threshold)

        # Create video manager and scene manager
        video_manager = VideoManager([str(video_path)])
        scene_manager = SceneManager()

        # Add content detector with threshold
        # ContentDetector threshold: higher = fewer scenes (27 is good default)
        scene_manager.add_detector(ContentDetector(threshold=threshold))

        # Start video manager
        video_manager.set_downscale_factor()
        video_manager.start()

        # Detect scenes
        scene_manager.detect_scenes(frame_source=video_manager)
        scene_list = scene_manager.get_scene_list()

        video_manager.release()

        if len(scene_list) < 1:
            print("[SCENE] No scenes detected, using fixed interval fallback")
            return extract_frames_fixed_interval(video_path, output_dir, 3.0)

        print(f"[SCENE] Detected {len(scene_list)} scene changes")

        # Extract frame at the start of each scene
        frames = []
        for idx, scene in enumerate(scene_list):
            frame_num = idx + 1
            # Get scene start time in seconds
            start_time = scene[0].get_seconds()

            output_file = output_dir / f"scene_{frame_num:04d}.jpg"

            # Extract frame using FFmpeg
            cmd = [
                "ffmpeg",
                "-ss", f"{start_time:.3f}",
                "-i", str(video_path),
                "-vframes", "1",
                "-q:v", "2",
                str(output_file),
                "-y",
                "-loglevel", "error"
            ]

            subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)

            if output_file.exists():
                frames.append({
                    "timestamp": start_time,
                    "path": str(output_file),
                    "scene_number": frame_num
                })

        print(f"[SCENE] ✅ Extracted {len(frames)} scene frames with accurate timestamps")
        return frames

    except Exception as e:
        print(f"[SCENE] ⚠️ Scene detection error: {e}")
        print("[SCENE] Falling back to fixed interval (3 seconds)")
        import traceback
        print(traceback.format_exc())
        return extract_frames_fixed_interval(video_path, output_dir, 3.0)


def extract_frames_scene_detection_ffmpeg(
    video_path: Path,
    output_dir: Path,
    threshold: float
) -> List[Dict]:
    """
    FFmpeg-based scene detection fallback.
    Less accurate but doesn't require PySceneDetect.
    """
    print(f"[SCENE] Using FFmpeg scene detection...")

    # Normalize threshold for FFmpeg (0.0-1.0 range)
    # Lower threshold = more sensitive = more scenes
    normalized_threshold = threshold / 100.0

    try:
        # First pass: detect scene timestamps using showinfo
        cmd_detect = [
            "ffmpeg",
            "-i", str(video_path),
            "-vf", f"select='gt(scene\\,{normalized_threshold})',showinfo",
            "-f", "null",
            "-",
            "-loglevel", "info"
        ]

        result = subprocess.run(cmd_detect, capture_output=True, text=True, timeout=300)

        # Parse timestamps from output
        import re
        timestamps = []
        for line in result.stderr.split('\n'):
            if 'pts_time:' in line:
                match = re.search(r'pts_time:([\d.]+)', line)
                if match:
                    timestamps.append(float(match.group(1)))

        if len(timestamps) < 2:
            print(f"[SCENE] Only {len(timestamps)} scenes detected, using fixed interval")
            return extract_frames_fixed_interval(video_path, output_dir, 3.0)

        # Extract frames at detected timestamps
        frames = []
        for idx, timestamp in enumerate(timestamps[:50]):  # Limit to 50 scenes max
            frame_num = idx + 1
            output_file = output_dir / f"scene_{frame_num:04d}.jpg"

            cmd = [
                "ffmpeg",
                "-ss", f"{timestamp:.3f}",
                "-i", str(video_path),
                "-vframes", "1",
                "-q:v", "2",
                str(output_file),
                "-y",
                "-loglevel", "error"
            ]

            subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)

            if output_file.exists():
                frames.append({
                    "timestamp": timestamp,
                    "path": str(output_file),
                    "scene_number": frame_num
                })

        print(f"[SCENE] ✅ Extracted {len(frames)} scenes using FFmpeg method")
        return frames

    except Exception as e:
        print(f"[SCENE] FFmpeg scene detection failed: {e}")
        return extract_frames_fixed_interval(video_path, output_dir, 3.0)


def get_video_duration(video_path: str) -> float:
    """Get video duration in seconds using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10)
        return float(result.stdout.strip())
    except Exception as e:
        print(f"Failed to get video duration: {e}")
        return 0.0


def get_video_info(video_path: str) -> Dict:
    """Get video metadata using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate,codec_name",
        "-show_entries", "format=duration",
        "-of", "json",
        video_path
    ]
    
    try:
        import json
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=10)
        data = json.loads(result.stdout)
        
        stream = data.get("streams", [{}])[0]
        format_info = data.get("format", {})
        
        # Parse frame rate
        fps_str = stream.get("r_frame_rate", "0/1")
        fps_parts = fps_str.split("/")
        fps = float(fps_parts[0]) / float(fps_parts[1]) if len(fps_parts) == 2 else 0.0
        
        return {
            "width": stream.get("width", 0),
            "height": stream.get("height", 0),
            "fps": fps,
            "duration": float(format_info.get("duration", 0)),
            "codec": stream.get("codec_name", "unknown")
        }
    except Exception as e:
        print(f"Failed to get video info: {e}")
        return {
            "width": 0,
            "height": 0,
            "fps": 0.0,
            "duration": 0.0,
            "codec": "unknown"
        }