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
from types import ModuleType
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


def _bounded_score(raw_score: float, distance: str) -> float:
    if not math.isfinite(raw_score):
        raise QdrantClientProjectionExecutor._failure("search", "invalid_score", "Qdrant score must be finite")
    if distance == "Euclid":
        return 1.0 / (1.0 + max(0.0, raw_score))
    return max(0.0, min(1.0, (raw_score + 1.0) / 2.0))
