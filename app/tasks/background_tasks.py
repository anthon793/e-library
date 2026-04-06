from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.importer import import_verified_books

logger = logging.getLogger("hybrid_tasks")


@dataclass
class ImportJob:
    job_id: str
    query: str
    status: str = "queued"
    imported_count: int = 0
    checked_count: int = 0
    errors: list[str] = field(default_factory=list)


IMPORT_JOBS: dict[str, ImportJob] = {}


def create_job(query: str) -> ImportJob:
    job = ImportJob(job_id=uuid.uuid4().hex, query=query)
    IMPORT_JOBS[job.job_id] = job
    return job


def get_job(job_id: str) -> ImportJob | None:
    return IMPORT_JOBS.get(job_id)


def run_auto_import_job(job_id: str, query: str, category: str, field: str, max_results_per_source: int) -> None:
    job = IMPORT_JOBS.get(job_id)
    if not job:
        return

    job.status = "running"
    db: Session = SessionLocal()

    try:
        imported, checked, errors = asyncio.run(
            import_verified_books(
                db,
                query=query,
                category=category,
                field=field,
                max_results_per_source=max_results_per_source,
            )
        )
        job.imported_count = imported
        job.checked_count = checked
        job.errors.extend(errors)
        job.status = "completed"
    except Exception as exc:
        logger.exception("auto_import_failed job=%s", job_id)
        job.status = "failed"
        job.errors.append(str(exc))
    finally:
        db.close()
