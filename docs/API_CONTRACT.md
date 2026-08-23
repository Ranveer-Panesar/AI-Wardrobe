# API Contract — AI Wardrobe

Living document. Update this whenever an endpoint's shape changes — it's
the source of truth both of you build against, so frontend work doesn't
have to wait on backend implementation to start.

Base URL (dev): `http://localhost:8000`

---

## Auth

### `POST /auth/signup`
**Request**
```json
{ "email": "user@example.com", "phone": "+919876543210", "password": "min8chars" }
```
**Response `201`**
```json
{ "id": "uuid", "email": "user@example.com", "phone": "+919876543210" }
```
**Errors**: `409` if email or phone already registered, `422` on validation failure.

### `POST /auth/login`
**Request**
```json
{ "email": "user@example.com", "password": "min8chars" }
```
**Response `200`**
```json
{ "access_token": "jwt...", "refresh_token": "jwt...", "token_type": "bearer" }
```
**Errors**: `401` on bad credentials.

### `POST /auth/refresh`
**Request**
```json
{ "refresh_token": "jwt..." }
```
**Response `200`**: same shape as login.

### Auth header convention
All protected endpoints below expect:
```
Authorization: Bearer <access_token>
```

---

## Classification (implemented)

### `POST /classify`
**Request**: `multipart/form-data`, field `file` = image. Optional query
param `?include_embedding=true`.
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
Note: does not persist anything — pure classify-and-return. Not yet
auth-protected (add once wardrobe upload wraps it).

---

## Wardrobe (planned — Phase 2)

### `POST /wardrobe/items` (auth required)
Upload + classify + persist a garment in one call.
**Request**: `multipart/form-data`, field `file` = image.
**Response `201`**
```json
{
  "id": "uuid",
  "category": "casual shirt",
  "category_confidence": 0.87,
  "pattern": "striped",
  "formality": "smart casual",
  "dominant_colors": ["#1a3c5e", "#f2f2f2"],
  "image_url": "https://.../garment123.jpg",
  "created_at": "2026-08-14T12:00:00Z"
}
```

### `GET /wardrobe/items` (auth required)
**Response `200`**: array of the same shape as above (list the user's wardrobe).

### `PATCH /wardrobe/items/{id}` (auth required)
User correcting a misclassified field (e.g. category was wrong).
**Request**: any subset of `{category, pattern, formality}`.
**Response `200`**: updated item, same shape as `POST`.

---

## Outfits (planned — Phase 3/4)

### `POST /outfits/generate` (auth required)
**Request**
```json
{ "count": 5 }
```
**Response `200`**
```json
{
  "outfits": [
    {
      "id": "uuid",
      "garment_ids": ["uuid1", "uuid2"],
      "score": 0.82,
      "style_tags": { "casual": 0.7, "bold": 0.1, "formal": 0.05, "retro": 0.15 }
    }
  ]
}
```

---

## Render / VTON (planned — Phase 6)

### `POST /render/mannequin` (auth required)
**Request**
```json
{ "outfit_id": "uuid" }
```
**Response `202`** (async job — render takes several seconds)
```json
{ "job_id": "uuid", "status": "queued" }
```

### `POST /render/try-on` (auth required)
Same as above, plus a full-body user photo.
**Request**: `multipart/form-data`, fields `outfit_id` + `file` (person photo).
**Response `202`**: same shape as above.

### `GET /render/jobs/{job_id}` (auth required)
**Response `200`**
```json
{ "job_id": "uuid", "status": "done", "output_image_url": "https://.../render123.jpg" }
```
`status` is one of: `queued | processing | done | failed`.

---

## Conventions

- All timestamps: ISO 8601 UTC.
- All IDs: UUID strings.
- Errors: `{ "detail": "human-readable message" }` (FastAPI's default shape) — frontend can rely on this consistently across every endpoint.
- Pagination (once wardrobe lists get long): not yet specified — revisit if it becomes a real need.
