from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from .config import settings
from .database import create_tables, get_session
from .embeddings import embed_text
from .models import Memory, OutboxEvent
from .schemas import MemoryCreate, MemoryCreateResponse, SearchResponse, SearchResult, TaskResponse
from .services import create_memory_with_outbox
from .vectordb import QdrantMemoryIndex


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


@app.get("/memories/search", response_model=SearchResponse)
def search_memories(
    q: str = Query(min_length=1, max_length=2_000),
    limit: int = Query(default=5, ge=1, le=50),
    session: Session = Depends(get_session),
) -> SearchResponse:
    vector = embed_text(q, settings.embedding_dimensions)
    try:
        hits = QdrantMemoryIndex().search(vector, limit)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"vector search unavailable: {exc}",
        ) from exc

    if not hits:
        return SearchResponse(query=q, results=[])

    ids = [hit.memory_id for hit in hits]
    memories = session.execute(select(Memory).where(Memory.id.in_(ids))).scalars().all()
    memory_by_id = {memory.id: memory for memory in memories}

    results = []
    for hit in hits:
        memory = memory_by_id.get(hit.memory_id)
        if memory is None:
            continue
        results.append(
            SearchResult(
                memory_id=memory.id,
                content=memory.content,
                conversation_id=memory.conversation_id,
                role=memory.role,
                metadata=memory.metadata_json,
                score=hit.score,
                created_at=memory.created_at,
            )
        )
    return SearchResponse(query=q, results=results)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}
