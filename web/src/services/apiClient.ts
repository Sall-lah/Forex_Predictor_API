/**
 * Thin typed HTTP client used by every fetch site in the frontend.
 *
 * On a non-2xx response the client attempts to parse the JSON body and
 * surface the FastAPI `detail` field as the thrown `Error.message`. If
 * the body is not JSON, it falls back to `response.statusText`. This
 * single helper replaces the older `apiClient` (now removed) and is
 * the only place in the app that knows how to read FastAPI error
 * responses.
 */

const API_BASE_URL = '/api/v1';

async function parseDetail(response: Response): Promise<string> {
  const fallback = response.statusText || `HTTP ${response.status}`;
  try {
    const data: unknown = await response.clone().json();
    if (
      data !== null &&
      typeof data === 'object' &&
      'detail' in data
    ) {
      const detail = (data as { detail: unknown }).detail;
      if (typeof detail === 'string') return detail;
      try {
        return JSON.stringify(detail);
      } catch {
        return fallback;
      }
    }
  } catch {
    // Body was not JSON; fall through.
  }
  return fallback;
}

export async function get<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`);
  if (!response.ok) {
    const message = await parseDetail(response);
    throw new Error(message);
  }
  return (await response.json()) as T;
}

export async function post<T>(endpoint: string, body: unknown): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const message = await parseDetail(response);
    throw new Error(message);
  }
  return (await response.json()) as T;
}
