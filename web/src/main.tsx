import React from 'react';
import ReactDOM from 'react-dom/client';
import { CandlesPage } from './pages/CandlesPage';
import './index.css';

document.title = 'Forex Candles';

const root = document.getElementById('app');
if (!root) {
  throw new Error('Missing #app root element');
}

ReactDOM.createRoot(root).render(
  <React.StrictMode>
    <CandlesPage />
  </React.StrictMode>
);
