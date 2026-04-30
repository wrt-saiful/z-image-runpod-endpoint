FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV HF_HUB_ENABLE_HF_TRANSFER=1

RUN apt-get update && apt-get install -y \
    git curl wget ffmpeg libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /

RUN git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git /ComfyUI
WORKDIR /ComfyUI

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir runpod requests websocket-client pillow huggingface_hub hf_transfer

# 🔥 DOWNLOAD MODEL DURING BUILD (IMPORTANT)
RUN mkdir -p models/text_encoders models/diffusion_models models/vae

RUN huggingface-cli download Comfy-Org/z_image_turbo \
    split_files/text_encoders/qwen_3_4b.safetensors \
    --local-dir models/text_encoders

RUN huggingface-cli download Comfy-Org/z_image_turbo \
    split_files/diffusion_models/z_image_turbo_bf16.safetensors \
    --local-dir models/diffusion_models

RUN huggingface-cli download Comfy-Org/z_image_turbo \
    split_files/vae/ae.safetensors \
    --local-dir models/vae

COPY handler.py /handler.py
COPY start.sh /start.sh
COPY workflows /workflows

RUN chmod +x /start.sh

EXPOSE 8188
CMD ["/start.sh"]