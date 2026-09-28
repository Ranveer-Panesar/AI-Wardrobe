import { apiFetch } from './client';

const UPLOADS_BASE = 'http://localhost:8000';

/**
 * Resolve a garment image_url (e.g. "/uploads/abc.jpg") to a full URL.
 */
export function resolveImageUrl(imageUrl) {
  if (!imageUrl) return null;
  if (imageUrl.startsWith('http')) return imageUrl;
  return `${UPLOADS_BASE}${imageUrl}`;
}

/**
 * GET /wardrobe/items  →  { items: [...], total: number }
 */
export async function getItems() {
  const res = await apiFetch('/wardrobe/items');
  if (!res.ok) throw new Error('Failed to fetch wardrobe');
  return res.json();
}

/**
 * POST /wardrobe/items (multipart)  →  GarmentResponse
 */
export async function uploadItem(file) {
  const form = new FormData();
  form.append('file', file);
  const res = await apiFetch('/wardrobe/items', {
    method: 'POST',
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Upload failed');
  }
  return res.json();
}

/**
 * DELETE /wardrobe/items/{id}  →  204 No Content
 */
export async function deleteItem(id) {
  const res = await apiFetch(`/wardrobe/items/${id}`, { method: 'DELETE' });
  if (!res.ok && res.status !== 204) throw new Error('Delete failed');
}
