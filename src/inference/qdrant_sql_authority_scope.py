"""SQL-authority scope membrane for Qdrant projection and recall.

This module wraps the existing ``QdrantProjectionExecutor`` protocol. It adds a
stable SQL-authority reference to projection payloads and rejects recall hits
that belong to another SQL authority before SQL rehydration.

The wrapper does not import qdrant-client, open sockets, start services, or
access SHM. A later binding patch may inject it around the existing concrete
qdrant-client executor.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import re
from typing import Sequence
from urllib.parse import urlparse

from inference.qdrant_projection_adapter import (
    QdrantProjectionExecutor,
    QdrantProjectionPoint,
    QdrantProjectionPolicy,
    QdrantProjectionTarget,
    QdrantProjectionWriteResult,
    QdrantRecallQuery,
    QdrantRecallResult,
)

_SCOPE_SCHEMA = "missipy.qdrant.sql_authority_scope.v1"
_TRANSPORT_SCHEMA = "missipy.qdrant.strict_grpc_transport.v1"
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_ALLOWED_STORE_KINDS = frozenset({"sqlite", "postgresql"})


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _require_typed_ref(name: str, value: str) -> None:
    _require_non_empty(name, value)
    if not _TYPED_REF_RE.fullmatch(value):
        raise ValueError(f"{name} must be a typed ref")


@dataclass(frozen=True, slots=True)
class QdrantSqlAuthorityScope:
    """Stable SQL authority identity stored in every Qdrant point payload."""

    authority_ref: str
    store_kind: str
    namespace: str = "autodoc-local"

    def __post_init__(self) -> None:
        _require_typed_ref("authority_ref", self.authority_ref)
        if self.store_kind not in _ALLOWED_STORE_KINDS:
            raise ValueError("store_kind must be sqlite or postgresql")
        _require_non_empty("namespace", self.namespace)

    @property
    def payload_items(self) -> tuple[tuple[str, str], ...]:
        return (
            ("sql_authority_ref", self.authority_ref),
            ("sql_store_kind", self.store_kind),
        )

    def to_filter_mapping(self) -> dict[str, object]:
        """Return a qdrant-client compatible filter description, data only."""

        return {
            "must": [
                {
                    "key": "sql_authority_ref",
                    "match": {"value": self.authority_ref},
                }
            ]
        }

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _SCOPE_SCHEMA,
            "authority_ref": self.authority_ref,
            "store_kind": self.store_kind,
            "namespace": self.namespace,
            "payload": dict(self.payload_items),
            "filter": self.to_filter_mapping(),
            "sql_path_disclosed": False,
        }


def derive_sqlite_authority_scope(
    db_path: str | Path,
    *,
    namespace: str = "autodoc-local",
) -> QdrantSqlAuthorityScope:
    """Derive a stable opaque authority ref without serializing the DB path."""

    _require_non_empty("namespace", namespace)
    canonical_path = str(Path(db_path).expanduser().resolve(strict=False))
    digest = sha256(
        f"{namespace}\x00sqlite\x00{canonical_path}".encode("utf-8")
    ).hexdigest()[:16]
    return QdrantSqlAuthorityScope(
        authority_ref=f"sql-authority:sqlite:{digest}",
        store_kind="sqlite",
        namespace=namespace,
    )


@dataclass(frozen=True, slots=True)
class QdrantStrictGrpcTransportPolicy:
    """Separate REST administration from strict gRPC data operations."""

    rest_admin_url: str = "http://127.0.0.1:6333"
    grpc_port: int = 6334
    prefer_grpc: bool = True
    strict_data_grpc: bool = True

    def __post_init__(self) -> None:
        parsed = urlparse(self.rest_admin_url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("rest_admin_url must be an http(s) URL with a host")
        if not 1 <= self.grpc_port <= 65535:
            raise ValueError("grpc_port must be between 1 and 65535")
        rest_port = parsed.port or (443 if parsed.scheme == "https" else 80)
        if rest_port == self.grpc_port:
            raise ValueError("REST administration port must differ from gRPC port")
        if self.strict_data_grpc and not self.prefer_grpc:
            raise ValueError("strict_data_grpc requires prefer_grpc")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _TRANSPORT_SCHEMA,
            "rest_admin_url": self.rest_admin_url,
            "rest_admin_only": True,
            "grpc_port": self.grpc_port,
            "prefer_grpc": self.prefer_grpc,
            "strict_data_grpc": self.strict_data_grpc,
            "requested_data_transport": "grpc" if self.prefer_grpc else "rest",
        }


def add_sql_authority_scope_to_point(
    point: QdrantProjectionPoint,
    scope: QdrantSqlAuthorityScope,
) -> QdrantProjectionPoint:
    """Return a new point with reserved scope payload fields."""

    payload = dict(point.payload)
    for key, expected in scope.payload_items:
        current = payload.get(key)
        if current is not None and current != expected:
            raise ValueError(f"point payload has conflicting {key}")
        payload[key] = expected
    return QdrantProjectionPoint(
        point_id=point.point_id,
        embedding_ref=point.embedding_ref,
        source_ref=point.source_ref,
        sql_context_ref=point.sql_context_ref,
        vector=point.vector,
        payload=tuple(sorted(payload.items())),
    )


class SqlAuthorityScopedQdrantExecutor:
    """Protocol-preserving scope wrapper around an existing executor."""

    def __init__(
        self,
        delegate: QdrantProjectionExecutor,
        scope: QdrantSqlAuthorityScope,
        *,
        recall_oversample_factor: int = 4,
    ) -> None:
        if recall_oversample_factor <= 0:
            raise ValueError("recall_oversample_factor must be > 0")
        self._delegate = delegate
        self._scope = scope
        self._recall_oversample_factor = recall_oversample_factor

    @property
    def scope(self) -> QdrantSqlAuthorityScope:
        return self._scope

    def upsert_points(
        self,
        points: Sequence[QdrantProjectionPoint],
        *,
        target: QdrantProjectionTarget,
        policy: QdrantProjectionPolicy,
    ) -> QdrantProjectionWriteResult:
        scoped_points = tuple(
            add_sql_authority_scope_to_point(point, self._scope)
            for point in points
        )
        return self._delegate.upsert_points(
            scoped_points,
            target=target,
            policy=policy,
        )

    def search_vector(
        self,
        vector: Sequence[float],
        *,
        target: QdrantProjectionTarget,
        policy: QdrantProjectionPolicy,
        query: QdrantRecallQuery,
    ) -> QdrantRecallResult:
        expanded_limit = min(
            policy.max_recall_hits,
            max(query.limit, query.limit * self._recall_oversample_factor),
        )
        expanded_query = QdrantRecallQuery(
            query_ref=query.query_ref,
            limit=expanded_limit,
            role=query.role,
        )
        result = self._delegate.search_vector(
            vector,
            target=target,
            policy=policy,
            query=expanded_query,
        )
        scoped_hits = tuple(
            hit
            for hit in result.hits
            if dict(hit.payload).get("sql_authority_ref")
            == self._scope.authority_ref
        )[: query.limit]
        return QdrantRecallResult(
            target=result.target,
            query=query,
            hits=scoped_hits,
            capped=(
                result.capped
                or result.hit_count >= expanded_limit
                or len(scoped_hits) < result.hit_count
            ),
        )

    def close(self) -> None:
        close = getattr(self._delegate, "close", None)
        if callable(close):
            close()
