FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    git curl wget ffmpeg libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /

RUN git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git /ComfyUI
WORKDIR /ComfyUI

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir runpod requests websocket-client pillow

# ✅ create model folders
RUN mkdir -p models/text_encoders models/diffusion_models models/vae models/loras

# 🔥 DIRECT DOWNLOAD (NO huggingface-cli)
RUN wget -q --show-progress -O models/text_encoders/qwen_3_4b.safetensors \
https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/qwen_3_4b.safetensors

RUN wget -q --show-progress -O models/diffusion_models/z_image_turbo_bf16.safetensors \
https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/diffusion_models/z_image_turbo_bf16.safetensors

RUN wget -q --show-progress -O models/vae/ae.safetensors \
https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/vae/ae.safetensors

# optional (faster / alt versions)
RUN wget -q --show-progress -O models/diffusion_models/z_image_turbo_nvfp4.safetensors \
https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/diffusion_models/z_image_turbo_nvfp4.safetensors

RUN wget -q --show-progress -O models/loras/z_image_turbo_distill_patch_lora_bf16.safetensors \
https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/loras/z_image_turbo_distill_patch_lora_bf16.safetensors

COPY handler.py /handler.py
COPY start.sh /start.sh
COPY workflows /workflows

RUN chmod +x /start.sh

EXPOSE 8188
CMD ["/start.sh"]