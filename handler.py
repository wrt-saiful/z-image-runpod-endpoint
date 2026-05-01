"""
RunPod Serverless handler for Z-Image Turbo.

Loads the model once at cold start, then serves inference requests.
Returns generated images as base64-encoded PNG strings.
"""

import os
import io
import base64
import traceback
from typing import Any, Dict

import torch
import runpod

# ---- Model loading (runs once per worker cold start) ----------------------

MODEL_ID = os.environ.get("MODEL_ID", "Tongyi-MAI/Z-Image-Turbo")
DTYPE = torch.bfloat16  # L40/A6000 support bf16 well
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

print(f"[init] Loading {MODEL_ID} on {DEVICE} with dtype={DTYPE}...")

# NOTE: The exact pipeline class depends on your installed diffusers version.
# Z-Image is a newer model — try these in order if one fails:
#   1. ZImagePipeline (if/when merged into diffusers main)
#   2. DiffusionPipeline.from_pretrained (auto-detect via model_index.json)
#   3. Custom code from the Tongyi-MAI repo
try:
    from diffusers import ZImagePipeline as Pipeline  # type: ignore
    print("[init] Using ZImagePipeline")
except ImportError:
    from diffusers import DiffusionPipeline as Pipeline
    print("[init] ZImagePipeline not found, falling back to DiffusionPipeline (auto-detect)")

pipe = Pipeline.from_pretrained(
    MODEL_ID,
    torch_dtype=DTYPE,
    # trust_remote_code may be needed if the model uses custom code
    trust_remote_code=True,
)
pipe = pipe.to(DEVICE)

# Optional speed-ups (uncomment if you have memory headroom and want speed)
# pipe.enable_xformers_memory_efficient_attention()
# pipe.unet = torch.compile(pipe.unet, mode="reduce-overhead")  # adds compile time

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
        steps = int(job_input.get("num_inference_steps", 8))   # turbo default
        guidance = float(job_input.get("guidance_scale", 3.5))
        num_images = int(job_input.get("num_images", 1))
        seed = job_input.get("seed")

        # Reproducible generator if a seed was given
        generator = None
        if seed is not None:
            generator = torch.Generator(device=DEVICE).manual_seed(int(seed))

        # Build call kwargs — only pass fields that are set, so we don't
        # break if the pipeline signature differs slightly.
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

        images = result.images  # list[PIL.Image]
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
