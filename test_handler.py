#!/usr/bin/env python3
"""
Test script for Z-Image Turbo handler
Can be used to test the handler locally or against deployed endpoint
"""

import os
import sys
import json
import base64
import argparse
from pathlib import Path

try:
    import requests
except ImportError:
    print("Installing requests...")
    os.system("pip install requests")
    import requests


def test_local():
    """Test the handler locally (requires ComfyUI setup)."""
    sys.path.insert(0, '/ComfyUI')
    sys.path.insert(0, './src')
    
    from handler import handler
    
    test_input = {
        "input": {
            "prompt": "a majestic snow leopard on a rocky cliff at sunset",
            "negative_prompt": "blurry, low quality",
            "width": 1024,
            "height": 1024,
            "num_inference_steps": 8,
            "guidance_scale": 3.5,
            "seed": 42,
            "return_type": "base64"
        }
    }
    
    print("Testing handler locally...")
    result = handler(test_input)
    
    print("\nResult:")
    print(json.dumps({k: v for k, v in result.items() if k != 'images_base64'}, indent=2))
    
    if 'images_base64' in result:
        print(f"\nGenerated {len(result['images_base64'])} image(s)")
        
        # Save first image
        output_dir = Path("./test_outputs")
        output_dir.mkdir(exist_ok=True)
        
        output_path = output_dir / "test_output.png"
        with open(output_path, 'wb') as f:
            f.write(base64.b64decode(result['images_base64'][0]))
        
        print(f"Saved to: {output_path}")


def test_endpoint(endpoint_id: str, api_key: str):
    """Test deployed RunPod endpoint."""
    
    url = f"https://api.runpod.ai/v2/{endpoint_id}/runsync"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": {
            "prompt": "a cinematic photo of a fox in a forest, golden hour lighting",
            "negative_prompt": "blurry, low quality, deformed",
            "width": 1024,
            "height": 1024,
            "num_inference_steps": 8,
            "guidance_scale": 3.5,
            "seed": 42,
            "return_type": "base64"
        }
    }
    
    print(f"Testing endpoint: {endpoint_id}")
    print(f"Prompt: {payload['input']['prompt']}")
    
    response = requests.post(url, json=payload, headers=headers, timeout=300)
    response.raise_for_status()
    
    result = response.json()
    
    if 'output' in result:
        output = result['output']
        print("\nResult:")
        print(json.dumps({k: v for k, v in output.items() if k != 'images_base64'}, indent=2))
        
        if 'images_base64' in output:
            print(f"\nGenerated {len(output['images_base64'])} image(s)")
            
            # Save first image
            output_dir = Path("./test_outputs")
            output_dir.mkdir(exist_ok=True)
            
            output_path = output_dir / "endpoint_test_output.png"
            with open(output_path, 'wb') as f:
                f.write(base64.b64decode(output['images_base64'][0]))
            
            print(f"Saved to: {output_path}")
    else:
        print("\nFull Response:")
        print(json.dumps(result, indent=2))


def test_batch(endpoint_id: str, api_key: str):
    """Test batch generation."""
    
    url = f"https://api.runpod.ai/v2/{endpoint_id}/runsync"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "input": {
            "prompt": "a beautiful landscape with mountains and lakes",
            "negative_prompt": "blurry",
            "width": 1024,
            "height": 1024,
            "num_inference_steps": 8,
            "guidance_scale": 3.5,
            "batch_size": 4,
            "return_type": "base64"
        }
    }
    
    print("Testing batch generation (4 images)...")
    
    response = requests.post(url, json=payload, headers=headers, timeout=300)
    response.raise_for_status()
    
    result = response.json()
    output = result.get('output', {})
    
    if 'images_base64' in output:
        print(f"\nGenerated {len(output['images_base64'])} image(s) in {output['parameters']['generation_time_seconds']}s")
        
        output_dir = Path("./test_outputs/batch")
        output_dir.mkdir(exist_ok=True, parents=True)
        
        for i, img_b64 in enumerate(output['images_base64']):
            output_path = output_dir / f"batch_{i}.png"
            with open(output_path, 'wb') as f:
                f.write(base64.b64decode(img_b64))
            print(f"Saved: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Z-Image Turbo handler")
    parser.add_argument("--mode", choices=["local", "endpoint", "batch"], default="endpoint",
                       help="Test mode")
    parser.add_argument("--endpoint-id", help="RunPod endpoint ID")
    parser.add_argument("--api-key", help="RunPod API key")
    
    args = parser.parse_args()
    
    if args.mode == "local":
        test_local()
    elif args.mode == "batch":
        endpoint_id = args.endpoint_id or os.environ.get('RUNPOD_ENDPOINT_ID')
        api_key = args.api_key or os.environ.get('RUNPOD_API_KEY')
        
        if not endpoint_id or not api_key:
            print("Error: Provide --endpoint-id and --api-key or set RUNPOD_ENDPOINT_ID and RUNPOD_API_KEY env vars")
            sys.exit(1)
        
        test_batch(endpoint_id, api_key)
    else:
        endpoint_id = args.endpoint_id or os.environ.get('RUNPOD_ENDPOINT_ID')
        api_key = args.api_key or os.environ.get('RUNPOD_API_KEY')
        
        if not endpoint_id or not api_key:
            print("Error: Provide --endpoint-id and --api-key or set RUNPOD_ENDPOINT_ID and RUNPOD_API_KEY env vars")
            sys.exit(1)
        
        test_endpoint(endpoint_id, api_key)
