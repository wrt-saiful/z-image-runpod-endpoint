"""
RunPod Serverless handler for Z-Image Turbo via ComfyUI API.

This handler starts ComfyUI in the background and sends workflow requests to it.
ComfyUI handles all the model loading and inference - we just wrap it with RunPod's API.
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

# ComfyUI settings
COMFY_DIR = "/app/ComfyUI"
COMFY_PORT = 8188
COMFY_URL = f"http://127.0.0.1:{COMFY_PORT}"

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
max_wait = 60
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
    raise RuntimeError("ComfyUI failed to start within 60 seconds")

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
    """
    Generate an image using ComfyUI's API.
    Returns the image as PNG bytes.
    """
    # Create a copy of the workflow and customize it
    workflow = json.loads(json.dumps(BASE_WORKFLOW))
    
    # Update parameters
    workflow["3"]["inputs"]["seed"] = seed if seed is not None else int(time.time())
    workflow["3"]["inputs"]["steps"] = steps
    workflow["3"]["inputs"]["cfg"] = cfg
    workflow["5"]["inputs"]["width"] = width
    workflow["5"]["inputs"]["height"] = height
    workflow["6"]["inputs"]["text"] = prompt
    workflow["7"]["inputs"]["text"] = negative_prompt
    
    # Generate unique client_id for this request
    client_id = str(uuid.uuid4())
    
    # Queue the prompt
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
            # Check if completed
            outputs = history[prompt_id].get("outputs", {})
            if outputs:
                # Find the SaveImage node output (node "9" in our workflow)
                for node_id, node_output in outputs.items():
                    if "images" in node_output:
                        image_info = node_output["images"][0]
                        filename = image_info["filename"]
                        subfolder = image_info.get("subfolder", "")
                        
                        # Download the image
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
                        
            # Check for errors
            status = history[prompt_id].get("status", {})
            if status.get("status_str") == "error":
                error_details = status.get("messages", [])
                raise RuntimeError(f"ComfyUI execution failed: {error_details}")
        
        time.sleep(1)


def image_to_base64(img_bytes: bytes) -> str:
    """Convert image bytes to base64 string."""
    return base64.b64encode(img_bytes).decode("utf-8")


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
        "guidance_scale": 3.5,                       // optional, CFG
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

        negative_prompt = job_input.get("negative_prompt", "")
        width = int(job_input.get("width", 1024))
        height = int(job_input.get("height", 1024))
        steps = int(job_input.get("num_inference_steps", 8))
        cfg = float(job_input.get("guidance_scale", 3.5))
        seed = job_input.get("seed")
        num_images = int(job_input.get("num_images", 1))

        # Generate images
        b64_images = []
        for i in range(num_images):
            # Use different seeds for multiple images
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


# ---- RunPod entrypoint -----------------------------------------------------

if __name__ == "__main__":
    runpod.serverless.start({"handler": handler})
