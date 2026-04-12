# Phase 1 Context: Foundation & Orchestration

## Overview
This phase focuses on establishing the monorepo structure, initializing the new React + Express frontend application in the `/web` directory, and configuring a unified task runner to boot both the existing Python backend (`/api`) and the new frontend (`/web`) concurrently.

## Key Decisions

1. **Root Dependency Management (Task Runner Root)**
   - We will implement a lightweight `package.json` at the project root.
   - Its sole purpose is to act as a task runner using `concurrently` (or a similar tool) to boot both applications with a single command.
   - All Node/React dependencies will live inside `web/package.json`, avoiding complex workspace configurations since the backend is Python-based.

2. **Web Directory Structure (Integrated Web App)**
   - We will use a single `package.json` inside the `web/` directory.
   - The React frontend and the Express backend-for-frontend (BFF) will share this directory.
   - **Development**: Express will act as an API proxy to the Python backend to avoid CORS issues and simplify routing. Vite will handle the React dev server.
   - **Production**: Express will serve the built React static files alongside proxying API requests to the Python backend.

## Tech Stack
- Frontend: React 19, Vite 6
- Backend-for-Frontend: Express 5
- Orchestration: `concurrently`

## Success Criteria Reminder
1. Running a single command from the project root starts both the FastAPI backend and Express web server.
2. Stopping the runner cleanly terminates both processes without leaving zombie instances.
3. The React app is accessible in the browser and successfully routes API requests to the backend via the Express proxy.