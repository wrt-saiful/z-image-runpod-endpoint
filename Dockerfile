FROM runpod/pytorch:2.2.1-py3.10-cuda12.1.1-devel-ubuntu22.04

SHELL ["/bin/bash", "-c"]

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    COMFYUI_PATH=/ComfyUI

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    git \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install ComfyUI
WORKDIR /
RUN git clone https://github.com/comfyanonymous/ComfyUI.git && \
    cd ComfyUI && \
    pip install --no-cache-dir -r requirements.txt

# Install additional dependencies for serverless handler
RUN pip install --no-cache-dir \
    runpod \
    pillow \
    boto3 \
    requests

# Install ComfyUI Manager (for custom nodes management)
WORKDIR /ComfyUI/custom_nodes
RUN git clone https://github.com/ltdrdata/ComfyUI-Manager.git

# Create necessary directories
WORKDIR /ComfyUI
RUN mkdir -p models/checkpoints models/clip models/vae models/controlnet models/loras

# Copy handler and utilities
COPY src/handler.py /ComfyUI/handler.py
COPY src/utils.py /ComfyUI/utils.py
COPY src/model_manager.py /ComfyUI/model_manager.py
COPY workflows/ /ComfyUI/workflows/

# Set working directory
WORKDIR /ComfyUI

# Run the handler
CMD ["python", "-u", "handler.py"]
