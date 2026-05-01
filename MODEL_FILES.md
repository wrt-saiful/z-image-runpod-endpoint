# Z-Image Turbo Model Files Manifest

Repository: **Comfy-Org/z_image_turbo**  
Base URL: `https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main`

## Core Model Files (REQUIRED)

### 1. Diffusion Model (UNet)
- **Path**: `split_files/diffusion_models/z_image_turbo.safetensors`
- **Full URL**: https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/diffusion_models/z_image_turbo.safetensors
- **Size**: ~8.0 GB
- **Description**: Main image generation model checkpoint

### 2. Text Encoder (CLIP)
- **Path**: `split_files/text_encoders/clip_l.safetensors`
- **Full URL**: https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/clip_l.safetensors
- **Size**: ~500 MB
- **Description**: CLIP text encoder for processing prompts

### 3. VAE (Autoencoder)
- **Path**: `split_files/vae/ae.safetensors`
- **Full URL**: https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/vae/ae.safetensors
- **Size**: ~300 MB
- **Description**: Variational autoencoder for latent/pixel space conversion

## Configuration Files (REQUIRED for diffusers)

### 4. Model Index
- **Path**: `model_index.json`
- **Full URL**: https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/model_index.json
- **Size**: ~1 KB
- **Description**: Diffusers pipeline configuration

## Optional Files

### 5. README
- **Path**: `README.md`
- **Full URL**: https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/README.md
- **Description**: Model documentation and usage instructions

### 6. Config
- **Path**: `config.json`
- **Full URL**: https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/config.json
- **Description**: Additional model configuration (if present)

### 7. Scheduler Config
- **Path**: `scheduler/scheduler_config.json`
- **Full URL**: https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/scheduler/scheduler_config.json
- **Description**: Sampling scheduler parameters (if present)

### 8. Tokenizer Files
- **Path**: `tokenizer/tokenizer_config.json`
- **Full URL**: https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/tokenizer/tokenizer_config.json

- **Path**: `tokenizer/vocab.json`
- **Full URL**: https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/tokenizer/vocab.json

## Total Download Size

**Minimum**: ~8.8 GB (core files only)  
**Complete**: ~9.0 GB (with all optional files)

## Directory Structure After Download

```
/models/z-image-turbo/
├── diffusion_models/
│   └── z_image_turbo.safetensors    (~8.0 GB)
├── text_encoders/
│   └── clip_l.safetensors           (~500 MB)
├── vae/
│   └── ae.safetensors               (~300 MB)
├── model_index.json                 (~1 KB)
├── README.md                        (optional)
├── config.json                      (optional)
├── scheduler_config.json            (optional)
├── tokenizer_config.json            (optional)
└── vocab.json                       (optional)
```

## Alternative: Use HuggingFace Hub Snapshot Download

If you prefer using the HuggingFace Hub library instead of wget:

```python
from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="Comfy-Org/z_image_turbo",
    local_dir="/models/z-image-turbo",
    local_dir_use_symlinks=False,
    # Optional: download only specific patterns
    allow_patterns=[
        "split_files/**/*.safetensors",
        "*.json",
        "*.md"
    ]
)
```

## Notes

- All `.safetensors` files are in PyTorch format (safe tensors)
- The model uses ComfyUI's split-file structure (files are in `split_files/` subdirectories)
- CLIP L (large) is the standard text encoder for this model
- The VAE filename `ae.safetensors` stands for "autoencoder"
- For production use, verify file checksums after download (not included here)
