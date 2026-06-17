from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import worker
from app.models import Base, OutboxEvent, OutboxStatus
from app.schemas import MemoryCreate
from app.services import create_memory_with_outbox


class FakeIndex:
    def __init__(self) -> None:
        self.upserted: list[tuple[str, str, list[float]]] = []

    def upsert_memory(self, memory, vector: list[float]) -> None:
        self.upserted.append((memory.id, memory.content, vector))


def make_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def test_process_once_indexes_memory_and_completes_event(monkeypatch) -> None:
    Session = make_session()
    monkeypatch.setattr(worker, "SessionLocal", Session)

    with Session() as session:
        memory, event = create_memory_with_outbox(session, MemoryCreate(content="remember this"))
        memory_id = memory.id
        event_id = event.id

    index = FakeIndex()

    assert worker.process_once(index=index) is True
    assert index.upserted[0][0] == memory_id
    assert index.upserted[0][1] == "remember this"
    assert len(index.upserted[0][2]) == worker.settings.embedding_dimensions

    with Session() as session:
        event = session.get(OutboxEvent, event_id)
        assert event is not None
        assert event.status == OutboxStatus.COMPLETED.value
