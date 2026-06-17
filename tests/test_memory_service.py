from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base, OutboxEvent, OutboxStatus
from app.schemas import MemoryCreate
from app.services import create_memory_with_outbox


def make_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def test_create_memory_writes_outbox_event() -> None:
    Session = make_session()

    with Session() as session:
        memory, event = create_memory_with_outbox(
            session,
            MemoryCreate(content="remember this", metadata={"source": "test"}),
        )

        stored_event = session.get(OutboxEvent, event.id)
        assert stored_event is not None
        assert stored_event.aggregate_id == memory.id
        assert stored_event.status == OutboxStatus.PENDING.value
        assert stored_event.payload == {"memory_id": memory.id}

