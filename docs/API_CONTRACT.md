# API Contract — AI Wardrobe

Living document — update whenever an endpoint shape changes.
Frontend builds against this; backend implements it. If they diverge, fix this file first.

**Base URL (dev):** `http://localhost:8000`  
**Interactive docs:** `http://localhost:8000/docs` (Swagger UI, always up to date)  
**Status:** ✅ = implemented & tested | 🔜 = planned

---

## Conventions

- **Auth:** All protected endpoints require `Authorization: Bearer <access_token>` header.
- **IDs:** All IDs are UUID strings.
- **Timestamps:** ISO 8601 UTC, e.g. `"2026-08-31T18:00:00Z"`.
- **Errors:** Always `{ "detail": "human-readable message" }` — consistent across every endpoint.
- **Image URLs:** Relative paths like `/uploads/<uuid>.jpg` — prefix with `http://localhost:8000` in dev to get a full URL.

---

## Auth

### `POST /auth/signup`
Create a new user account.

**Request**
```json
{
  "email": "user@example.com",
  "phone": "+919876543210",
  "password": "Secure@123"
}
```

**Password rules** (enforced server-side — show these in the signup form):
- At least 8 characters
- At least one uppercase letter
- At least one digit
- At least one special character (`!@#$%^&*` etc.)

**Phone rules:** International format, 8–15 digits. Leading `+` is optional but recommended. E.g. `+919876543210`, `919876543210`.

**Response `201`**
```json
{ "id": "uuid", "email": "user@example.com", "phone": "+919876543210" }
```

**Errors**
| Code | Reason |
|------|--------|
| `409` | Email or phone already registered |
| `422` | Validation failure (bad email, weak password, bad phone) — `detail` lists all failed rules |

---

### `POST /auth/login`
**Request**
```json
{ "email": "user@example.com", "password": "Secure@123" }
```

**Response `200`**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```
Store `access_token` in memory / localStorage. Store `refresh_token` in an httpOnly cookie or secure storage. Access token expires in **30 minutes**.

**Errors**
| Code | Reason |
|------|--------|
| `401` | Invalid email or password (intentionally vague — no user enumeration) |

---

### `POST /auth/refresh`
Rotate both tokens. Call this when the access token expires.

**Request**
```json
{ "refresh_token": "eyJ..." }
```

**Response `200`** — same shape as login. **Both** tokens are replaced (old refresh token is invalidated).

**Errors**
| Code | Reason |
|------|--------|
| `401` | Refresh token invalid or expired |

---

## Wardrobe ✅

All wardrobe endpoints require auth. Items are always scoped to the authenticated user — you'll only ever see your own garments.

### `POST /wardrobe/items` — Upload & classify a garment
**Request:** `multipart/form-data`

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `file` | image file | ✅ | JPEG, PNG, WebP — anything Pillow can read |
| `include_embedding` | bool (query param) | ❌ | Default `false`. Set `true` to store the Fashion-CLIP embedding (needed for Phase 4 ML scoring). |

**Response `201`**
```json
{
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "category": "casual shirt",
  "category_confidence": 0.87,
  "pattern": "striped",
  "formality": "smart casual",
  "dominant_colors": ["#1a3c5e", "#f2f2f2", "#c0392b"],
  "image_url": "/uploads/3fa85f64-5717-4562-b3fc-2c963f66afa6.jpg",
  "created_at": "2026-08-31T18:00:00"
}
```

To show the image: `http://localhost:8000` + `image_url`.

**Errors**
| Code | Reason |
|------|--------|
| `400` | File is not an image / corrupt image |
| `401` | Missing or invalid token |

---

### `GET /wardrobe/items` — List all garments ✅
**Response `200`**
```json
{
  "items": [ /* array of garment objects (same shape as POST response) */ ],
  "total": 12
}
```
Returns newest first. No pagination yet — revisit if needed.

---

### `PATCH /wardrobe/items/{id}` — Correct a misclassification ✅
Send only the fields you want to change.

**Request**
```json
{ "category": "blazer", "pattern": "solid" }
```
All fields optional: `category`, `pattern`, `formality`.

**Response `200`** — updated garment object (same shape as POST).

**Errors**
| Code | Reason |
|------|--------|
| `404` | Garment not found (or belongs to a different user) |

---

### `DELETE /wardrobe/items/{id}` — Remove a garment ✅
**Response `204 No Content`**

**Errors**
| Code | Reason |
|------|--------|
| `404` | Garment not found |

---

## Outfits ✅

### `POST /outfits/generate` — Generate outfit suggestions
Runs the rule-based engine over the user's wardrobe and returns the top N scored combinations. Each outfit is **persisted** to the DB so VTON can reference it by ID later.

**Request**
```json
{ "count": 5 }
```
`count`: 1–20, default 5.

**Response `200`**
```json
{
  "outfits": [
    {
      "id": "uuid",
      "garment_ids": ["uuid-shirt", "uuid-trousers"],
      "score": 0.82,
      "style_tags": { "casual": 0.70, "formal": 0.10, "bold": 0.10, "retro": 0.10 }
    }
  ]
}
```

`score`: 0–1 composite compatibility score (colour harmony + formality match + pattern clash).  
`style_tags`: probability breakdown across four style axes — values sum to ~1.

**Errors**
| Code | Reason |
|------|--------|
| `422` | Fewer than 2 garments in wardrobe |

---

### `GET /outfits/saved` — Retrieve previously generated outfits ✅
**Response `200`**
```json
{
  "outfits": [ /* array of outfit objects */ ],
  "total": 10
}
```
Newest first.

---

## Classification (standalone) ✅

### `POST /classify`
Classify an image without saving anything — useful for previewing classification before upload.

**Request:** `multipart/form-data`, field `file` = image. Optional query param `?include_embedding=true`.

**Response `200`**
```json
{
  "category": "casual shirt",
  "category_confidence": 0.87,
  "pattern": "striped",
  "formality": "smart casual",
  "dominant_colors": ["#1a3c5e", "#f2f2f2"],
  "embedding": null
}
```
Not auth-protected. Does **not** persist anything.

---

## Render / VTON 🔜 (Phase 6)

Endpoints below are **planned** — shapes are final so frontend can build against them now.

### `POST /render/mannequin`
Render the outfit on a generic mannequin.

**Request**
```json
{ "outfit_id": "uuid" }
```

**Response `202`** (async — renders take several seconds)
```json
{ "job_id": "uuid", "status": "queued" }
```

---

### `POST /render/try-on`
Render the outfit on a user-provided full-body photo.

**Request:** `multipart/form-data`

| Field | Type | Required |
|-------|------|----------|
| `outfit_id` | string (UUID) | ✅ |
| `file` | image (full-body photo) | ✅ |

**Response `202`**
```json
{ "job_id": "uuid", "status": "queued" }
```

---

### `GET /render/jobs/{job_id}`
Poll for render result.

**Response `200`**
```json
{
  "job_id": "uuid",
  "status": "done",
  "output_image_url": "/renders/uuid.jpg"
}
```
`status` values: `queued` → `processing` → `done` | `failed`

Poll every 2–3 seconds until `status` is `done` or `failed`. Recommended: use a 60-second timeout.
