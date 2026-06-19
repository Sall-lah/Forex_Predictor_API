/**
 * Public types for the candlestick frontend.
 *
 * Keep this file lean: anything that is purely an internal shape
 * (live-feed message envelopes, request payloads) lives next to the
 * module that owns it.
 */

export interface HealthResponse {
  status: string;
  service?: string;
}
