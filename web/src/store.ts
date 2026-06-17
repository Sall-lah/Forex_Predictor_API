import { configureStore } from '@reduxjs/toolkit';
import { predictionApi } from './services/predictionApi';

export const store = configureStore({
  reducer: {
    [predictionApi.reducerPath]: predictionApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(predictionApi.middleware),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
