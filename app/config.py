from __future__ import annotations

import os
import socket
from dataclasses import dataclass


def _get_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


def _get_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    return float(value)


@dataclass(frozen=True)
class Settings:
    database_url: str
    qdrant_url: str
    qdrant_collection: str
    embedding_dimensions: int
    worker_poll_interval_seconds: float
    outbox_lease_seconds: int
    worker_id: str


def load_settings() -> Settings:
    return Settings(
        database_url=os.getenv(
            "DATABASE_URL",
            "mysql+pymysql://memory:memory@localhost:3306/memory",
        ),
        qdrant_url=os.getenv("QDRANT_URL", "http://localhost:6333"),
        qdrant_collection=os.getenv("QDRANT_COLLECTION", "memories"),
        embedding_dimensions=_get_int("EMBEDDING_DIMENSIONS", 384),
        worker_poll_interval_seconds=_get_float("WORKER_POLL_INTERVAL_SECONDS", 2.0),
        outbox_lease_seconds=_get_int("OUTBOX_LEASE_SECONDS", 60),
        worker_id=os.getenv("WORKER_ID", socket.gethostname()),
    )


settings = load_settings()

