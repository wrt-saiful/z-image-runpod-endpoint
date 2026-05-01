"""
RunPod Serverless handler for Z-Image Turbo via ComfyUI API.
Downloads models on first run to network volume at /runpod-volume
"""

import os
import io
import json
import base64
import time
import traceback
import subprocess
import requests
from pathlib import Path
from typing import Any, Dict
import uuid

import runpod

# Paths
COMFY_DIR = "/app/ComfyUI"
VOLUME_DIR = "/runpod-volume"
COMFY_PORT = 8188
COMFY_URL = f"http://127.0.0.1:{COMFY_PORT}"

# Model paths - use network volume if available, fallback to local
if os.path.exists(VOLUME_DIR):
    MODELS_BASE = f"{VOLUME_DIR}/models"
else:
    MODELS_BASE = f"{COMFY_DIR}/models"

CHECKPOINT_DIR = f"{MODELS_BASE}/checkpoints"
CLIP_DIR = f"{MODELS_BASE}/clip"
VAE_DIR = f"{MODELS_BASE}/vae"

# Create symlinks from ComfyUI to network volume
os.makedirs(CHECKPOINT_DIR, exist_ok=True)
os.makedirs(CLIP_DIR, exist_ok=True)
os.makedirs(VAE_DIR, exist_ok=True)

# Symlink network volume to ComfyUI directories
if os.path.exists(VOLUME_DIR):
    for src, dst in [
        (CHECKPOINT_DIR, f"{COMFY_DIR}/models/checkpoints"),
        (CLIP_DIR, f"{COMFY_DIR}/models/clip"),
        (VAE_DIR, f"{COMFY_DIR}/models/vae"),
    ]:
        if not os.path.islink(dst):
            os.system(f"rm -rf {dst}")
            os.symlink(src, dst)
            print(f"[init] Linked {dst} -> {src}")


def download_model_files():
    """Download Z-Image Turbo model files if not present."""
    
    files_to_check = [
        (f"{CHECKPOINT_DIR}/z_image_turbo.safetensors", 
         "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/diffusion_models/z_image_turbo.safetensors",
         "checkpoint"),
        (f"{CLIP_DIR}/clip_l.safetensors",
         "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/clip_l.safetensors",
         "CLIP text encoder"),
        (f"{VAE_DIR}/ae.safetensors",
         "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/vae/ae.safetensors",
         "VAE"),
    ]
    
    for filepath, url, name in files_to_check:
        if os.path.exists(filepath):
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"[init] ✓ {name} already exists ({size_mb:.1f} MB)")
            continue
            
        print(f"[init] Downloading {name} from HuggingFace...")
        print(f"[init] URL: {url}")
        print(f"[init] This may take 5-10 minutes depending on your connection...")
        
        # Download with progress
        result = os.system(f"wget --progress=bar:force:noscroll -O '{filepath}' '{url}'")
        
        if result != 0:
            raise RuntimeError(f"Failed to download {name} (exit code {result})")
        
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        print(f"[init] ✓ Downloaded {name} ({size_mb:.1f} MB)")
    
    print("[init] All model files ready!")


# Download models on startup
print("[init] Checking model files...")
download_model_files()

# Start ComfyUI server in background
print("[init] Starting ComfyUI server...")
comfy_process = subprocess.Popen(
    ["python", "main.py", "--listen", "0.0.0.0", "--port", str(COMFY_PORT)],
    cwd=COMFY_DIR,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)

# Wait for ComfyUI to be ready
print("[init] Waiting for ComfyUI to start...")
max_wait = 120  # Increased for first-time model loading
start_time = time.time()
while time.time() - start_time < max_wait:
    try:
        response = requests.get(f"{COMFY_URL}/history", timeout=2)
        if response.status_code == 200:
            print("[init] ComfyUI is ready!")
            break
    except:
        time.sleep(2)
else:
    raise RuntimeError("ComfyUI failed to start within 120 seconds")

# Load base workflow template
with open("/app/workflow_api.json", "r") as f:
    BASE_WORKFLOW = json.load(f)


def generate_image(
    prompt: str,
    negative_prompt: str = "",
    width: int = 1024,
    height: int = 1024,
    steps: int = 8,
    cfg: float = 3.5,
    seed: int = None,
) -> bytes:
    """Generate an image using ComfyUI's API."""
    workflow = json.loads(json.dumps(BASE_WORKFLOW))
    
    workflow["3"]["inputs"]["seed"] = seed if seed is not None else int(time.time())
    workflow["3"]["inputs"]["steps"] = steps
    workflow["3"]["inputs"]["cfg"] = cfg
    workflow["5"]["inputs"]["width"] = width
    workflow["5"]["inputs"]["height"] = height
    workflow["6"]["inputs"]["text"] = prompt
    workflow["7"]["inputs"]["text"] = negative_prompt
    
    client_id = str(uuid.uuid4())
    
    response = requests.post(
        f"{COMFY_URL}/prompt",
        json={"prompt": workflow, "client_id": client_id},
        timeout=300
    )
    
    if response.status_code != 200:
        raise RuntimeError(f"Failed to queue prompt: {response.text}")
    
    prompt_id = response.json()["prompt_id"]
    
    # Poll for completion
    while True:
        history_resp = requests.get(f"{COMFY_URL}/history/{prompt_id}", timeout=10)
        history = history_resp.json()
        
        if prompt_id in history:
            outputs = history[prompt_id].get("outputs", {})
            if outputs:
                for node_id, node_output in outputs.items():
                    if "images" in node_output:
                        image_info = node_output["images"][0]
                        filename = image_info["filename"]
                        subfolder = image_info.get("subfolder", "")
                        
                        params = {
                            "filename": filename,
                            "subfolder": subfolder,
                            "type": "output"
                        }
                        img_response = requests.get(
                            f"{COMFY_URL}/view",
                            params=params,
                            timeout=30
                        )
                        return img_response.content
                        
            status = history[prompt_id].get("status", {})
            if status.get("status_str") == "error":
                error_details = status.get("messages", [])
                raise RuntimeError(f"ComfyUI execution failed: {error_details}")
        
        time.sleep(1)


def image_to_base64(img_bytes: bytes) -> str:
    """Convert image bytes to base64 string."""
    return base64.b64encode(img_bytes).decode("utf-8")


def handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """RunPod handler - same API as before."""
    try:
        job_input = event.get("input", {}) or {}

        prompt = job_input.get("prompt")
        if not prompt:
            return {"error": "Missing required field: 'prompt'"}

        negative_prompt = job_input.get("negative_prompt", "")
        width = int(job_input.get("width", 1024))
        height = int(job_input.get("height", 1024))
        steps = int(job_input.get("num_inference_steps", 8))
        cfg = float(job_input.get("guidance_scale", 3.5))
        seed = job_input.get("seed")
        num_images = int(job_input.get("num_images", 1))

        b64_images = []
        for i in range(num_images):
            current_seed = seed + i if seed is not None else None
            
            img_bytes = generate_image(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                steps=steps,
                cfg=cfg,
                seed=current_seed,
            )
            
            b64_images.append(image_to_base64(img_bytes))

        return {
            "images": b64_images,
            "parameters": {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "width": width,
                "height": height,
                "num_inference_steps": steps,
                "guidance_scale": cfg,
                "seed": seed,
                "num_images": num_images,
            },
        }

    except Exception as e:
        return {
            "error": str(e),
            "traceback": traceback.format_exc(),
        }


if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
