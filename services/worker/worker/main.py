from __future__ import annotations

import argparse
import logging
import signal
import time
from typing import Literal

from psycopg import OperationalError
from psycopg.errors import UndefinedTable

from worker.jsonlog import configure_logging
from worker.queue import claim_job, connect, fail_unhandled_job, recover_stale_jobs
from worker.settings import get_settings

logger = logging.getLogger("worker.main")

QueueName = Literal["ingest", "analysis"]
running = True


def _handle_stop(signum: int, _frame: object) -> None:
    global running
    logger.info("received_stop_signal", extra={"signal": signum})
    running = False


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Parecer Literário worker")
    parser.add_argument(
        "--queue",
        choices=("ingest", "analysis"),
        required=True,
        help="Queue this process should claim from",
    )
    return parser.parse_args(argv)


def run(queue: QueueName) -> None:
    settings = get_settings()
    extra = {"queue": queue, "workerId": settings.worker_id}
    logger.info("worker_starting", extra=extra)

    conn = None
    while running:
        try:
            if conn is None or conn.closed:
                conn = connect(settings.database_url)
            recovered = recover_stale_jobs(conn, settings.job_stale_minutes)
            if recovered:
                logger.info("recovered_stale_jobs", extra={**extra, "count": recovered})

            job = claim_job(conn, queue, settings.worker_id)
            if job is None:
                time.sleep(settings.poll_interval_seconds)
                continue

            job_extra = {**extra, "jobId": job["id"], "orderId": job["order_id"]}
            logger.info("job_claimed_but_unhandled_in_f0", extra=job_extra)
            fail_unhandled_job(
                conn,
                job["id"],
                "F0: pipeline handlers are not implemented yet",
            )
        except (OperationalError, UndefinedTable) as exc:
            logger.warning("database_not_ready", extra={**extra, "error": str(exc)})
            if conn is not None:
                conn.close()
                conn = None
            time.sleep(5)

    if conn is not None:
        conn.close()
    logger.info("worker_stopped", extra=extra)


def main(argv: list[str] | None = None) -> None:
    configure_logging()
    args = parse_args(argv)
    signal.signal(signal.SIGINT, _handle_stop)
    signal.signal(signal.SIGTERM, _handle_stop)
    run(args.queue)


if __name__ == "__main__":
    main()
