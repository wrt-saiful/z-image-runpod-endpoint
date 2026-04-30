import runpod
import requests
import uuid
import json
import time
import base64

COMFY_URL = "http://127.0.0.1:8188"
WORKFLOW_PATH = "/workflows/zimage_turbo_api.json"


def queue_prompt(workflow):
    r = requests.post(f"{COMFY_URL}/prompt", json={
        "prompt": workflow,
        "client_id": str(uuid.uuid4())
    })
    return r.json()["prompt_id"]


def get_result(prompt_id):
    while True:
        res = requests.get(f"{COMFY_URL}/history/{prompt_id}").json()
        if prompt_id in res:
            outputs = res[prompt_id]["outputs"]

            for node in outputs.values():
                if "images" in node:
                    img = node["images"][0]

                    data = requests.get(f"{COMFY_URL}/view", params={
                        "filename": img["filename"],
                        "subfolder": img.get("subfolder", ""),
                        "type": img.get("type", "output")
                    }).content

                    return base64.b64encode(data).decode()

        time.sleep(1)


def handler(event):
    data = event.get("input", {})

    prompt = data.get("prompt", "A cinematic AI image")
    negative = data.get("negative_prompt", "")

    with open(WORKFLOW_PATH) as f:
        workflow = json.load(f)

    # CHANGE node IDs based on your workflow
    workflow["6"]["inputs"]["text"] = prompt
    workflow["7"]["inputs"]["text"] = negative

    pid = queue_prompt(workflow)
    img = get_result(pid)

    return {"image": img}


runpod.serverless.start({"handler": handler})