import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';

export interface PredictionResponse {
  pair: string;
  probability_up: number;
  probability_down: number;
  probability_straight: number;
  computed_at: string;
  valid_until: string;
}

export const predictionApi = createApi({
  reducerPath: 'predictionApi',
  baseQuery: fetchBaseQuery({ baseUrl: '/api/v1' }),
  endpoints: (builder) => ({
    getPrediction: builder.query<PredictionResponse, string>({
      query: (pair) => ({
        url: '/prediction/predict',
        method: 'POST',
        body: { pair },
      }),
    }),
  }),
});

export const { useGetPredictionQuery } = predictionApi;
