import runpod
import requests
import websocket
import uuid
import json
import time
import base64
import os

COMFY_URL = "http://127.0.0.1:8188"
WORKFLOW_PATH = "/workflows/zimage_turbo_api.json"


def queue_prompt(workflow):
    payload = {"prompt": workflow, "client_id": str(uuid.uuid4())}
    r = requests.post(f"{COMFY_URL}/prompt", json=payload, timeout=30)
    r.raise_for_status()
    return r.json()["prompt_id"]


def wait_for_result(prompt_id, timeout=300):
    start = time.time()

    while time.time() - start < timeout:
        history = requests.get(f"{COMFY_URL}/history/{prompt_id}", timeout=30).json()

        if prompt_id in history:
            outputs = history[prompt_id]["outputs"]

            for node_id, node_output in outputs.items():
                if "images" in node_output:
                    image = node_output["images"][0]
                    filename = image["filename"]
                    subfolder = image.get("subfolder", "")
                    image_type = image.get("type", "output")

                    params = {
                        "filename": filename,
                        "subfolder": subfolder,
                        "type": image_type
                    }

                    img = requests.get(f"{COMFY_URL}/view", params=params, timeout=60)
                    img.raise_for_status()

                    return base64.b64encode(img.content).decode("utf-8")

        time.sleep(1)

    raise TimeoutError("Generation timed out")


def handler(event):
    try:
        data = event.get("input", {})

        prompt = data.get("prompt", "A cinematic portrait photo")
        negative = data.get("negative_prompt", "")
        width = int(data.get("width", 1024))
        height = int(data.get("height", 1024))
        steps = int(data.get("steps", 8))
        seed = int(data.get("seed", 123456))

        with open(WORKFLOW_PATH, "r") as f:
            workflow = json.load(f)

        # IMPORTANT:
        # Change these node IDs after exporting workflow API JSON from ComfyUI.
        workflow["6"]["inputs"]["text"] = prompt
        workflow["7"]["inputs"]["text"] = negative
        workflow["5"]["inputs"]["width"] = width
        workflow["5"]["inputs"]["height"] = height
        workflow["3"]["inputs"]["steps"] = steps
        workflow["3"]["inputs"]["seed"] = seed

        prompt_id = queue_prompt(workflow)
        image_base64 = wait_for_result(prompt_id)

        return {
            "success": True,
            "image": image_base64
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


runpod.serverless.start({"handler": handler})