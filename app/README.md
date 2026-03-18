# Desktop Assistant Starter

Simple Electron + Next.js starter app for your assistant frontend.

## Requirements

- Node.js 20+
- Your backend server running (default expected URL: http://127.0.0.1:8000)

## Run in Development

1. Open terminal in this folder.
2. Install dependencies:

	npm install

3. Start desktop app:

	npm run dev

This starts:

- Next.js web UI on http://localhost:3000
- Electron shell that loads that UI

## Project Structure

- electron/main.js: Electron main process and backend health ping IPC
- electron/preload.js: Secure bridge from renderer to main process
- src/app/page.js: Starter assistant UI
- src/app/page.module.css: UI styles

## Backend Connectivity

The UI has a backend URL input and checks the endpoint:

- GET /health

If needed, set a default backend URL with:

- NEXT_PUBLIC_BACKEND_URL
