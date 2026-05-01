"""
RunPod Serverless handler for Z-Image Turbo (ComfyUI checkpoint format).

This version loads from the split safetensors files directly using diffusers'
checkpoint loading utilities, handling the ComfyUI-native format.
"""

import os
import io
import base64
import traceback
from typing import Any, Dict

import torch
import runpod

# ---- Model loading (runs once per worker cold start) ----------------------

MODEL_DIR = "/models/z-image-turbo"
DTYPE = torch.bfloat16
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print(f"[init] Loading Z-Image Turbo from {MODEL_DIR} on {DEVICE} with dtype={DTYPE}...")

try:
    # Try loading as a complete diffusers pipeline first
    from diffusers import DiffusionPipeline
    
    pipe = DiffusionPipeline.from_pretrained(
        MODEL_DIR,
        torch_dtype=DTYPE,
        trust_remote_code=True,
        local_files_only=True,  # Use only the baked-in files
    )
    pipe = pipe.to(DEVICE)
    print("[init] Loaded via DiffusionPipeline")

except Exception as e1:
    print(f"[init] DiffusionPipeline failed: {e1}")
    print("[init] Attempting manual component loading from ComfyUI format...")
    
    try:
        # Manual loading from individual safetensors files
        from diffusers import (
            AutoencoderKL,
            UNet2DConditionModel, 
            DDPMScheduler,
            DiffusionPipeline
        )
        from transformers import CLIPTextModel, CLIPTokenizer
        
        # Load components individually
        unet = UNet2DConditionModel.from_single_file(
            f"{MODEL_DIR}/diffusion_models/z_image_turbo.safetensors",
            torch_dtype=DTYPE,
        )
        
        vae = AutoencoderKL.from_single_file(
            f"{MODEL_DIR}/vae/ae.safetensors",
            torch_dtype=DTYPE,
        )
        
        # CLIP text encoder - try to load from safetensors or fall back to HF hub
        try:
            text_encoder = CLIPTextModel.from_single_file(
                f"{MODEL_DIR}/text_encoders/clip_l.safetensors",
                torch_dtype=DTYPE,
            )
        except:
            print("[init] Loading text encoder from HF hub...")
            text_encoder = CLIPTextModel.from_pretrained(
                "openai/clip-vit-large-patch14",
                torch_dtype=DTYPE,
            )
        
        tokenizer = CLIPTokenizer.from_pretrained("openai/clip-vit-large-patch14")
        
        scheduler = DDPMScheduler.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0",
            subfolder="scheduler",
        )
        
        # Construct pipeline from components
        pipe = DiffusionPipeline(
            unet=unet,
            vae=vae,
            text_encoder=text_encoder,
            tokenizer=tokenizer,
            scheduler=scheduler,
        )
        pipe = pipe.to(DEVICE)
        print("[init] Loaded via manual component assembly")
        
    except Exception as e2:
        print(f"[init] Manual loading also failed: {e2}")
        raise RuntimeError(f"Could not load model. Tried DiffusionPipeline and manual loading. Last error: {e2}")

print("[init] Model loaded and ready.")


# ---- Helpers ---------------------------------------------------------------

def image_to_base64(img) -> str:
    """Convert a PIL image to a base64-encoded PNG string."""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# ---- Handler ---------------------------------------------------------------

def handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Expected input shape:
    {
      "input": {
        "prompt": "a cinematic photo of a fox in a forest",
        "negative_prompt": "blurry, low quality",   // optional
        "width": 1024,                               // optional, default 1024
        "height": 1024,                              // optional, default 1024
        "num_inference_steps": 8,                    // turbo => few steps
        "guidance_scale": 3.5,                       // optional
        "seed": 42,                                  // optional, random if absent
        "num_images": 1                              // optional, default 1
      }
    }
    """
    try:
        job_input = event.get("input", {}) or {}

        prompt = job_input.get("prompt")
        if not prompt:
            return {"error": "Missing required field: 'prompt'"}

        negative_prompt = job_input.get("negative_prompt")
        width = int(job_input.get("width", 1024))
        height = int(job_input.get("height", 1024))
        steps = int(job_input.get("num_inference_steps", 8))
        guidance = float(job_input.get("guidance_scale", 3.5))
        num_images = int(job_input.get("num_images", 1))
        seed = job_input.get("seed")

        # Reproducible generator if a seed was given
        generator = None
        if seed is not None:
            generator = torch.Generator(device=DEVICE).manual_seed(int(seed))

        call_kwargs: Dict[str, Any] = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "num_inference_steps": steps,
            "guidance_scale": guidance,
            "num_images_per_prompt": num_images,
        }
        if negative_prompt:
            call_kwargs["negative_prompt"] = negative_prompt
        if generator is not None:
            call_kwargs["generator"] = generator

        with torch.inference_mode():
            result = pipe(**call_kwargs)

        images = result.images
        b64_images = [image_to_base64(img) for img in images]

        return {
            "images": b64_images,
            "parameters": {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "num_inference_steps": steps,
                "guidance_scale": guidance,
                "seed": seed,
                "num_images": num_images,
            },
        }

    except Exception as e:
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


# ---- RunPod entrypoint -----------------------------------------------------

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
