from worker.queue import CLAIM_SQL


def test_claim_sql_uses_skip_locked() -> None:
    normalized = " ".join(CLAIM_SQL.split())
    assert "FOR UPDATE SKIP LOCKED" in normalized
    assert "status = 'queued'" in normalized
    assert "attempts = attempts + 1" in normalized
