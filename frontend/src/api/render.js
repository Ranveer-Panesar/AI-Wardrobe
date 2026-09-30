import { apiFetch } from './client';

const BASE = 'http://localhost:8000';

/**
 * POST /render/garment  →  { job_id }
 * Direct garment render — bypasses the outfit_id requirement.
 * Sends as FormData because the backend render routes use Form fields.
 */
export async function startMannequinRender(garmentId) {
  const token = localStorage.getItem('ai_wardrobe_token');
  const form = new FormData();
  form.append('garment_id', garmentId);

  const res = await fetch(`${BASE}/render/garment`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Render request failed');
  }
  return res.json(); // { job_id }
}

/**
 * POST /render/mannequin  →  { job_id }
 * Queues a mannequin render for an outfit.
 */
export async function startOutfitRender(outfitId) {
  const token = localStorage.getItem('ai_wardrobe_token');
  const form = new FormData();
  form.append('outfit_id', outfitId);

  const res = await fetch(`${BASE}/render/mannequin`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Outfit render request failed');
  }
  return res.json(); // { job_id }
}


/**
 * GET /render/jobs/{jobId}  →  { status, output_image_url?, error_message? }
 * Poll until status === 'done' or 'failed'.
 */
export async function getRenderJob(jobId) {
  const res = await apiFetch(`/render/jobs/${jobId}`);
  if (!res.ok) throw new Error('Failed to poll render job');
  return res.json();
}

/**
 * Poll a render job every `intervalMs` ms until it resolves.
 * Calls onProgress({ status, elapsedSeconds }) on each tick.
 * Times out after `timeoutMs` (default 10 min — covers first-run model download).
 * Returns the final image URL when done.
 */
export async function pollRenderJob(jobId, onProgress, intervalMs = 2000, timeoutMs = 600_000) {
  const startTime = Date.now();
  return new Promise((resolve, reject) => {
    const timer = setInterval(async () => {
      const elapsedSeconds = Math.round((Date.now() - startTime) / 1000);

      // Hard timeout guard
      if (elapsedSeconds * 1000 > timeoutMs) {
        clearInterval(timer);
        reject(new Error(`Render timed out after ${Math.round(timeoutMs / 60000)} minutes`));
        return;
      }

      try {
        const job = await getRenderJob(jobId);
        onProgress({ ...job, elapsedSeconds });

        if (job.status === 'done') {
          clearInterval(timer);
          const raw = job.output_image_url || job.image_url || '';
          const fullUrl = raw.startsWith('http') ? raw : `${BASE}${raw}`;
          resolve(fullUrl);
        } else if (job.status === 'failed' || job.status === 'error') {
          clearInterval(timer);
          reject(new Error(job.error_message || job.error || 'Render failed'));
        }
      } catch (err) {
        clearInterval(timer);
        reject(err);
      }
    }, intervalMs);
  });
}

/**
 * POST /outfits/generate  →  { outfits: [...] }
 * Payload: { count?: number } — the engine reads the user's wardrobe from the DB.
 */
export async function getOutfitRecommendations(payload = {}) {
  const res = await apiFetch('/outfits/generate', {
    method: 'POST',
    body: JSON.stringify({ count: payload.count || 6 }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Recommendation failed');
  }
  return res.json();
}
