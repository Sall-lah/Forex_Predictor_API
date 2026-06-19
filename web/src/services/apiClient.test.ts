import { describe, expect, it, vi, beforeEach, afterEach } from 'vitest';
import { get, post } from './apiClient';

function mockResponse(opts: {
  ok?: boolean;
  status?: number;
  statusText?: string;
  body?: unknown;
}): Response {
  return {
    ok: opts.ok ?? true,
    status: opts.status ?? 200,
    statusText: opts.statusText ?? '',
    json: () => Promise.resolve(opts.body),
    clone() {
      return {
        ok: this.ok,
        status: this.status,
        statusText: this.statusText,
        json: () => Promise.resolve(opts.body),
      } as Response;
    },
  } as unknown as Response;
}

describe('apiClient', () => {
  let fetchSpy: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchSpy = vi.fn();
    vi.stubGlobal('fetch', fetchSpy);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('get', () => {
    it('returns parsed JSON on success', async () => {
      fetchSpy.mockResolvedValue(mockResponse({ ok: true, body: { data: 'test' } }));

      const result = await get<{ data: string }>('/test');

      expect(result).toEqual({ data: 'test' });
      expect(fetchSpy).toHaveBeenCalledWith('/api/v1/test');
    });

    it('throws parsed detail on error response', async () => {
      fetchSpy.mockResolvedValue(
        mockResponse({
          ok: false,
          status: 422,
          statusText: 'Unprocessable Entity',
          body: { detail: 'Invalid pair' },
        }),
      );

      await expect(get('/test')).rejects.toThrow('Invalid pair');
    });

    it('falls back to statusText when body has no detail', async () => {
      fetchSpy.mockResolvedValue(
        mockResponse({
          ok: false,
          status: 500,
          statusText: 'Internal Server Error',
          body: { message: 'something' },
        }),
      );

      await expect(get('/test')).rejects.toThrow('Internal Server Error');
    });
  });

  describe('post', () => {
    it('sends body and returns parsed JSON', async () => {
      fetchSpy.mockResolvedValue(mockResponse({ ok: true, body: { result: 'ok' } }));

      const result = await post<{ result: string }>('/predict', { pair: 'BTC/USD' });

      expect(result).toEqual({ result: 'ok' });
      expect(fetchSpy).toHaveBeenCalledWith('/api/v1/predict', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ pair: 'BTC/USD' }),
      });
    });

    it('throws on network error', async () => {
      fetchSpy.mockRejectedValue(new TypeError('Failed to fetch'));

      await expect(post('/predict', {})).rejects.toThrow('Failed to fetch');
    });
  });
});
