#!/usr/bin/env python3
"""
RunPod Serverless Handler for Z-Image Turbo
Full-featured implementation with img2img, batch generation, and flexible output options
"""

import os
import sys
import json
import time
import random
import traceback
from pathlib import Path

import runpod

# Add ComfyUI to path
sys.path.append('/ComfyUI')
import execution
import server
from nodes import NODE_CLASS_MAPPINGS

# Import our utilities
from model_manager import ensure_all_models, get_model_info
from utils import format_response, validate_input, cleanup_old_outputs, get_system_info

# Initialize
print("=" * 60)
print("Z-Image Turbo RunPod Handler Starting...")
print("=" * 60)

# Download models if needed
print("\n[Init] Checking models...")
model_status = ensure_all_models()
if not model_status:
    print("[Init] WARNING: Some models failed to download")

print("\n[Init] Model Status:")
print(json.dumps(get_model_info(), indent=2))

print("\n[Init] System Info:")
print(json.dumps(get_system_info(), indent=2))

# Initialize ComfyUI
print("\n[Init] Initializing ComfyUI...")
server_instance = server.PromptServer(None)
execution_queue = execution.PromptQueue(server_instance)

print("\n[Init] ✓ Ready to process requests!")
print("=" * 60)


def build_txt2img_workflow(params: dict) -> dict:
    """Build ComfyUI workflow for text-to-image generation."""
    return {
        "3": {
            "inputs": {
                "seed": params['seed'],
                "steps": params['steps'],
                "cfg": params['cfg'],
                "sampler_name": params.get('sampler', 'euler'),
                "scheduler": params.get('scheduler', 'normal'),
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0]
            },
            "class_type": "KSampler"
        },
        "4": {
            "inputs": {
                "ckpt_name": "z_image_turbo.safetensors"
            },
            "class_type": "CheckpointLoaderSimple"
        },
        "5": {
            "inputs": {
                "width": params['width'],
                "height": params['height'],
                "batch_size": params.get('batch_size', 1)
            },
            "class_type": "EmptyLatentImage"
        },
        "6": {
            "inputs": {
                "text": params['prompt'],
                "clip": ["4", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "7": {
            "inputs": {
                "text": params['negative_prompt'],
                "clip": ["4", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "8": {
            "inputs": {
                "samples": ["3", 0],
                "vae": ["4", 2]
            },
            "class_type": "VAEDecode"
        },
        "9": {
            "inputs": {
                "filename_prefix": f"z_image_{params['seed']}",
                "images": ["8", 0]
            },
            "class_type": "SaveImage"
        }
    }


def build_img2img_workflow(params: dict) -> dict:
    """Build ComfyUI workflow for image-to-image generation."""
    return {
        "1": {
            "inputs": {
                "image": params['init_image_base64'],
                "upload": "image"
            },
            "class_type": "LoadImage"
        },
        "2": {
            "inputs": {
                "pixels": ["1", 0],
                "vae": ["4", 2]
            },
            "class_type": "VAEEncode"
        },
        "3": {
            "inputs": {
                "seed": params['seed'],
                "steps": params['steps'],
                "cfg": params['cfg'],
                "sampler_name": params.get('sampler', 'euler'),
                "scheduler": params.get('scheduler', 'normal'),
                "denoise": params.get('denoising_strength', 0.75),
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["2", 0]
            },
            "class_type": "KSampler"
        },
        "4": {
            "inputs": {
                "ckpt_name": "z_image_turbo.safetensors"
            },
            "class_type": "CheckpointLoaderSimple"
        },
        "6": {
            "inputs": {
                "text": params['prompt'],
                "clip": ["4", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "7": {
            "inputs": {
                "text": params['negative_prompt'],
                "clip": ["4", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "8": {
            "inputs": {
                "samples": ["3", 0],
                "vae": ["4", 2]
            },
            "class_type": "VAEDecode"
        },
        "9": {
            "inputs": {
                "filename_prefix": f"z_image_img2img_{params['seed']}",
                "images": ["8", 0]
            },
            "class_type": "SaveImage"
        }
    }


def execute_workflow(workflow: dict, timeout: int = 300) -> list:
    """
    Execute ComfyUI workflow and return output image paths.
    
    Returns:
        List of output image file paths
    """
    prompt_id = str(random.randint(100000, 999999))
    
    # Validate workflow
    valid = execution.validate_prompt(workflow)
    if not valid[0]:
        raise Exception(f"Invalid workflow: {valid[1]}")
    
    # Queue the workflow
    execution_queue.put((0, prompt_id, workflow, {}, []))
    
    # Wait for completion
    start_time = time.time()
    while time.time() - start_time < timeout:
        history = server_instance.prompt_queue.get_history(prompt_id)
        
        if prompt_id in history:
            outputs = history[prompt_id].get('outputs', {})
            
            # Find SaveImage node outputs
            for node_id, node_output in outputs.items():
                if 'images' in node_output:
                    image_paths = []
                    for img_info in node_output['images']:
                        img_path = f"/ComfyUI/output/{img_info['filename']}"
                        if os.path.exists(img_path):
                            image_paths.append(img_path)
                    
                    if image_paths:
                        return image_paths
            
            # Check for errors
            status = history[prompt_id].get('status', {})
            if status.get('status_str') == 'error':
                messages = status.get('messages', [])
                raise Exception(f"ComfyUI execution failed: {messages}")
        
        time.sleep(0.5)
    
    raise Exception(f"Workflow execution timed out after {timeout}s")


def handler(event):
    """
    Main RunPod handler function.
    
    Input format:
    {
        "input": {
            "prompt": "a cinematic photo of a fox in a forest",
            "negative_prompt": "blurry, low quality",
            "width": 1024,
            "height": 1024,
            "num_inference_steps": 8,
            "guidance_scale": 3.5,
            "seed": 42,
            "batch_size": 1,
            "return_type": "both",  // "base64", "url", or "both"
            
            // Optional: For img2img
            "mode": "txt2img",  // or "img2img"
            "init_image_base64": "...",  // Required for img2img
            "denoising_strength": 0.75,  // For img2img, 0.0-1.0
            
            // Optional: Advanced
            "sampler": "euler",  // euler, dpmpp_2m, etc.
            "scheduler": "normal"  // normal, karras, exponential
        }
    }
    """
    try:
        start_time = time.time()
        
        # Get input
        input_data = event.get('input', {})
        
        # Validate input
        is_valid, error_msg = validate_input(input_data)
        if not is_valid:
            return {"error": error_msg}
        
        # Extract parameters
        mode = input_data.get('mode', 'txt2img')
        prompt = input_data['prompt']
        negative_prompt = input_data.get('negative_prompt', '')
        width = input_data.get('width', 1024)
        height = input_data.get('height', 1024)
        steps = input_data.get('num_inference_steps', 8)
        cfg = input_data.get('guidance_scale', 3.5)
        seed = input_data.get('seed', random.randint(0, 2**32 - 1))
        batch_size = input_data.get('batch_size', 1)
        return_type = input_data.get('return_type', 'base64')
        
        # Build workflow parameters
        workflow_params = {
            'prompt': prompt,
            'negative_prompt': negative_prompt,
            'width': width,
            'height': height,
            'steps': steps,
            'cfg': cfg,
            'seed': seed,
            'batch_size': batch_size,
            'sampler': input_data.get('sampler', 'euler'),
            'scheduler': input_data.get('scheduler', 'normal')
        }
        
        # Build workflow based on mode
        if mode == 'img2img':
            if 'init_image_base64' not in input_data:
                return {"error": "init_image_base64 required for img2img mode"}
            
            workflow_params['init_image_base64'] = input_data['init_image_base64']
            workflow_params['denoising_strength'] = input_data.get('denoising_strength', 0.75)
            workflow = build_img2img_workflow(workflow_params)
        else:
            workflow = build_txt2img_workflow(workflow_params)
        
        # Execute workflow
        print(f"\n[Handler] Processing: {prompt[:50]}...")
        print(f"[Handler] Mode: {mode}, Size: {width}x{height}, Steps: {steps}, CFG: {cfg}")
        
        image_paths = execute_workflow(workflow)
        
        # Format response
        generation_time = time.time() - start_time
        
        parameters = {
            'mode': mode,
            'prompt': prompt,
            'negative_prompt': negative_prompt,
            'width': width,
            'height': height,
            'steps': steps,
            'cfg': cfg,
            'seed': seed,
            'batch_size': batch_size,
            'generation_time_seconds': round(generation_time, 2)
        }
        
        response = format_response(image_paths, parameters, return_type)
        
        print(f"[Handler] ✓ Generated {len(image_paths)} image(s) in {generation_time:.2f}s")
        
        # Cleanup old outputs
        cleanup_old_outputs("/ComfyUI/output", max_age_hours=1)
        
        return response
        
    except Exception as e:
        print(f"\n[Handler] ✗ Error: {str(e)}")
        print(traceback.format_exc())
        return {
            "error": str(e),
            "traceback": traceback.format_exc()
        }


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Starting RunPod serverless worker...")
    print("=" * 60 + "\n")
    runpod.serverless.start({"handler": handler})
