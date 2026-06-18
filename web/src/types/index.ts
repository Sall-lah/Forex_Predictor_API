/**
 * Public types for the candlestick frontend.
 *
 * Keep this file lean: anything that is purely an internal shape
 * (live-feed message envelopes, request payloads) lives next to the
 * module that owns it.
 */

export interface PredictionProbabilities {
  up: number;
  down: number;
  straight: number;
}

export interface PredictionResponse {
  pair: string;
  probability_up: number;
  probability_down: number;
  probability_straight: number;
  computed_at: string;
  valid_until: string;
}

export interface HealthResponse {
  status: string;
  service?: string;
}
