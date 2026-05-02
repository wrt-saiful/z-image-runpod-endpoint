# Z-Image Turbo RunPod Serverless

🚀 Production-ready RunPod Serverless endpoint for [Z-Image Turbo](https://comfyanonymous.github.io/ComfyUI_examples/z_image/) model using ComfyUI backend.

[![Deploy on RunPod](https://img.shields.io/badge/Deploy-RunPod-purple)](https://runpod.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

- 🎨 **Text-to-Image** generation with Z-Image Turbo
- 🖼️ **Image-to-Image** transformation support
- 📦 **Batch generation** (up to 4 images per request)
- 🔗 **Flexible output** (base64, URL, or both)
- ⚡ **Network volume support** (fast builds, persistent models)
- 🛠️ **ControlNet ready** (infrastructure in place)
- 📊 **Detailed logging** and error handling
- 🧪 **Comprehensive testing** suite included

## 🎯 Quick Start

### 1. Build & Push Docker Image

```bash
# Clone this repo
git clone https://github.com/YOUR_USERNAME/z-image-turbo-runpod.git
cd z-image-turbo-runpod

# Build
docker build -t YOUR_DOCKERHUB_USER/z-image-turbo:latest .

# Push
docker push YOUR_DOCKERHUB_USER/z-image-turbo:latest
```

**Build time:** ~10 minutes (no models included, fast!)

### 2. Create Network Volume on RunPod

1. Go to [RunPod Console](https://runpod.io) → **Storage** → **Network Volumes**
2. Click **+ Network Volume**
3. **Name:** `z-image-models`
4. **Size:** 15 GB
5. **Data Center:** Select same region as your endpoint
6. Click **Create**

### 3. Create Serverless Endpoint

1. Go to **Serverless** → **+ New Endpoint**
2. **Container Image:** `YOUR_DOCKERHUB_USER/z-image-turbo:latest`
3. **GPU Types:** Select 48GB tier (A6000, L40, L40S)
4. **Container Disk:** 20 GB
5. **Network Volume:** 
   - Select `z-image-models`
   - Mount path: `/runpod-volume`
6. **Workers:**
   - Min: 0 (scale to zero)
   - Max: 1-3 (based on your needs)
7. **Idle Timeout:** 60 seconds
8. **FlashBoot:** Enable ✅
9. Click **Deploy**

### 4. Test Your Endpoint

```bash
export RUNPOD_API_KEY="your_api_key_here"
export RUNPOD_ENDPOINT_ID="your_endpoint_id_here"

python tests/test_handler.py
```

## 📡 API Usage

### Basic Text-to-Image

```python
import requests
import os

url = f"https://api.runpod.ai/v2/{os.environ['RUNPOD_ENDPOINT_ID']}/runsync"
headers = {
    "Authorization": f"Bearer {os.environ['RUNPOD_API_KEY']}",
    "Content-Type": "application/json"
}

payload = {
    "input": {
        "prompt": "a majestic snow leopard on a rocky cliff at sunset, cinematic lighting",
        "negative_prompt": "blurry, low quality, deformed",
        "width": 1024,
        "height": 1024,
        "num_inference_steps": 8,
        "guidance_scale": 3.5,
        "seed": 42,
        "return_type": "base64"  # or "url" or "both"
    }
}

response = requests.post(url, json=payload, headers=headers)
result = response.json()

# Get base64 image
image_b64 = result['output']['images_base64'][0]
```

### Image-to-Image

```python
import base64

# Read your init image
with open('input.png', 'rb') as f:
    init_image_b64 = base64.b64encode(f.read()).decode()

payload = {
    "input": {
        "mode": "img2img",
        "prompt": "transform into a watercolor painting",
        "negative_prompt": "blurry, low quality",
        "init_image_base64": init_image_b64,
        "denoising_strength": 0.75,  # 0.0 to 1.0
        "width": 1024,
        "height": 1024,
        "num_inference_steps": 8,
        "guidance_scale": 3.5,
        "return_type": "base64"
    }
}

response = requests.post(url, json=payload, headers=headers)
```

### Batch Generation

```python
payload = {
    "input": {
        "prompt": "a beautiful landscape with mountains",
        "width": 1024,
        "height": 1024,
        "num_inference_steps": 8,
        "batch_size": 4,  # Generate 4 images at once
        "return_type": "base64"
    }
}
```

## 📋 API Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prompt` | string | **required** | Text description of desired image |
| `negative_prompt` | string | `""` | What to avoid in generation |
| `width` | int | `1024` | Image width (512-2048) |
| `height` | int | `1024` | Image height (512-2048) |
| `num_inference_steps` | int | `8` | Number of denoising steps (1-50) |
| `guidance_scale` | float | `3.5` | CFG scale (1.0-20.0) |
| `seed` | int | random | Random seed for reproducibility |
| `batch_size` | int | `1` | Number of images to generate (1-4) |
| `return_type` | string | `"base64"` | Output format: `"base64"`, `"url"`, or `"both"` |
| `mode` | string | `"txt2img"` | Generation mode: `"txt2img"` or `"img2img"` |
| `init_image_base64` | string | - | Base64 encoded init image (for img2img) |
| `denoising_strength` | float | `0.75` | Strength for img2img (0.0-1.0) |
| `sampler` | string | `"euler"` | Sampler name |
| `scheduler` | string | `"normal"` | Scheduler type |

## 🚀 First Run

**Important:** The first request will take ~10-15 minutes as models download to the network volume:

- `z_image_turbo.safetensors` (8 GB)
- `clip_l.safetensors` (500 MB)
- `ae.safetensors` (300 MB)

After the first download, all subsequent requests are fast (~2-3s per image).

## ⚡ Performance

| Metric | Value |
|--------|-------|
| **Cold start** | ~15s (with FlashBoot) |
| **First inference** | 10-15 min (one-time model download) |
| **Warm inference** | 2-3s (1024x1024, 8 steps, L40) |
| **Batch of 4** | ~6-8s |

## 🔧 Advanced Configuration

### Using S3 for Image URLs

To enable URL output, set the `S3_BUCKET` environment variable in your RunPod endpoint:

```bash
S3_BUCKET=your-bucket-name
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
```

Then use `"return_type": "url"` or `"both"` in your requests.

### Custom Samplers

Supported samplers:
- `euler` (default, fast)
- `euler_ancestral`
- `dpmpp_2m`
- `dpmpp_2m_karras`
- `heun`
- `dpm_2`
- `lms`
- `ddim`

### Multiple Seeds

For variation with batch generation:

```python
payload = {
    "input": {
        "prompt": "a fox in a forest",
        "seed": 42,
        "batch_size": 4
    }
}
# Generates 4 images with seeds: 42, 43, 44, 45
```

## 🛠️ Development

### Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run local test (requires ComfyUI setup)
python tests/test_handler.py --mode local

# Test deployed endpoint
python tests/test_handler.py --endpoint-id YOUR_ID --api-key YOUR_KEY

# Test batch generation
python tests/test_handler.py --mode batch
```

### Project Structure

```
.
├── Dockerfile              # Container setup
├── src/
│   ├── handler.py         # Main RunPod handler
│   ├── model_manager.py   # Model download manager
│   └── utils.py           # Helper functions
├── workflows/
│   └── txt2img_basic.json # Example ComfyUI workflow
├── tests/
│   └── test_handler.py    # Test suite
├── README.md
└── LICENSE
```

## 📊 Monitoring & Debugging

### Check Model Status

The handler logs model status on startup:

```
[ModelManager] Using network volume: /runpod-volume/models
[ModelManager] ✓ checkpoint: Already exists (8123.4 MB)
[ModelManager] ✓ clip: Already exists (492.1 MB)
[ModelManager] ✓ vae: Already exists (312.8 MB)
```

### System Information

On startup, the handler logs GPU and system info:

```json
{
  "platform": "Linux-5.15.0",
  "python_version": "3.10.12",
  "torch_version": "2.2.1",
  "cuda_available": true,
  "cuda_version": "12.1",
  "gpu_name": "NVIDIA L40",
  "gpu_memory_gb": 48.0
}
```

## 🐛 Troubleshooting

### Models Not Downloading

**Check network volume mount:**
```bash
# Should show /runpod-volume
ls -la /
```

**Verify HuggingFace access from worker:**
```bash
curl -I https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/diffusion_models/z_image_turbo.safetensors
```

### Out of Memory

- Reduce `batch_size` to 1
- Lower `width` and `height` to 768x768
- Use 48GB GPU tier (A6000/L40)

### Slow Inference

- Check GPU is being used: Look for "cuda_available": true in logs
- Verify model files are in network volume (not downloading each time)
- First inference is always slower (~5s) due to model loading

### Request Timeout

- First request takes 10-15 min (model download)
- Increase timeout to 900s for first request
- Check RunPod logs for download progress

## 📝 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Credits

- **Z-Image Turbo Model:** [ComfyUI Examples](https://comfyanonymous.github.io/ComfyUI_examples/z_image/)
- **ComfyUI:** [comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
- **RunPod:** [runpod.io](https://runpod.io)

## 🤝 Contributing

Contributions welcome! Please open an issue or PR.

## 📮 Support

- Create an [Issue](https://github.com/YOUR_USERNAME/z-image-turbo-runpod/issues)
- Check [RunPod Documentation](https://docs.runpod.io)
- Join [RunPod Discord](https://discord.gg/runpod)

---

**Made with ❤️ for the RunPod community**
