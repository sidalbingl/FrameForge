"""
AI inference module for FrameForge.
Handles BLIP model loading and image captioning with robust error handling.
"""

import torch
from transformers import BlipProcessor, BlipForConditionalGeneration, Blip2Processor, Blip2ForConditionalGeneration
from PIL import Image
import logging
import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_model(model_name: str = "Salesforce/blip-image-captioning-base"):
    """
    Load BLIP model and processor.

    Args:
        model_name: HuggingFace model name

    Returns:
        Tuple of (model, processor, is_blip2)
    """
    try:
        logger.info(f"Loading model: {model_name}")

        # For now, use BLIP base (BLIP-2 has compatibility issues)
        processor = BlipProcessor.from_pretrained(
            model_name,
            do_rescale=True,
            do_normalize=True
        )
        model = BlipForConditionalGeneration.from_pretrained(model_name)

        # Move to GPU if available
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = model.to(device)
        model.eval()  # Set to evaluation mode

        logger.info(f"BLIP model loaded successfully on {device}")

        # Return False for is_blip2 (we'll use text prompts with BLIP base instead)
        return model, processor, False

    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise


def generate_caption(
    model,
    processor,
    image_path: str,
    max_length: int = 150,  # Longer for more detailed descriptions
    num_beams: int = 8,  # More beams for better quality
    length_penalty: float = 1.0,  # Encourage longer captions
    is_blip2: bool = False,  # NEW: Flag for BLIP-2 model
    custom_prompt: str = None  # NEW: Custom prompt for BLIP-2
) -> str:
    """
    Generate detailed, high-quality caption for an image.

    Args:
        model: BLIP or BLIP-2 model
        processor: BLIP or BLIP-2 processor
        image_path: Path to image file
        max_length: Maximum caption length (tokens)
        num_beams: Beam search width (higher = better quality but slower)
        length_penalty: Penalty for caption length (>1 encourages longer)
        is_blip2: Whether using BLIP-2 model (supports prompts)
        custom_prompt: Custom prompt for BLIP-2 (cinematic analysis)

    Returns:
        Generated caption string
    """
    try:
        print(f"[CAPTION] Loading image: {image_path}")

        # Load image
        raw_image = Image.open(image_path)

        # KRITIK FIX: PIL Image'ı numpy array'e çevir, sonra tekrar PIL'e dönüştür
        # Bu, memory layout sorunlarını çözer
        image_array = np.array(raw_image)

        # Ensure RGB (some images might be RGBA or grayscale)
        if len(image_array.shape) == 2:  # Grayscale
            image_array = np.stack([image_array] * 3, axis=-1)
        elif image_array.shape[2] == 4:  # RGBA
            image_array = image_array[:, :, :3]

        # Convert back to PIL with explicit RGB mode
        image = Image.fromarray(image_array, mode='RGB')

        print(f"[CAPTION] Image processed (size: {image.size}, mode: {image.mode})")

        # Process image - Generate natural captions without prompts
        # Note: BLIP is not instruction-following, prompts get included in output
        print(f"[CAPTION] Generating natural caption...")
        inputs = processor(images=image, return_tensors="pt")

        # Move to device
        device = next(model.parameters()).device
        print(f"[CAPTION] Moving to device: {device}")
        inputs = {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}

        # Generate caption with optimized parameters for quality
        print(f"[CAPTION] Generating high-quality detailed caption...")
        with torch.no_grad():
            generated_ids = model.generate(
                **inputs,
                max_length=max_length,
                min_length=15,  # Ensure minimum detail
                num_beams=num_beams,
                length_penalty=length_penalty,
                repetition_penalty=1.5,  # Strongly reduce repetition
                no_repeat_ngram_size=3,  # Prevent 3-gram repetition
                early_stopping=False  # Generate full caption
            )

        # Decode caption
        caption = processor.tokenizer.decode(generated_ids[0], skip_special_tokens=True)
        print(f"[CAPTION] Raw caption: '{caption}'")

        # Clean and format caption
        caption = caption.strip()

        # Remove common artifacts and unwanted prefixes
        caption = caption.replace("arafed", "").replace("araffe", "")

        # Remove repetitive prefixes that AI models sometimes add
        prefixes_to_remove = [
            "you are a professional screenplay writer analyzing a film scene.",
            "describe this frame in a cinematic, visual storytelling style.",
            "focus on composition, mood, actions, and visual elements.",
            "write in present tense like a screenplay:",
            "describe this frame in a cinematic",
            "a professional screenplay scene description:",
            "a cinematic scene showing",
            "cinematic scene showing",
            "a scene showing",
            "scene showing",
            "in a cinematic style",
            "there is",
            "this is",
            "image shows",
            "picture shows",
            "the image shows",
            "the scene shows"
        ]

        # Remove all matching prefixes (some captions may have multiple)
        caption_lower = caption.lower()
        cleaned = False
        while not cleaned:
            cleaned = True
            for prefix in prefixes_to_remove:
                if caption_lower.startswith(prefix):
                    # Remove prefix
                    caption = caption[len(prefix):].strip()
                    caption_lower = caption.lower()
                    cleaned = False
                    break

        # Normalize whitespace
        caption = ' '.join(caption.split())

        if caption and len(caption) > 0:
            # Capitalize first letter for cinematic style
            if len(caption) > 1:
                caption = caption[0].upper() + caption[1:]
            else:
                caption = caption.upper()

            # Ensure ends with period if it's a complete sentence
            if len(caption) > 10 and not caption.endswith(('.', '!', '?')):
                caption += '.'

        print(f"[CAPTION] Final caption: '{caption}'")

        return caption if caption else "Scene from the video"

    except FileNotFoundError as e:
        print(f"[CAPTION] ERROR: Image file not found: {image_path}")
        print(f"[CAPTION] Error: {e}")
        return "Image not found"

    except Exception as e:
        print(f"[CAPTION] ERROR: Caption generation FAILED for {image_path}")
        print(f"[CAPTION] Error type: {type(e).__name__}")
        print(f"[CAPTION] Error message: {str(e)}")
        import traceback
        print(f"[CAPTION] Traceback: {traceback.format_exc()}")
        return "Scene from the video"


def generate_batch_captions(
    model,
    processor,
    image_paths: list,
    max_length: int = 50,
    num_beams: int = 4,
    batch_size: int = 4
) -> list:
    """
    Generate captions for multiple images in batches.
    
    Args:
        model: BLIP model
        processor: BLIP processor
        image_paths: List of image paths
        max_length: Maximum caption length
        num_beams: Beam search parameter
        batch_size: Number of images per batch
        
    Returns:
        List of captions
    """
    captions = []
    device = next(model.parameters()).device
    
    # Process in batches
    for i in range(0, len(image_paths), batch_size):
        batch_paths = image_paths[i:i+batch_size]
        
        try:
            # Load and convert images
            images = []
            valid_indices = []
            
            for idx, path in enumerate(batch_paths):
                try:
                    # Load image
                    raw_image = Image.open(path)
                    
                    # Convert to numpy then back to PIL (fixes memory issues)
                    image_array = np.array(raw_image)
                    
                    # Ensure RGB
                    if len(image_array.shape) == 2:
                        image_array = np.stack([image_array] * 3, axis=-1)
                    elif image_array.shape[2] == 4:
                        image_array = image_array[:, :, :3]
                    
                    image = Image.fromarray(image_array, mode='RGB')
                    images.append(image)
                    valid_indices.append(idx)
                    
                except Exception as e:
                    logger.error(f"Failed to load image {path}: {e}")
                    captions.append("Scene from the video")
            
            if not images:
                continue
            
            # Process batch using processor directly (standard BLIP usage)
            inputs = processor(images=images, return_tensors="pt")
            inputs = {k: v.to(device) if isinstance(v, torch.Tensor) else v for k, v in inputs.items()}
            
            # Generate captions
            with torch.no_grad():
                generated_ids = model.generate(
                    **inputs,
                    max_length=max_length,
                    num_beams=num_beams,
                    early_stopping=True,
                    do_sample=False
                )
            
            # Decode captions - use tokenizer.batch_decode instead of processor.batch_decode
            batch_captions = processor.tokenizer.batch_decode(generated_ids, skip_special_tokens=True)
            
            # Clean and add captions
            for caption in batch_captions:
                caption = caption.strip()
                if caption and len(caption) > 0:
                    # Safely capitalize first letter
                    if len(caption) > 1:
                        caption = caption[0].upper() + caption[1:]
                    else:
                        caption = caption.upper()
                captions.append(caption)
                
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            # Add fallback captions for failed batch
            for _ in batch_paths:
                captions.append("Scene from the video")
    
    return captions


def test_model(model, processor, test_image_path: str = None):
    """
    Test model with a sample image.
    
    Args:
        model: BLIP model
        processor: BLIP processor
        test_image_path: Optional test image path
    """
    if test_image_path:
        try:
            caption = generate_caption(model, processor, test_image_path)
            logger.info(f"✅ Test caption: {caption}")
            return True
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            return False
    else:
        logger.info("⚠️ No test image provided, skipping test")
        return True