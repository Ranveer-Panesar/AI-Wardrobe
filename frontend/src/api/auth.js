import { apiFetch } from './client';

/**
 * POST /auth/login  →  { access_token, refresh_token }
 */
export async function login(email, password) {
  const res = await apiFetch('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Login failed');
  }
  return res.json(); // { access_token, refresh_token }
}

/**
 * POST /auth/signup  →  { id, email, phone }
 */
export async function signup(email, phone, password) {
  const res = await apiFetch('/auth/signup', {
    method: 'POST',
    body: JSON.stringify({ email, phone, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || 'Sign up failed');
  }
  return res.json();
}
