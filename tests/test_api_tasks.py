import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from app.main import get_task
from app.models import Base
from app.schemas import MemoryCreate
from app.services import create_memory_with_outbox


def make_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def test_get_task_returns_outbox_status() -> None:
    Session = make_session()

    with Session() as session:
        _, event = create_memory_with_outbox(session, MemoryCreate(content="remember this"))

        response = get_task(event.id, session)

        assert response.id == event.id
        assert response.aggregate_id == event.aggregate_id
        assert response.status == "pending"
