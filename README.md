# E-Library

Academic E-Library web application with:
- FastAPI backend
- React + Vite frontend
- Hybrid library model (local/internal books + external Google Books preview support)
- Mobile-first reading flow

## Features

- Category-based library for:
  - Cybersecurity
  - Data Science
  - Artificial Intelligence
- Search from internal library by field/category
- Google Books embedded preview integration (volume ID based)
- Mobile behavior:
  - Library-first landing experience
  - Tap a book to open reader directly
  - Full-screen mobile reader with close button back to Library
- Admin and lecturer capabilities for upload/import/management

## Project Structure

- app: FastAPI backend
- frontend: React frontend (Vite)
- uploads: local uploaded assets
- DEPLOYMENT.md: deployment instructions

## Requirements

- Python 3.10+
- Node.js 18+
- npm

## Local Setup

1. Clone repository
2. Create and activate Python virtual environment
3. Install backend dependencies
4. Install frontend dependencies

Windows PowerShell example:

1) Backend setup
- cd c:\Users\ameha\Downloads\E-library
- python -m venv .venv
- .\.venv\Scripts\Activate.ps1
- pip install -r requirements.txt

2) Frontend setup
- cd frontend
- npm install

## Environment Variables

Copy .env.example to .env and update values as needed.

Important variables:
- SECRET_KEY
- DATABASE_URL
- UPLOAD_DIR
- GOOGLE_BOOKS_API_KEY (optional but recommended)
- CORS_ORIGINS

## Run Locally

Backend:
- cd c:\Users\ameha\Downloads\E-library
- .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000

Frontend:
- cd c:\Users\ameha\Downloads\E-library\frontend
- npm run dev

Then open the frontend URL printed by Vite.

## Build Frontend

- cd c:\Users\ameha\Downloads\E-library\frontend
- npm run build

This creates frontend/dist which can be served by FastAPI in production.

## Authentication Notes

Default seeded users on startup:
- admin / admin123
- lecturer / lecturer123

Use only for development and change credentials in production.

## Deployment

A Dockerfile is included for single-service deployment (backend + built frontend).

Quick path:
- Push repository to GitHub
- Deploy on Render as Docker web service
- Set environment variables in platform dashboard

Detailed steps are in DEPLOYMENT.md.

## API Overview

Main backend areas:
- /api/auth endpoints in app/routers/auth.py
- /books hybrid library endpoints in app/routers/hybrid_books.py
- /api/books endpoints for compatibility and Google-related endpoints

## Mobile UX Summary

- Library is the primary landing page experience for mobile users
- Sidebar navigation is available as a mobile drawer
- Selecting a book opens reader directly
- Reader fills screen on mobile with a Close button back to Library

## Troubleshooting

If backend does not start:
- Check .env values
- Ensure virtual environment is active
- Ensure DATABASE_URL is valid
- Check terminal output for stack trace

If frontend does not start:
- Ensure dependencies are installed in frontend
- Run npm run build to verify compile errors

If Google preview fails:
- Some titles are restricted by publisher and not embeddable
- Ensure valid volume ID and network access to Google Books scripts

## License

Add your preferred license here (MIT, Apache-2.0, etc).
