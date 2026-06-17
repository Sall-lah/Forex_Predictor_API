import { useGetPredictionQuery } from '../services/predictionApi';

export const usePrediction = (pair: string) => {
  const { data, error, isLoading, isFetching } = useGetPredictionQuery(pair, {
    pollingInterval: 10000,
  });

  let computedAt: Date | null = null;
  let validUntil: Date | null = null;

  if (data) {
    if (data.computed_at) computedAt = new Date(data.computed_at);
    if (data.valid_until) validUntil = new Date(data.valid_until);
  }

  return {
    probabilities: data ? {
      up: data.probability_up,
      down: data.probability_down,
      straight: data.probability_straight,
    } : null,
    computedAt,
    validUntil,
    isLoading: isLoading || isFetching,
    error,
  };
};
