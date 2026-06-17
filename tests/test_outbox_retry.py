from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, OutboxStatus
from app.schemas import MemoryCreate
from app.services import claim_next_outbox_event, create_memory_with_outbox, mark_outbox_failed


def make_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def test_failed_event_returns_to_pending_before_max_retries() -> None:
    Session = make_session()

    with Session() as session:
        _, event = create_memory_with_outbox(session, MemoryCreate(content="remember this"))
        event.max_retries = 2
        session.commit()
        claimed = claim_next_outbox_event(session, "worker-1", lease_seconds=30)
        assert claimed is not None

        mark_outbox_failed(session, claimed, RuntimeError("temporary"))

        assert claimed.status == OutboxStatus.PENDING.value
        assert claimed.retry_count == 1
        assert claimed.last_error == "temporary"


def test_failed_event_moves_to_failed_at_max_retries() -> None:
    Session = make_session()

    with Session() as session:
        _, event = create_memory_with_outbox(session, MemoryCreate(content="remember this"))
        event.max_retries = 1
        session.commit()
        claimed = claim_next_outbox_event(session, "worker-1", lease_seconds=30)
        assert claimed is not None

        mark_outbox_failed(session, claimed, RuntimeError("still broken"))

        assert claimed.status == OutboxStatus.FAILED.value
        assert claimed.retry_count == 1
        assert claimed.last_error == "still broken"
