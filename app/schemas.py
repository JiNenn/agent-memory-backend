from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MemoryCreate(BaseModel):
    content: str = Field(min_length=1, max_length=20_000)
    conversation_id: str | None = Field(default=None, max_length=128)
    role: str = Field(default="user", max_length=32)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryCreateResponse(BaseModel):
    memory_id: str
    task_id: str
    status: str


class TaskResponse(BaseModel):
    id: str
    event_type: str
    aggregate_id: str
    status: str
    retry_count: int
    max_retries: int
    locked_by: str | None
    locked_until: datetime | None
    last_error: str | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class SearchResult(BaseModel):
    memory_id: str
    content: str
    conversation_id: str | None
    role: str
    metadata: dict[str, Any]
    score: float
    created_at: datetime


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]

