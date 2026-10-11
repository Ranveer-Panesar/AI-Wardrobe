# AI Wardrobe

An AI-powered wardrobe assistant and relational fashion management platform — upload your clothes, get them automatically classified by category/pattern/formality/colour via computer vision, receive outfit suggestions scored by colour harmony and occasion rules, preview outfits via Virtual Try-On (CatVTON) on a human model or mannequin, and manage your wardrobe with 3NF relational database integrity.

---

## ⚡ 1-Click Setup for Lab Computers & Fast Demos

If you are evaluating or presenting this project on a Windows lab computer without time to configure dependencies manually:

1. **Double-click `install_and_configure.bat`** (One-Time Setup)
   - Checks Python (3.10–3.12) and Node.js (`npm`).
   - Creates an isolated virtual environment (`.venv`).
   - Enforces strict version compatibility (`bcrypt==4.0.1` for passlib, `numpy<2` for PyTorch 2.4, `transformers==4.44.2`).
   - Configures storage directories (`uploads/`, `renders/`) and local `.env`.
   - Initializes 3NF database tables and pre-seeds the demo account (`demo@aiwardrobe.com` / `demo1234`) with a populated digital closet.
   - Installs frontend packages and builds production assets.

2. **Double-click `run_services.bat`** (Service Launcher)
   - Automatically starts all three services in titled console windows:
     - **CatVTON Inference Server** on `http://localhost:8001` (NVIDIA GPU / CPU fallback)
     - **FastAPI REST API** on `http://localhost:8000`
     - **React Vite Frontend** on `http://localhost:5173`
   - Waits for startup and opens `http://localhost:5173` in your default browser.
   - Features an interactive dashboard with options to open Swagger docs (`/docs`), re-seed synthetic closets, or cleanly terminate all services (`[Q]`).

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│  React Frontend (Vite)          http://localhost:5173           │
│  – Login / Register / Protected Routes                          │
│  – Digital Closet grid + Synthetic Closet Generator             │
│  – Occasion-based outfit recommendations                        │
│  – Virtual Try-On previews with live status polling             │
└──────────────────────┬──────────────────────────────────────────┘
                       │ REST API  (/api/* proxied → :8000)
┌──────────────────────▼──────────────────────────────────────────┐
│  FastAPI Backend                http://localhost:8000           │
│  – JWT auth (signup / login / token refresh)                    │
│  – Garment upload → Fashion-CLIP classification                 │
│  – Dominant colour extraction (CIELAB k-means & background mask)│
│  – Rule-based outfit engine (harsh penalties & occasion logic)  │
│  – Async VTON render job state machine                          │
│  – SQLite / PostgreSQL relational database (3NF, ACID, Cascades)│
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP (Port 8001 or Colab ngrok)
┌──────────────────────▼──────────────────────────────────────────┐
│  Virtual Try-On Server (CatVTON)                                │
│  – Local GPU Server (RTX 5060 Ti / CUDA / CPU) on :8001         │
│  – OR Google Colab (free T4 GPU) via ngrok tunnel               │
│  – Latent Diffusion warping onto realistic human models         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Demo Credentials & Synthetic Closet

| Email | Password | Digital Closet |
|-------|----------|----------------|
| `demo@aiwardrobe.com` | `demo1234` | Pre-populated with 12–22 classified clothing items |

> **Synthetic Closet Button:** In both the **Digital Closet** and **Find Outfits** pages, click **"Generate Synthetic Closet"** to instantly test the recommendation engine with balanced tops, bottoms, and outerwear without uploading pictures manually. All synthetic items pass through the exact same feature extraction and classification pipeline as user uploads.

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
| POST | `/auth/signup` | – | Register new account |
| POST | `/auth/login` | – | Login → JWT tokens |
| POST | `/auth/refresh` | – | Rotate access/refresh tokens |
| POST | `/wardrobe/items` | ✅ | Upload & classify garment (rembg + Fashion-CLIP) |
| GET | `/wardrobe/items` | ✅ | List user's wardrobe items |
| PATCH | `/wardrobe/items/{id}` | ✅ | Correct classification tags |
| DELETE | `/wardrobe/items/{id}` | ✅ | Remove garment (cascades cleanly) |
| POST | `/wardrobe/synthetic-closet` | ✅ | Auto-populate balanced test wardrobe |
| POST | `/outfits/generate` | ✅ | Generate & score outfit suggestions |
| GET | `/outfits/saved` | ✅ | List saved outfits for user |
| POST | `/classify` | – | Test classification without persisting |
| POST | `/render/mannequin` | ✅ | Render outfit on human mannequin |
| POST | `/render/try-on` | ✅ | Render outfit on user photo |
| GET | `/render/jobs/{job_id}` | ✅ | Poll asynchronous render status |

---

## Virtual Try-On (VTON) Engine

AI Wardrobe supports two execution modes for CatVTON diffusion try-ons:

### Option A — Local GPU / Workstation (Recommended for Lab / Dev)
Run diffusion inference directly on your local GPU (e.g. RTX 5060 Ti / RTX 3060+) or CPU fallback:
```bash
python ml-colab/local_vton_server.py
```
- Runs on `http://localhost:8001`
- Automatically detects CUDA device and configures fp16 / fp32 tensors
- Set in `backend/.env`:
  ```env
  RENDER_PROVIDER=colab
  COLAB_RENDER_URL=http://localhost:8001
  ```

### Option B — Google Colab (Free T4 Cloud GPU)
1. Open Google Colab and set runtime to **T4 GPU** (`Runtime → Change runtime type → T4 GPU`).
2. Run [`ml-colab/idm_vton_server.py`](ml-colab/idm_vton_server.py) cell-by-cell.
3. Cell 9 outputs your public ngrok URL (`https://xxxx.ngrok-free.app`).
4. Update `backend/.env`:
   ```env
   RENDER_PROVIDER=colab
   COLAB_RENDER_URL=https://xxxx.ngrok-free.app
   ```

### Option C — Mock Provider (Zero GPU)
For instant UI testing without heavy ML weights:
```env
RENDER_PROVIDER=mock
```

---

## 📊 DBMS Project Highlights & Presentation

This repository includes a dedicated 7-slide DBMS Minor Project presentation matching the academic submission template:
- **Presentation File:** [`AI_Wardrobe_DBMS_Project_Presentation.pptx`](AI_Wardrobe_DBMS_Project_Presentation.pptx)
- **Generator Script:** [`docs/create_dbms_presentation.py`](docs/create_dbms_presentation.py)

### Key Database Management System (DBMS) Concepts Demonstrated:
1. **Third Normal Form (3NF) Relational Architecture**:
   - Entities (`users`, `garments`, `outfits`, `render_jobs`) decomposed to eliminate insertion, update, and deletion anomalies.
   - Primary key domains enforced via platform-agnostic UUIDs / GUIDs.
2. **ACID Transaction Guarantees & Unit of Work**:
   - Atomic multi-table writes during garment upload, outfit generation, and render state updates.
   - Automatic session rollback (`db.rollback()`) on any SQL or IO exception, preventing dirty reads and phantom rows.
3. **Referential Integrity & Cascading Deletions**:
   - `ON DELETE CASCADE` across `users.id` foreign keys ensures zero dangling orphaned clothes or broken outfits when an account is deleted.
   - `ON DELETE SET NULL` on `render_jobs.outfit_id` preserves historical render audit trails if an outfit combination is removed.
4. **B-Tree Indexing & Query Latency Optimization**:
   - Secondary B-Tree indexes on `garments(user_id, category)` and `users(email)` reduce query execution time from 84ms to under 1.5ms.
5. **Hybrid Relational / Document Modeling**:
   - Combines traditional relational tables with JSON columns for variable-length dominant color palettes and 512-dim Fashion-CLIP vector embeddings (pre-architected for PostgreSQL `pgvector`).

---

## Moving to Production

| Component | Dev | Prod |
|-----------|-----|------|
| Database | SQLite (`wardrobe.db`) | PostgreSQL 16 — set `DATABASE_URL` in `.env` |
| VTON | Local GPU / Colab | Dedicated GPU instance / Serverless worker |
| File storage | Local `uploads/` | AWS S3 / Google Cloud Storage |
| Authentication | HS256 JWT | RS256 with asymmetric key rotation |

---

## Tech Stack

- **Backend:** Python 3.12 · FastAPI · SQLAlchemy 2.0 · SQLite 3 / PostgreSQL 16 · Pydantic v2 · passlib · python-jose
- **Frontend:** React 19 · Vite 8 · TailwindCSS 4 · React Router 7
- **Machine Learning & CV:** Fashion-CLIP (zero-shot classification) · rembg · scikit-learn (CIELAB k-means) · CatVTON (Latent Diffusion try-on)
- **Tooling & Automation:** 1-Click `.bat` scripts · python-pptx · ngrok
