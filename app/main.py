from __future__ import annotations

from fastapi import Depends, FastAPI, status
from sqlalchemy.orm import Session

from .database import create_tables, get_session
from .schemas import MemoryCreate, MemoryCreateResponse
from .services import create_memory_with_outbox


app = FastAPI(title="Agent Memory Backend", version="0.1.0")


@app.on_event("startup")
def on_startup() -> None:
    create_tables(retries=10, delay_seconds=2)


@app.post("/memories", response_model=MemoryCreateResponse, status_code=status.HTTP_202_ACCEPTED)
def create_memory(
    request: MemoryCreate,
    session: Session = Depends(get_session),
) -> MemoryCreateResponse:
    memory, event = create_memory_with_outbox(session, request)
    return MemoryCreateResponse(memory_id=memory.id, task_id=event.id, status=event.status)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}

