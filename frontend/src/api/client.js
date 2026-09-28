const BASE_URL = '/api';

function getToken() {
  return localStorage.getItem('ai_wardrobe_token');
}

export async function apiFetch(path, options = {}) {
  const token = getToken();

  const headers = {
    ...options.headers,
  };

  // Only set Content-Type for JSON bodies (not for FormData)
  if (options.body && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  // On 401 (expired/invalid token), clear local auth state
  if (res.status === 401) {
    localStorage.removeItem('ai_wardrobe_token');
    window.dispatchEvent(new Event('auth:logout'));
  }

  return res;
}
