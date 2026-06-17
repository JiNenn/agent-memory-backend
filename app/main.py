from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from .database import create_tables, get_session
from .models import OutboxEvent
from .schemas import MemoryCreate, MemoryCreateResponse, TaskResponse
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


@app.get("/tasks/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, session: Session = Depends(get_session)) -> TaskResponse:
    event = session.get(OutboxEvent, task_id)
    if event is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="task not found")
    return TaskResponse(
        id=event.id,
        event_type=event.event_type,
        aggregate_id=event.aggregate_id,
        status=event.status,
        retry_count=event.retry_count,
        max_retries=event.max_retries,
        locked_by=event.locked_by,
        locked_until=event.locked_until,
        last_error=event.last_error,
        created_at=event.created_at,
        updated_at=event.updated_at,
        completed_at=event.completed_at,
    )


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
