/**
 * Lightweight helper for the BFF `/health` endpoint. Routes through
 * the shared `apiClient` for consistent error handling.
 */

import { get } from './apiClient';

export interface HealthResponse {
  status: string;
  service?: string;
}

export async function fetchHealth(): Promise<HealthResponse> {
  // `/health` is served by the BFF (not the API prefix), so we hit
  // the root path directly.
  const response = await fetch('/health');
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`);
  }
  return (await response.json()) as HealthResponse;
}

// Re-export `get` so tests can assert the apiClient is the source.
export { get };
