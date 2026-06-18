/**
 * Lightweight helper for the `/health` endpoint. Routes through
 * the Vite proxy to the FastAPI backend.
 */

import { get } from './apiClient';

export interface HealthResponse {
  status: string;
  service?: string;
}

export async function fetchHealth(): Promise<HealthResponse> {
  // `/health` is proxied through Vite to the backend root path.
  const response = await fetch('/health');
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`);
  }
  return (await response.json()) as HealthResponse;
}

// Re-export `get` so tests can assert the apiClient is the source.
export { get };
