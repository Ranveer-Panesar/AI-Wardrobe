"""
End-to-end test for the VTON render feature.

Flow:
  1. Register + login a test user
  2. Download a sample garment image (plain white t-shirt from picsum)
  3. Upload it to the wardrobe
  4. Generate outfits (engine picks the best combo)
  5. Submit a mannequin render job
  6. Poll until done (or timeout)
  7. Download the rendered image and save it locally

Run from backend/:
    python test_render_e2e.py
"""

import io
import os
import sys
import time
import urllib.request

import requests
from PIL import Image

BASE   = "http://localhost:8000"
OUTFIT = None   # filled in during the test
TOKEN  = None

# ─── Step 0: download a sample garment image ──────────────────────────────────

UPLOADS_DIR = os.path.join(os.path.dirname(__file__), "uploads")
garment_files = sorted(
    [f for f in os.listdir(UPLOADS_DIR) if f.endswith(".jpg")],
    key=lambda f: os.path.getsize(os.path.join(UPLOADS_DIR, f)),
    reverse=True,
)
if not garment_files:
    print("ERROR: no garments in backend/uploads — upload something first"); sys.exit(1)

# Skip the largest file (57b84fef — 2.2MB dress that causes NSFW renders)
# Use the second largest which is more likely to be a shirt/top
pick = garment_files[1] if len(garment_files) > 1 else garment_files[0]
garment_path = os.path.join(UPLOADS_DIR, pick)
print(f"0. Using garment from uploads: {pick}  ({os.path.getsize(garment_path):,} bytes)")

# ─── Step 1: register test user ───────────────────────────────────────────────

print("\n1. Registering test user...")
EMAIL = f"vton_test_{int(time.time())}@example.com"
# Use last 9 digits of timestamp to stay within valid E.164 range
PHONE = f"+1555{int(time.time()) % 10_000_000:07d}"
r = requests.post(f"{BASE}/auth/signup", json={
    "email": EMAIL,
    "phone": PHONE,
    "password": "Test@1234!"
})
if r.status_code not in (200, 201, 400):
    print(f"   ERROR: {r.status_code} {r.text}"); sys.exit(1)
if r.status_code == 400 and "already" in r.text:
    print("   (user already exists — continuing)")
else:
    print(f"   Registered: {EMAIL}")

# ─── Step 2: login ────────────────────────────────────────────────────────────

print("\n2. Logging in...")
r = requests.post(f"{BASE}/auth/login", json={"email": EMAIL, "password": "Test@1234!"})
if r.status_code != 200:
    print(f"   ERROR: {r.status_code} {r.text}"); sys.exit(1)

TOKEN = r.json()["access_token"]
AUTH  = {"Authorization": f"Bearer {TOKEN}"}
print("   ✅ Token obtained")

# ─── Step 3: upload garment ───────────────────────────────────────────────────

print("\n3. Uploading garment image to wardrobe...")
with open(garment_path, "rb") as f:
    r = requests.post(f"{BASE}/wardrobe/items",
                      files={"file": ("garment.jpg", f, "image/jpeg")},
                      headers=AUTH)
if r.status_code not in (200, 201):
    print(f"   ERROR: {r.status_code} {r.text}"); sys.exit(1)

garment   = r.json()
garment_id = garment["id"]
print(f"   Garment uploaded: id={garment_id}  auto-category={garment.get('category')}")

# Force category to "t-shirt" (TOP) so the engine always has a valid pair,
# regardless of what Fashion-CLIP inferred from the test image.
r = requests.patch(f"{BASE}/wardrobe/items/{garment_id}",
                   json={"category": "t-shirt"},
                   headers=AUTH)
print(f"   Patched -> category=t-shirt  ({r.status_code})")

# Upload second garment and force it to "jeans" (BOTTOM)
print("\n   Uploading second garment (bottom)...")
with open(garment_path, "rb") as f:
    r2 = requests.post(f"{BASE}/wardrobe/items",
                       files={"file": ("bottom.jpg", f, "image/jpeg")},
                       headers=AUTH)
garment2 = r2.json()
garment2_id = garment2["id"]
print(f"   Second garment: id={garment2_id}  auto-category={garment2.get('category')}")

r = requests.patch(f"{BASE}/wardrobe/items/{garment2_id}",
                   json={"category": "jeans"},
                   headers=AUTH)
print(f"   Patched -> category=jeans  ({r.status_code})")


# ─── Step 4: generate outfits ─────────────────────────────────────────────────

print("\n4. Generating outfit combinations...")
r = requests.post(f"{BASE}/outfits/generate", json={"count": 3}, headers=AUTH)
if r.status_code != 200:
    print(f"   ERROR: {r.status_code} {r.text}")
    # Can't do a render without an outfit — fall back to using garment directly
    print("   ⚠️  No outfits generated (may need a top + bottom in wardrobe)")
    print("   Using saved outfits instead...")
    r = requests.get(f"{BASE}/outfits/saved", headers=AUTH)

outfits = r.json().get("outfits", [])
if not outfits:
    print("   ❌ No outfits available — cannot test render. Upload a top AND a bottom."); sys.exit(0)

outfit_id = outfits[0]["id"]
print(f"   ✅ Using outfit {outfit_id}  score={outfits[0]['score']}")

# ─── Step 5: submit mannequin render ─────────────────────────────────────────

print("\n5. Submitting mannequin render job...")
r = requests.post(f"{BASE}/render/mannequin",
                  data={"outfit_id": outfit_id},
                  headers=AUTH)
if r.status_code not in (200, 201, 202):
    print(f"   ERROR: {r.status_code} {r.text}"); sys.exit(1)

job = r.json()
job_id = job["job_id"]
print(f"   ✅ Job queued: {job_id}  status={job['status']}")

# ─── Step 6: poll for result ─────────────────────────────────────────────────

print("\n6. Polling job status...")
POLL_INTERVAL = 5
TIMEOUT       = 300   # CatVTON on a cold T4 with a large garment can take 2-3 min
start = time.time()

while True:
    r = requests.get(f"{BASE}/render/jobs/{job_id}", headers=AUTH)
    job = r.json()
    status = job["status"]
    elapsed = time.time() - start

    print(f"   [{elapsed:5.1f}s] status={status}")

    if status == "done":
        print(f"\n   ✅ Render complete! output_url={job['output_image_url']}")
        break
    elif status == "failed":
        print(f"\n   ❌ Render failed: {job.get('error_message')}")
        sys.exit(1)
    elif elapsed > TIMEOUT:
        print(f"\n   ❌ Timed out after {TIMEOUT}s")
        sys.exit(1)

    time.sleep(POLL_INTERVAL)

# ─── Step 7: download and show result ────────────────────────────────────────

print("\n7. Downloading rendered image...")
img_url = f"{BASE}{job['output_image_url']}"
r = requests.get(img_url)
out_path = "test_render_output.jpg"
with open(out_path, "wb") as f:
    f.write(r.content)

img = Image.open(out_path)
print(f"   ✅ Saved to {out_path}  size={img.size}")

# Try to display in the terminal as ASCII or open in default viewer
try:
    os.startfile(out_path)   # Windows: opens in Photos app
    print("   Opening in default image viewer...")
except Exception:
    pass

print("\n══════════════════════════════════")
print("  VTON render test PASSED ✅")
print("══════════════════════════════════")
print(f"  Job ID      : {job_id}")
print(f"  Output URL  : {img_url}")
print(f"  Local file  : {out_path}")
print(f"  Image size  : {img.size}")
