import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from app.main import search_memories
from app.models import Base
from app.schemas import MemoryCreate
from app.services import create_memory_with_outbox
from app.vectordb import VectorHit


def make_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class FakeMemoryIndex:
    def search(self, vector: list[float], limit: int) -> list[VectorHit]:
        return [VectorHit(memory_id=self.memory_id, score=0.9)]


def test_search_memories_loads_memory_body_from_mysql(monkeypatch) -> None:
    Session = make_session()

    with Session() as session:
        memory, _ = create_memory_with_outbox(
            session,
            MemoryCreate(content="Qdrant は検索 index として扱う"),
        )
        fake_index = FakeMemoryIndex()
        fake_index.memory_id = memory.id
        monkeypatch.setattr("app.main.QdrantMemoryIndex", lambda: fake_index)

        response = search_memories("search index", 5, session)

        assert response.query == "search index"
        assert len(response.results) == 1
        assert response.results[0].memory_id == memory.id
        assert response.results[0].content == memory.content
        assert response.results[0].score == 0.9
