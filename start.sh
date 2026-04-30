#!/bin/bash

cd /ComfyUI

# link models from volume
rm -rf /ComfyUI/models
ln -s /runpod-volume/models /ComfyUI/models

# start comfyui
python3 main.py --listen 127.0.0.1 --port 8188 --disable-auto-launch &
COMFY_PID=$!

# wait until ready
until curl -s http://127.0.0.1:8188/system_stats > /dev/null; do
  sleep 1
done

echo "ComfyUI ready"

# start handler
python3 /handler.py