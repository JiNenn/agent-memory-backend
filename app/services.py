from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from .models import Memory, OutboxEvent, OutboxEventType, OutboxStatus, utcnow
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


def claim_next_outbox_event(
    session: Session,
    worker_id: str,
    lease_seconds: int,
    now: datetime | None = None,
) -> OutboxEvent | None:
    current_time = now or utcnow()
    expired_processing = and_(
        OutboxEvent.status == OutboxStatus.PROCESSING.value,
        OutboxEvent.locked_until.is_not(None),
        OutboxEvent.locked_until < current_time,
    )
    statement = (
        select(OutboxEvent)
        .where(or_(OutboxEvent.status == OutboxStatus.PENDING.value, expired_processing))
        .order_by(OutboxEvent.created_at.asc())
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    event = session.execute(statement).scalar_one_or_none()
    if event is None:
        return None

    event.status = OutboxStatus.PROCESSING.value
    event.locked_by = worker_id
    event.locked_until = current_time + timedelta(seconds=lease_seconds)
    event.last_error = None
    session.commit()
    session.refresh(event)
    return event


def mark_outbox_completed(session: Session, event: OutboxEvent) -> None:
    event.status = OutboxStatus.COMPLETED.value
    event.locked_by = None
    event.locked_until = None
    event.completed_at = utcnow()
    session.commit()
