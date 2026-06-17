import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from app.main import create_memory
from app.models import Base
from app.schemas import MemoryCreate


def make_session():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def test_create_memory_endpoint_returns_task_id() -> None:
    Session = make_session()

    with Session() as session:
        response = create_memory(MemoryCreate(content="remember this"), session)

        assert response.memory_id
        assert response.task_id
        assert response.status == "pending"
