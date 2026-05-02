"""
Utility functions for Z-Image Turbo handler
"""

import os
import io
import base64
import boto3
import time
from pathlib import Path
from typing import Optional, Dict, Any
from PIL import Image


def image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string."""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')


def base64_to_image(base64_string: str) -> Image.Image:
    """Convert base64 string to PIL Image."""
    image_data = base64.b64decode(base64_string)
    return Image.open(io.BytesIO(image_data))


def save_base64_image(base64_string: str, output_path: str):
    """Save base64 encoded image to file."""
    image = base64_to_image(base64_string)
    image.save(output_path)


def upload_to_s3(file_path: str, bucket: str, key: str) -> Optional[str]:
    """
    Upload file to S3 and return public URL.
    Requires AWS credentials in environment.
    """
    try:
        s3_client = boto3.client('s3')
        s3_client.upload_file(file_path, bucket, key)
        url = f"https://{bucket}.s3.amazonaws.com/{key}"
        return url
    except Exception as e:
        print(f"[Utils] S3 upload failed: {str(e)}")
        return None


def upload_to_temp_storage(file_path: str) -> Optional[str]:
    """
    Upload to temporary storage and return URL.
    This is a placeholder - implement based on your storage preference.
    Options: S3, Cloudinary, DigitalOcean Spaces, etc.
    """
    # Example: Use S3
    bucket = os.environ.get('S3_BUCKET')
    if not bucket:
        return None
    
    filename = os.path.basename(file_path)
    timestamp = int(time.time())
    key = f"z-image-turbo/{timestamp}/{filename}"
    
    return upload_to_s3(file_path, bucket, key)


def format_response(
    images: list,
    parameters: Dict[str, Any],
    return_type: str = "base64"
) -> Dict[str, Any]:
    """
    Format the API response based on return type.
    
    Args:
        images: List of image file paths
        parameters: Generation parameters used
        return_type: "base64", "url", or "both"
    
    Returns:
        Formatted response dictionary
    """
    response = {
        "status": "success",
        "parameters": parameters
    }
    
    if return_type in ["base64", "both"]:
        response["images_base64"] = [image_to_base64(img) for img in images]
    
    if return_type in ["url", "both"]:
        urls = []
        for img_path in images:
            url = upload_to_temp_storage(img_path)
            if url:
                urls.append(url)
        
        if urls:
            response["images_url"] = urls
        else:
            response["images_url"] = []
            response["url_note"] = "S3_BUCKET not configured, only base64 available"
    
    response["image_count"] = len(images)
    
    return response


def validate_input(input_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate input data for the handler.
    
    Returns:
        (is_valid, error_message)
    """
    # Check required fields
    if 'prompt' not in input_data:
        return False, "Missing required field: 'prompt'"
    
    # Validate dimensions
    width = input_data.get('width', 1024)
    height = input_data.get('height', 1024)
    
    if not (512 <= width <= 2048):
        return False, f"Width must be between 512 and 2048, got {width}"
    
    if not (512 <= height <= 2048):
        return False, f"Height must be between 512 and 2048, got {height}"
    
    # Validate steps
    steps = input_data.get('num_inference_steps', 8)
    if not (1 <= steps <= 50):
        return False, f"Steps must be between 1 and 50, got {steps}"
    
    # Validate CFG
    cfg = input_data.get('guidance_scale', 3.5)
    if not (1.0 <= cfg <= 20.0):
        return False, f"CFG must be between 1.0 and 20.0, got {cfg}"
    
    # Validate batch size
    batch_size = input_data.get('batch_size', 1)
    if not (1 <= batch_size <= 4):
        return False, f"Batch size must be between 1 and 4, got {batch_size}"
    
    return True, None


def cleanup_old_outputs(output_dir: str, max_age_hours: int = 24):
    """
    Clean up old output files to save disk space.
    
    Args:
        output_dir: Directory containing output files
        max_age_hours: Maximum age of files to keep
    """
    if not os.path.exists(output_dir):
        return
    
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    for filename in os.listdir(output_dir):
        filepath = os.path.join(output_dir, filename)
        
        if not os.path.isfile(filepath):
            continue
        
        file_age = current_time - os.path.getmtime(filepath)
        
        if file_age > max_age_seconds:
            try:
                os.remove(filepath)
                print(f"[Utils] Cleaned up old file: {filename}")
            except Exception as e:
                print(f"[Utils] Failed to delete {filename}: {str(e)}")


def get_system_info() -> Dict[str, Any]:
    """Get system information for debugging."""
    import torch
    import platform
    
    info = {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "torch_version": torch.__version__,
        "cuda_available": torch.cuda.is_available(),
    }
    
    if torch.cuda.is_available():
        info["cuda_version"] = torch.version.cuda
        info["gpu_name"] = torch.cuda.get_device_name(0)
        info["gpu_memory_gb"] = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 2)
    
    return info
