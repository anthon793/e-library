# Hybrid Book Acquisition and PDF Delivery System

## Architecture Pipeline

Search Sources -> Metadata Extraction -> PDF Link Extraction -> PDF Validation -> Database Storage -> API Delivery

## Implemented Components

- `app/models/hybrid_book.py`: PostgreSQL-ready SQLAlchemy model for verified hybrid books.
- `app/schemas/hybrid_book.py`: Request/response schemas.
- `app/crud.py`: Duplicate detection, list/search CRUD.
- `app/services/google_books.py`: Google Books metadata fetch.
- `app/services/open_library_hybrid.py`: Open Library metadata fetch.
- `app/services/doab.py`: DOAB metadata fetch.
- `app/services/openstax.py`: OpenStax metadata fetch.
- `app/services/gutenberg.py`: Gutenberg metadata fetch.
- `app/services/pdf_validator.py`: HEAD + range probe PDF validator.
- `app/services/importer.py`: Hybrid import orchestration.
- `app/services/revalidator.py`: Link re-validation service.
- `app/tasks/background_tasks.py`: In-memory background import job tracking.
- `app/utils/link_extractor.py`: Candidate link extraction and ranking.
- `app/utils/file_storage.py`: PDF upload storage and optional cover image storage.
- `app/utils/rate_limiter.py`: Source-level rate limiting helper.
- `app/routers/hybrid_books.py`: New `/books` endpoints.

## Database Fields (`hybrid_books`)

- `id`
- `title`
- `author`
- `description`
- `category`
- `cover_image`
- `download_link`
- `source`
- `is_verified`
- `file_size`
- `created_at`
- `last_checked`

Additional operational fields:
- `publisher`
- `published_year`
- `local_file_path`

## API Endpoints

### Auto Import

- `POST /books/auto-import`
  - Body:
  ```json
  {
    "query": "machine learning",
    "category": "artificial-intelligence",
    "max_results_per_source": 8
  }
  ```

- `GET /books/auto-import/{job_id}`
  - Returns background job status.

### Book Access

- `GET /books`
  - Supports: `skip`, `limit`, `category`, `author`, `source`
- `GET /books/search?q=...`
- `GET /books/{id}`
- `GET /books/{id}/view`
- `GET /books/{id}/download`
- `GET /books/{id}/stream`

### Manual Upload

- `POST /books/upload` (multipart/form-data)
  - Fields: `title`, `author`, `description`, `category`, `publisher`, `published_year`, `cover_image`, `file`

### Maintenance

- `POST /books/revalidate-links?limit=100`

## Environment Variables

Use `.env.example` as template.

Important values:
- `DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/elibrary`
- `UPLOAD_DIR=uploads`
- `HYBRID_IMPORT_MAX_RESULTS_PER_SOURCE=8`
- `HYBRID_PDF_VALIDATION_TIMEOUT=20`

## Run Instructions

1. Create virtual environment and install dependencies:

```bash
pip install -r requirements.txt
```

2. Set `.env` with PostgreSQL `DATABASE_URL`.

3. Start API:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

4. Open docs:

- `http://127.0.0.1:8000/docs`

## Notes on Scaling

- Current background jobs use FastAPI `BackgroundTasks` and in-memory state.
- For production, replace with Celery + Redis worker queue.
- Schedule `/books/revalidate-links` via cron or task scheduler.
