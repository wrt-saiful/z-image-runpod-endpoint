#!/usr/bin/env bash
set -e

COMFY_DIR="/ComfyUI"
VOLUME_MODELS="/runpod-volume/models"

echo "Checking models..."

mkdir -p "$VOLUME_MODELS/text_encoders" "$VOLUME_MODELS/diffusion_models" "$VOLUME_MODELS/vae"

test -f "$VOLUME_MODELS/text_encoders/qwen_3_4b.safetensors" || { echo "Missing qwen_3_4b.safetensors"; exit 1; }
test -f "$VOLUME_MODELS/diffusion_models/z_image_turbo_bf16.safetensors" || { echo "Missing z_image_turbo_bf16.safetensors"; exit 1; }
test -f "$VOLUME_MODELS/vae/ae.safetensors" || { echo "Missing ae.safetensors"; exit 1; }

rm -rf "$COMFY_DIR/models"
ln -s "$VOLUME_MODELS" "$COMFY_DIR/models"

cd "$COMFY_DIR"

python main.py \
  --listen 127.0.0.1 \
  --port 8188 \
  --disable-auto-launch \
  --disable-metadata \
  --preview-method none &

echo "Waiting for ComfyUI..."

until curl -fsS "http://127.0.0.1:8188/system_stats" > /dev/null; do
  sleep 1
done

echo "ComfyUI ready"

python /handler.py