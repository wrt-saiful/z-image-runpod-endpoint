# CUDA 12.1 + Python 3.10 base — known good with current torch wheels.
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/runpod-volume/huggingface \
    TRANSFORMERS_CACHE=/runpod-volume/huggingface \
    HF_HUB_ENABLE_HF_TRANSFER=1

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 python3-pip python3.10-venv \
    git wget curl ca-certificates \
    libgl1 libglib2.0-0 \
 && ln -sf /usr/bin/python3.10 /usr/bin/python \
 && ln -sf /usr/bin/python3.10 /usr/bin/python3 \
 && rm -rf /var/lib/apt/lists/*

# Torch matched to CUDA 12.1
RUN pip install --upgrade pip && \
    pip install torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cu121

WORKDIR /app

# Python deps
COPY requirements.txt .
RUN pip install -r requirements.txt && \
    pip install hf_transfer

# ---- Bake the model into the image (recommended) -----------------------
# This avoids a multi-GB download on every cold start. Comment this block
# out if you'd rather use a network volume and download on first run.
ARG MODEL_ID=Tongyi-MAI/Z-Image-Turbo
ENV MODEL_ID=${MODEL_ID}
RUN python -c "from huggingface_hub import snapshot_download; \
    snapshot_download(repo_id='${MODEL_ID}', \
                      local_dir='/models/z-image-turbo', \
                      local_dir_use_symlinks=False)"
ENV MODEL_ID=/models/z-image-turbo
# ------------------------------------------------------------------------

COPY handler.py .

CMD ["python", "-u", "handler.py"]
