FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV HF_HUB_ENABLE_HF_TRANSFER=1

RUN apt-get update && apt-get install -y \
    git python3 python3-pip ffmpeg libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /

# clone ComfyUI
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /ComfyUI

WORKDIR /ComfyUI

# install minimal deps
COPY requirements.txt .
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt

# install ComfyUI core only
RUN pip3 install --no-cache-dir -r requirements.txt || true

# copy app
COPY handler.py /handler.py
COPY start.sh /start.sh
COPY workflows /workflows

RUN chmod +x /start.sh

EXPOSE 8188

CMD ["/start.sh"]