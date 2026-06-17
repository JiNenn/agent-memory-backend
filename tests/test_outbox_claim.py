from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, OutboxStatus
from app.schemas import MemoryCreate
from app.services import claim_next_outbox_event, create_memory_with_outbox


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
