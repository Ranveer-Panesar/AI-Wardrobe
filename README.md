# AI Wardrobe

An AI-powered wardrobe assistant — upload your clothes, get them automatically classified by category/pattern/formality/colour, receive outfit suggestions scored by colour harmony and style compatibility, and preview outfits via Virtual Try-On rendered on a mannequin or your own photo.

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│  React Frontend (Vite)          http://localhost:5173           │
│  – Login / Register                                             │
│  – Upload garments + view wardrobe grid                         │
│  – Browse outfit suggestions                                    │
│  – Trigger VTON render + poll for result                        │
└──────────────────────┬──────────────────────────────────────────┘
                       │ REST API  (/api/* proxied → :8000)
┌──────────────────────▼──────────────────────────────────────────┐
│  FastAPI Backend                http://localhost:8000           │
│  – JWT auth (signup / login / token refresh)                    │
│  – Garment upload → Fashion-CLIP classification                 │
│  – Dominant colour extraction (HSV background-filtered)        │
│  – Rule-based outfit engine (colour ΔE + formality + pattern)   │
│  – Async VTON render jobs (mannequin or try-on photo)           │
│  – SQLite database (dev) — Postgres-ready schema                │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP (ngrok tunnel)
┌──────────────────────▼──────────────────────────────────────────┐
│  Google Colab  (free T4 GPU)     https://<ngrok>.ngrok-free.app │
│  – CatVTON model (~3GB, fits free T4)                           │
│  – FastAPI server exposes /try-on and /health                   │
│  – Only needed when RENDER_PROVIDER=colab                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

Four tables — fully relational, normalized to 3NF, Postgres-compatible:

```
users
  id (UUID PK)
  email (unique, indexed)
  phone (unique, indexed)
  password_hash
  storage_mode  ("local" | "cloud")
  created_at

garments
  id (UUID PK)
  user_id (FK → users.id  ON DELETE CASCADE)
  category            e.g. "casual shirt", "jeans"
  category_confidence float 0–1
  pattern             e.g. "solid", "striped", "plaid"
  formality           e.g. "casual", "formal", "smart casual"
  dominant_colors     JSON ["#rrggbb", ...]
  embedding           JSON (512-float Fashion-CLIP vector, nullable)
  image_url           relative path e.g. "/uploads/<uuid>.jpg"
  created_at

outfits
  id (UUID PK)
  user_id    (FK → users.id  ON DELETE CASCADE)
  garment_ids  JSON [uuid, ...]
  score        float 0–1  (composite compatibility)
  style_tags   JSON {"casual": 0.7, "formal": 0.1, ...}
  created_at

render_jobs
  id (UUID PK)
  user_id   (FK → users.id    ON DELETE CASCADE)
  outfit_id (FK → outfits.id  ON DELETE SET NULL)
  render_type   "mannequin" | "try_on"
  status        "queued" → "processing" → "done" | "failed"
  output_image_url  "/renders/<uuid>.jpg"  (set when done)
  error_message     (set when failed)
  created_at
  updated_at
```

---

## Repo Structure

```
AI-Wardrobe/
├── backend/
│   ├── app/
│   │   ├── main.py              FastAPI app — routers + static file mounts
│   │   ├── config.py            Settings (reads .env)
│   │   ├── database.py          SQLAlchemy engine + session factory
│   │   ├── models/              ORM table definitions
│   │   │   ├── user.py
│   │   │   ├── garment.py       (also contains Outfit model)
│   │   │   └── render_job.py
│   │   ├── schemas/             Pydantic request/response shapes
│   │   ├── routers/             HTTP route handlers
│   │   │   ├── auth.py
│   │   │   ├── wardrobe.py
│   │   │   ├── outfits.py
│   │   │   ├── classify.py
│   │   │   └── render.py
│   │   └── services/
│   │       ├── classifier.py    Fashion-CLIP zero-shot classification
│   │       ├── color_extraction.py  Background-filtered colour extraction
│   │       ├── outfit_engine.py     Rule-based outfit scoring
│   │       └── render/          VTON provider abstraction
│   │           ├── base.py      Abstract base class
│   │           ├── mock.py      MockProvider (no GPU needed)
│   │           └── colab.py     ColabProvider (CatVTON via ngrok)
│   ├── Dummy/
│   │   └── male-mannequins-500x500.png   Reference image for mannequin renders
│   ├── .env.example             Copy to .env, fill in secrets
│   ├── requirements.txt
│   └── test_render_e2e.py       End-to-end VTON test script
│
├── frontend/
│   ├── src/
│   │   ├── api/                 Typed API client wrappers
│   │   │   ├── client.js        Axios instance
│   │   │   ├── auth.js
│   │   │   └── wardrobe.js
│   │   ├── context/
│   │   │   └── AuthContext.jsx  Global auth state (JWT storage)
│   │   ├── components/
│   │   │   ├── DigitalCloset.jsx   Wardrobe grid (live API)
│   │   │   └── ProtectedRoute.jsx
│   │   └── pages/
│   │       ├── LoginPage.jsx
│   │       └── RegisterPage.jsx
│   └── vite.config.js           Proxies /api/* → backend :8000
│
├── ml-colab/
│   └── idm_vton_server.py       CatVTON server — run cell-by-cell in Colab
│
└── docs/
    ├── API_CONTRACT.md          Full endpoint reference (shapes + errors)
    └── PROJECT_PLAN.md          Phase-by-phase progress tracker
```

---

## Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Python | 3.12 | Earlier may work, not tested |
| Node.js | 18+ | For the React frontend |
| npm | 9+ | Comes with Node |
| Git | any | |

> **No GPU required** for local dev — the backend defaults to `RENDER_PROVIDER=mock` which skips Colab entirely.

---

## Quick Start (Local Dev)

### 1 — Clone

```bash
git clone https://github.com/Ranveer-Panesar/AI-Wardrobe.git
cd AI-Wardrobe
```

### 2 — Backend setup

```bash
cd backend

# Create and activate a virtual environment (recommended)
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create your .env file
copy .env.example .env        # Windows
# cp .env.example .env        # macOS/Linux

# Edit .env — the defaults work for local dev.
# At minimum, change JWT_SECRET to a long random string.
```

**`.env` for local dev** (copy from `.env.example`, defaults already set):

```env
ENV=development
DATABASE_URL=sqlite:///./wardrobe.db
JWT_SECRET=replace-this-with-a-long-random-string
RENDER_PROVIDER=mock          # use "colab" only when Colab is running
COLAB_RENDER_URL=             # fill in ngrok URL when using colab provider
```

### 3 — Start the backend

```bash
# From the backend/ folder, with venv active:
uvicorn app.main:app --reload
```

- API: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

The SQLite database (`wardrobe.db`) is created automatically on first run.

### 4 — Frontend setup

```bash
cd ../frontend
npm install
npm run dev
```

App opens at `http://localhost:5173`.

> Vite automatically proxies all `/api/*` requests to the backend — no CORS configuration needed during dev.

---

## Using the App

1. **Register** at `/register` — email, international phone (`+91...`), strong password
2. **Log in** at `/login`
3. **Upload garments** — drag an image, it's auto-classified (category, pattern, formality, colours)
4. **Correct misclassifications** — click any garment card to edit its category/pattern/formality
5. **Generate outfits** — the engine scores all valid combinations from your wardrobe and returns the top N
6. **Virtual Try-On** — see the [VTON section](#virtual-try-on-vton-with-google-colab) below

**Password rules:** min 8 chars · 1 uppercase · 1 digit · 1 special character (`!@#$%^&*` etc.)

---

## API Quick Reference

Full contract in [`docs/API_CONTRACT.md`](docs/API_CONTRACT.md).

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/auth/signup` | – | Register |
| POST | `/auth/login` | – | Login → JWT |
| POST | `/auth/refresh` | – | Rotate tokens |
| POST | `/wardrobe/items` | ✅ | Upload & classify garment |
| GET | `/wardrobe/items` | ✅ | List all garments |
| PATCH | `/wardrobe/items/{id}` | ✅ | Correct classification |
| DELETE | `/wardrobe/items/{id}` | ✅ | Remove garment |
| POST | `/outfits/generate` | ✅ | Generate outfit suggestions |
| GET | `/outfits/saved` | ✅ | List saved outfits |
| POST | `/classify` | – | Classify without saving |
| POST | `/render/mannequin` | ✅ | Render outfit on mannequin |
| POST | `/render/try-on` | ✅ | Render on user photo |
| GET | `/render/jobs/{job_id}` | ✅ | Poll render status |

---

## Virtual Try-On (VTON) with Google Colab

VTON requires a GPU (T4 on free Colab). The backend works without it — it just returns mock renders.

### One-time setup

1. Go to [Google Colab](https://colab.research.google.com/) and open a **new notebook**
2. Set runtime to **T4 GPU**: `Runtime → Change runtime type → T4 GPU`
3. Get a free ngrok token: [dashboard.ngrok.com](https://dashboard.ngrok.com/get-started/your-authtoken)
4. Add secrets to Colab (`🔑` sidebar):
   - `HF_TOKEN` — HuggingFace token (needed to download CatVTON weights, free account)
   - `NGROK_TOKEN` — your ngrok auth token
5. Copy the contents of [`ml-colab/idm_vton_server.py`](ml-colab/idm_vton_server.py) into notebook cells — each `# CELL N` comment marks a new cell boundary

### Run the Colab server

Run all cells (top to bottom). Cell 9 will print:

```
CatVTON server is LIVE!
   Public URL : https://xxxx-xx-xxx.ngrok-free.app
   Add to backend/.env:
   RENDER_PROVIDER=colab
   COLAB_RENDER_URL=https://xxxx-xx-xxx.ngrok-free.app
```

### Connect backend to Colab

Update `backend/.env`:

```env
RENDER_PROVIDER=colab
COLAB_RENDER_URL=https://xxxx-xx-xxx.ngrok-free.app
```

Restart the backend. VTON renders now route to Colab (~90–135 seconds per render on T4).

> **Keep the Colab tab open** — the ngrok tunnel closes when the notebook stops.  
> **Free tier:** max 5 tunnels per ngrok session. Cell 9 kills stale tunnels automatically.

### Run the E2E test

```bash
# From backend/ with venv active and backend running:
$env:PYTHONUTF8=1; python test_render_e2e.py
```

---

## Moving to Production

The codebase is production-ready with these swap-outs:

| Component | Dev | Prod |
|-----------|-----|------|
| Database | SQLite (`wardrobe.db`) | PostgreSQL — set `DATABASE_URL` in env |
| VTON | Colab (free T4) | Vendor API (Fashn.ai / Revery.ai) — set `RENDER_PROVIDER=vendor` |
| File storage | Local `uploads/` folder | Cloud storage (S3 / GCS) — set `STORAGE_MODE_DEFAULT=cloud` |
| JWT secret | Any string | Long random secret, rotated periodically |

---

## Common Issues

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` from `backend/` with venv active |
| `NetworkError` on frontend | Backend isn't running — start `uvicorn` first |
| Upload returns `500` | Check the backend terminal for the traceback |
| Fashion-CLIP slow on first upload | Model downloads ~400MB on first run — wait for it |
| `ngrok: tunnel limit` | Re-run Cell 9 in Colab — it kills stale tunnels before opening a new one |
| Port 8001 in use on Colab | Re-run Cell 9 — it runs `fuser -k 8001/tcp` before starting |
| VTON render NSFW / garbled | Use a real human model photo (not a plastic mannequin) as the person reference |

---

## Tech Stack

**Backend:** Python 3.12 · FastAPI · SQLAlchemy · SQLite/PostgreSQL · Pydantic · passlib/bcrypt · python-jose (JWT)

**Frontend:** React 18 · Vite · TailwindCSS · Axios

**ML / AI:** Fashion-CLIP (zero-shot classification) · CatVTON (virtual try-on, runs on Colab T4)

**Infrastructure:** ngrok (Colab tunnel) · Google Colab (free GPU)
