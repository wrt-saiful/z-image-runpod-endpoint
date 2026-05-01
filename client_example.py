"""
Minimal client for calling your RunPod Z-Image Turbo endpoint.

Usage:
    export RUNPOD_API_KEY=...
    export RUNPOD_ENDPOINT_ID=...
    python client_example.py "a fox in a forest"
"""

import os
import sys
import time
import base64
import requests

API_KEY = os.environ["RUNPOD_API_KEY"]
ENDPOINT_ID = os.environ["RUNPOD_ENDPOINT_ID"]
BASE = f"https://api.runpod.ai/v2/{ENDPOINT_ID}"
HEADERS = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}


def run_sync(prompt: str) -> dict:
    """Synchronous call — blocks until done. Use for short jobs (<30s)."""
    payload = {
        "input": {
            "prompt": prompt,
            "width": 1024,
            "height": 1024,
            "num_inference_steps": 8,
            "guidance_scale": 3.5,
            "seed": 42,
        }
    }
    r = requests.post(f"{BASE}/runsync", json=payload, headers=HEADERS, timeout=300)
    r.raise_for_status()
    return r.json()


def run_async(prompt: str) -> dict:
    """Async call — returns a job id, then polls /status/{id}."""
    payload = {"input": {"prompt": prompt, "num_inference_steps": 8}}
    r = requests.post(f"{BASE}/run", json=payload, headers=HEADERS, timeout=30)
    r.raise_for_status()
    job_id = r.json()["id"]
    print(f"Job queued: {job_id}")

    while True:
        s = requests.get(f"{BASE}/status/{job_id}", headers=HEADERS, timeout=30).json()
        status = s.get("status")
        print(f"  status={status}")
        if status in ("COMPLETED", "FAILED", "CANCELLED"):
            return s
        time.sleep(2)


def save_b64_image(b64: str, path: str):
    with open(path, "wb") as f:
        f.write(base64.b64decode(b64))
    print(f"Saved -> {path}")


if __name__ == "__main__":
    prompt = sys.argv[1] if len(sys.argv) > 1 else "a fox in a forest"
    print(f"Prompt: {prompt}")

    result = run_sync(prompt)
    output = result.get("output", {})

    if "error" in output:
        print("ERROR:", output["error"])
        sys.exit(1)

    for i, b64 in enumerate(output.get("images", [])):
        save_b64_image(b64, f"out_{i}.png")
