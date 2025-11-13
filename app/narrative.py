"""
FrameForge - Narrative Analysis Module
Uses Google Gemini Pro to analyze video content and generate screenplay format output.
"""

import os
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai not available. Narrative analysis disabled.")


def initialize_gemini(api_key: str = None) -> bool:
    """
    Initialize Gemini API with the provided API key.

    Args:
        api_key: Google API key (defaults to GOOGLE_API_KEY env var)

    Returns:
        True if successful, False otherwise
    """
    if not GEMINI_AVAILABLE:
        print("ERROR: Gemini not available")
        return False

    if api_key is None:
        api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        print("ERROR: GOOGLE_API_KEY not found in environment")
        return False

    try:
        genai.configure(api_key=api_key)
        print("SUCCESS: Gemini API initialized")
        return True
    except Exception as e:
        print(f"ERROR: Failed to initialize Gemini: {e}")
        return False


def upload_video_to_gemini(video_path: str, display_name: str = None) -> Optional[Any]:
    """
    Upload video file to Gemini for analysis.

    Args:
        video_path: Path to video file
        display_name: Optional display name for the video

    Returns:
        Uploaded video file object or None if failed
    """
    if not GEMINI_AVAILABLE:
        return None

    try:
        print(f"Uploading video to Gemini: {video_path}")

        video_file = genai.upload_file(
            path=video_path,
            display_name=display_name or Path(video_path).name
        )

        print(f"Video uploaded: {video_file.name}")

        # Wait for video to be processed
        print("Waiting for video processing...")
        while video_file.state.name == "PROCESSING":
            time.sleep(2)
            video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED":
            print(f"ERROR: Video processing failed")
            return None

        print(f"Video ready for analysis")
        return video_file

    except Exception as e:
        print(f"ERROR: Video upload failed: {e}")
        return None


def generate_screenplay_from_video(
    video_file,
    frame_data: List[Dict[str, Any]] = None,
    model_name: str = "gemini-2.5-pro"
) -> Dict[str, Any]:
    """
    Generate screenplay format analysis from video using Gemini.

    Args:
        video_file: Uploaded video file object from Gemini
        frame_data: Optional list of frame captions and timestamps
        model_name: Gemini model to use

    Returns:
        Dict containing screenplay and analysis
    """
    if not GEMINI_AVAILABLE:
        return {"error": "Gemini not available"}

    try:
        # Prepare context from frame data
        frame_context = ""
        if frame_data:
            frame_context = "\n\nKey Frames Extracted:\n"
            for idx, frame in enumerate(frame_data[:20]):  # Limit to 20 frames for context
                timestamp = frame.get("timestamp", 0)
                caption = frame.get("caption", "")
                frame_context += f"[{timestamp:.1f}s] {caption}\n"

        # Create detailed prompt for screenplay generation
        prompt = f"""Analyze this video and create a professional screenplay format breakdown.

{frame_context}

Please provide a comprehensive analysis in the following structure:

1. **LOGLINE** (1-2 sentences summarizing the entire video)

2. **SYNOPSIS** (Paragraph describing the full narrative arc)

3. **SCREENPLAY FORMAT**:
   Write the video content as a proper screenplay with:
   - Scene headings (INT./EXT. LOCATION - TIME)
   - Action descriptions (present tense, visual details)
   - Character actions and movements
   - Any visible text or dialogue

4. **TECHNICAL ANALYSIS**:
   - Shot types and camera movements
   - Visual style and mood
   - Key visual elements

5. **NARRATIVE STRUCTURE**:
   - Beginning/Setup
   - Middle/Development
   - End/Resolution

Format the screenplay section exactly like a real film script. Be detailed and cinematic in your descriptions."""

        # Initialize model
        model = genai.GenerativeModel(model_name)

        print(f"Generating screenplay analysis...")

        # Generate content
        response = model.generate_content(
            [video_file, prompt],
            request_options={"timeout": 300}  # 5 minute timeout
        )

        # Handle multi-part responses
        try:
            screenplay_text = response.text
        except ValueError:
            # Response has multiple parts, concatenate them
            screenplay_text = ""
            for part in response.parts:
                if hasattr(part, 'text'):
                    screenplay_text += part.text

        print(f"Screenplay generated ({len(screenplay_text)} characters)")

        # Parse the response into structured format
        result = {
            "screenplay_full": screenplay_text,
            "model_used": model_name,
            "timestamp": time.time(),
            "frame_count": len(frame_data) if frame_data else 0
        }

        # Try to extract sections
        result["logline"] = extract_section(screenplay_text, "LOGLINE", "SYNOPSIS")
        result["synopsis"] = extract_section(screenplay_text, "SYNOPSIS", "SCREENPLAY FORMAT")
        result["screenplay"] = extract_section(screenplay_text, "SCREENPLAY FORMAT", "TECHNICAL ANALYSIS")
        result["technical_analysis"] = extract_section(screenplay_text, "TECHNICAL ANALYSIS", "NARRATIVE STRUCTURE")
        result["narrative_structure"] = extract_section(screenplay_text, "NARRATIVE STRUCTURE", None)

        return result

    except Exception as e:
        print(f"ERROR: Screenplay generation failed: {e}")
        import traceback
        print(traceback.format_exc())
        return {"error": str(e)}


def generate_screenplay_from_captions(
    frame_data: List[Dict[str, Any]],
    video_metadata: Dict[str, Any] = None,
    model_name: str = "gemini-2.5-flash"  # Fast and efficient for captions
) -> Dict[str, Any]:
    """
    Generate screenplay from frame captions without video upload (faster, cheaper).

    Args:
        frame_data: List of frame dicts with timestamps and captions
        video_metadata: Optional video metadata (duration, etc.)
        model_name: Gemini model to use

    Returns:
        Dict containing screenplay and analysis
    """
    if not GEMINI_AVAILABLE:
        return {"error": "Gemini not available"}

    try:
        # Build concise frame timeline (limit to avoid token overflow)
        timeline = "VIDEO ANALYSIS:\n" + "="*50 + "\n\n"

        # Add metadata first
        if video_metadata:
            duration = video_metadata.get("duration", 0)
            timeline += f"Duration: {duration:.1f}s | Total Frames: {len(frame_data)}\n\n"

        # Sample frames intelligently - take beginning, middle, end + some in between
        total_frames = len(frame_data)
        if total_frames <= 15:
            # Use all frames if 15 or fewer
            selected_frames = frame_data
        else:
            # Sample strategically: first 3, last 3, and evenly spaced middle frames
            indices = [0, 1, 2]  # Beginning
            middle_count = min(9, total_frames - 6)  # Middle frames
            step = (total_frames - 6) // middle_count if middle_count > 0 else 1
            indices.extend(range(3, total_frames - 3, step))
            indices.extend([total_frames - 3, total_frames - 2, total_frames - 1])  # End
            selected_frames = [frame_data[i] for i in indices if i < total_frames]

        for frame in selected_frames:
            frame_num = frame.get("frame_number", 0)
            timestamp = frame.get("timestamp", 0)
            caption = frame.get("caption", "")
            scene_num = frame.get("scene_number")

            timeline += f"[{timestamp:.1f}s]"
            if scene_num:
                timeline += f" Scene {scene_num}"
            timeline += f": {caption}\n"

        prompt = f"""{timeline}

Below is a list of frame captions extracted from a video.
Based on these captions, analyze the possible context and narrative flow of the video.

Rules:
- Do not invent anything that cannot be reasonably inferred from the captions.
- If the captions are incomplete or disconnected, acknowledge the gaps and try to form the most coherent interpretation possible.
- Never create scene numbers, timestamps, or lists like "Scene 1, Scene 2."
- Do not use screenplay formatting (FADE IN, EXT/INT, etc.).

Your output must contain the following sections:

📌 LOGLINE:
A single minimal sentence that captures the overall feeling or idea of the video.

📖 STORY SUMMARY:
Write 1–3 paragraphs that form the most coherent narrative possible from the captions.
If there is no strong narrative connection, explicitly say so, but still provide an "observational, holistic interpretation" of what the scenes collectively suggest.

🎭 THEME ANALYSIS:
Identify 2–4 themes that can reasonably be inferred from the visuals—such as atmosphere, human behavior, environment, symbolism, or repetition.
Theme titles should be short, with 1–2 sentences of explanation each."""

        # Initialize model
        model = genai.GenerativeModel(model_name)

        print(f"Generating screenplay from captions...")

        # Generate content
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.7,
                max_output_tokens=4096,
            )
        )

        # Handle multi-part responses
        try:
            screenplay_text = response.text
        except ValueError:
            # Response has multiple parts, concatenate them
            screenplay_text = ""
            for part in response.parts:
                if hasattr(part, 'text'):
                    screenplay_text += part.text

        print(f"Screenplay generated ({len(screenplay_text)} characters)")

        # Parse into structured format
        result = {
            "screenplay_full": screenplay_text,
            "model_used": model_name,
            "timestamp": time.time(),
            "frame_count": len(frame_data)
        }

        # Extract sections - emoji markers
        result["logline"] = extract_section(screenplay_text, "📌 LOGLINE:", "📖 STORY SUMMARY:")
        result["synopsis"] = extract_section(screenplay_text, "📖 STORY SUMMARY:", "🎭 THEME ANALYSIS:")
        result["visual_style"] = extract_section(screenplay_text, "🎭 THEME ANALYSIS:", None)

        # Keep these empty for backwards compatibility with frontend
        result["scenes_breakdown"] = ""
        result["screenplay"] = ""
        result["themes"] = ""

        return result

    except Exception as e:
        print(f"ERROR: Screenplay generation failed: {e}")
        import traceback
        print(traceback.format_exc())
        return {"error": str(e)}


def extract_section(text: str, start_marker: str, end_marker: Optional[str]) -> str:
    """
    Extract a section of text between two markers.

    Args:
        text: Full text to search
        start_marker: Starting marker
        end_marker: Ending marker (None for end of text)

    Returns:
        Extracted section text
    """
    try:
        start_idx = text.find(start_marker)
        if start_idx == -1:
            return ""

        start_idx += len(start_marker)

        if end_marker:
            end_idx = text.find(end_marker, start_idx)
            if end_idx == -1:
                return text[start_idx:].strip()
            return text[start_idx:end_idx].strip()
        else:
            return text[start_idx:].strip()

    except Exception as e:
        print(f"Warning: Section extraction failed: {e}")
        return ""


def format_screenplay_html(screenplay_dict: Dict[str, Any]) -> str:
    """
    Format screenplay data as HTML for display.

    Args:
        screenplay_dict: Dictionary containing screenplay sections

    Returns:
        HTML formatted screenplay
    """
    html = """
    <div class="screenplay-document">
        <style>
            .screenplay-document {
                font-family: 'Courier New', monospace;
                max-width: 800px;
                margin: 0 auto;
                padding: 40px;
                background: white;
                line-height: 1.6;
            }
            .screenplay-title {
                text-align: center;
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 40px;
            }
            .screenplay-section {
                margin-bottom: 30px;
            }
            .screenplay-section h2 {
                font-size: 18px;
                font-weight: bold;
                text-decoration: underline;
                margin-bottom: 10px;
            }
            .screenplay-content {
                white-space: pre-wrap;
                font-size: 12pt;
            }
        </style>

        <div class="screenplay-title">VIDEO SCREENPLAY</div>
    """

    sections = [
        ("LOGLINE", screenplay_dict.get("logline", "")),
        ("SYNOPSIS", screenplay_dict.get("synopsis", "")),
        ("SCREENPLAY", screenplay_dict.get("screenplay", "")),
        ("SCENES BREAKDOWN", screenplay_dict.get("scenes_breakdown", "")),
        ("VISUAL STYLE", screenplay_dict.get("visual_style", "")),
        ("THEMES", screenplay_dict.get("themes", ""))
    ]

    for title, content in sections:
        if content:
            html += f"""
            <div class="screenplay-section">
                <h2>{title}</h2>
                <div class="screenplay-content">{content}</div>
            </div>
            """

    html += "</div>"
    return html


def cleanup_gemini_file(video_file) -> bool:
    """
    Delete uploaded file from Gemini.

    Args:
        video_file: Uploaded file object

    Returns:
        True if successful
    """
    if not GEMINI_AVAILABLE or not video_file:
        return False

    try:
        genai.delete_file(video_file.name)
        print(f"Deleted video from Gemini: {video_file.name}")
        return True
    except Exception as e:
        print(f"WARNING: Failed to delete video: {e}")
        return False
