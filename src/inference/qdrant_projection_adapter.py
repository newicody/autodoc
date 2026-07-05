"""Qdrant projection adapter boundary for OpenVINO embedding vectors.

0119 turns validated embedding vectors into Qdrant-ready projection points while
preserving SQLContextStore as the durable context authority.  The adapter does
not import qdrant-client, PostgreSQL drivers, OpenVINO, HTTP clients, sockets,
or kernel components.  It prepares deterministic point payloads carrying
``sql_context_ref`` so later retrieval can always re-hydrate from SQL.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import math
import re
from typing import Protocol, Sequence

from inference.openvino_embedding_adapter import OpenVINOEmbeddingBatch, OpenVINOEmbeddingVector

_TARGET_SCHEMA = "missipy.qdrant_projection.target.v1"
_POINT_SCHEMA = "missipy.qdrant_projection.point.v1"
_BATCH_SCHEMA = "missipy.qdrant_projection.batch.v1"
_WRITE_SCHEMA = "missipy.qdrant_projection.write.v1"
_HIT_SCHEMA = "missipy.qdrant_projection.hit.v1"
_RECALL_SCHEMA = "missipy.qdrant_projection.recall.v1"
_ALLOWED_DISTANCES = frozenset({"Cosine", "Dot", "Euclid"})
_ALLOWED_ROLES = frozenset({"passage", "query"})
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_SQL_REF_RE = re.compile(r"^sql:[^\s].*$")


class QdrantProjectionExecutor(Protocol):
    """Injected execution membrane for a real or fake Qdrant backend."""

    def upsert_points(
        self,
        points: Sequence[QdrantProjectionPoint],
        *,
        target: QdrantProjectionTarget,
        policy: QdrantProjectionPolicy,
    ) -> QdrantProjectionWriteResult: ...

    def search_vector(
        self,
        vector: Sequence[float],
        *,
        target: QdrantProjectionTarget,
        policy: QdrantProjectionPolicy,
        query: QdrantRecallQuery,
    ) -> QdrantRecallResult: ...


@dataclass(frozen=True, slots=True)
class QdrantProjectionTarget:
    """Data-only local Qdrant projection target.

    The target documents the local service installed on Gentoo/OpenRC.  It is not
    a client and it does not open network connections.
    """

    collection_name: str = "autodoc_context_embeddings"
    endpoint_ref: str = "qdrant:local:6333"
    vector_dimension: int = 384
    distance: str = "Cosine"
    storage_path: str = "/srv/autodoc/qdrant/storage"
    snapshots_path: str = "/srv/autodoc/qdrant/snapshots"

    def __post_init__(self) -> None:
        _require_non_empty("collection_name", self.collection_name)
        _require_typed_ref("endpoint_ref", self.endpoint_ref)
        if self.vector_dimension <= 0:
            raise ValueError("vector_dimension must be > 0")
        if self.distance not in _ALLOWED_DISTANCES:
            raise ValueError("distance must be Cosine, Dot, or Euclid")
        _require_non_empty("storage_path", self.storage_path)
        _require_non_empty("snapshots_path", self.snapshots_path)

    @property
    def backend_ref(self) -> str:
        return f"qdrant:collection:{self.collection_name}"

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _TARGET_SCHEMA,
            "collection_name": self.collection_name,
            "endpoint_ref": self.endpoint_ref,
            "backend_ref": self.backend_ref,
            "vector_dimension": self.vector_dimension,
            "distance": self.distance,
            "storage_path": self.storage_path,
            "snapshots_path": self.snapshots_path,
            "runtime_import": "external adapter only; no qdrant-client import here",
        }


@dataclass(frozen=True, slots=True)
class QdrantProjectionPolicy:
    """Bounded deterministic projection policy."""

    max_points: int = 128
    max_recall_hits: int = 32
    require_sql_context_ref: bool = True
    require_normalized_vectors: bool = True
    normalization_tolerance: float = 1e-4

    def __post_init__(self) -> None:
        if self.max_points <= 0:
            raise ValueError("max_points must be > 0")
        if self.max_recall_hits <= 0:
            raise ValueError("max_recall_hits must be > 0")
        if self.normalization_tolerance <= 0:
            raise ValueError("normalization_tolerance must be > 0")


@dataclass(frozen=True, slots=True)
class QdrantProjectionPoint:
    """Qdrant-ready point with SQL authority ref in lightweight payload."""

    point_id: str
    embedding_ref: str
    source_ref: str
    sql_context_ref: str
    vector: tuple[float, ...]
    payload: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_typed_ref("point_id", self.point_id)
        _require_typed_ref("embedding_ref", self.embedding_ref)
        _require_typed_ref("source_ref", self.source_ref)
        _require_sql_ref("sql_context_ref", self.sql_context_ref)
        if not self.vector:
            raise ValueError("vector must not be empty")
        object.__setattr__(self, "vector", tuple(float(value) for value in self.vector))
        object.__setattr__(self, "payload", _normalize_payload(self.payload))

    @property
    def dimension(self) -> int:
        return len(self.vector)

    @property
    def l2_norm(self) -> float:
        return math.sqrt(sum(value * value for value in self.vector))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _POINT_SCHEMA,
            "point_id": self.point_id,
            "embedding_ref": self.embedding_ref,
            "source_ref": self.source_ref,
            "sql_context_ref": self.sql_context_ref,
            "dimension": self.dimension,
            "l2_norm": self.l2_norm,
            "payload": dict(self.payload),
            "vector": list(self.vector),
        }


@dataclass(frozen=True, slots=True)
class QdrantProjectionBatch:
    """Serializable set of points ready for an injected Qdrant executor."""

    target: QdrantProjectionTarget
    points: tuple[QdrantProjectionPoint, ...]
    capped: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "points", tuple(self.points))
        for point in self.points:
            if point.dimension != self.target.vector_dimension:
                raise ValueError("point dimension must match target vector_dimension")

    @property
    def point_count(self) -> int:
        return len(self.points)

    @property
    def point_ids(self) -> tuple[str, ...]:
        return tuple(point.point_id for point in self.points)

    @property
    def sql_context_refs(self) -> tuple[str, ...]:
        return tuple(point.sql_context_ref for point in self.points)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _BATCH_SCHEMA,
            "target": self.target.to_mapping(),
            "point_count": self.point_count,
            "point_ids": list(self.point_ids),
            "sql_context_refs": list(self.sql_context_refs),
            "capped": self.capped,
            "points": [point.to_mapping() for point in self.points],
        }


@dataclass(frozen=True, slots=True)
class QdrantProjectionWriteResult:
    """Result returned by an injected projection executor."""

    target: QdrantProjectionTarget
    point_ids: tuple[str, ...]
    acknowledged: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "point_ids", _normalize_typed_refs(self.point_ids))

    @property
    def point_count(self) -> int:
        return len(self.point_ids)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _WRITE_SCHEMA,
            "target": self.target.to_mapping(),
            "point_count": self.point_count,
            "point_ids": list(self.point_ids),
            "acknowledged": self.acknowledged,
        }


@dataclass(frozen=True, slots=True)
class QdrantRecallQuery:
    """Bounded recall query metadata for an injected Qdrant search executor."""

    query_ref: str
    limit: int = 16
    role: str = "query"

    def __post_init__(self) -> None:
        _require_typed_ref("query_ref", self.query_ref)
        if self.limit <= 0:
            raise ValueError("limit must be > 0")
        if self.role not in _ALLOWED_ROLES:
            raise ValueError("role must be passage or query")


@dataclass(frozen=True, slots=True)
class QdrantRecallHit:
    """Lightweight recall hit that must be re-hydrated from SQL."""

    point_id: str
    sql_context_ref: str
    score: float
    source_ref: str = ""
    payload: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_typed_ref("point_id", self.point_id)
        _require_sql_ref("sql_context_ref", self.sql_context_ref)
        if self.source_ref:
            _require_typed_ref("source_ref", self.source_ref)
        if not 0.0 <= float(self.score) <= 1.0:
            raise ValueError("score must be between 0 and 1")
        object.__setattr__(self, "score", float(self.score))
        object.__setattr__(self, "payload", _normalize_payload(self.payload))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _HIT_SCHEMA,
            "point_id": self.point_id,
            "sql_context_ref": self.sql_context_ref,
            "score": self.score,
            "source_ref": self.source_ref,
            "payload": dict(self.payload),
        }


@dataclass(frozen=True, slots=True)
class QdrantRecallResult:
    """Recall result carrying only refs; SQL remains authority for content."""

    target: QdrantProjectionTarget
    query: QdrantRecallQuery
    hits: tuple[QdrantRecallHit, ...]
    capped: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "hits", tuple(self.hits))

    @property
    def hit_count(self) -> int:
        return len(self.hits)

    @property
    def sql_context_refs(self) -> tuple[str, ...]:
        return unique_sql_context_refs_from_recall(self)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _RECALL_SCHEMA,
            "target": self.target.to_mapping(),
            "query_ref": self.query.query_ref,
            "hit_count": self.hit_count,
            "sql_context_refs": list(self.sql_context_refs),
            "capped": self.capped,
            "hits": [hit.to_mapping() for hit in self.hits],
        }


class QdrantProjectionAdapter:
    """Build and upsert Qdrant projection points via an injected executor."""

    def __init__(
        self,
        executor: QdrantProjectionExecutor,
        target: QdrantProjectionTarget | None = None,
        policy: QdrantProjectionPolicy | None = None,
    ) -> None:
        self._executor = executor
        self._target = target or QdrantProjectionTarget()
        self._policy = policy or QdrantProjectionPolicy()

    @property
    def target(self) -> QdrantProjectionTarget:
        return self._target

    @property
    def policy(self) -> QdrantProjectionPolicy:
        return self._policy

    def build_projection_batch(self, embedding_batch: OpenVINOEmbeddingBatch) -> QdrantProjectionBatch:
        return build_qdrant_projection_batch(embedding_batch, self._target, self._policy)

    def upsert_embedding_batch(self, embedding_batch: OpenVINOEmbeddingBatch) -> QdrantProjectionWriteResult:
        batch = self.build_projection_batch(embedding_batch)
        return self._executor.upsert_points(batch.points, target=self._target, policy=self._policy)

    def recall_by_vector(self, vector: Sequence[float], query: QdrantRecallQuery) -> QdrantRecallResult:
        return self._executor.search_vector(vector, target=self._target, policy=self._policy, query=query)


def build_qdrant_projection_batch(
    embedding_batch: OpenVINOEmbeddingBatch,
    target: QdrantProjectionTarget | None = None,
    policy: QdrantProjectionPolicy | None = None,
) -> QdrantProjectionBatch:
    """Build a bounded Qdrant projection batch from validated embeddings."""

    effective_target = target or QdrantProjectionTarget(vector_dimension=embedding_batch.target.dimension)
    effective_policy = policy or QdrantProjectionPolicy()
    points: list[QdrantProjectionPoint] = []
    capped = embedding_batch.capped
    for embedding in embedding_batch.vectors:
        if len(points) >= effective_policy.max_points:
            capped = True
            break
        points.append(build_qdrant_projection_point(embedding, effective_target, effective_policy))
    return QdrantProjectionBatch(target=effective_target, points=tuple(points), capped=capped)


def build_qdrant_projection_point(
    embedding: OpenVINOEmbeddingVector,
    target: QdrantProjectionTarget | None = None,
    policy: QdrantProjectionPolicy | None = None,
) -> QdrantProjectionPoint:
    """Build one deterministic Qdrant-ready point from an embedding vector."""

    effective_target = target or QdrantProjectionTarget(vector_dimension=embedding.dimension)
    effective_policy = policy or QdrantProjectionPolicy()
    if embedding.dimension != effective_target.vector_dimension:
        raise ValueError("embedding dimension must match target vector_dimension")
    if effective_policy.require_normalized_vectors and not math.isclose(
        embedding.l2_norm,
        1.0,
        rel_tol=effective_policy.normalization_tolerance,
        abs_tol=effective_policy.normalization_tolerance,
    ):
        raise ValueError("embedding vector must be normalized before Qdrant projection")
    sql_context_ref = _sql_context_ref_from_embedding(embedding)
    if effective_policy.require_sql_context_ref and sql_context_ref is None:
        raise ValueError("embedding metadata must include sql context_ref")
    if sql_context_ref is None:
        sql_context_ref = "sql:unknown"
    payload = _projection_payload(embedding, sql_context_ref, effective_target)
    return QdrantProjectionPoint(
        point_id=_point_id_for_embedding(embedding, effective_target),
        embedding_ref=embedding.embedding_ref,
        source_ref=embedding.source_ref,
        sql_context_ref=sql_context_ref,
        vector=embedding.vector,
        payload=payload,
    )


def unique_sql_context_refs_from_recall(
    recall: QdrantRecallResult,
    *,
    max_refs: int | None = None,
) -> tuple[str, ...]:
    """Return de-duplicated SQL refs in recall order for SQL re-hydration."""

    if max_refs is not None and max_refs <= 0:
        raise ValueError("max_refs must be > 0")
    refs: list[str] = []
    seen: set[str] = set()
    for hit in recall.hits:
        if hit.sql_context_ref in seen:
            continue
        seen.add(hit.sql_context_ref)
        refs.append(hit.sql_context_ref)
        if max_refs is not None and len(refs) >= max_refs:
            break
    return tuple(refs)


def local_qdrant_projection_target(
    *,
    collection_name: str = "autodoc_context_embeddings",
    vector_dimension: int = 384,
) -> QdrantProjectionTarget:
    """Return the documented local Qdrant projection target."""

    return QdrantProjectionTarget(collection_name=collection_name, vector_dimension=vector_dimension)


def _projection_payload(
    embedding: OpenVINOEmbeddingVector,
    sql_context_ref: str,
    target: QdrantProjectionTarget,
) -> tuple[tuple[str, str], ...]:
    payload = {
        "sql_context_ref": sql_context_ref,
        "source_ref": embedding.source_ref,
        "embedding_ref": embedding.embedding_ref,
        "role": embedding.role,
        "embedding_backend_ref": embedding.backend_ref,
        "qdrant_backend_ref": target.backend_ref,
    }
    for key, value in embedding.metadata:
        payload.setdefault(key, value)
    return tuple(sorted((key, value) for key, value in payload.items()))


def _sql_context_ref_from_embedding(embedding: OpenVINOEmbeddingVector) -> str | None:
    metadata = dict(embedding.metadata)
    context_ref = metadata.get("context_ref")
    if context_ref:
        _require_sql_ref("context_ref", context_ref)
        return context_ref
    marker = "ctx-fragment:"
    if embedding.source_ref.startswith(marker):
        candidate = embedding.source_ref[len(marker) :]
        if _SQL_REF_RE.match(candidate):
            return candidate
    return None


def _point_id_for_embedding(embedding: OpenVINOEmbeddingVector, target: QdrantProjectionTarget) -> str:
    digest = hashlib.sha256()
    digest.update(target.collection_name.encode("utf-8"))
    digest.update(b"\0")
    digest.update(embedding.embedding_ref.encode("utf-8"))
    digest.update(b"\0")
    digest.update(embedding.source_ref.encode("utf-8"))
    return f"qdrant-point:{digest.hexdigest()[:16]}"


def _normalize_payload(values: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    normalized: list[tuple[str, str]] = []
    seen: set[str] = set()
    for key, value in values:
        _require_non_empty("payload key", key)
        _require_non_empty("payload value", value)
        if key in seen:
            raise ValueError("payload keys must be unique")
        seen.add(key)
        normalized.append((key, value))
    return tuple(sorted(normalized))


def _normalize_typed_refs(values: tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        _require_typed_ref("ref", value)
        if value not in seen:
            seen.add(value)
            normalized.append(value)
    return tuple(normalized)


def _require_sql_ref(name: str, value: str) -> None:
    _require_non_empty(name, value)
    if not _SQL_REF_RE.match(value):
        raise ValueError(f"{name} must be a sql:* reference")


def _require_typed_ref(name: str, value: str) -> None:
    _require_non_empty(name, value)
    if not _TYPED_REF_RE.match(value):
        raise ValueError(f"{name} must be a typed reference")


def _require_non_empty(name: str, value: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{name} must not be empty")
