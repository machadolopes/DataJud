from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "../../.env"), extra="ignore")

    database_url: str
    worker_id: str = "worker-local"
    job_stale_minutes: int = 60
    job_heartbeat_seconds: int = 30
    poll_interval_seconds: float = 2.0
    llm_mode: str = "mock"
    email_provider: str = "mailpit"


@lru_cache(maxsize=1)
def get_settings() -> WorkerSettings:
    worker_id = os.environ.get("WORKER_ID") or os.environ.get("HOSTNAME") or "worker-local"
    return WorkerSettings(worker_id=worker_id)  # type: ignore[call-arg]
