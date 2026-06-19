/**
 * `usePrediction(pair)` polls `POST /api/v1/prediction/predict` every
 * 10 s via SWR and exposes the probability payload plus loading /
 * error state to the consumer.
 *
 * Uses SWR's `mutate` so two components consuming the same pair share
 * a single in-flight request per 10-second window.
 */

import useSWR from 'swr';
import { post } from '../services/apiClient';

export interface PredictionResponse {
  pair: string;
  probability_up: number;
  probability_down: number;
  probability_straight: number;
  computed_at: string;
  valid_until: string;
}

export interface PredictionProbabilities {
  up: number;
  down: number;
  straight: number;
}

export interface UsePredictionResult {
  probabilities: PredictionProbabilities | null;
  isLoading: boolean;
  error: Error | null;
  computedAt: Date | null;
  validUntil: Date | null;
}

const fetcher = async (key: string): Promise<PredictionResponse> => {
  const [, pair] = key.split('|');
  return post<PredictionResponse>('/prediction/predict', { pair });
};

export function usePrediction(pair: string): UsePredictionResult {
  const { data, error, isLoading } = useSWR<PredictionResponse>(
    pair ? `prediction|${pair}` : null,
    fetcher,
    { refreshInterval: 10_000 },
  );

  const computedAt = data?.computed_at ? new Date(data.computed_at) : null;
  const validUntil = data?.valid_until ? new Date(data.valid_until) : null;

  return {
    probabilities: data
      ? {
          up: data.probability_up,
          down: data.probability_down,
          straight: data.probability_straight,
        }
      : null,
    isLoading,
    error: error ?? null,
    computedAt,
    validUntil,
  };
}
