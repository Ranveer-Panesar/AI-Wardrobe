# AI Wardrobe Recommendation System — Project Plan & Todo

Team: Ranveer (Python backend — request handling, combination engine, classification, image generation/VTON), Teammate (React frontend + databases)
Stack: React (Vite) + FastAPI + PostgreSQL + Fashion-CLIP + Colab (VTON showcase) + Vendor VTON API (primary)

---

## Phase 0 — Setup & Foundations

- [x] Repo created, initial commit pushed
- [ ] Write API contract (endpoints + request/response JSON shapes) — do this together before diverging
- [x] Repo structure: `frontend/`, `backend/`, `ml-colab/`, `docs/`
- [x] Backend scaffold: FastAPI + config + DB connection + health check
- [ ] Frontend scaffold: Vite + React + routing
- [ ] Dev database: local Postgres or SQLite (start SQLite for zero-setup, migrate to Postgres later)
- [ ] Colab notebook skeleton (empty for now, filled in Phase 6)
- [x] `.gitignore`, `.env.example`
- [ ] Branch protection on `main` enabled on GitHub
- [ ] Both devs comfortable with the PR cycle (branch → commit → push → PR → review → merge)

## Phase 1 — Auth

- [ ] `User` DB model (email, phone, password_hash, storage_mode, created_at) — owned by frontend/DB dev
- [ ] Signup endpoint (email + phone + password) — owned by backend dev
- [ ] Password hashing (bcrypt/argon2)
- [ ] Login endpoint → JWT access + refresh token
- [ ] Email/phone OTP verification (stub first, real SMS/email provider later)
- [ ] Refresh token rotation + revocation
- [ ] Frontend: signup/login pages, token storage, protected routes

## Phase 2 — Wardrobe Upload & Classification

- [ ] `Garment` DB model (category, subcategory, colors, pattern, embedding, image_url, user_id) — owned by frontend/DB dev
- [ ] Image upload endpoint (multipart) — owned by backend dev
- [ ] Integrate Fashion-CLIP: zero-shot category classification
- [ ] Extract + store Fashion-CLIP embedding per garment
- [ ] Color extraction (k-means on image)
- [ ] Frontend: upload flow, wardrobe grid view, correction UI

## Phase 3 — Rule-Based Outfit Engine

- [ ] Category compatibility matrix
- [ ] Color-distance scoring function
- [ ] Formality-level scoring
- [ ] Pattern-clash penalty
- [ ] Combination generator (valid combos from a user's wardrobe)
- [ ] Ranking — return top N scored outfits
- [ ] Frontend: outfit suggestions UI

## Phase 4 — ML Compatibility Head (on Fashion-CLIP embeddings)

- [ ] Download Polyvore Outfits dataset
- [ ] Build positive/negative training pairs
- [ ] Train small MLP/two-tower compatibility head (Colab)
- [ ] Export weights, load into backend inference
- [ ] Blend rule-engine score + learned compatibility score

## Phase 5 — Style Classification (bold / retro / casual / formal)

- [ ] Define taxonomy precisely
- [ ] Hand-label a seed set of outfits
- [ ] Train small classifier on Fashion-CLIP embeddings
- [ ] Attach style label(s) to each generated outfit

## Phase 6 — Virtual Try-On

- [ ] Sign up for vendor VTON API (Fashn.ai / Revery.ai) — primary path
- [ ] `RenderProvider` abstraction in backend: `MockProvider` / `ColabProvider` / `VendorAPIProvider`
- [ ] Colab notebook: CatVTON (or IDM-VTON) + FastAPI + ngrok
- [ ] Mannequin render endpoint
- [ ] Full-body user-photo render endpoint
- [ ] Async job queue for renders
- [ ] Frontend: render trigger + "generating..." state + result display

## Phase 7 — Polish & Demo Prep

- [ ] Error handling + loading states across the app
- [ ] Deploy frontend + backend + DB
- [ ] Data export / delete-account flow
- [ ] Write up final report
- [ ] Prepare demo script + fallback plan for demo day
