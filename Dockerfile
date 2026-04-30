FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV HF_HUB_ENABLE_HF_TRANSFER=1

RUN apt-get update && apt-get install -y \
    git wget curl python3 python3-pip python3-venv ffmpeg libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /

RUN git clone https://github.com/comfyanonymous/ComfyUI.git /ComfyUI

WORKDIR /ComfyUI

RUN pip3 install --upgrade pip
RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
RUN pip3 install -r requirements.txt
RUN pip3 install runpod requests websocket-client pillow huggingface_hub[hf_transfer]

# Download Z-Image Turbo models
RUN mkdir -p models/text_encoders models/diffusion_models models/vae

RUN huggingface-cli download Comfy-Org/z_image_turbo \
    split_files/text_encoders/qwen_3_4b.safetensors \
    --local-dir /ComfyUI/models --local-dir-use-symlinks False

RUN huggingface-cli download Comfy-Org/z_image_turbo \
    split_files/diffusion_models/z_image_turbo_bf16.safetensors \
    --local-dir /ComfyUI/models --local-dir-use-symlinks False

RUN huggingface-cli download Comfy-Org/z_image_turbo \
    split_files/vae/ae.safetensors \
    --local-dir /ComfyUI/models --local-dir-use-symlinks False

RUN mv /ComfyUI/models/split_files/text_encoders/* /ComfyUI/models/text_encoders/ && \
    mv /ComfyUI/models/split_files/diffusion_models/* /ComfyUI/models/diffusion_models/ && \
    mv /ComfyUI/models/split_files/vae/* /ComfyUI/models/vae/ && \
    rm -rf /ComfyUI/models/split_files

COPY handler.py /handler.py
COPY start.sh /start.sh
COPY workflows /workflows

RUN chmod +x /start.sh

EXPOSE 8188

CMD ["/start.sh"]