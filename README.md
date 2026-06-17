# Forex Predictor

A monorepo for the Forex Predictor application, containing both the backend API and the frontend web application.

## Setup Instructions

### Prerequisites
- Node.js (for the web frontend)
- Conda (for the backend API environment)

### Unified Development Setup

We provide a unified script that runs both the frontend and backend concurrently. The backend is automatically executed within the required conda environment, so manual activation is not needed.

1. Create the backend conda environment (one-time setup):
   ```bash
   cd api
   conda env create -f environment.yml
   cd ..
   ```
   **Note:** The unified runner requires the conda environment to be explicitly named `forex_prediction` (which is the default configured in `environment.yml`).

2. Install frontend dependencies (one-time setup):
   ```bash
   npm run install:all
   ```

3. Copy `api/.env.example` to `api/.env` and update any configuration values.

4. Launch both the backend API and the frontend web app simultaneously:
   ```bash
   npm run dev
   ```

## Features

### Backend API
- Built with FastAPI for high performance and automatic interactive API documentation.
- Robust configuration management via environment variables.
- Configured with `pytest` for unit testing.

### Frontend Web App
- Powered by React/Vite for fast development and build processes.
- Styled using Tailwind CSS for responsive and modern UI.
- Designed to consume the Backend API to deliver forex predictions.
