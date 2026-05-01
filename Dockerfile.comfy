# ComfyUI-based RunPod Serverless setup for Z-Image Turbo
# Uses ComfyUI's API as middleware - the native format for this model

FROM nvidia/cuda:12.1.1-cudnn8-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3-pip python3.10-venv \
    git wget curl ca-certificates \
    libgl1 libglib2.0-0 libsm6 libxext6 libxrender-dev \
 && ln -sf /usr/bin/python3.10 /usr/bin/python \
 && ln -sf /usr/bin/python3.10 /usr/bin/python3 \
 && rm -rf /var/lib/apt/lists/*

# Install PyTorch for CUDA 12.1
RUN pip install --upgrade pip && \
    pip install torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cu121

WORKDIR /app

# Clone ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /app/ComfyUI && \
    cd /app/ComfyUI && \
    pip install -r requirements.txt && \
    pip install runpod huggingface_hub

# Download Z-Image Turbo model files directly
RUN mkdir -p /app/ComfyUI/models/checkpoints && \
    mkdir -p /app/ComfyUI/models/clip && \
    mkdir -p /app/ComfyUI/models/vae

# Download model components from Comfy-Org repo
RUN echo "Downloading Z-Image Turbo checkpoint..." && \
    wget -O /app/ComfyUI/models/checkpoints/z_image_turbo.safetensors \
    https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/diffusion_models/z_image_turbo.safetensors

RUN echo "Downloading CLIP text encoder..." && \
    wget -O /app/ComfyUI/models/clip/clip_l.safetensors \
    https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/text_encoders/clip_l.safetensors

RUN echo "Downloading VAE..." && \
    wget -O /app/ComfyUI/models/vae/ae.safetensors \
    https://huggingface.co/Comfy-Org/z_image_turbo/resolve/main/split_files/vae/ae.safetensors

# Verify downloads
RUN echo "=== Model files downloaded ===" && \
    ls -lh /app/ComfyUI/models/checkpoints/ && \
    ls -lh /app/ComfyUI/models/clip/ && \
    ls -lh /app/ComfyUI/models/vae/ && \
    du -sh /app/ComfyUI/models/

# Copy handler and workflow
COPY comfy_handler.py /app/
COPY workflow_api.json /app/

WORKDIR /app

CMD ["python", "-u", "comfy_handler.py"]
