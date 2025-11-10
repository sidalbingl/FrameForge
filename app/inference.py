"""
FrameForge - Vision-Language Model Inference (Cloud Run GPU Ready)
Enhanced with dialogue-aware caption generation
"""

import os
import torch
from PIL import Image
from typing import Tuple, Optional, List

try:
    from transformers import BlipProcessor, BlipForConditionalGeneration
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False
    print("Warning: transformers not available. Using stub implementation.")


def get_device() -> str:
    """Determine the best available device (GPU > CPU)."""
    if torch.cuda.is_available():
        return "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    else:
        return "cpu"


def load_model(model_name: str = "Salesforce/blip-image-captioning-base") -> Tuple[Optional[object], Optional[object]]:
    """
    Load a vision-language model for GPU inference on Cloud Run.
    """
    if not TRANSFORMERS_AVAILABLE:
        print("Using stub model (transformers not installed)")
        return None, None

    device = get_device()
    print(f"Loading model '{model_name}' on device: {device}")

    try:
        # Cloud Run'da sadece /tmp dizini yazılabilir
        cache_dir = os.getenv("TRANSFORMERS_CACHE", "/tmp/hf_cache")
        os.makedirs(cache_dir, exist_ok=True)

        processor = BlipProcessor.from_pretrained(model_name, cache_dir=cache_dir)
        model = BlipForConditionalGeneration.from_pretrained(
            model_name,
            cache_dir=cache_dir,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32
        )
        model.to(device)
        model.eval()

        print(f"✅ Model loaded successfully on {device}")
        return model, processor

    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return None, None


def generate_caption(
    model: Optional[object],
    processor: Optional[object],
    image_path: str,
    prompt: str = "a detailed cinematic shot showing",
    dialogue_context: Optional[str] = None
) -> str:
    """
    Generate a detailed caption for a single image frame.
    
    Args:
        model: BLIP model
        processor: BLIP processor
        image_path: Path to image file
        prompt: Text prompt to guide generation
        dialogue_context: Optional dialogue text to influence caption (NEW)
        
    Returns:
        Caption string
    """
    if model is None or processor is None:
        return f"Scene from video: {os.path.basename(image_path)}"

    try:
        image = Image.open(image_path).convert("RGB")
        device = get_device()
        
        # If dialogue available, create enriched prompt
        if dialogue_context:
            # Add dialogue hint to the prompt
            enriched_prompt = f"{prompt} (dialogue: {dialogue_context[:100]})"
        else:
            enriched_prompt = prompt
        
        # Process image with prompt
        inputs = processor(images=image, text=enriched_prompt, return_tensors="pt").to(device)

        with torch.no_grad():
            # Generate caption with increased length
            generated_ids = model.generate(
                **inputs,
                max_length=80,
                min_length=20
            )

        caption = processor.batch_decode(generated_ids, skip_special_tokens=True)[0].strip()
        
        # Clean up caption
        if caption.lower().startswith(prompt.lower()):
            caption = caption[len(prompt):].strip()
        
        # Capitalize first letter
        if caption and len(caption) > 0:
            caption = caption[0].upper() + caption[1:]

        return caption if caption else "A scene from the video"

    except Exception as e:
        print(f"❌ Error generating caption: {e}")
        return f"A scene from the video"


def generate_enhanced_caption_with_dialogue(
    model: Optional[object],
    processor: Optional[object],
    image_path: str,
    dialogues: List[str]
) -> str:
    """
    Generate caption enhanced with dialogue information.
    
    This function combines visual description with dialogue context
    to create a richer scene description.
    
    Args:
        model: BLIP model
        processor: BLIP processor
        image_path: Path to image file
        dialogues: List of dialogue strings for this scene
        
    Returns:
        Enhanced caption combining visual and dialogue info
    """
    # Generate visual caption
    visual_caption = generate_caption(model, processor, image_path)
    
    # If no dialogues, return visual caption only
    if not dialogues:
        return visual_caption
    
    # Combine visual and dialogue
    dialogue_text = " ".join(dialogues)
    
    # Create enhanced description
    enhanced = f"{visual_caption}"
    
    # Add dialogue indicator if present
    if len(dialogue_text) > 0:
        # Add dialogue summary to caption
        enhanced += f" [Dialogue: \"{dialogue_text[:150]}{'...' if len(dialogue_text) > 150 else ''}\"]"
    
    return enhanced