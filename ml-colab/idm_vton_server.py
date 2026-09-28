# CatVTON Server for AI Wardrobe
# ================================
# Run this notebook in Google Colab (GPU runtime — T4 or better).
#
# CatVTON ("Concatenation Is All You Need") is a lightweight VTON model
# (~3GB weights vs IDM-VTON's ~14GB) — designed to run on free Colab T4.
# Paper: https://arxiv.org/abs/2411.10499
#
# Once running, copy the ngrok URL into your backend/.env:
#   RENDER_PROVIDER=colab
#   COLAB_RENDER_URL=https://xxxx-xx-xxx-xx-xxx.ngrok-free.app
#
# API exposed by this server:
#   POST /try-on      — fields: garment_image (file), person_image (file)
#   POST /mannequin   — fields: garment_image (file)
#   GET  /health      — returns {"status": "ok", "model": "CatVTON"}

# ──────────────────────────────────────────────────────────────────────────────
# CELL 1 — Runtime check
# ──────────────────────────────────────────────────────────────────────────────
import subprocess

try:
    result = subprocess.run(["nvidia-smi"], capture_output=True, text=True)
    has_gpu = result.returncode == 0
except FileNotFoundError:
    has_gpu = False

if not has_gpu:
    raise RuntimeError(
        "\n\n❌  No GPU detected!\n"
        "   Go to: Runtime → Change runtime type → Hardware accelerator → T4 GPU\n"
        "   Then re-run all cells.\n"
    )

gpu_info = [l for l in result.stdout.splitlines() if "MiB" in l or "Tesla" in l or "T4" in l]
print("✅ GPU detected:", gpu_info[0].strip() if gpu_info else "GPU OK")

# ──────────────────────────────────────────────────────────────────────────────
# CELL 2 — Install dependencies
# ──────────────────────────────────────────────────────────────────────────────
# CatVTON uses standard diffusers — no pinning needed.
subprocess.run([
    "pip", "install", "-q",
    "fastapi", "uvicorn[standard]", "python-multipart",
    "pyngrok",
    "diffusers>=0.27.0",
    "transformers>=4.40.0",
    "accelerate",
    "huggingface_hub",
    "torchvision",
    "einops",
    "Pillow",
    "numpy",
], check=True)
print("✅ Dependencies installed")

# ──────────────────────────────────────────────────────────────────────────────
# CELL 3 — HuggingFace login
# ──────────────────────────────────────────────────────────────────────────────
from huggingface_hub import login

try:
    from google.colab import userdata
    HF_TOKEN = userdata.get("HF_TOKEN")
except Exception:
    HF_TOKEN = ""   # ← paste your token here if not using Colab secrets

if HF_TOKEN:
    login(token=HF_TOKEN, add_to_git_credential=False)
    print("✅ HuggingFace logged in")
else:
    print("⚠️  No HF_TOKEN — using anonymous access")

# ──────────────────────────────────────────────────────────────────────────────
# CELL 4 — Clone CatVTON repo
# ──────────────────────────────────────────────────────────────────────────────
import os

if not os.path.exists("/content/CatVTON"):
    subprocess.run([
        "git", "clone", "--depth=1",
        "https://github.com/Zheng-Chong/CatVTON.git",
        "/content/CatVTON"
    ], check=True)
    print("✅ CatVTON cloned")
else:
    print("✅ CatVTON already cloned")

os.chdir("/content/CatVTON")

# ──────────────────────────────────────────────────────────────────────────────
# CELL 5 — Load CatVTON pipeline
# ──────────────────────────────────────────────────────────────────────────────
# CatVTON total weight: ~3GB — comfortably fits on free T4
import gc
import sys
import torch

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
sys.path.insert(0, "/content/CatVTON")

DEVICE = "cuda"
DTYPE  = torch.float16

def _free_memory():
    gc.collect()
    torch.cuda.empty_cache()
    used     = torch.cuda.memory_allocated() / 1e9
    reserved = torch.cuda.memory_reserved()  / 1e9
    print(f"   VRAM: {used:.1f}GB used / {reserved:.1f}GB reserved")

# CatVTON exposes its own pipeline class
from model.pipeline import CatVTONPipeline

# Base inpainting model (SD 1.5 inpainting — ~1.7GB)
BASE_CKPT     = "booksforcharlie/stable-diffusion-inpainting"
# CatVTON attention adapters (~0.3GB on top)
CATVTON_CKPT  = "zhengchong/CatVTON"

print("Loading CatVTON pipeline (base SD + CatVTON adapters)...")
pipe = CatVTONPipeline(
    base_ckpt=BASE_CKPT,
    attn_ckpt=CATVTON_CKPT,
    attn_ckpt_version="mix",
    weight_dtype=DTYPE,
    use_tf32=True,
    device=DEVICE,
)
_free_memory()
print("✅ CatVTON pipeline ready")

# ──────────────────────────────────────────────────────────────────────────────
# CELL 6 — Geometric mask (no DensePose / detectron2 needed)
# ──────────────────────────────────────────────────────────────────────────────
# CatVTON just needs a binary PIL mask marking the region to inpaint.
# AutoMasker (DensePose + SCHP) is optional — a geometric upper-body rectangle
# is sufficient for studio-lit garment photos and works without any extra deps.
import io
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

TARGET_W, TARGET_H = 768, 1024


def make_upper_body_mask(w: int = TARGET_W, h: int = TARGET_H) -> Image.Image:
    """
    White rectangle covering the upper-body torso area on a black background.
    Coordinates are fractions of image dimensions — works for any aspect ratio.
    Soft-blurred edges help the diffusion model blend cleanly at boundaries.
    """
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    # Torso region: y 15-62 %, x 8-92 %
    x0, y0 = int(w * 0.08), int(h * 0.15)
    x1, y1 = int(w * 0.92), int(h * 0.62)
    draw.rectangle([x0, y0, x1, y1], fill=255)
    # Slight blur so the boundary isn't a hard pixel edge
    mask = mask.filter(ImageFilter.GaussianBlur(radius=6))
    return mask


def make_full_body_mask(w: int = TARGET_W, h: int = TARGET_H) -> Image.Image:
    """Full torso + lower body — used for mannequin / dress mode."""
    mask = Image.new("L", (w, h), 0)
    draw = ImageDraw.Draw(mask)
    x0, y0 = int(w * 0.08), int(h * 0.15)
    x1, y1 = int(w * 0.92), int(h * 0.90)
    draw.rectangle([x0, y0, x1, y1], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(radius=6))
    return mask


# Pre-compute masks (reused for every request)
_UPPER_MASK = make_upper_body_mask()
_FULL_MASK  = make_full_body_mask()

# Fallback mannequin used only when /mannequin is called directly (not via backend).
# When called from the backend, the real mannequin PNG is sent as person_image to /try-on.
_MANNEQUIN_IMG = Image.new("RGB", (TARGET_W, TARGET_H), color="#c8bfb6")

print("Geometric masks ready")

# ──────────────────────────────────────────────────────────────────────────────
# CELL 7 — Inference helpers
# ──────────────────────────────────────────────────────────────────────────────

def _bytes_to_pil(data: bytes) -> Image.Image:
    return Image.open(io.BytesIO(data)).convert("RGB")


def _pil_to_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def _resize(img: Image.Image) -> Image.Image:
    return img.resize((TARGET_W, TARGET_H), Image.LANCZOS)


def _run_catvton(
    person_img: Image.Image,
    garment_img: Image.Image,
    mask: Image.Image,
) -> Image.Image:
    """Core CatVTON inference."""
    person_img  = _resize(person_img)
    garment_img = _resize(garment_img)

    with torch.inference_mode():
        result = pipe(
            image=person_img,
            condition_image=garment_img,
            mask=mask,
            num_inference_steps=50,
            guidance_scale=2.5,
            height=TARGET_H,
            width=TARGET_W,
            generator=torch.Generator(DEVICE).manual_seed(42),
        )[0]

    return result


def run_try_on(person_bytes: bytes, garment_bytes: bytes) -> bytes:
    person_img  = _bytes_to_pil(person_bytes)
    garment_img = _bytes_to_pil(garment_bytes)
    result = _run_catvton(person_img, garment_img, mask=_UPPER_MASK)
    return _pil_to_bytes(result)


def run_mannequin(garment_bytes: bytes) -> bytes:
    garment_img = _bytes_to_pil(garment_bytes)
    result = _run_catvton(_MANNEQUIN_IMG, garment_img, mask=_FULL_MASK)
    return _pil_to_bytes(result)


print("✅ Inference helpers ready")

# ──────────────────────────────────────────────────────────────────────────────
# CELL 8 — FastAPI server
# ──────────────────────────────────────────────────────────────────────────────
import threading
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import Response

vton_app = FastAPI(title="CatVTON Colab Server")


@vton_app.get("/health")
def health():
    return {"status": "ok", "model": "CatVTON", "device": DEVICE}


@vton_app.post("/try-on")
async def try_on_endpoint(
    garment_image: UploadFile = File(...),
    person_image:  UploadFile = File(...),
):
    """Virtual try-on: person wearing the garment. Returns JPEG bytes."""
    try:
        garment_bytes = await garment_image.read()
        person_bytes  = await person_image.read()
        result = run_try_on(person_bytes, garment_bytes)
        return Response(content=result, media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Render failed: {e}")


@vton_app.post("/mannequin")
async def mannequin_endpoint(garment_image: UploadFile = File(...)):
    """Render garment on neutral mannequin. Returns JPEG bytes."""
    try:
        garment_bytes = await garment_image.read()
        result = run_mannequin(garment_bytes)
        return Response(content=result, media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Render failed: {e}")


print("✅ FastAPI app defined")

# ──────────────────────────────────────────────────────────────────────────────
# CELL 9 — Start server + ngrok tunnel
# ──────────────────────────────────────────────────────────────────────────────
import time
from pyngrok import ngrok

# Add your ngrok token as a Colab secret named NGROK_TOKEN
# https://dashboard.ngrok.com/get-started/your-authtoken
try:
    from google.colab import userdata
    NGROK_TOKEN = userdata.get("NGROK_TOKEN")
except Exception:
    NGROK_TOKEN = ""   # ← paste your token here

if NGROK_TOKEN:
    ngrok.set_auth_token(NGROK_TOKEN)
else:
    print("No NGROK_TOKEN — tunnel limited to 60 min / 1 connection")
    print("Get a free token: https://dashboard.ngrok.com/get-started/your-authtoken")

# Kill ALL existing tunnels before opening a new one.
# Free tier allows max 5 tunnels per agent session — reruns accumulate stale ones.
print("Closing any stale ngrok tunnels...")
ngrok.kill()        # kills the local ngrok process entirely
time.sleep(1)       # brief pause so the port is released

if NGROK_TOKEN:
    ngrok.set_auth_token(NGROK_TOKEN)   # re-authenticate after kill

# Kill whatever is already on port 8001 (leftover uvicorn from a previous run)
import subprocess
subprocess.run(["fuser", "-k", "8001/tcp"], capture_output=True)
time.sleep(1)

def _start_server():
    uvicorn.run(vton_app, host="0.0.0.0", port=8001, log_level="warning")

server_thread = threading.Thread(target=_start_server, daemon=True)
server_thread.start()
time.sleep(2)  # let uvicorn bind

tunnel     = ngrok.connect(8001, "http")
public_url = tunnel.public_url

print("\n" + "=" * 60)
print("CatVTON server is LIVE!")
print(f"   Public URL : {public_url}")
print()
print("   Add to backend/.env:")
print(f"   RENDER_PROVIDER=colab")
print(f"   COLAB_RENDER_URL={public_url}")
print()
print(f"   Health check: curl {public_url}/health")
print("=" * 60)
print("\nKeep this notebook running — tunnel closes when you stop it.")
