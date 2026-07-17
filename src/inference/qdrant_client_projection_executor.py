"""Concrete qdrant-client execution membrane for the existing Qdrant protocol.

The module is deliberately narrow: it translates Autodoc projection points and
recall queries to the official ``qdrant-client`` SDK.  It does not start Qdrant,
create collections, own durable context, touch Scheduler, or participate in the
SHM data-plane.  SQL references remain the durable authority carried by Qdrant
payloads.
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib import import_module
from importlib import metadata as importlib_metadata
from importlib.util import find_spec
import math
from types import MappingProxyType, ModuleType
from typing import Any, Callable, Mapping, Sequence
import uuid

from inference.qdrant_projection_adapter import (
    QdrantProjectionPoint,
    QdrantProjectionPolicy,
    QdrantProjectionTarget,
    QdrantProjectionWriteResult,
    QdrantRecallHit,
    QdrantRecallQuery,
    QdrantRecallResult,
)

_REQUIRED_DISTRIBUTION = "qdrant-client"
_REQUIRED_VERSION = "1.18.0"
_QDRANT_POINT_NAMESPACE = uuid.UUID("bd4ca470-1a18-45d9-b112-dae28983cb41")


@dataclass(frozen=True, slots=True)
class QdrantClientConnectionConfig:
    """Immutable, secret-free connection settings for the SDK factory."""

    url: str = "http://127.0.0.1:6333"
    timeout_seconds: float = 10.0
    prefer_grpc: bool = False
    grpc_port: int = 6334
    wait_for_write: bool = True
    check_compatibility: bool = True

    def __post_init__(self) -> None:
        if not self.url or not self.url.strip():
            raise ValueError("url must not be empty")
        if not self.url.startswith(("http://", "https://")):
            raise ValueError("url must start with http:// or https://")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")
        if not 1 <= self.grpc_port <= 65535:
            raise ValueError("grpc_port must be between 1 and 65535")

    def to_mapping(self) -> dict[str, object]:
        return {
            "url": self.url,
            "timeout_seconds": self.timeout_seconds,
            "prefer_grpc": self.prefer_grpc,
            "grpc_port": self.grpc_port,
            "wait_for_write": self.wait_for_write,
            "check_compatibility": self.check_compatibility,
            "api_key_serialized": False,
        }


@dataclass(frozen=True, slots=True)
class QdrantClientEffectGate:
    """Explicit operator/policy authority required before Qdrant effects."""

    policy_decision_id: str
    allow_write: bool = False
    allow_search: bool = False

    def __post_init__(self) -> None:
        if not self.policy_decision_id.startswith("policy:"):
            raise ValueError("policy_decision_id must start with policy:")

    def to_mapping(self) -> dict[str, object]:
        return {
            "policy_decision_id": self.policy_decision_id,
            "allow_write": self.allow_write,
            "allow_search": self.allow_search,
        }


@dataclass(frozen=True, slots=True)
class QdrantClientExecutionFailure:
    """Serializable failure raised by the SDK execution membrane."""

    operation: str
    category: str
    message: str
    retryable: bool = False

    def to_mapping(self) -> dict[str, object]:
        return {
            "operation": self.operation,
            "category": self.category,
            "message": self.message,
            "retryable": self.retryable,
        }


class QdrantClientExecutionError(RuntimeError):
    """Exception carrying an immutable, serializable execution failure."""

    def __init__(self, failure: QdrantClientExecutionFailure) -> None:
        self.failure = failure
        super().__init__(f"{failure.operation}: {failure.category}: {failure.message}")


@dataclass(frozen=True, slots=True)
class QdrantClientDependencyReadiness:
    """Read-only dependency readiness result; no client or network is opened."""

    installed: bool
    version: str
    required_version: str = _REQUIRED_VERSION
    network_used: bool = False
    qdrant_called: bool = False

    @property
    def valid(self) -> bool:
        return self.installed and self.version == self.required_version

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": "autodoc.qdrant_client_dependency_readiness.v1",
            "valid": self.valid,
            "installed": self.installed,
            "version": self.version,
            "required_version": self.required_version,
            "network_used": self.network_used,
            "qdrant_called": self.qdrant_called,
            "starts_qdrant": False,
            "touches_shm": False,
            "sql_remains_authority": True,
        }


@dataclass(frozen=True, slots=True)
class QdrantClientReferenceHit:
    """Reference-only hit returned by one named-vector SDK query."""

    point_id: str
    sql_ref: str
    source_ref: str
    score: float
    payload: Mapping[str, object]

    def __post_init__(self) -> None:
        for name in ("point_id", "sql_ref", "source_ref"):
            value = getattr(self, name)
            if not _is_typed_ref(value):
                raise ValueError(f"{name} must be a typed reference")
        if not math.isfinite(float(self.score)):
            raise ValueError("score must be finite")
        compact = _reference_payload(self.payload)
        if compact.get("sql_ref", self.sql_ref) != self.sql_ref:
            raise ValueError("payload sql_ref differs from hit sql_ref")
        if compact.get("source_ref", self.source_ref) != self.source_ref:
            raise ValueError("payload source_ref differs from hit source_ref")
        object.__setattr__(self, "score", float(self.score))
        object.__setattr__(self, "payload", MappingProxyType(compact))

    def to_mapping(self) -> dict[str, object]:
        return {
            "point_id": self.point_id,
            "sql_ref": self.sql_ref,
            "source_ref": self.source_ref,
            "score": self.score,
            "payload": dict(self.payload),
            "reference_only": True,
            "vectors_serialized": False,
        }


@dataclass(frozen=True, slots=True)
class QdrantClientReferencePoint:
    """Reference-only readback for one exact named-vector point."""

    collection_name: str
    point_id: str
    sql_ref: str
    source_ref: str
    payload: Mapping[str, object]

    def __post_init__(self) -> None:
        if not self.collection_name.strip():
            raise ValueError("collection_name must not be empty")
        for name in ("point_id", "sql_ref", "source_ref"):
            if not _is_typed_ref(getattr(self, name)):
                raise ValueError(f"{name} must be a typed reference")
        compact = _reference_payload(self.payload)
        if compact.get("point_id", self.point_id) != self.point_id:
            raise ValueError("payload point_id differs from readback point_id")
        if compact.get("sql_ref", self.sql_ref) != self.sql_ref:
            raise ValueError("payload sql_ref differs from readback sql_ref")
        if compact.get("source_ref", self.source_ref) != self.source_ref:
            raise ValueError("payload source_ref differs from readback source_ref")
        object.__setattr__(self, "payload", MappingProxyType(compact))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": "missipy.qdrant.reference_point_readback.v1",
            "collection_name": self.collection_name,
            "point_id": self.point_id,
            "sql_ref": self.sql_ref,
            "source_ref": self.source_ref,
            "payload": dict(self.payload),
            "boundaries": {
                "reference_only": True,
                "vectors_serialized": False,
                "authoritative_content_serialized": False,
                "sql_remains_authority": True,
            },
        }


@dataclass(frozen=True, slots=True)
class QdrantNamedHybridProjectionResult:
    """Reference-only receipt for one named dense+sparse point upsert."""

    collection_name: str
    point_id: str
    dense_vector_name: str
    sparse_vector_name: str
    acknowledged: bool = True

    def __post_init__(self) -> None:
        if not self.collection_name.strip():
            raise ValueError("collection_name must not be empty")
        if not _is_typed_ref(self.point_id):
            raise ValueError("point_id must be a typed reference")
        for name in ("dense_vector_name", "sparse_vector_name"):
            if not _is_identifier(getattr(self, name)):
                raise ValueError(f"{name} must be a stable identifier")
        if self.dense_vector_name == self.sparse_vector_name:
            raise ValueError("dense and sparse vector names must differ")
        if not self.acknowledged:
            raise ValueError("named hybrid projection must be acknowledged")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": "missipy.qdrant.named_hybrid_projection_result.v1",
            "collection_name": self.collection_name,
            "point_id": self.point_id,
            "dense_vector_name": self.dense_vector_name,
            "sparse_vector_name": self.sparse_vector_name,
            "acknowledged": self.acknowledged,
            "boundaries": {
                "reference_only_receipt": True,
                "vectors_serialized": False,
                "authoritative_content_serialized": False,
                "sql_remains_authority": True,
            },
        }


class QdrantClientProjectionExecutor:
    """Implement the existing QdrantProjectionExecutor with qdrant-client."""

    def __init__(
        self,
        *,
        client: Any,
        models_module: Any,
        config: QdrantClientConnectionConfig,
        gate: QdrantClientEffectGate,
    ) -> None:
        self._client = client
        self._models = models_module
        self._config = config
        self._gate = gate

    @property
    def config(self) -> QdrantClientConnectionConfig:
        return self._config

    @property
    def gate(self) -> QdrantClientEffectGate:
        return self._gate

    def upsert_points(
        self,
        points: Sequence[QdrantProjectionPoint],
        *,
        target: QdrantProjectionTarget,
        policy: QdrantProjectionPolicy,
    ) -> QdrantProjectionWriteResult:
        """Upsert validated points while preserving their typed Autodoc refs."""

        self._require_allowed("upsert", self._gate.allow_write)
        bounded = tuple(points)
        if len(bounded) > policy.max_points:
            raise self._failure("upsert", "policy_limit", "point count exceeds policy.max_points")
        qdrant_points = []
        for point in bounded:
            if point.dimension != target.vector_dimension:
                raise self._failure("upsert", "dimension_mismatch", "point dimension does not match target")
            payload = _payload_for_point(point)
            qdrant_points.append(
                self._models.PointStruct(
                    id=_qdrant_storage_id(point.point_id),
                    vector=list(point.vector),
                    payload=payload,
                )
            )
        try:
            response = self._client.upsert(
                collection_name=target.collection_name,
                points=qdrant_points,
                wait=self._config.wait_for_write,
            )
        except Exception as exc:  # SDK exception families vary by transport/version.
            raise self._wrapped_failure("upsert", exc) from exc
        if not _write_acknowledged(response):
            raise self._failure("upsert", "not_acknowledged", "Qdrant did not acknowledge the write")
        return QdrantProjectionWriteResult(
            target=target,
            point_ids=tuple(point.point_id for point in bounded),
            acknowledged=True,
        )

    def upsert_named_hybrid_point(
        self,
        *,
        collection_name: str,
        point_id: str,
        dense_vector_name: str,
        dense_values: Sequence[float],
        sparse_vector_name: str,
        sparse_indices: Sequence[int],
        sparse_values: Sequence[float],
        payload: Mapping[str, object],
        dense_dimension: int = 384,
    ) -> QdrantNamedHybridProjectionResult:
        """Upsert one canonical named dense+sparse point behind the write gate."""

        operation = "upsert_named_hybrid"
        self._require_allowed(operation, self._gate.allow_write)
        if not collection_name or not collection_name.strip():
            raise self._failure(operation, "invalid_collection", "collection_name is required")
        if not _is_typed_ref(point_id):
            raise self._failure(operation, "invalid_point_id", "point_id must be typed")
        if not _is_identifier(dense_vector_name) or not _is_identifier(sparse_vector_name):
            raise self._failure(operation, "invalid_vector_name", "named vectors require stable identifiers")
        if dense_vector_name == sparse_vector_name:
            raise self._failure(operation, "invalid_vector_name", "dense and sparse vector names must differ")
        if dense_dimension != 384:
            raise self._failure(operation, "dimension_mismatch", "multilingual-e5-small dimension must be 384")

        dense = tuple(float(value) for value in dense_values)
        if len(dense) != dense_dimension or any(not math.isfinite(value) for value in dense):
            raise self._failure(operation, "invalid_dense_vector", "dense vector must contain 384 finite values")
        dense_norm = math.sqrt(sum(value * value for value in dense))
        if not math.isclose(dense_norm, 1.0, rel_tol=1e-4, abs_tol=1e-4):
            raise self._failure(operation, "invalid_dense_vector", "dense vector must have unit norm")

        indices = tuple(int(index) for index in sparse_indices)
        values = tuple(float(value) for value in sparse_values)
        if (
            not indices
            or len(indices) != len(values)
            or len(set(indices)) != len(indices)
            or any(index < 0 for index in indices)
            or any(not math.isfinite(value) or value <= 0 for value in values)
        ):
            raise self._failure(operation, "invalid_sparse_vector", "sparse indices and values must be aligned and valid")

        compact_payload = _canonical_named_projection_payload(payload, point_id=point_id)
        point = self._models.PointStruct(
            id=_qdrant_storage_id(point_id),
            vector={
                dense_vector_name: list(dense),
                sparse_vector_name: self._models.SparseVector(
                    indices=list(indices),
                    values=list(values),
                ),
            },
            payload=compact_payload,
        )
        try:
            response = self._client.upsert(
                collection_name=collection_name,
                points=[point],
                wait=self._config.wait_for_write,
            )
        except Exception as exc:
            raise self._wrapped_failure(operation, exc) from exc
        if not _write_acknowledged(response):
            raise self._failure(operation, "not_acknowledged", "Qdrant did not acknowledge the named hybrid write")
        return QdrantNamedHybridProjectionResult(
            collection_name=collection_name,
            point_id=point_id,
            dense_vector_name=dense_vector_name,
            sparse_vector_name=sparse_vector_name,
            acknowledged=True,
        )

    def read_named_reference_point(
        self,
        *,
        collection_name: str,
        point_id: str,
    ) -> QdrantClientReferencePoint | None:
        """Read one exact point with payload only and vectors disabled."""

        operation = "read_named_reference_point"
        self._require_allowed(operation, self._gate.allow_search)
        if not collection_name or not collection_name.strip():
            raise self._failure(
                operation,
                "invalid_collection",
                "collection_name is required",
            )
        if not _is_typed_ref(point_id):
            raise self._failure(
                operation,
                "invalid_point_id",
                "point_id must be typed",
            )
        try:
            response = self._client.retrieve(
                collection_name=collection_name,
                ids=[_qdrant_storage_id(point_id)],
                with_payload=True,
                with_vectors=False,
            )
        except Exception as exc:
            raise self._wrapped_failure(operation, exc) from exc
        records = tuple(response or ())
        if not records:
            return None
        if len(records) != 1:
            raise self._failure(
                operation,
                "ambiguous_readback",
                "Qdrant returned more than one exact point",
            )
        payload = _reference_payload(
            _as_mapping(getattr(records[0], "payload", {}))
        )
        observed_point_id = str(
            payload.get("point_id")
            or payload.get("autodoc_point_ref")
            or ""
        )
        if observed_point_id != point_id:
            raise self._failure(
                operation,
                "point_id_mismatch",
                "Qdrant payload point_id differs from requested point_id",
            )
        sql_ref = str(
            payload.get("sql_ref")
            or payload.get("sql_context_ref")
            or ""
        )
        source_ref = str(payload.get("source_ref") or sql_ref)
        if not _is_typed_ref(sql_ref) or not _is_typed_ref(source_ref):
            raise self._failure(
                operation,
                "missing_sql_reference",
                "Qdrant exact point must contain typed SQL references",
            )
        payload["point_id"] = point_id
        payload["sql_ref"] = sql_ref
        payload["source_ref"] = source_ref
        return QdrantClientReferencePoint(
            collection_name=collection_name,
            point_id=point_id,
            sql_ref=sql_ref,
            source_ref=source_ref,
            payload=payload,
        )

    def search_vector(
        self,
        vector: Sequence[float],
        *,
        target: QdrantProjectionTarget,
        policy: QdrantProjectionPolicy,
        query: QdrantRecallQuery,
    ) -> QdrantRecallResult:
        """Query Qdrant and return reference-only hits for SQL rehydration."""

        self._require_allowed("search", self._gate.allow_search)
        values = tuple(float(value) for value in vector)
        if len(values) != target.vector_dimension:
            raise self._failure("search", "dimension_mismatch", "query dimension does not match target")
        limit = min(query.limit, policy.max_recall_hits)
        try:
            response = self._client.query_points(
                collection_name=target.collection_name,
                query=list(values),
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )
        except Exception as exc:  # SDK exception families vary by transport/version.
            raise self._wrapped_failure("search", exc) from exc
        raw_hits = tuple(getattr(response, "points", response) or ())
        hits = tuple(_recall_hit_from_scored_point(item, target=target) for item in raw_hits[:limit])
        return QdrantRecallResult(target=target, query=query, hits=hits, capped=len(raw_hits) > limit)

    def query_named_dense(
        self,
        vector: Sequence[float],
        *,
        collection_name: str,
        vector_name: str,
        limit: int,
        filter_mapping: Mapping[str, object],
    ) -> tuple[QdrantClientReferenceHit, ...]:
        """Query one named dense vector and return reference-only hits."""

        values = tuple(float(value) for value in vector)
        if not values or any(not math.isfinite(value) for value in values):
            raise self._failure(
                "search_dense",
                "invalid_vector",
                "dense query vector must contain finite values",
            )
        return self._query_named_points(
            operation="search_dense",
            query_value=list(values),
            collection_name=collection_name,
            vector_name=vector_name,
            limit=limit,
            filter_mapping=filter_mapping,
        )

    def query_named_sparse(
        self,
        indices: Sequence[int],
        values: Sequence[float],
        *,
        collection_name: str,
        vector_name: str,
        limit: int,
        filter_mapping: Mapping[str, object],
    ) -> tuple[QdrantClientReferenceHit, ...]:
        """Query one named sparse vector and return reference-only hits."""

        normalized_indices = tuple(int(index) for index in indices)
        normalized_values = tuple(float(value) for value in values)
        if (
            not normalized_indices
            or len(normalized_indices) != len(normalized_values)
            or len(set(normalized_indices)) != len(normalized_indices)
            or any(index < 0 for index in normalized_indices)
            or any(not math.isfinite(value) or value <= 0 for value in normalized_values)
        ):
            raise self._failure(
                "search_sparse",
                "invalid_sparse_vector",
                "sparse query indices and values must be aligned and valid",
            )
        sparse_vector = self._models.SparseVector(
            indices=list(normalized_indices),
            values=list(normalized_values),
        )
        return self._query_named_points(
            operation="search_sparse",
            query_value=sparse_vector,
            collection_name=collection_name,
            vector_name=vector_name,
            limit=limit,
            filter_mapping=filter_mapping,
        )

    def _query_named_points(
        self,
        *,
        operation: str,
        query_value: object,
        collection_name: str,
        vector_name: str,
        limit: int,
        filter_mapping: Mapping[str, object],
    ) -> tuple[QdrantClientReferenceHit, ...]:
        self._require_allowed(operation, self._gate.allow_search)
        if not collection_name or not collection_name.strip():
            raise self._failure(operation, "invalid_collection", "collection_name is required")
        if not vector_name or not vector_name.strip():
            raise self._failure(operation, "invalid_vector_name", "vector_name is required")
        if limit <= 0:
            raise self._failure(operation, "invalid_limit", "limit must be > 0")
        query_filter = _sdk_filter(self._models, filter_mapping)
        try:
            response = self._client.query_points(
                collection_name=collection_name,
                query=query_value,
                using=vector_name,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )
        except Exception as exc:
            raise self._wrapped_failure(operation, exc) from exc
        raw_hits = tuple(getattr(response, "points", response) or ())
        return tuple(
            _reference_hit_from_scored_point(item, operation=operation)
            for item in raw_hits[:limit]
        )

    def close(self) -> None:
        """Close the injected SDK client when it exposes a close method."""

        close = getattr(self._client, "close", None)
        if callable(close):
            close()

    def _require_allowed(self, operation: str, allowed: bool) -> None:
        if not allowed:
            raise self._failure(operation, "gate_denied", "effect gate does not allow this operation")

    @staticmethod
    def _failure(operation: str, category: str, message: str, *, retryable: bool = False) -> QdrantClientExecutionError:
        return QdrantClientExecutionError(
            QdrantClientExecutionFailure(
                operation=operation,
                category=category,
                message=message,
                retryable=retryable,
            )
        )

    @classmethod
    def _wrapped_failure(cls, operation: str, exc: Exception) -> QdrantClientExecutionError:
        message = str(exc).strip() or type(exc).__name__
        return cls._failure(operation, type(exc).__name__, message[:500], retryable=True)


def build_qdrant_client_projection_executor(
    config: QdrantClientConnectionConfig,
    gate: QdrantClientEffectGate,
    *,
    api_key: str | None = None,
    client_factory: Callable[..., Any] | None = None,
    models_module: ModuleType | Any | None = None,
) -> QdrantClientProjectionExecutor:
    """Build the executor, importing qdrant-client only at this IO boundary."""

    factory = client_factory
    models = models_module
    if factory is None:
        package = import_module("qdrant_client")
        factory = getattr(package, "QdrantClient")
    if models is None:
        models = import_module("qdrant_client.models")
    kwargs: dict[str, object] = {
        "url": config.url,
        "timeout": config.timeout_seconds,
        "prefer_grpc": config.prefer_grpc,
        "check_compatibility": config.check_compatibility,
    }
    if config.prefer_grpc:
        kwargs["grpc_port"] = config.grpc_port
    if api_key:
        kwargs["api_key"] = api_key
    client = factory(**kwargs)
    return QdrantClientProjectionExecutor(client=client, models_module=models, config=config, gate=gate)


def inspect_qdrant_client_dependency() -> QdrantClientDependencyReadiness:
    """Inspect package presence/version without importing it or using network."""

    installed = find_spec("qdrant_client") is not None
    version = ""
    if installed:
        try:
            version = importlib_metadata.version(_REQUIRED_DISTRIBUTION)
        except importlib_metadata.PackageNotFoundError:
            installed = False
    return QdrantClientDependencyReadiness(installed=installed, version=version)


def _payload_for_point(point: QdrantProjectionPoint) -> dict[str, object]:
    payload: dict[str, object] = dict(point.payload)
    payload["sql_context_ref"] = point.sql_context_ref
    payload["sql_ref"] = point.sql_context_ref
    payload["autodoc_point_ref"] = point.point_id
    payload["embedding_ref"] = point.embedding_ref
    payload["source_ref"] = point.source_ref
    return payload


def _qdrant_storage_id(point_ref: str) -> str:
    return str(uuid.uuid5(_QDRANT_POINT_NAMESPACE, point_ref))


def _write_acknowledged(response: object) -> bool:
    if response is False or response is None:
        return False
    status = getattr(response, "status", "")
    if hasattr(status, "value"):
        status = status.value
    text = str(status).lower()
    return not text or text in {"acknowledged", "completed"}


def _recall_hit_from_scored_point(item: object, *, target: QdrantProjectionTarget) -> QdrantRecallHit:
    payload = _as_mapping(getattr(item, "payload", {}))
    sql_ref = str(payload.get("sql_ref") or payload.get("sql_context_ref") or "")
    if not sql_ref.startswith("sql:"):
        raise QdrantClientProjectionExecutor._failure(
            "search",
            "missing_sql_ref",
            "Qdrant hit payload must contain sql_ref",
        )
    raw_id = str(getattr(item, "id", "unknown"))
    point_ref = str(payload.get("autodoc_point_ref") or f"qdrant-point:{raw_id}")
    source_ref = str(payload.get("source_ref") or "")
    compact_payload = _string_payload(payload)
    compact_payload["sql_ref"] = sql_ref
    compact_payload["sql_context_ref"] = sql_ref
    return QdrantRecallHit(
        point_id=point_ref,
        sql_context_ref=sql_ref,
        score=_bounded_score(float(getattr(item, "score", 0.0)), target.distance),
        source_ref=source_ref,
        payload=tuple(sorted(compact_payload.items())),
    )


def _as_mapping(value: object) -> Mapping[str, object]:
    if isinstance(value, Mapping):
        return value
    model_dump = getattr(value, "model_dump", None)
    if callable(model_dump):
        dumped = model_dump()
        if isinstance(dumped, Mapping):
            return dumped
    return {}


def _string_payload(payload: Mapping[str, object]) -> dict[str, str]:
    result: dict[str, str] = {}
    for key, value in payload.items():
        if isinstance(value, (str, int, float, bool)):
            result[str(key)] = str(value)
    return result



_FORBIDDEN_REFERENCE_PAYLOAD_FIELDS = frozenset(
    {"vector", "values", "embedding", "body", "content", "local_path"}
)


def _sdk_filter(models_module: object, value: Mapping[str, object]) -> object:
    payload = dict(value)
    if not payload:
        return None
    filter_type = getattr(models_module, "Filter", None)
    if filter_type is None:
        return payload
    validator = getattr(filter_type, "model_validate", None)
    if callable(validator):
        return validator(payload)
    return filter_type(**payload)


def _reference_hit_from_scored_point(
    item: object,
    *,
    operation: str,
) -> QdrantClientReferenceHit:
    payload = _as_mapping(getattr(item, "payload", {}))
    compact = _reference_payload(payload)
    sql_ref = str(compact.get("sql_ref") or compact.get("sql_context_ref") or "")
    if not _is_typed_ref(sql_ref):
        raise QdrantClientProjectionExecutor._failure(
            operation,
            "missing_sql_ref",
            "Qdrant hit payload must contain a typed sql_ref",
        )
    source_ref = str(compact.get("source_ref") or sql_ref)
    if not _is_typed_ref(source_ref):
        raise QdrantClientProjectionExecutor._failure(
            operation,
            "missing_source_ref",
            "Qdrant hit payload must contain a typed source_ref",
        )
    raw_id = str(getattr(item, "id", "unknown"))
    point_ref = str(
        compact.get("autodoc_point_ref")
        or compact.get("point_id")
        or f"qdrant-point:{raw_id}"
    )
    compact["sql_ref"] = sql_ref
    compact["source_ref"] = source_ref
    return QdrantClientReferenceHit(
        point_id=point_ref,
        sql_ref=sql_ref,
        source_ref=source_ref,
        score=float(getattr(item, "score", 0.0)),
        payload=compact,
    )


def _reference_payload(payload: Mapping[str, object]) -> dict[str, object]:
    forbidden = _FORBIDDEN_REFERENCE_PAYLOAD_FIELDS.intersection(payload)
    if forbidden:
        raise QdrantClientProjectionExecutor._failure(
            "search",
            "forbidden_payload",
            "Qdrant reference hit contains forbidden fields: "
            + ", ".join(sorted(forbidden)),
        )
    result: dict[str, object] = {}
    for key, value in payload.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            result[str(key)] = value
    return result


def _is_typed_ref(value: object) -> bool:
    if not isinstance(value, str) or ":" not in value:
        return False
    prefix, suffix = value.split(":", 1)
    return bool(prefix) and bool(suffix) and prefix[0].islower()


_NAMED_PROJECTION_REQUIRED_FIELDS = frozenset(
    {
        "point_id",
        "sql_ref",
        "source_ref",
        "source_content_digest",
        "context_revision_ref",
        "branch_ref",
        "project_ref",
        "conversation_ref",
        "artifact_kind",
        "contribution_kind",
        "specialist_ref",
        "laboratory_ref",
        "security_scope",
        "valid",
        "superseded_by",
    }
)


def _canonical_named_projection_payload(
    payload: Mapping[str, object],
    *,
    point_id: str,
) -> dict[str, object]:
    compact = _reference_payload(payload)
    keys = frozenset(compact)
    missing = _NAMED_PROJECTION_REQUIRED_FIELDS.difference(keys)
    unknown = keys.difference(_NAMED_PROJECTION_REQUIRED_FIELDS)
    if missing:
        raise QdrantClientProjectionExecutor._failure(
            "upsert_named_hybrid",
            "missing_payload_fields",
            "canonical projection payload misses: " + ", ".join(sorted(missing)),
        )
    if unknown:
        raise QdrantClientProjectionExecutor._failure(
            "upsert_named_hybrid",
            "unknown_payload_fields",
            "canonical projection payload has unknown fields: " + ", ".join(sorted(unknown)),
        )
    if compact["point_id"] != point_id:
        raise QdrantClientProjectionExecutor._failure(
            "upsert_named_hybrid", "point_id_mismatch", "payload point_id differs from point_id"
        )
    for field_name in (
        "point_id",
        "sql_ref",
        "source_ref",
        "context_revision_ref",
        "branch_ref",
        "project_ref",
        "conversation_ref",
        "specialist_ref",
        "laboratory_ref",
        "security_scope",
    ):
        if not _is_typed_ref(compact[field_name]):
            raise QdrantClientProjectionExecutor._failure(
                "upsert_named_hybrid", "invalid_payload_ref", f"{field_name} must be typed"
            )
    superseded_by = compact["superseded_by"]
    if superseded_by not in ("", None) and not _is_typed_ref(superseded_by):
        raise QdrantClientProjectionExecutor._failure(
            "upsert_named_hybrid", "invalid_payload_ref", "superseded_by must be empty or typed"
        )
    digest = compact["source_content_digest"]
    if not isinstance(digest, str) or len(digest) != 71 or not digest.startswith("sha256:"):
        raise QdrantClientProjectionExecutor._failure(
            "upsert_named_hybrid", "invalid_digest", "source_content_digest must be sha256:*"
        )
    try:
        int(digest[7:], 16)
    except ValueError as exc:
        raise QdrantClientProjectionExecutor._failure(
            "upsert_named_hybrid", "invalid_digest", "source_content_digest must be hexadecimal"
        ) from exc
    for field_name in ("artifact_kind", "contribution_kind"):
        if not _is_identifier(compact[field_name]):
            raise QdrantClientProjectionExecutor._failure(
                "upsert_named_hybrid", "invalid_payload_identifier", f"{field_name} must be stable"
            )
    if not isinstance(compact["valid"], bool):
        raise QdrantClientProjectionExecutor._failure(
            "upsert_named_hybrid", "invalid_payload_validity", "valid must be a boolean"
        )
    return compact


def _is_identifier(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    return value[0].islower() and all(
        character.islower() or character.isdigit() or character in "_.-"
        for character in value
    )

def _bounded_score(raw_score: float, distance: str) -> float:
    if not math.isfinite(raw_score):
        raise QdrantClientProjectionExecutor._failure("search", "invalid_score", "Qdrant score must be finite")
    if distance == "Euclid":
        return 1.0 / (1.0 + max(0.0, raw_score))
    return max(0.0, min(1.0, (raw_score + 1.0) / 2.0))
