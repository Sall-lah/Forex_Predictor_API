export interface ApiResponse<T> {
  data: T;
  status: string;
}

export interface HealthResponse {
  status: string;
  service: string;
}

export interface MarketData {
  time: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}
