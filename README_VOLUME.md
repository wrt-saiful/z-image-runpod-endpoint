# Z-Image Turbo on RunPod Serverless (Network Volume Approach)

**IMPORTANT**: Due to network restrictions during Docker build, this setup downloads models on **first run** to a RunPod network volume.

## Why Network Volume?

Your build environment blocks `huggingface.co`, so we can't download models during `docker build`. Instead:

1. Build a lightweight image (~5GB, no models)
2. Attach a RunPod network volume
3. Models download once on first cold start (~10 minutes)
4. Subsequent workers reuse the downloaded models (instant startup)

## Quick Start

### 1. Build the image

```bash
docker build -f Dockerfile.comfy-volume -t YOUR_USERNAME/z-image-turbo:v1 .
docker push YOUR_USERNAME/z-image-turbo:v1
```

This build is **fast** (~10 minutes) because it doesn't download models.

### 2. Create a Network Volume in RunPod

1. RunPod Console → **Storage** → **Network Volumes**
2. Click **+ Network Volume**
3. **Name**: `z-image-models`
4. **Size**: 15GB (models are ~9GB, leave room for outputs)
5. **Data Center**: Same region as your endpoint
6. Click **Create**

### 3. Create the Endpoint

1. RunPod Console → **Serverless** → **+ New Endpoint**
2. **Container Image**: `YOUR_USERNAME/z-image-turbo:v1`
3. **GPU Types**: Select 48GB tier (A6000, L40, L40S)
4. **Container Disk**: 20GB
5. **Network Volume**: Select `z-image-models`, mount at `/runpod-volume`
6. **Workers**:
   - Min: 0 (scale to zero when idle)
   - Max: 1-3
7. **Idle Timeout**: 60s (longer for first run with downloads)
8. **FlashBoot**: Enable
9. Click **Deploy**

### 4. First Request (Downloads Models)

The **first request** will take ~10-15 minutes as it downloads:
- Checkpoint: 8GB
- CLIP: 500MB
- VAE: 300MB

You'll see progress in the logs:
```
[init] Downloading checkpoint from HuggingFace...
[init] This may take 5-10 minutes...
```

### 5. Subsequent Requests (Fast!)

After the first download:
- **Cold start**: ~10-15s (ComfyUI loads models from volume)
- **Warm inference**: ~2s per image

Models persist in the network volume across all workers.

## Architecture

```
Container Startup
  ↓
Check /runpod-volume/models/
  ↓
Models missing? → Download from HuggingFace (first run only)
  ↓
Models present? → Skip download (all future runs)
  ↓
Start ComfyUI → Load models from volume
  ↓
Ready for requests
```

## API Usage (Same as Before)

```bash
export RUNPOD_API_KEY=rpa_xxx
export RUNPOD_ENDPOINT_ID=xxxxxxxx
python client_example.py "a majestic snow leopard on a cliff"
```

Request format:
```json
{
  "input": {
    "prompt": "a cinematic photo of a fox in a forest",
    "negative_prompt": "blurry, low quality",
    "width": 1024,
    "height": 1024,
    "num_inference_steps": 8,
    "guidance_scale": 3.5,
    "seed": 42
  }
}
```

## Costs

**Network Volume**: ~$0.10/GB/month = ~$1.50/month for 15GB  
**Compute**: Only when processing requests (serverless)  

The small network volume cost is worth it to avoid:
- Slow cold starts downloading models every time
- Build complexity and failures
- Huge Docker images

## Troubleshooting

**First request times out:**
- The 10-minute download is expected
- Check logs to confirm download is progressing
- If it fails, the next request will retry

**"Failed to download" error:**
- Check that HuggingFace is accessible from the worker
- Verify the network volume is mounted at `/runpod-volume`
- Check available space: `df -h /runpod-volume`

**Models download every time:**
- Verify the same network volume is attached to all workers
- Check the mount path is exactly `/runpod-volume`

**Out of space:**
- Increase network volume size to 20GB+
- Clean old ComfyUI output images: `rm -rf /runpod-volume/ComfyUI/output/*`

## Why This Approach?

| Approach | Build Time | First Cold Start | Image Size | Pros |
|----------|------------|------------------|------------|------|
| Bake in image | ❌ Fails (HF blocked) | 10s | 14GB | N/A - can't build |
| Network volume | ✅ 10 min | 10-15 min (first) / 15s (after) | 5GB | Works with network restrictions |

The network volume approach is **the only option** when HuggingFace is blocked during build, and it's actually a good pattern for production (easier to update models, smaller images, shared across workers).

## Updating Models

To update to a new model version:

1. Delete the old files from the volume:
   ```bash
   # SSH into a worker or use RunPod's terminal
   rm -rf /runpod-volume/models/*
   ```

2. Restart the endpoint - it will download fresh models on next request

Or keep multiple model versions in subdirectories and modify the handler to select between them.
