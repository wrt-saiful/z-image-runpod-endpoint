# ComfyUI-based RunPod Serverless for Z-Image Turbo
# Models download on FIRST RUN to network volume (not during build)
# This avoids needing HuggingFace access during Docker build

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

# Create model directories (will be populated from network volume)
RUN mkdir -p /app/ComfyUI/models/checkpoints && \
    mkdir -p /app/ComfyUI/models/clip && \
    mkdir -p /app/ComfyUI/models/vae

# Copy handler and workflow
COPY comfy_handler_with_download.py /app/comfy_handler.py
COPY workflow_api.json /app/

WORKDIR /app

# Handler will download models on first run if not present
CMD ["python", "-u", "comfy_handler.py"]
