from __future__ import annotations

from sqlalchemy.orm import Session

from .models import Memory, OutboxEvent, OutboxEventType
from .schemas import MemoryCreate


def create_memory_with_outbox(session: Session, request: MemoryCreate) -> tuple[Memory, OutboxEvent]:
    memory = Memory(
        conversation_id=request.conversation_id,
        role=request.role,
        content=request.content,
        metadata_json=request.metadata,
    )
    session.add(memory)
    session.flush()

    event = OutboxEvent(
        event_type=OutboxEventType.MEMORY_CREATED.value,
        aggregate_type="memory",
        aggregate_id=memory.id,
        payload={"memory_id": memory.id},
    )
    session.add(event)
    session.commit()
    return memory, event

