# How to Start — AI Wardrobe (Dev)

## Quick Start (Lab Computers / Windows 1-Click Setup)

Simply use the two automated batch scripts in the project root:

1. **`install_and_configure.bat`** (One-time setup)
   - Verifies Python and Node.js
   - Creates/configures `.venv` virtual environment
   - Enforces strict version compatibilities (`bcrypt==4.0.1`, `numpy<2`, `torch==2.4.1`)
   - Initializes database and seeds `demo@aiwardrobe.com` (password: `demo1234`) with digital closet items
   - Installs frontend dependencies and builds production assets

2. **`run_services.bat`** (Launch all services)
   - Starts CatVTON Server on `http://localhost:8001`
   - Starts FastAPI Backend on `http://localhost:8000`
   - Starts Vite React Frontend on `http://localhost:5173`
   - Automatically opens your browser to `http://localhost:5173`
   - Provides an interactive dashboard to view docs or cleanly terminate all services

---

## Prerequisites (one-time setup)

**Backend**
- Python 3.12
- Install dependencies:
  ```bash
  cd "e:\AI Wardrobe Parent\AI Wardrobe dev\backend"
  pip install -r requirements.txt
  ```

**Frontend**
- Node.js 18+ / npm
- Install dependencies:
  ```bash
  cd "e:\AI Wardrobe Parent\AI Wardrobe dev\frontend"
  npm install
  ```

**Environment file** — copy the example and fill in secrets (only needed if you change defaults):
```bash
cd "e:\AI Wardrobe Parent\AI Wardrobe dev\backend"
copy .env.example .env
```
For local dev the defaults in `.env.example` work out of the box (SQLite, no cloud keys needed).

---

## Start

**Terminal 1 — Backend (FastAPI)**
```bash
cd "e:\AI Wardrobe Parent\AI Wardrobe dev\backend"
uvicorn app.main:app --reload
```
Runs at → `http://localhost:8000`  
API docs → `http://localhost:8000/docs`

**Terminal 2 — Frontend (Vite + React)**
```bash
cd "e:\AI Wardrobe Parent\AI Wardrobe dev\frontend"
npm run dev
```
Runs at → `http://localhost:5173`

> The Vite dev server proxies `/api/*` to the backend automatically — no CORS issues.

---

## Test accounts

| Email | Password | Notes |
|-------|----------|-------|
| `demo@aiwardrobe.com` | `demo1234` | Pre-seeded with garments (if seed was run) |

To register a fresh account: go to `http://localhost:5173/register`

**Password requirements:** 8+ chars, 1 uppercase, 1 digit, 1 special character (e.g. `Test@1234`)

---

## Useful URLs

| URL | What it is |
|-----|------------|
| `http://localhost:5173` | React frontend |
| `http://localhost:8000/docs` | Swagger UI — interactive API explorer |
| `http://localhost:8000/redoc` | ReDoc — readable API reference |
| `http://localhost:8000/health` | Backend health check |

---

## Database

Dev uses **SQLite** — the file is `backend/wardrobe.db` (auto-created on first run).  
No setup needed. To reset it: delete `wardrobe.db` and restart the backend.

When moving to production: swap `DATABASE_URL` in `.env` to a PostgreSQL connection string.

---

## Common issues

| Problem | Fix |
|---------|-----|
| `npm: not recognized` | Node.js not on PATH — open a new terminal after installing Node |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` from the `backend/` folder |
| `NetworkError when fetching` | Backend isn't running — start Terminal 1 |
| Upload returns `500` | Check the backend terminal for the traceback |
| CLIP model slow first time | Fashion-CLIP downloads ~400MB model on first classify — wait for it |
