from __future__ import annotations

import logging
import time

from .config import settings
from .database import SessionLocal, create_tables
from .embeddings import embed_text
from .models import Memory, OutboxEventType
from .services import claim_next_outbox_event, mark_outbox_completed, mark_outbox_failed
from .vectordb import QdrantMemoryIndex


logger = logging.getLogger(__name__)


def process_once(index: QdrantMemoryIndex | None = None) -> bool:
    with SessionLocal() as session:
        event = claim_next_outbox_event(
            session=session,
            worker_id=settings.worker_id,
            lease_seconds=settings.outbox_lease_seconds,
        )
        if event is None:
            return False

        try:
            if event.event_type != OutboxEventType.MEMORY_CREATED.value:
                raise ValueError(f"unsupported event type: {event.event_type}")
            memory = session.get(Memory, event.aggregate_id)
            if memory is None:
                raise ValueError(f"memory not found: {event.aggregate_id}")
            vector = embed_text(memory.content, settings.embedding_dimensions)
            index = index or QdrantMemoryIndex()
            index.upsert_memory(memory, vector)
            mark_outbox_completed(session, event)
            logger.info("completed outbox event %s", event.id)
        except Exception as exc:
            logger.exception("failed outbox event %s", event.id)
            mark_outbox_failed(session, event, exc)
        return True


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    create_tables(retries=10, delay_seconds=2)
    logger.info("worker started as %s", settings.worker_id)
    while True:
        processed = process_once()
        if not processed:
            time.sleep(settings.worker_poll_interval_seconds)


if __name__ == "__main__":
    main()
