#!/bin/bash

cd /ComfyUI

python3 main.py --listen 127.0.0.1 --port 8188 --disable-auto-launch &
COMFY_PID=$!

echo "Waiting for ComfyUI..."
until curl -s http://127.0.0.1:8188/system_stats > /dev/null; do
  sleep 1
done

echo "ComfyUI ready."

python3 /handler.py