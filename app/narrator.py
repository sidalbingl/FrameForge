"""
FrameForge - Intelligent Storyboard Narrator
Combines visual analysis and dialogue into a coherent narrative story.
"""

from typing import List, Dict, Any, Optional
from datetime import timedelta


def format_timestamp(seconds: float) -> str:
    """
    Format seconds to readable timestamp (MM:SS or HH:MM:SS).
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted string like "01:23" or "1:23:45"
    """
    td = timedelta(seconds=int(seconds))
    total_seconds = int(td.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def merge_consecutive_dialogues(scenes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge dialogues from consecutive scenes that are close together.
    
    This prevents repeating the same dialogue for every frame.
    
    Args:
        scenes: List of scene dicts with dialogues
        
    Returns:
        Scenes with merged/deduplicated dialogues
    """
    if not scenes:
        return scenes
    
    result = []
    seen_dialogues = set()
    
    for scene in scenes:
        # Copy scene
        new_scene = scene.copy()
        
        # Deduplicate dialogues
        if scene.get("dialogues"):
            unique_dialogues = []
            for dialogue in scene["dialogues"]:
                # Create a key for deduplication (first 50 chars)
                dialogue_key = dialogue[:50].lower().strip()
                
                if dialogue_key not in seen_dialogues:
                    unique_dialogues.append(dialogue)
                    seen_dialogues.add(dialogue_key)
            
            new_scene["dialogues"] = unique_dialogues
            new_scene["has_dialogue"] = len(unique_dialogues) > 0
        
        result.append(new_scene)
    
    return result


def create_narrative_story(
    scenes: List[Dict[str, Any]],
    full_transcript: str = "",
    language: str = "en",
    style: str = "documentary"
) -> str:
    """
    Create a coherent narrative story from scenes and transcript.
    
    This is the main function that combines visual descriptions and dialogues
    into a flowing, readable narrative.
    
    Args:
        scenes: List of scene dicts with captions and dialogues
        full_transcript: Complete audio transcript
        language: Language code (for formatting)
        style: Narrative style - "documentary", "screenplay", "blog", "summary"
        
    Returns:
        Formatted narrative story as a string
    """
    # Deduplicate dialogues
    scenes = merge_consecutive_dialogues(scenes)
    
    # Choose narrative generator based on style
    if style == "screenplay":
        return create_screenplay_format(scenes, full_transcript)
    elif style == "blog":
        return create_blog_post_format(scenes, full_transcript)
    elif style == "summary":
        return create_executive_summary(scenes, full_transcript)
    else:  # documentary (default)
        return create_documentary_format(scenes, full_transcript)


def create_documentary_format(scenes: List[Dict[str, Any]], full_transcript: str) -> str:
    """
    Create a documentary-style narrative.
    
    Format:
    - Natural flowing text
    - Scene descriptions integrated with dialogue
    - Timestamp references
    """
    narrative_parts = []
    
    # Introduction
    if full_transcript and len(full_transcript) > 50:
        narrative_parts.append("The video begins with narration...")
    else:
        narrative_parts.append("The video opens...")
    
    narrative_parts.append("\n\n")
    
    # Process each scene
    for i, scene in enumerate(scenes):
        timestamp = format_timestamp(scene["timestamp"])
        caption = scene.get("caption", "A scene from the video")
        dialogues = scene.get("dialogues", [])
        
        # Remove the [Dialogue: ...] part from caption if present
        if "[Dialogue:" in caption:
            caption = caption.split("[Dialogue:")[0].strip()
        
        # Start with visual description
        if i == 0:
            narrative_parts.append(f"{caption}.")
        else:
            # Add transition words
            transitions = ["Next, ", "Then, ", "Subsequently, ", "Following this, ", ""]
            transition = transitions[min(i % len(transitions), len(transitions) - 1)]
            narrative_parts.append(f"\n\n{transition}{caption.lower()}.")
        
        # Integrate dialogue naturally
        if dialogues and len(dialogues) > 0:
            # Combine all dialogues for this scene
            dialogue_text = " ".join(dialogues)
            
            # Add dialogue with natural integration
            if len(dialogues) == 1:
                narrative_parts.append(f' We hear: "{dialogue_text}"')
            else:
                narrative_parts.append(f' The narration continues: "{dialogue_text}"')
        
        # Add timestamp reference for important scenes
        if i % 3 == 0:  # Every 3rd scene
            narrative_parts.append(f" ({timestamp})")
    
    # Conclusion
    narrative_parts.append("\n\n")
    
    if full_transcript:
        # Add summary of key message
        narrative_parts.append("Throughout the video, the narrative explores the themes and ideas presented, ")
        narrative_parts.append("creating a cohesive story that engages the viewer from beginning to end.")
    
    return "".join(narrative_parts)


def create_screenplay_format(scenes: List[Dict[str, Any]], full_transcript: str) -> str:
    """
    Create a screenplay-style format.
    
    Format:
    - INT./EXT. scene headers
    - Action lines
    - Dialogue formatted as NARRATOR:
    """
    screenplay_parts = []
    
    # Title
    screenplay_parts.append("VIDEO SCREENPLAY\n")
    screenplay_parts.append("=" * 60)
    screenplay_parts.append("\n\n")
    
    for i, scene in enumerate(scenes):
        scene_number = i + 1
        timestamp = format_timestamp(scene["timestamp"])
        caption = scene.get("caption", "A scene")
        dialogues = scene.get("dialogues", [])
        
        # Remove [Dialogue: ...] part
        if "[Dialogue:" in caption:
            caption = caption.split("[Dialogue:")[0].strip()
        
        # Scene header
        screenplay_parts.append(f"SCENE {scene_number} - {timestamp}\n\n")
        
        # Action line (visual description)
        screenplay_parts.append(f"{caption.upper()}\n\n")
        
        # Dialogue
        if dialogues:
            for dialogue in dialogues:
                screenplay_parts.append("NARRATOR\n")
                screenplay_parts.append(f"{dialogue}\n\n")
        
        screenplay_parts.append("\n")
    
    return "".join(screenplay_parts)


def create_blog_post_format(scenes: List[Dict[str, Any]], full_transcript: str) -> str:
    """
    Create a blog post / article format.
    
    Format:
    - Catchy introduction
    - Numbered or bulleted sections
    - Conversational tone
    """
    blog_parts = []
    
    # Title
    blog_parts.append("# Video Story Breakdown\n\n")
    
    # Introduction
    if full_transcript and len(full_transcript) > 50:
        preview = full_transcript[:150] + "..."
        blog_parts.append(f"*\"{preview}\"*\n\n")
    
    blog_parts.append("Let me walk you through what happens in this video:\n\n")
    
    # Process scenes
    for i, scene in enumerate(scenes):
        timestamp = format_timestamp(scene["timestamp"])
        caption = scene.get("caption", "Something happens")
        dialogues = scene.get("dialogues", [])
        
        # Remove [Dialogue: ...] part
        if "[Dialogue:" in caption:
            caption = caption.split("[Dialogue:")[0].strip()
        
        # Section header
        blog_parts.append(f"## {timestamp} - Scene {i + 1}\n\n")
        
        # Description
        blog_parts.append(f"{caption}. ")
        
        # Add dialogue naturally
        if dialogues:
            dialogue_text = " ".join(dialogues)
            blog_parts.append(f'Here\'s what we hear: *"{dialogue_text}"*')
        
        blog_parts.append("\n\n")
    
    # Conclusion
    blog_parts.append("---\n\n")
    blog_parts.append("**Takeaway:** ")
    blog_parts.append("This video presents a compelling narrative that flows naturally from scene to scene.")
    
    return "".join(blog_parts)


def create_executive_summary(scenes: List[Dict[str, Any]], full_transcript: str) -> str:
    """
    Create a concise executive summary.
    
    Format:
    - Brief overview
    - Key points
    - Total duration
    """
    summary_parts = []
    
    # Header
    summary_parts.append("EXECUTIVE SUMMARY\n")
    summary_parts.append("=" * 60)
    summary_parts.append("\n\n")
    
    # Overview
    summary_parts.append("Overview:\n")
    summary_parts.append(f"This video contains {len(scenes)} distinct scenes")
    
    if full_transcript:
        summary_parts.append(" with accompanying narration")
    
    summary_parts.append(".\n\n")
    
    # Key moments
    summary_parts.append("Key Moments:\n\n")
    
    # Select important scenes (first, middle, last + any with dialogue)
    important_indices = [0]  # First scene
    if len(scenes) > 2:
        important_indices.append(len(scenes) // 2)  # Middle scene
    if len(scenes) > 1:
        important_indices.append(len(scenes) - 1)  # Last scene
    
    # Add scenes with dialogue
    for i, scene in enumerate(scenes):
        if scene.get("has_dialogue") and i not in important_indices:
            important_indices.append(i)
    
    important_indices = sorted(set(important_indices))[:5]  # Max 5 key moments
    
    for idx in important_indices:
        scene = scenes[idx]
        timestamp = format_timestamp(scene["timestamp"])
        caption = scene.get("caption", "Scene")
        
        # Remove [Dialogue: ...] part
        if "[Dialogue:" in caption:
            caption = caption.split("[Dialogue:")[0].strip()
        
        summary_parts.append(f"• {timestamp}: {caption}\n")
    
    # Full transcript section
    if full_transcript:
        summary_parts.append("\n\nNarration Excerpt:\n")
        preview = full_transcript[:300]
        if len(full_transcript) > 300:
            preview += "..."
        summary_parts.append(f'"{preview}"\n')
    
    return "".join(summary_parts)


def create_structured_storyboard(
    scenes: List[Dict[str, Any]],
    audio_info: Dict[str, Any],
    style: str = "documentary"
) -> Dict[str, Any]:
    """
    Create a complete structured storyboard with narrative.
    
    This is the main API that combines everything into a user-friendly format.
    
    Args:
        scenes: List of scene dicts
        audio_info: Audio analysis results
        style: Narrative style
        
    Returns:
        Complete storyboard with narrative story
    """
    # Create the narrative story
    narrative = create_narrative_story(
        scenes,
        full_transcript=audio_info.get("full_transcript", ""),
        language=audio_info.get("language", "en"),
        style=style
    )
    
    # Count stats
    total_scenes = len(scenes)
    scenes_with_dialogue = sum(1 for s in scenes if s.get("has_dialogue", False))
    
    # Create structured output
    storyboard = {
        "narrative_style": style,
        "narrative_story": narrative,
        "statistics": {
            "total_scenes": total_scenes,
            "scenes_with_dialogue": scenes_with_dialogue,
            "has_audio": audio_info.get("has_audio", False),
            "language": audio_info.get("language", None)
        },
        "scenes": scenes,  # Keep for reference
        "full_transcript": audio_info.get("full_transcript", "")  # Keep for reference
    }
    
    return storyboard