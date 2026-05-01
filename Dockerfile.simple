FROM runpod/pytorch:2.2.1-py3.10-cuda12.1.1-devel-ubuntu22.04

# Set working directory
WORKDIR /

# Update and install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    git \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git
WORKDIR /ComfyUI
RUN pip install -r requirements.txt
RUN pip install runpod

# Install ComfyUI Manager (helps with custom nodes)
WORKDIR /ComfyUI/custom_nodes
RUN git clone https://github.com/ltdrdata/ComfyUI-Manager.git

# Go back to ComfyUI root
WORKDIR /ComfyUI

# Copy handler script
ADD handler.py /ComfyUI/handler.py

# Set the environment variable for network volume
ENV COMFYUI_PATH=/ComfyUI

# Handler will download models on first run
CMD ["python", "handler.py"]
