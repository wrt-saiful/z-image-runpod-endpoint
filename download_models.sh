#!/bin/bash
# Download all Z-Image Turbo model files from Comfy-Org/z_image_turbo
# Can be used in Dockerfile or run standalone to populate a network volume

set -e  # Exit on error

BASE_URL="https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main"
MODEL_DIR="${MODEL_DIR:-/models/z-image-turbo}"

echo "[download] Creating directory structure..."
mkdir -p "$MODEL_DIR/diffusion_models"
mkdir -p "$MODEL_DIR/text_encoders"
mkdir -p "$MODEL_DIR/vae"

# Function to download with retry
download_file() {
    local url="$1"
    local output="$2"
    local max_retries=3
    local retry=0
    
    echo "[download] Fetching: $url"
    
    while [ $retry -lt $max_retries ]; do
        if wget --progress=bar:force:noscroll -O "$output" "$url" 2>&1; then
            echo "[download] ✓ Downloaded: $output"
            return 0
        else
            retry=$((retry + 1))
            echo "[download] ✗ Retry $retry/$max_retries..."
            sleep 2
        fi
    done
    
    echo "[download] ✗ Failed after $max_retries attempts: $url"
    return 1
}

echo "[download] Starting download of Z-Image Turbo model files..."

# Core model files (REQUIRED)
download_file \
    "$BASE_URL/split_files/diffusion_models/z_image_turbo.safetensors" \
    "$MODEL_DIR/diffusion_models/z_image_turbo.safetensors"

download_file \
    "$BASE_URL/split_files/text_encoders/clip_l.safetensors" \
    "$MODEL_DIR/text_encoders/clip_l.safetensors"

download_file \
    "$BASE_URL/split_files/vae/ae.safetensors" \
    "$MODEL_DIR/vae/ae.safetensors"

# Config and metadata files (REQUIRED for diffusers)
download_file \
    "$BASE_URL/model_index.json" \
    "$MODEL_DIR/model_index.json"

# Additional helpful files (optional, won't fail build if missing)
download_file \
    "$BASE_URL/README.md" \
    "$MODEL_DIR/README.md" || true

download_file \
    "$BASE_URL/config.json" \
    "$MODEL_DIR/config.json" || true

# Try to get any scheduler config if it exists
download_file \
    "$BASE_URL/scheduler/scheduler_config.json" \
    "$MODEL_DIR/scheduler_config.json" || true

# Try to get tokenizer files if they exist in the repo
download_file \
    "$BASE_URL/tokenizer/tokenizer_config.json" \
    "$MODEL_DIR/tokenizer_config.json" || true

download_file \
    "$BASE_URL/tokenizer/vocab.json" \
    "$MODEL_DIR/vocab.json" || true

echo ""
echo "[download] ================================================"
echo "[download] Download complete! Model files in: $MODEL_DIR"
echo "[download] ================================================"
echo ""

# Show directory tree and sizes
if command -v tree &> /dev/null; then
    tree -h "$MODEL_DIR"
else
    du -h --max-depth=2 "$MODEL_DIR"
fi

echo ""
echo "[download] Total size:"
du -sh "$MODEL_DIR"
