# Z-Image Turbo on RunPod Serverless

Direct `diffusers`-based deployment, returns base64 PNGs. Targets 48GB GPUs (A6000 / L40 / L40S).

## Files

| File | Purpose |
|---|---|
| `handler.py` | RunPod handler — loads pipeline once, generates images per request |
| `Dockerfile` | CUDA 12.1 + torch 2.4 + diffusers (from source) + model baked in |
| `requirements.txt` | Python deps |
| `test_input.json` | Sample input for local testing |
| `client_example.py` | Example HTTP client for the deployed endpoint |

## Model Loading Strategy

This setup downloads model files **directly from Comfy-Org/z_image_turbo** via wget in the Dockerfile:

- **Diffusion model**: `split_files/diffusion_models/z_image_turbo.safetensors` (~8GB)
- **Text encoder**: `split_files/text_encoders/clip_l.safetensors` (~500MB)
- **VAE**: `split_files/vae/ae.safetensors` (~300MB)
- **Config files**: `model_index.json`, `README.md`, etc.

All files are baked into `/models/z-image-turbo/` at build time — **no network volume needed, no cold-start downloads**.

### Two Handler Options

**`handler.py`** (recommended first try):
- Attempts to load via `DiffusionPipeline.from_pretrained()` auto-detection
- Falls back to `ZImagePipeline` if available in your diffusers version
- Simplest approach if diffusers recognizes the model structure

**`handler_comfy_format.py`** (ComfyUI checkpoint loader):
- Loads individual safetensors files using `from_single_file()`
- Manually assembles UNet, VAE, text encoder, scheduler into a pipeline
- More robust for ComfyUI-native checkpoint formats
- Use this if `handler.py` fails with "unrecognized model format"

To switch handlers, change the Dockerfile's last line from:
```dockerfile
COPY handler.py .
CMD ["python", "-u", "handler.py"]
```
to:
```dockerfile
COPY handler_comfy_format.py handler.py
CMD ["python", "-u", "handler.py"]
```

## Build & push

```bash
# 1. Build (this will download ~15-20GB of model weights into the image)
docker build -t YOUR_DOCKERHUB_USER/z-image-turbo:v1 .

# 2. Push to a registry RunPod can pull from
docker push YOUR_DOCKERHUB_USER/z-image-turbo:v1
```

If the image gets too big, switch to using a **RunPod network volume** instead of baking the model in:

1. Create a network volume in the RunPod console.
2. Comment out the `RUN python -c "...snapshot_download..."` block in `Dockerfile`.
3. Set `MODEL_ID=Tongyi-MAI/Z-Image-Turbo` as an env var on the endpoint — first cold start will download to `/runpod-volume/huggingface` and subsequent starts will reuse it.

## Deploy on RunPod

1. RunPod Console → **Serverless → New Endpoint**.
2. **Container image:** `YOUR_DOCKERHUB_USER/z-image-turbo:v1`
3. **GPU types:** select 48GB tier (A6000, L40, L40S).
4. **Container disk:** 30GB+ if model is baked in.
5. **Workers:** min 0 (scale to zero), max 1–3.
6. **Idle timeout:** 5–30s depending on traffic patterns. Lower = cheaper, more cold starts.
7. **Active workers:** 0 unless you need always-on (you pay for these even when idle).
8. **FlashBoot:** enable — cuts cold start latency significantly.
9. **HF token:** if the repo is gated, add `HF_TOKEN` as an env var.

## Test locally (without GPU it'll error, but validates the flow)

```bash
python handler.py --rp_serve_api    # starts a local server
# in another shell:
curl -X POST http://localhost:8000/runsync \
  -H "Content-Type: application/json" \
  --data @test_input.json
```

Or test on RunPod's UI — there's a **"Run"** tab on every endpoint where you can paste `test_input.json`.

## Call from a client

```bash
export RUNPOD_API_KEY=rpa_xxx
export RUNPOD_ENDPOINT_ID=xxxxxxxx
python client_example.py "a cinematic photo of a fox in a forest"
```

## Tuning notes

- Z-Image **Turbo** is tuned for ~6–10 steps. Don't waste time on 30+.
- `guidance_scale` for turbo variants is usually low (1.0–4.0). Higher CFG often hurts.
- bf16 is faster and stable on L40/A6000. Use fp16 only if you hit a bf16-incompatible op.
- If you want to add `torch.compile` for speed, expect 30–60s extra warm-up on the first request after cold start. Worth it only if your worker stays warm.
- For multi-image batches, increase `num_images_per_prompt` rather than calling N times.
