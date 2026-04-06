# Deploy E-Library Online

This app is now set up for single-service deployment with Docker (FastAPI + built React frontend served by FastAPI).

## 1. Required Environment Variables

Set these in your host (Render, Railway, Fly, etc):

- `SECRET_KEY` : strong random string
- `DATABASE_URL` : PostgreSQL URL (recommended for production)
- `UPLOAD_DIR` : `uploads`
- `GOOGLE_BOOKS_API_KEY` : optional but recommended
- `CORS_ORIGINS` : comma-separated origins (for same-domain deploy, this can be your app URL)

Example:

- `CORS_ORIGINS=https://your-app.onrender.com,https://www.yourdomain.com`

## 2. Deploy on Render (Recommended)

1. Push repo to GitHub.
2. In Render: New -> Web Service -> Connect repo.
3. Choose **Docker** environment.
4. Set environment variables above.
5. Deploy.

Render will use `Dockerfile` at repo root and expose your service.

## 3. Verify Deployment

After deploy:

- Open `https://<your-domain>/library`
- Test login and category navigation
- Open a book and verify reader loads
- Test Google preview on a known embeddable volume

## 4. Notes

- Frontend is served from `frontend/dist` by FastAPI in `app/main.py`.
- Keep `DATABASE_URL` persistent (managed Postgres), not SQLite for production.
- If authentication cookies are used cross-domain, ensure frontend and backend are same site or configure cookie/cors policy accordingly.
