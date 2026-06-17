from datetime import timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, OutboxStatus, utcnow
from app.schemas import MemoryCreate
from app.services import claim_next_outbox_event, create_memory_with_outbox, mark_outbox_completed


def make_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def test_claim_next_pending_outbox_event() -> None:
    Session = make_session()

    with Session() as session:
        _, event = create_memory_with_outbox(session, MemoryCreate(content="remember this"))

        claimed = claim_next_outbox_event(session, "worker-1", lease_seconds=30)

        assert claimed is not None
        assert claimed.id == event.id
        assert claimed.status == OutboxStatus.PROCESSING.value
        assert claimed.locked_by == "worker-1"
        assert claimed.locked_until is not None


def test_expired_processing_event_can_be_reclaimed() -> None:
    Session = make_session()

    with Session() as session:
        _, event = create_memory_with_outbox(session, MemoryCreate(content="remember this"))
        event.status = OutboxStatus.PROCESSING.value
        event.locked_by = "dead-worker"
        event.locked_until = utcnow() - timedelta(seconds=1)
        session.commit()

        claimed = claim_next_outbox_event(session, "worker-2", lease_seconds=30)

        assert claimed is not None
        assert claimed.id == event.id
        assert claimed.locked_by == "worker-2"


def test_completed_event_clears_lock() -> None:
    Session = make_session()

    with Session() as session:
        _, event = create_memory_with_outbox(session, MemoryCreate(content="remember this"))
        claimed = claim_next_outbox_event(session, "worker-1", lease_seconds=30)
        assert claimed is not None

        mark_outbox_completed(session, claimed)

        stored_event = session.get(type(event), event.id)
        assert stored_event is not None
        assert stored_event.status == OutboxStatus.COMPLETED.value
        assert stored_event.locked_by is None
        assert stored_event.locked_until is None
        assert stored_event.completed_at is not None
