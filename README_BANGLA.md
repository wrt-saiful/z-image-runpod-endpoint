# Z-Image Turbo RunPod Serverless - শুরু করার গাইড

## 🎯 এটা কি?

এটি একটি সম্পূর্ণ প্রস্তুত RunPod Serverless endpoint যা Z-Image Turbo AI মডেল ব্যবহার করে ছবি তৈরি করে।

## ⚡ দ্রুত শুরু করুন

### ১. Repository Clone করুন

```bash
git clone https://github.com/YOUR_USERNAME/z-image-turbo-runpod.git
cd z-image-turbo-runpod
```

### ২. Docker Image Build করুন

```bash
./build.sh
```

এটি জিজ্ঞাসা করবে:
- আপনার Docker Hub username
- Push করতে চান কিনা

**Build time:** প্রায় ১০ মিনিট

### ৩. RunPod এ Network Volume তৈরি করুন

1. [RunPod Console](https://runpod.io) এ যান
2. **Storage** → **Network Volumes** → **+ Network Volume**
3. বিস্তারিত:
   - Name: `z-image-models`
   - Size: `15 GB`
   - Region: আপনার endpoint এর সাথে একই
4. **Create** ক্লিক করুন

### ৪. Serverless Endpoint তৈরি করুন

1. **Serverless** → **+ New Endpoint**
2. Configuration:
   - **Container Image:** `YOUR_USERNAME/z-image-turbo:latest`
   - **GPU:** 48GB tier (A6000, L40, L40S)
   - **Container Disk:** 20 GB
   - **Network Volume:** `z-image-models` at `/runpod-volume`
   - **Workers:** Min 0, Max 1-3
   - **Idle Timeout:** 60 seconds
   - **FlashBoot:** Enable করুন ✅
3. **Deploy** ক্লিক করুন

### ৫. Test করুন

```bash
export RUNPOD_API_KEY="আপনার_API_key"
export RUNPOD_ENDPOINT_ID="আপনার_endpoint_id"

python tests/test_handler.py
```

## 🎨 কিভাবে ব্যবহার করবেন

### Python থেকে

```python
import requests
import os

url = f"https://api.runpod.ai/v2/{os.environ['RUNPOD_ENDPOINT_ID']}/runsync"
headers = {
    "Authorization": f"Bearer {os.environ['RUNPOD_API_KEY']}",
    "Content-Type": "application/json"
}

payload = {
    "input": {
        "prompt": "একটি সুন্দর বাংলাদেশী গ্রামের দৃশ্য, সূর্যাস্তের সময়",
        "negative_prompt": "ঘোলা, নিম্নমানের",
        "width": 1024,
        "height": 1024,
        "num_inference_steps": 8,
        "guidance_scale": 3.5,
        "return_type": "base64"
    }
}

response = requests.post(url, json=payload, headers=headers)
result = response.json()

# Base64 image পান
image_b64 = result['output']['images_base64'][0]

# সংরক্ষণ করুন
import base64
with open('output.png', 'wb') as f:
    f.write(base64.b64decode(image_b64))
```

## 📊 বৈশিষ্ট্য

### ✨ কি কি করতে পারে

- **Text-to-Image:** টেক্সট থেকে ছবি তৈরি করুন
- **Image-to-Image:** একটি ছবিকে পরিবর্তন করুন
- **Batch Generation:** একসাথে ৪টি পর্যন্ত ছবি তৈরি করুন
- **Flexible Output:** Base64 অথবা URL আকারে ছবি পান

### ⚡ Performance

- **প্রথম request:** ১০-১৫ মিনিট (models download হবে)
- **পরবর্তী requests:** মাত্র ২-৩ সেকেন্ড!
- **Cold start:** ~১৫ সেকেন্ড

## 🔧 Advanced বৈশিষ্ট্য

### একসাথে অনেক ছবি (Batch)

```python
payload = {
    "input": {
        "prompt": "সুন্দর প্রকৃতির দৃশ্য",
        "batch_size": 4,  # ৪টি ছবি একসাথে
        "return_type": "base64"
    }
}
```

### Image-to-Image

```python
import base64

# আপনার ছবি পড়ুন
with open('input.png', 'rb') as f:
    init_image = base64.b64encode(f.read()).decode()

payload = {
    "input": {
        "mode": "img2img",
        "prompt": "watercolor painting style এ পরিবর্তন করুন",
        "init_image_base64": init_image,
        "denoising_strength": 0.75,
        "return_type": "base64"
    }
}
```

## 💰 খরচ

- **Network Volume:** ~$১.৫০/মাস (১৫GB)
- **Compute:** শুধু যখন ব্যবহার করবেন (serverless!)
- **First download:** বিনামূল্যে (শুধু সময় লাগে)

## 🐛 সমস্যা সমাধান

### প্রথম request timeout হচ্ছে?

- এটি স্বাভাবিক! প্রথম request এ models download হয় (১০-১৫ মিনিট)
- Logs চেক করুন download progress দেখার জন্য

### Models প্রতিবার download হচ্ছে?

- Network volume ঠিকভাবে mount হয়েছে কিনা চেক করুন
- Path অবশ্যই `/runpod-volume` হতে হবে

### Out of memory error?

- `batch_size` কমিয়ে ১ করুন
- `width` এবং `height` ৭৬৮ এ কমিয়ে দিন
- ৪৮GB GPU tier ব্যবহার করুন

## 📚 আরও জানুন

- **Full README:** [README.md](README.md) (ইংরেজিতে বিস্তারিত)
- **API Documentation:** README এর "API Parameters" section দেখুন
- **Examples:** `tests/test_handler.py` ফাইলে আরও উদাহরণ আছে

## 🤝 সাহায্য প্রয়োজন?

- [Issue তৈরি করুন](https://github.com/YOUR_USERNAME/z-image-turbo-runpod/issues)
- [RunPod Discord](https://discord.gg/runpod) এ যোগ দিন

---

**সফলতার সাথে deploy করার পর আপনার নিজের AI image generator আছে! 🎉**
