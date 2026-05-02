"""
Model Manager for Z-Image Turbo
Downloads models to network volume on first run
"""

import os
import sys
import urllib.request
from pathlib import Path
from typing import Dict, List

# Model configurations
MODELS = {
    "z_image_turbo": {
        "checkpoint": {
            "url": "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/diffusion_models/z_image_turbo.safetensors",
            "path": "checkpoints/z_image_turbo.safetensors",
            "size_mb": 8000
        },
        "clip": {
            "url": "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/clip_l.safetensors",
            "path": "clip/clip_l.safetensors",
            "size_mb": 500
        },
        "vae": {
            "url": "https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/vae/ae.safetensors",
            "path": "vae/ae.safetensors",
            "size_mb": 300
        }
    }
}

# Determine model path (network volume or local)
VOLUME_PATH = "/runpod-volume"
COMFYUI_PATH = "/ComfyUI"

if os.path.exists(VOLUME_PATH):
    MODELS_BASE = f"{VOLUME_PATH}/models"
    print(f"[ModelManager] Using network volume: {MODELS_BASE}")
else:
    MODELS_BASE = f"{COMFYUI_PATH}/models"
    print(f"[ModelManager] Using local storage: {MODELS_BASE}")


def download_with_progress(url: str, filepath: str):
    """Download file with progress bar."""
    
    def progress_hook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(downloaded * 100.0 / total_size, 100)
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            sys.stdout.write(f"\r  Progress: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)")
            sys.stdout.flush()
    
    print(f"[ModelManager] Downloading: {os.path.basename(filepath)}")
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    try:
        urllib.request.urlretrieve(url, filepath, reporthook=progress_hook)
        print()  # New line after progress
        
        # Verify download
        if os.path.exists(filepath):
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"[ModelManager] ✓ Downloaded successfully ({size_mb:.1f} MB)")
            return True
        else:
            print(f"[ModelManager] ✗ Download failed: File not found")
            return False
            
    except Exception as e:
        print(f"\n[ModelManager] ✗ Download failed: {str(e)}")
        return False


def setup_symlinks():
    """Create symlinks from ComfyUI to network volume."""
    if MODELS_BASE == f"{COMFYUI_PATH}/models":
        return  # No symlinks needed for local storage
    
    model_types = ["checkpoints", "clip", "vae", "controlnet", "loras"]
    
    for model_type in model_types:
        src = f"{MODELS_BASE}/{model_type}"
        dst = f"{COMFYUI_PATH}/models/{model_type}"
        
        # Create source directory
        os.makedirs(src, exist_ok=True)
        
        # Remove destination if it exists and is not a symlink
        if os.path.exists(dst) and not os.path.islink(dst):
            import shutil
            shutil.rmtree(dst)
        
        # Create symlink
        if not os.path.exists(dst):
            os.symlink(src, dst)
            print(f"[ModelManager] Linked: {dst} -> {src}")


def ensure_model(model_name: str) -> bool:
    """Ensure a specific model is downloaded."""
    
    if model_name not in MODELS:
        print(f"[ModelManager] Unknown model: {model_name}")
        return False
    
    model_config = MODELS[model_name]
    all_downloaded = True
    
    for component_name, component in model_config.items():
        filepath = f"{MODELS_BASE}/{component['path']}"
        
        if os.path.exists(filepath):
            size_mb = os.path.getsize(filepath) / (1024 * 1024)
            print(f"[ModelManager] ✓ {component_name}: Already exists ({size_mb:.1f} MB)")
        else:
            print(f"[ModelManager] Downloading {component_name}...")
            success = download_with_progress(component['url'], filepath)
            if not success:
                all_downloaded = False
    
    return all_downloaded


def ensure_all_models() -> bool:
    """Ensure all required models are downloaded."""
    print("[ModelManager] Checking models...")
    
    # Setup symlinks first
    setup_symlinks()
    
    # Download models
    success = True
    for model_name in MODELS.keys():
        if not ensure_model(model_name):
            success = False
    
    if success:
        print("[ModelManager] ✓ All models ready!")
    else:
        print("[ModelManager] ✗ Some models failed to download")
    
    return success


def get_model_info() -> Dict:
    """Get information about downloaded models."""
    info = {}
    
    for model_name, model_config in MODELS.items():
        info[model_name] = {}
        for component_name, component in model_config.items():
            filepath = f"{MODELS_BASE}/{component['path']}"
            if os.path.exists(filepath):
                size_mb = os.path.getsize(filepath) / (1024 * 1024)
                info[model_name][component_name] = {
                    "exists": True,
                    "size_mb": round(size_mb, 2),
                    "path": filepath
                }
            else:
                info[model_name][component_name] = {
                    "exists": False,
                    "size_mb": 0,
                    "path": filepath
                }
    
    return info


if __name__ == "__main__":
    # Test mode
    ensure_all_models()
    print("\nModel Info:")
    import json
    print(json.dumps(get_model_info(), indent=2))
