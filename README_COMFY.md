# Z-Image Turbo on RunPod Serverless (ComfyUI Backend)

Production-ready setup using **ComfyUI as middleware** - the native format for Z-Image Turbo. Returns base64 PNGs via RunPod API.

## Architecture

```
RunPod Request → comfy_handler.py → ComfyUI API → Z-Image Turbo → PNG → base64 → Response
```

ComfyUI runs as a background service inside the container and handles all model loading, inference, and GPU management.

## Why ComfyUI?

✅ **Native format** - `Comfy-Org/z_image_turbo` ships in ComfyUI checkpoint format  
✅ **Battle-tested** - ComfyUI's model loading is more robust than early diffusers support  
✅ **Easier debugging** - ComfyUI has mature error handling and logging  
✅ **Direct downloads** - wget the .safetensors files, no conversion needed  
✅ **Future-proof** - Easy to add ControlNet, LoRAs, custom nodes later

## Files

| File | Purpose |
|---|---|
| `Dockerfile.comfy` | ComfyUI + Z-Image Turbo setup, models baked in |
| `comfy_handler.py` | RunPod handler that talks to ComfyUI API |
| `workflow_api.json` | Base ComfyUI workflow template (programmatically modified per request) |
| `client_example.py` | HTTP client for the deployed endpoint |
| `test_input.json` | Sample request payload |

## Build & Deploy

```bash
# 1. Build (downloads ~9GB of models directly via wget)
docker build -f Dockerfile.comfy -t YOUR_USERNAME/z-image-turbo-comfy:v1 .

# 2. Push
docker push YOUR_USERNAME/z-image-turbo-comfy:v1

# 3. Deploy on RunPod
#    - Container image: YOUR_USERNAME/z-image-turbo-comfy:v1
#    - GPU: 48GB tier (A6000, L40, L40S)
#    - Container disk: 30GB
#    - Workers: min 0, max 1-3
#    - Idle timeout: 10-30s
#    - Enable FlashBoot
```

## Model Downloads

The Dockerfile downloads these files at build time:

- **Checkpoint**: `z_image_turbo.safetensors` (~8GB)  
  → `/app/ComfyUI/models/checkpoints/`

- **CLIP**: `clip_l.safetensors` (~500MB)  
  → `/app/ComfyUI/models/clip/`

- **VAE**: `ae.safetensors` (~300MB)  
  → `/app/ComfyUI/models/vae/`

All direct wget from `Comfy-Org/z_image_turbo` repo - no HuggingFace Hub API needed.

## API Usage

### Request format (same as before)

```json
{
  "input": {
    "prompt": "a cinematic photo of a fox in a forest",
    "negative_prompt": "blurry, low quality",
    "width": 1024,
    "height": 1024,
    "num_inference_steps": 8,
    "guidance_scale": 3.5,
    "seed": 42,
    "num_images": 1
  }
}
```

### Response format

```json
{
  "images": ["base64_png_string"],
  "parameters": { ... }
}
```

### Using the client

```bash
export RUNPOD_API_KEY=rpa_xxx
export RUNPOD_ENDPOINT_ID=xxxxxxxx
python client_example.py "a majestic snow leopard on a cliff"
```

## How It Works

1. **Cold start**: Container boots, ComfyUI server starts in background (~10-15s with FlashBoot)
2. **Request arrives**: RunPod calls `comfy_handler.py`
3. **Handler**:
   - Loads `workflow_api.json` template
   - Injects user's prompt, size, seed, etc.
   - POSTs workflow to ComfyUI at `http://localhost:8188/prompt`
4. **ComfyUI**:
   - Loads checkpoint (first run only, ~5s)
   - Runs inference (~1-2s for 8 steps on L40)
   - Saves PNG to output folder
5. **Handler**:
   - Polls ComfyUI for completion
   - Fetches PNG from `/view` endpoint
   - Converts to base64
   - Returns to RunPod

## Advantages Over Direct Diffusers

| Aspect | ComfyUI | Direct Diffusers |
|--------|---------|------------------|
| Model loading | ✅ Native .safetensors | ⚠️ Needs conversion or bleeding-edge diffusers |
| Stability | ✅ Mature, proven | ⚠️ Z-Image support is new |
| Debugging | ✅ Clear ComfyUI logs | ❌ Stack traces through PyTorch internals |
| Build time | ✅ Simple wget | ⚠️ Depends on HuggingFace Hub API |
| Extensibility | ✅ Add nodes, LoRAs, ControlNet easily | ❌ Code changes required |

## Troubleshooting

**Build fails on model download:**
```bash
# Test downloads individually
wget https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/diffusion_models/z_image_turbo.safetensors
```

**ComfyUI won't start:**
- Check logs for missing dependencies
- Increase startup wait timeout in `comfy_handler.py` (line 32)

**First request is slow:**
- ComfyUI loads models on first inference (~5s one-time cost)
- Subsequent requests are fast (~1-2s)
- Use "Active workers: 1" to keep warm if you need instant response

**Out of memory:**
- 48GB GPU is recommended
- For 24GB GPUs, reduce resolution or add `--lowvram` flag to ComfyUI startup

## Performance

**Cold start** (FlashBoot enabled): 10-15s  
**Model load** (first request only): ~5s  
**Inference** (8 steps, 1024x1024, L40): ~1-2s  
**Warm requests**: ~2-3s total

## Extending

To add features (LoRA, ControlNet, upscaling):

1. Download additional models to ComfyUI folders during build
2. Modify `workflow_api.json` to include new nodes
3. Update `comfy_handler.py` to accept new parameters
4. Rebuild and redeploy

ComfyUI's node-based system makes this much easier than code-level diffusers changes.
