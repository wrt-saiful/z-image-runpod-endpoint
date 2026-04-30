FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV COMFYUI_PATH=/ComfyUI
ENV COMFYUI_PORT=8188

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl wget ffmpeg libgl1 libglib2.0-0 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /

RUN git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git /ComfyUI

WORKDIR /ComfyUI

RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir runpod requests websocket-client pillow huggingface_hub hf_transfer

COPY handler.py /handler.py
COPY start.sh /start.sh
COPY workflows /workflows

RUN chmod +x /start.sh

EXPOSE 8188

CMD ["/start.sh"]