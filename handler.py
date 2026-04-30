import base64
import copy
import json
import os
import time
import uuid
from typing import Any, Dict

import requests
import runpod


COMFY_URL = os.getenv("COMFY_URL", "http://127.0.0.1:8188")
WORKFLOW_PATH = os.getenv("WORKFLOW_PATH", "/workflows/zimage_turbo_api.json")
TIMEOUT_SECONDS = int(os.getenv("TIMEOUT_SECONDS", "300"))


with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
    BASE_WORKFLOW = json.load(f)


def set_node_input(workflow: Dict[str, Any], node_id: str, key: str, value: Any):
    if node_id in workflow and "inputs" in workflow[node_id]:
        workflow[node_id]["inputs"][key] = value


def queue_prompt(workflow: Dict[str, Any]) -> str:
    payload = {
        "prompt": workflow,
        "client_id": str(uuid.uuid4())
    }

    r = requests.post(f"{COMFY_URL}/prompt", json=payload, timeout=30)
    r.raise_for_status()

    data = r.json()

    if "prompt_id" not in data:
        raise RuntimeError(f"No prompt_id returned: {data}")

    return data["prompt_id"]


def wait_for_image(prompt_id: str) -> str:
    start = time.time()

    while time.time() - start < TIMEOUT_SECONDS:
        r = requests.get(f"{COMFY_URL}/history/{prompt_id}", timeout=30)
        r.raise_for_status()

        history = r.json()

        if prompt_id in history:
            outputs = history[prompt_id].get("outputs", {})

            for output in outputs.values():
                images = output.get("images")
                if images:
                    img = images[0]

                    view_params = {
                        "filename": img["filename"],
                        "subfolder": img.get("subfolder", ""),
                        "type": img.get("type", "output")
                    }

                    img_res = requests.get(
                        f"{COMFY_URL}/view",
                        params=view_params,
                        timeout=60
                    )
                    img_res.raise_for_status()

                    return base64.b64encode(img_res.content).decode("utf-8")

        time.sleep(0.5)

    raise TimeoutError("Image generation timeout")


def handler(event):
    try:
        data = event.get("input", {})

        prompt = data.get("prompt", "A cinematic futuristic AI server room")
        negative_prompt = data.get("negative_prompt", "blurry, low quality")
        width = int(data.get("width", 1024))
        height = int(data.get("height", 1024))
        steps = int(data.get("steps", 8))
        cfg = float(data.get("cfg", 1.0))
        seed = int(data.get("seed", int(time.time())))

        workflow = copy.deepcopy(BASE_WORKFLOW)

        # Change these node IDs based on your exported API workflow JSON
        POSITIVE_NODE = os.getenv("POSITIVE_NODE", "6")
        NEGATIVE_NODE = os.getenv("NEGATIVE_NODE", "7")
        LATENT_NODE = os.getenv("LATENT_NODE", "5")
        SAMPLER_NODE = os.getenv("SAMPLER_NODE", "3")

        set_node_input(workflow, POSITIVE_NODE, "text", prompt)
        set_node_input(workflow, NEGATIVE_NODE, "text", negative_prompt)
        set_node_input(workflow, LATENT_NODE, "width", width)
        set_node_input(workflow, LATENT_NODE, "height", height)
        set_node_input(workflow, SAMPLER_NODE, "steps", steps)
        set_node_input(workflow, SAMPLER_NODE, "cfg", cfg)
        set_node_input(workflow, SAMPLER_NODE, "seed", seed)

        prompt_id = queue_prompt(workflow)
        image_base64 = wait_for_image(prompt_id)

        return {
            "success": True,
            "seed": seed,
            "image_base64": image_base64
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


runpod.serverless.start({"handler": handler})