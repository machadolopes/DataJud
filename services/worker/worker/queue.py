from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import psycopg
from psycopg.rows import dict_row

logger = logging.getLogger(__name__)

CLAIM_SQL = """
UPDATE jobs
SET status = 'running',
    locked_at = now(),
    locked_by = %(worker_id)s,
    attempts = attempts + 1,
    updated_at = now()
WHERE id = (
  SELECT id
  FROM jobs
  WHERE queue = %(queue)s
    AND status = 'queued'
    AND run_after <= now()
  ORDER BY created_at
  FOR UPDATE SKIP LOCKED
  LIMIT 1
)
RETURNING *
"""

RECOVER_SQL = """
UPDATE jobs
SET status = 'queued',
    locked_at = NULL,
    locked_by = NULL,
    updated_at = now()
WHERE status = 'running'
  AND locked_at < now() - (%(stale_minutes)s * interval '1 minute')
"""

HEARTBEAT_SQL = """
UPDATE jobs
SET locked_at = now(),
    updated_at = now()
WHERE id = %(job_id)s
  AND status = 'running'
  AND locked_by = %(worker_id)s
"""


def connect(database_url: str) -> psycopg.Connection[Any]:
    return psycopg.connect(database_url, row_factory=dict_row, autocommit=True)


def recover_stale_jobs(conn: psycopg.Connection[Any], stale_minutes: int) -> int:
    with conn.cursor() as cur:
        cur.execute(RECOVER_SQL, {"stale_minutes": stale_minutes})
        return cur.rowcount or 0


def claim_job(
    conn: psycopg.Connection[Any],
    queue: str,
    worker_id: str,
) -> dict[str, Any] | None:
    with conn.cursor() as cur:
        cur.execute(CLAIM_SQL, {"queue": queue, "worker_id": worker_id})
        row = cur.fetchone()
        return dict(row) if row else None


def heartbeat(conn: psycopg.Connection[Any], job_id: str, worker_id: str) -> None:
    with conn.cursor() as cur:
        cur.execute(HEARTBEAT_SQL, {"job_id": job_id, "worker_id": worker_id})


def fail_unhandled_job(
    conn: psycopg.Connection[Any],
    job_id: str,
    last_error: str,
    run_after: datetime | None = None,
) -> None:
    """Return an F0-claimed job to the queue so later phases can process it."""
    scheduled = run_after or (datetime.now(timezone.utc) + timedelta(minutes=5))
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE jobs
            SET status = 'queued',
                locked_at = NULL,
                locked_by = NULL,
                last_error = %(last_error)s,
                run_after = %(run_after)s,
                updated_at = now()
            WHERE id = %(job_id)s
            """,
            {"job_id": job_id, "last_error": last_error, "run_after": scheduled},
        )
