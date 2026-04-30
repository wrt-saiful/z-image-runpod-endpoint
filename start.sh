#!/bin/bash

cd /ComfyUI

python main.py --listen 127.0.0.1 --port 8188 --disable-auto-launch &

until curl -s http://127.0.0.1:8188/system_stats > /dev/null; do
  sleep 1
done

python /handler.py