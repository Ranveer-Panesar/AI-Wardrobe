# AI Wardrobe Recommendation System — Project Plan & Todo

Team: Ranveer (Python backend — request handling, combination engine, classification, image generation/VTON), Teammate (React frontend)
Stack: React (Vite) + FastAPI + SQLite (dev) → PostgreSQL (prod) + Fashion-CLIP + Colab (VTON showcase) + Vendor VTON API (primary)

---

## Phase 0 — Setup & Foundations

- [x] Repo created, initial commit pushed
- [x] Repo structure: `frontend/`, `backend/`, `ml-colab/`, `docs/`
- [x] Backend scaffold: FastAPI + config + DB connection + health check
- [x] `.gitignore`, `.env.example`
- [x] Dev database: SQLite (`wardrobe.db`) — zero-setup, ready to migrate to Postgres
- [ ] Write API contract (endpoints + request/response JSON shapes) — share with frontend dev
- [ ] Frontend scaffold: Vite + React + routing *(frontend dev)*
- [ ] Colab notebook skeleton (empty for now, filled in Phase 6)
- [ ] Branch protection on `main` enabled on GitHub

---

## Phase 1 — Auth

- [x] `User` DB model (email, phone, password_hash, storage_mode, created_at)
- [x] Signup endpoint (`POST /auth/signup` — email + phone + password)
- [x] Strong password validation (≥8 chars, uppercase, digit, special char)
- [x] Phone validation (E.164 international format)
- [x] Email validation (Pydantic `EmailStr`)
- [x] Password hashing (bcrypt via passlib)
- [x] Login endpoint → JWT access + refresh token (`POST /auth/login`)
- [x] Refresh token rotation (`POST /auth/refresh`)
- [ ] Email/phone OTP verification (stub exists, real SMS/email provider later)
- [ ] Frontend: login/register pages connected to API *(in progress — frontend dev)*
- [ ] Frontend: token storage, protected routes *(in progress — frontend dev)*

---

## Phase 2 — Wardrobe Upload & Classification

- [x] `Garment` DB model (category, colors, pattern, formality, embedding, image_url, user_id FK)
- [x] Garment–User relationship (FK with CASCADE delete, filtered by `user_id` on every query)
- [x] Image upload endpoint (`POST /wardrobe/items`, multipart)
- [x] Fashion-CLIP zero-shot category classification
- [x] Fashion-CLIP zero-shot pattern classification (solid, striped, plaid, …)
- [x] Fashion-CLIP zero-shot formality classification
- [x] Fashion-CLIP embedding stored per garment (for Phase 4)
- [x] Dominant color extraction (background-removed via rembg, then k-means)
- [x] List garments endpoint (`GET /wardrobe/items`)
- [x] Patch garment endpoint (`PATCH /wardrobe/items/{id}`)
- [x] Delete garment endpoint (`DELETE /wardrobe/items/{id}`)
- [x] Uploaded images served as static files (`/uploads/`)
- [ ] Frontend: upload flow, wardrobe grid view, correction UI *(frontend dev)*

---

## Phase 3 — Rule-Based Outfit Engine

- [x] Category compatibility matrix
- [x] Color-distance scoring (CIELAB ΔE)
- [x] Formality-level scoring
- [x] Pattern-clash penalty
- [x] Combination generator (valid combos from a user's wardrobe)
- [x] Ranking — return top N scored outfits (`POST /outfits/generate`)
- [x] Outfit persistence to DB
- [ ] Frontend: outfit suggestions UI *(frontend dev)*

---

## Phase 4 — ML Compatibility Head (on Fashion-CLIP embeddings)

- [ ] Download Polyvore Outfits dataset
- [ ] Build positive/negative training pairs
- [ ] Train small MLP/two-tower compatibility head (Colab)
- [ ] Export weights, load into backend inference
- [ ] Blend rule-engine score + learned compatibility score

---

## Phase 5 — Style Classification (bold / retro / casual / formal)

- [ ] Define taxonomy precisely
- [ ] Hand-label a seed set of outfits
- [ ] Train small classifier on Fashion-CLIP embeddings
- [ ] Attach style label(s) to each generated outfit

---

## Phase 6 — Virtual Try-On

- [ ] Sign up for vendor VTON API — **or** use free IDM-VTON on Colab ← going this route
- [x] `RenderProvider` abstraction: `MockProvider` / `ColabProvider` (IDM-VTON via ngrok)
- [x] Colab script: `ml-colab/idm_vton_server.py` (IDM-VTON + FastAPI + ngrok)
- [x] Mannequin render endpoint (`POST /render/mannequin`)
- [x] Full-body user-photo render endpoint (`POST /render/try-on`)
- [x] Async job queue (`RenderJob` DB model + FastAPI `BackgroundTasks`)
- [x] Poll endpoint (`GET /render/jobs/{job_id}`)
- [x] Rendered images served as static files (`/renders/`)
- [x] Get ngrok auth token + run the Colab notebook (one-time setup) — ✅ LIVE
- [ ] Frontend: render trigger + "generating..." state + result display *(frontend dev)*

---

## Phase 7 — Polish & Demo Prep

- [ ] Error handling + loading states across the app
- [ ] Deploy frontend + backend + DB
- [ ] Data export / delete-account flow
- [ ] Write up final report
- [ ] Prepare demo script + fallback plan for demo day
