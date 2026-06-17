from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

from .config import Settings, settings
from .models import Memory


@dataclass(frozen=True)
class VectorHit:
    memory_id: str
    score: float


class QdrantMemoryIndex:
    def __init__(self, config: Settings = settings) -> None:
        self.config = config
        self.client = QdrantClient(url=config.qdrant_url)

    def ensure_collection(self) -> None:
        existing = {collection.name for collection in self.client.get_collections().collections}
        if self.config.qdrant_collection in existing:
            return
        self.client.create_collection(
            collection_name=self.config.qdrant_collection,
            vectors_config=VectorParams(
                size=self.config.embedding_dimensions,
                distance=Distance.COSINE,
            ),
        )

    def upsert_memory(self, memory: Memory, vector: list[float]) -> None:
        self.ensure_collection()
        self.client.upsert(
            collection_name=self.config.qdrant_collection,
            points=[
                PointStruct(
                    id=memory.id,
                    vector=vector,
                    payload={
                        "memory_id": memory.id,
                        "conversation_id": memory.conversation_id,
                        "role": memory.role,
                    },
                )
            ],
        )

    def search(self, vector: list[float], limit: int) -> list[VectorHit]:
        self.ensure_collection()
        raw_hits = self._query(vector, limit)
        hits: list[VectorHit] = []
        for raw_hit in raw_hits:
            payload = getattr(raw_hit, "payload", None) or {}
            point_id = payload.get("memory_id") or getattr(raw_hit, "id")
            hits.append(VectorHit(memory_id=str(point_id), score=float(raw_hit.score)))
        return hits

    def _query(self, vector: list[float], limit: int) -> list[Any]:
        if hasattr(self.client, "query_points"):
            response = self.client.query_points(
                collection_name=self.config.qdrant_collection,
                query=vector,
                limit=limit,
            )
            return list(response.points)
        return list(
            self.client.search(
                collection_name=self.config.qdrant_collection,
                query_vector=vector,
                limit=limit,
            )
        )

