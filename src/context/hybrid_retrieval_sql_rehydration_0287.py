"""Hybrid Qdrant retrieval with SQL-authoritative rehydration.

Phase 0287-r7-r8-r4 composes the existing OpenVINO/E5 query-embedding
boundary, the canonical Qdrant profile from r8-r3 and the SQL context-revision
authority from r8-r2.  It does not create another search engine and it does
not import qdrant-client or OpenVINO.

The injected Qdrant executor returns reference-only dense and sparse
candidates.  Reciprocal-rank fusion, authority-scope validation, grouping and
SQL rehydration happen locally.  Raw vectors and authoritative content never
appear in Qdrant payloads or serialized retrieval reports.  Scheduler and
ControlProxy are not imported or modified by this read-side composition.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from math import isfinite, log, sqrt
from types import MappingProxyType
from typing import Any, Literal, Protocol
import hashlib
import re

from context.context_revision_sql_authority_0287 import (
    ContextArtifactDescriptor,
    ContextAuthorityObject,
    ContextRevision,
)
from context.qdrant_canonical_profile_0287 import QdrantCollectionProfile

HYBRID_RETRIEVAL_VERSION = "0287.r7.r8.r4"
HYBRID_FILTER_SCHEMA = "missipy.retrieval.hybrid_filter.v1"
DENSE_QUERY_EMBEDDING_SCHEMA = "missipy.retrieval.dense_query_embedding.v1"
SPARSE_LEXICAL_QUERY_SCHEMA = "missipy.retrieval.sparse_lexical_query.v1"
HYBRID_QUERY_SCHEMA = "missipy.retrieval.hybrid_query.v1"
HYBRID_CANDIDATE_SCHEMA = "missipy.retrieval.hybrid_candidate.v1"
HYBRID_HIT_SCHEMA = "missipy.retrieval.hybrid_hit.v1"
REHYDRATED_AUTHORITY_ITEM_SCHEMA = (
    "missipy.retrieval.rehydrated_authority_item.v1"
)
HYBRID_RESULT_SCHEMA = "missipy.retrieval.hybrid_result.v1"
HYBRID_REPORT_SCHEMA = "missipy.retrieval.hybrid_report.v1"

RetrievalSource = Literal["dense", "sparse"]
GroupingField = Literal["none", "document_ref", "contribution_ref", "source_ref"]

_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_.-]*$")
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)
_GROUP_FIELDS = frozenset({"none", "document_ref", "contribution_ref", "source_ref"})
_FORBIDDEN_SERIALIZED_FIELDS = frozenset(
    {"vector", "values", "embedding", "body", "content", "local_path"}
)


class HybridRetrievalError(ValueError):
    """Raised when retrieval scope, fusion or SQL authority is inconsistent."""


class DenseQueryEmbedder(Protocol):
    """Injected existing E5/OpenVINO query embedding boundary."""

    def embed_query(
        self,
        query_text: str,
        *,
        query_ref: str,
        vector_name: str,
    ) -> "DenseQueryEmbedding": ...


class QdrantHybridQueryExecutor(Protocol):
    """Injected Qdrant query extension over the existing projection backend."""

    def search_dense(
        self,
        embedding: "DenseQueryEmbedding",
        *,
        query: "HybridRetrievalQuery",
        collection: QdrantCollectionProfile,
    ) -> Sequence["HybridRetrievalCandidate"]: ...

    def search_sparse(
        self,
        sparse_query: "SparseLexicalQuery",
        *,
        query: "HybridRetrievalQuery",
        collection: QdrantCollectionProfile,
    ) -> Sequence["HybridRetrievalCandidate"]: ...


class SqlAuthorityReader(Protocol):
    """Read-only subset of the r8-r2 SQL authority store."""

    def get_object(self, object_ref: str) -> ContextAuthorityObject | None: ...

    def get_artifact(
        self,
        artifact_ref: str,
    ) -> ContextArtifactDescriptor | None: ...

    def get_revision(self, revision_ref: str) -> ContextRevision | None: ...


@dataclass(frozen=True, slots=True)
class HybridRetrievalFilter:
    """Mandatory authority and context filters for every Qdrant sub-query."""

    schema: str
    context_revision_ref: str
    branch_ref: str
    project_ref: str
    security_scope: str
    conversation_ref: str = ""
    specialist_ref: str = ""
    laboratory_ref: str = ""
    sql_authority_ref: str = ""
    artifact_kinds: tuple[str, ...] = ()
    contribution_kinds: tuple[str, ...] = ()
    require_valid: bool = True
    include_superseded: bool = False

    def __post_init__(self) -> None:
        if self.schema != HYBRID_FILTER_SCHEMA:
            raise HybridRetrievalError("unsupported hybrid filter schema")
        for name in (
            "context_revision_ref",
            "branch_ref",
            "project_ref",
            "security_scope",
        ):
            _require_typed_ref(name, getattr(self, name))
        for name in (
            "conversation_ref",
            "specialist_ref",
            "laboratory_ref",
            "sql_authority_ref",
        ):
            value = getattr(self, name)
            if value:
                _require_typed_ref(name, value)
        object.__setattr__(
            self,
            "artifact_kinds",
            _normalize_identifiers("artifact_kinds", self.artifact_kinds),
        )
        object.__setattr__(
            self,
            "contribution_kinds",
            _normalize_identifiers(
                "contribution_kinds",
                self.contribution_kinds,
            ),
        )
        if not isinstance(self.require_valid, bool):
            raise HybridRetrievalError("require_valid must be a boolean")
        if not isinstance(self.include_superseded, bool):
            raise HybridRetrievalError("include_superseded must be a boolean")
        if not self.require_valid and not self.include_superseded:
            raise HybridRetrievalError(
                "invalid points cannot be selected without superseded history"
            )

    def to_qdrant_filter(self) -> dict[str, object]:
        must: list[dict[str, object]] = [
            _match("context_revision_ref", self.context_revision_ref),
            _match("branch_ref", self.branch_ref),
            _match("project_ref", self.project_ref),
            _match("security_scope", self.security_scope),
        ]
        for field_name in (
            "conversation_ref",
            "specialist_ref",
            "laboratory_ref",
            "sql_authority_ref",
        ):
            value = getattr(self, field_name)
            if value:
                must.append(_match(field_name, value))
        if self.require_valid:
            must.append(_match("valid", True))
        if self.artifact_kinds:
            must.append(_match_any("artifact_kind", self.artifact_kinds))
        if self.contribution_kinds:
            must.append(
                _match_any("contribution_kind", self.contribution_kinds)
            )
        return {"must": must}

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "context_revision_ref": self.context_revision_ref,
            "branch_ref": self.branch_ref,
            "project_ref": self.project_ref,
            "security_scope": self.security_scope,
            "conversation_ref": self.conversation_ref,
            "specialist_ref": self.specialist_ref,
            "laboratory_ref": self.laboratory_ref,
            "sql_authority_ref": self.sql_authority_ref,
            "artifact_kinds": list(self.artifact_kinds),
            "contribution_kinds": list(self.contribution_kinds),
            "require_valid": self.require_valid,
            "include_superseded": self.include_superseded,
            "qdrant_filter": self.to_qdrant_filter(),
        }


@dataclass(frozen=True, slots=True)
class DenseQueryEmbedding:
    """Validated query embedding; serialized mappings never expose values."""

    schema: str
    query_ref: str
    vector_name: str
    model_ref: str
    model_revision: str
    backend_ref: str
    values: tuple[float, ...]
    normalized: bool = True
    role: Literal["query"] = "query"

    def __post_init__(self) -> None:
        if self.schema != DENSE_QUERY_EMBEDDING_SCHEMA:
            raise HybridRetrievalError("unsupported dense embedding schema")
        for name in ("query_ref", "model_ref", "backend_ref"):
            _require_typed_ref(name, getattr(self, name))
        _require_identifier("vector_name", self.vector_name)
        _require_text("model_revision", self.model_revision)
        if self.role != "query":
            raise HybridRetrievalError("dense embedding role must be query")
        if not isinstance(self.normalized, bool) or not self.normalized:
            raise HybridRetrievalError("dense query embedding must be normalized")
        normalized_values = tuple(float(value) for value in self.values)
        if not normalized_values or any(not isfinite(value) for value in normalized_values):
            raise HybridRetrievalError("dense embedding values must be finite")
        norm = sqrt(sum(value * value for value in normalized_values))
        if abs(norm - 1.0) > 1e-4:
            raise HybridRetrievalError("dense query embedding must have unit norm")
        object.__setattr__(self, "values", normalized_values)

    @property
    def dimension(self) -> int:
        return len(self.values)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "query_ref": self.query_ref,
            "vector_name": self.vector_name,
            "model_ref": self.model_ref,
            "model_revision": self.model_revision,
            "backend_ref": self.backend_ref,
            "dimension": self.dimension,
            "normalized": self.normalized,
            "role": self.role,
            "raw_vector_serialized": False,
        }


@dataclass(frozen=True, slots=True)
class SparseLexicalQuery:
    """Deterministic sparse lexical query for the Qdrant sparse vector path."""

    schema: str
    query_ref: str
    vector_name: str
    terms: tuple[str, ...]
    indices: tuple[int, ...]
    weights: tuple[float, ...]

    def __post_init__(self) -> None:
        if self.schema != SPARSE_LEXICAL_QUERY_SCHEMA:
            raise HybridRetrievalError("unsupported sparse lexical query schema")
        _require_typed_ref("query_ref", self.query_ref)
        _require_identifier("vector_name", self.vector_name)
        if not self.terms:
            raise HybridRetrievalError("sparse query requires at least one term")
        if not (
            len(self.terms) == len(self.indices) == len(self.weights)
        ):
            raise HybridRetrievalError("sparse terms, indices and weights must align")
        if len(set(self.indices)) != len(self.indices):
            raise HybridRetrievalError("sparse indices must be unique")
        if any(index < 0 for index in self.indices):
            raise HybridRetrievalError("sparse indices must be >= 0")
        if any(not isfinite(float(weight)) or float(weight) <= 0 for weight in self.weights):
            raise HybridRetrievalError("sparse weights must be finite and > 0")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "query_ref": self.query_ref,
            "vector_name": self.vector_name,
            "term_count": len(self.terms),
            "terms": list(self.terms),
            "indices": list(self.indices),
            "weights": list(self.weights),
        }


@dataclass(frozen=True, slots=True)
class HybridRetrievalQuery:
    """One bounded dense+sparse retrieval request."""

    schema: str
    query_ref: str
    task_ref: str
    query_text: str
    filter: HybridRetrievalFilter
    dense_vector_name: str = "dense_e5_v1"
    sparse_vector_name: str = "sparse_lexical_v1"
    dense_candidate_limit: int = 32
    sparse_candidate_limit: int = 32
    final_limit: int = 16
    group_by: GroupingField = "document_ref"
    reciprocal_rank_k: int = 60

    def __post_init__(self) -> None:
        if self.schema != HYBRID_QUERY_SCHEMA:
            raise HybridRetrievalError("unsupported hybrid query schema")
        _require_typed_ref("query_ref", self.query_ref)
        _require_typed_ref("task_ref", self.task_ref)
        _require_text("query_text", self.query_text)
        _require_identifier("dense_vector_name", self.dense_vector_name)
        _require_identifier("sparse_vector_name", self.sparse_vector_name)
        if self.dense_vector_name == self.sparse_vector_name:
            raise HybridRetrievalError("dense and sparse vector names must differ")
        for name in (
            "dense_candidate_limit",
            "sparse_candidate_limit",
            "final_limit",
            "reciprocal_rank_k",
        ):
            value = getattr(self, name)
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                raise HybridRetrievalError(f"{name} must be a positive integer")
        if self.final_limit > self.dense_candidate_limit + self.sparse_candidate_limit:
            raise HybridRetrievalError("final_limit exceeds the candidate budget")
        if self.group_by not in _GROUP_FIELDS:
            raise HybridRetrievalError("unsupported group_by field")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "query_ref": self.query_ref,
            "task_ref": self.task_ref,
            "query_text_digest": _sha256_text(self.query_text),
            "filter": self.filter.to_mapping(),
            "dense_vector_name": self.dense_vector_name,
            "sparse_vector_name": self.sparse_vector_name,
            "dense_candidate_limit": self.dense_candidate_limit,
            "sparse_candidate_limit": self.sparse_candidate_limit,
            "final_limit": self.final_limit,
            "group_by": self.group_by,
            "reciprocal_rank_k": self.reciprocal_rank_k,
            "query_text_serialized": False,
        }


@dataclass(frozen=True, slots=True)
class HybridRetrievalCandidate:
    """Reference-only candidate returned by one Qdrant sub-query."""

    schema: str
    source: RetrievalSource
    point_id: str
    sql_ref: str
    source_ref: str
    score: float
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema != HYBRID_CANDIDATE_SCHEMA:
            raise HybridRetrievalError("unsupported hybrid candidate schema")
        if self.source not in {"dense", "sparse"}:
            raise HybridRetrievalError("candidate source must be dense or sparse")
        _require_text("point_id", self.point_id)
        _require_typed_ref("sql_ref", self.sql_ref)
        _require_typed_ref("source_ref", self.source_ref)
        if not isfinite(float(self.score)):
            raise HybridRetrievalError("candidate score must be finite")
        object.__setattr__(self, "score", float(self.score))
        object.__setattr__(self, "payload", _freeze_json_mapping(self.payload))
        payload = dict(self.payload)
        if payload.get("sql_ref", self.sql_ref) != self.sql_ref:
            raise HybridRetrievalError("candidate sql_ref conflicts with payload")
        forbidden = _FORBIDDEN_SERIALIZED_FIELDS.intersection(payload)
        if forbidden:
            raise HybridRetrievalError(
                "candidate payload contains forbidden fields: "
                + ", ".join(sorted(forbidden))
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "source": self.source,
            "point_id": self.point_id,
            "sql_ref": self.sql_ref,
            "source_ref": self.source_ref,
            "score": self.score,
            "payload": _thaw_json(self.payload),
        }


@dataclass(frozen=True, slots=True)
class HybridRetrievalHit:
    """Fused, grouped reference selected for SQL rehydration."""

    schema: str
    point_id: str
    sql_ref: str
    source_ref: str
    group_ref: str
    fused_score: float
    dense_rank: int | None
    sparse_rank: int | None
    dense_score: float | None
    sparse_score: float | None
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema != HYBRID_HIT_SCHEMA:
            raise HybridRetrievalError("unsupported hybrid hit schema")
        _require_text("point_id", self.point_id)
        _require_typed_ref("sql_ref", self.sql_ref)
        _require_typed_ref("source_ref", self.source_ref)
        _require_text("group_ref", self.group_ref)
        if not isfinite(float(self.fused_score)) or self.fused_score <= 0:
            raise HybridRetrievalError("fused_score must be finite and > 0")
        for name in ("dense_rank", "sparse_rank"):
            value = getattr(self, name)
            if value is not None and (
                not isinstance(value, int) or isinstance(value, bool) or value <= 0
            ):
                raise HybridRetrievalError(f"{name} must be a positive integer")
        object.__setattr__(self, "payload", _freeze_json_mapping(self.payload))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "point_id": self.point_id,
            "sql_ref": self.sql_ref,
            "source_ref": self.source_ref,
            "group_ref": self.group_ref,
            "fused_score": self.fused_score,
            "dense_rank": self.dense_rank,
            "sparse_rank": self.sparse_rank,
            "dense_score": self.dense_score,
            "sparse_score": self.sparse_score,
            "payload": _thaw_json(self.payload),
        }


@dataclass(frozen=True, slots=True)
class RehydratedAuthorityItem:
    """Authoritative SQL readback corresponding to one selected Qdrant ref."""

    schema: str
    sql_ref: str
    authority_kind: Literal["context_object", "artifact_descriptor"]
    content_digest: str
    title: str
    body: str
    storage_ref: str
    media_type: str
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema != REHYDRATED_AUTHORITY_ITEM_SCHEMA:
            raise HybridRetrievalError("unsupported rehydrated item schema")
        _require_typed_ref("sql_ref", self.sql_ref)
        if self.authority_kind not in {"context_object", "artifact_descriptor"}:
            raise HybridRetrievalError("unsupported authority_kind")
        _require_text("content_digest", self.content_digest)
        _require_text("title", self.title)
        if self.authority_kind == "context_object" and not self.body:
            if not self.storage_ref:
                raise HybridRetrievalError("authority object requires body or storage_ref")
        if self.storage_ref:
            _require_typed_ref("storage_ref", self.storage_ref)
        _require_text("media_type", self.media_type)
        object.__setattr__(self, "metadata", _freeze_json_mapping(self.metadata))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "sql_ref": self.sql_ref,
            "authority_kind": self.authority_kind,
            "content_digest": self.content_digest,
            "title": self.title,
            "body": self.body,
            "storage_ref": self.storage_ref,
            "media_type": self.media_type,
            "metadata": _thaw_json(self.metadata),
            "rehydrated_from_sql": True,
        }


@dataclass(frozen=True, slots=True)
class HybridRetrievalResult:
    """Final reference selection and SQL-authoritative content bundle."""

    schema: str
    query: HybridRetrievalQuery
    dense_embedding: DenseQueryEmbedding
    sparse_query: SparseLexicalQuery
    hits: tuple[HybridRetrievalHit, ...]
    items: tuple[RehydratedAuthorityItem, ...]
    dense_candidate_count: int
    sparse_candidate_count: int

    def __post_init__(self) -> None:
        if self.schema != HYBRID_RESULT_SCHEMA:
            raise HybridRetrievalError("unsupported hybrid result schema")
        object.__setattr__(self, "hits", tuple(self.hits))
        object.__setattr__(self, "items", tuple(self.items))
        if tuple(hit.sql_ref for hit in self.hits) != tuple(
            item.sql_ref for item in self.items
        ):
            raise HybridRetrievalError("hits and SQL readback must preserve order")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "query": self.query.to_mapping(),
            "dense_embedding": self.dense_embedding.to_mapping(),
            "sparse_query": self.sparse_query.to_mapping(),
            "dense_candidate_count": self.dense_candidate_count,
            "sparse_candidate_count": self.sparse_candidate_count,
            "hits": [hit.to_mapping() for hit in self.hits],
            "items": [item.to_mapping() for item in self.items],
            "boundaries": {
                "sql_is_authority": True,
                "qdrant_is_projection_only": True,
                "openvino_e5_used_behind_injected_port": True,
                "qdrant_search_used_behind_injected_port": True,
                "qdrant_write_performed": False,
                "raw_dense_vector_serialized": False,
                "control_proxy_modified": False,
                "scheduler_modified": False,
            },
        }


def build_sparse_lexical_query(
    query_text: str,
    *,
    query_ref: str,
    vector_name: str = "sparse_lexical_v1",
) -> SparseLexicalQuery:
    """Build a deterministic hashed sparse query from Unicode word tokens."""

    _require_text("query_text", query_text)
    _require_typed_ref("query_ref", query_ref)
    _require_identifier("vector_name", vector_name)
    tokens = tuple(token.casefold() for token in _TOKEN_RE.findall(query_text))
    if not tokens:
        raise HybridRetrievalError("query_text does not contain lexical tokens")
    counts = Counter(tokens)
    by_index: dict[int, tuple[str, float]] = {}
    for term, count in sorted(counts.items()):
        index = int.from_bytes(
            hashlib.sha256(term.encode("utf-8")).digest()[:4],
            "big",
        ) & 0x7FFFFFFF
        weight = 1.0 + log(float(count))
        existing = by_index.get(index)
        if existing is None:
            by_index[index] = (term, weight)
        else:
            by_index[index] = (existing[0] + "|" + term, existing[1] + weight)
    ordered = sorted(by_index.items())
    norm = sqrt(sum(weight * weight for _, (_, weight) in ordered))
    terms = tuple(term for _, (term, _) in ordered)
    indices = tuple(index for index, _ in ordered)
    weights = tuple(weight / norm for _, (_, weight) in ordered)
    return SparseLexicalQuery(
        schema=SPARSE_LEXICAL_QUERY_SCHEMA,
        query_ref=query_ref,
        vector_name=vector_name,
        terms=terms,
        indices=indices,
        weights=weights,
    )


def fuse_hybrid_candidates(
    dense_candidates: Sequence[HybridRetrievalCandidate],
    sparse_candidates: Sequence[HybridRetrievalCandidate],
    *,
    query: HybridRetrievalQuery,
) -> tuple[HybridRetrievalHit, ...]:
    """Validate scope, fuse by reciprocal rank and apply diversity grouping."""

    dense = _bounded_candidates(
        dense_candidates,
        expected_source="dense",
        limit=query.dense_candidate_limit,
        query=query,
    )
    sparse = _bounded_candidates(
        sparse_candidates,
        expected_source="sparse",
        limit=query.sparse_candidate_limit,
        query=query,
    )
    records: dict[str, dict[str, Any]] = {}
    for rank, candidate in enumerate(dense, 1):
        record = _merge_candidate(records, candidate)
        if record.get("dense_rank") is not None:
            raise HybridRetrievalError("dense results contain a duplicate point")
        record["dense_rank"] = rank
        record["dense_score"] = candidate.score
        record["fused_score"] += 1.0 / (query.reciprocal_rank_k + rank)
    for rank, candidate in enumerate(sparse, 1):
        record = _merge_candidate(records, candidate)
        if record.get("sparse_rank") is not None:
            raise HybridRetrievalError("sparse results contain a duplicate point")
        record["sparse_rank"] = rank
        record["sparse_score"] = candidate.score
        record["fused_score"] += 1.0 / (query.reciprocal_rank_k + rank)
    ordered_records = sorted(
        records.values(),
        key=lambda item: (
            -float(item["fused_score"]),
            str(item["sql_ref"]),
            str(item["point_id"]),
        ),
    )
    hits: list[HybridRetrievalHit] = []
    seen_groups: set[str] = set()
    for record in ordered_records:
        payload = dict(record["payload"])
        group_ref = _group_ref(query.group_by, record, payload)
        if group_ref in seen_groups:
            continue
        seen_groups.add(group_ref)
        hits.append(
            HybridRetrievalHit(
                schema=HYBRID_HIT_SCHEMA,
                point_id=str(record["point_id"]),
                sql_ref=str(record["sql_ref"]),
                source_ref=str(record["source_ref"]),
                group_ref=group_ref,
                fused_score=float(record["fused_score"]),
                dense_rank=record.get("dense_rank"),
                sparse_rank=record.get("sparse_rank"),
                dense_score=record.get("dense_score"),
                sparse_score=record.get("sparse_score"),
                payload=payload,
            )
        )
        if len(hits) >= query.final_limit:
            break
    return tuple(hits)


def execute_hybrid_retrieval(
    query: HybridRetrievalQuery,
    *,
    collection: QdrantCollectionProfile,
    embedder: DenseQueryEmbedder,
    executor: QdrantHybridQueryExecutor,
    authority_store: SqlAuthorityReader,
) -> HybridRetrievalResult:
    """Run dense+sparse retrieval and rehydrate selected refs from SQL."""

    dense_profile = _named_vector(collection, query.dense_vector_name, "dense")
    _named_vector(collection, query.sparse_vector_name, "sparse")
    embedding = embedder.embed_query(
        query.query_text,
        query_ref=query.query_ref,
        vector_name=query.dense_vector_name,
    )
    if embedding.vector_name != query.dense_vector_name:
        raise HybridRetrievalError("embedder returned the wrong vector_name")
    if embedding.dimension != dense_profile.dimension:
        raise HybridRetrievalError("query embedding dimension does not match profile")
    if embedding.model_ref != dense_profile.model_ref:
        raise HybridRetrievalError("query embedding model_ref does not match profile")
    if embedding.model_revision != dense_profile.model_revision:
        raise HybridRetrievalError("query embedding model_revision does not match profile")
    sparse_query = build_sparse_lexical_query(
        query.query_text,
        query_ref=query.query_ref,
        vector_name=query.sparse_vector_name,
    )
    dense_candidates = tuple(
        executor.search_dense(
            embedding,
            query=query,
            collection=collection,
        )
    )
    sparse_candidates = tuple(
        executor.search_sparse(
            sparse_query,
            query=query,
            collection=collection,
        )
    )
    hits = fuse_hybrid_candidates(
        dense_candidates,
        sparse_candidates,
        query=query,
    )
    revision = authority_store.get_revision(query.filter.context_revision_ref)
    if revision is None:
        raise HybridRetrievalError("context revision is absent from SQL authority")
    membership = {item.object_ref: item for item in revision.memberships}
    items = tuple(
        _rehydrate_hit(hit, membership=membership, store=authority_store)
        for hit in hits
    )
    return HybridRetrievalResult(
        schema=HYBRID_RESULT_SCHEMA,
        query=query,
        dense_embedding=embedding,
        sparse_query=sparse_query,
        hits=hits,
        items=items,
        dense_candidate_count=len(dense_candidates),
        sparse_candidate_count=len(sparse_candidates),
    )


def build_hybrid_retrieval_report(
    result: HybridRetrievalResult,
) -> dict[str, object]:
    mapping = result.to_mapping()
    return {
        "schema": HYBRID_REPORT_SCHEMA,
        "version": HYBRID_RETRIEVAL_VERSION,
        "query_ref": result.query.query_ref,
        "selected_sql_refs": [item.sql_ref for item in result.items],
        "hit_count": len(result.hits),
        "result": mapping,
        "boundaries": mapping["boundaries"],
    }


def _rehydrate_hit(
    hit: HybridRetrievalHit,
    *,
    membership: Mapping[str, Any],
    store: SqlAuthorityReader,
) -> RehydratedAuthorityItem:
    member = membership.get(hit.sql_ref)
    if member is None:
        raise HybridRetrievalError("Qdrant hit is not a member of the requested revision")
    if getattr(member, "state", None) != "active":
        raise HybridRetrievalError("Qdrant hit is not active in the requested revision")
    payload = dict(hit.payload)
    expected_digest = payload.get("source_content_digest")
    authority_object = store.get_object(hit.sql_ref)
    if authority_object is not None:
        if expected_digest and expected_digest != authority_object.content_digest:
            raise HybridRetrievalError("Qdrant source digest differs from SQL authority")
        return RehydratedAuthorityItem(
            schema=REHYDRATED_AUTHORITY_ITEM_SCHEMA,
            sql_ref=authority_object.object_ref,
            authority_kind="context_object",
            content_digest=authority_object.content_digest,
            title=authority_object.title,
            body=authority_object.body,
            storage_ref=authority_object.storage_ref or "",
            media_type=authority_object.media_type,
            metadata=authority_object.metadata,
        )
    artifact = store.get_artifact(hit.sql_ref)
    if artifact is not None:
        if expected_digest and expected_digest != artifact.content_digest:
            raise HybridRetrievalError("Qdrant source digest differs from SQL authority")
        return RehydratedAuthorityItem(
            schema=REHYDRATED_AUTHORITY_ITEM_SCHEMA,
            sql_ref=artifact.artifact_ref,
            authority_kind="artifact_descriptor",
            content_digest=artifact.content_digest,
            title=artifact.artifact_ref,
            body="",
            storage_ref=artifact.storage_ref,
            media_type=artifact.media_type,
            metadata=artifact.metadata,
        )
    raise HybridRetrievalError("Qdrant hit cannot be rehydrated from SQL authority")


def _bounded_candidates(
    candidates: Sequence[HybridRetrievalCandidate],
    *,
    expected_source: RetrievalSource,
    limit: int,
    query: HybridRetrievalQuery,
) -> tuple[HybridRetrievalCandidate, ...]:
    bounded = tuple(candidates[:limit])
    for candidate in bounded:
        if candidate.source != expected_source:
            raise HybridRetrievalError("executor returned a candidate for the wrong source")
        _validate_candidate_scope(candidate, query.filter)
    return bounded


def _validate_candidate_scope(
    candidate: HybridRetrievalCandidate,
    filter_: HybridRetrievalFilter,
) -> None:
    payload = dict(candidate.payload)
    expected = {
        "context_revision_ref": filter_.context_revision_ref,
        "branch_ref": filter_.branch_ref,
        "project_ref": filter_.project_ref,
        "security_scope": filter_.security_scope,
    }
    for field_name in (
        "conversation_ref",
        "specialist_ref",
        "laboratory_ref",
        "sql_authority_ref",
    ):
        value = getattr(filter_, field_name)
        if value:
            expected[field_name] = value
    for field_name, value in expected.items():
        if payload.get(field_name) != value:
            raise HybridRetrievalError(
                f"candidate payload scope mismatch for {field_name}"
            )
    if payload.get("sql_ref") != candidate.sql_ref:
        raise HybridRetrievalError("candidate payload sql_ref is missing or different")
    if payload.get("source_ref") != candidate.source_ref:
        raise HybridRetrievalError("candidate payload source_ref is missing or different")
    source_digest = payload.get("source_content_digest")
    if not isinstance(source_digest, str) or _SHA256_RE.fullmatch(source_digest) is None:
        raise HybridRetrievalError("candidate payload requires source_content_digest")
    if filter_.require_valid and payload.get("valid") is not True:
        raise HybridRetrievalError("candidate is not marked valid")
    if not filter_.include_superseded and payload.get("superseded_by"):
        raise HybridRetrievalError("candidate is superseded")
    if filter_.artifact_kinds and payload.get("artifact_kind") not in filter_.artifact_kinds:
        raise HybridRetrievalError("candidate artifact_kind is outside the filter")
    if (
        filter_.contribution_kinds
        and payload.get("contribution_kind") not in filter_.contribution_kinds
    ):
        raise HybridRetrievalError("candidate contribution_kind is outside the filter")


def _merge_candidate(
    records: dict[str, dict[str, Any]],
    candidate: HybridRetrievalCandidate,
) -> dict[str, Any]:
    record = records.get(candidate.point_id)
    if record is None:
        record = {
            "point_id": candidate.point_id,
            "sql_ref": candidate.sql_ref,
            "source_ref": candidate.source_ref,
            "payload": dict(candidate.payload),
            "fused_score": 0.0,
        }
        records[candidate.point_id] = record
        return record
    if record["sql_ref"] != candidate.sql_ref:
        raise HybridRetrievalError("one point_id cannot reference two SQL objects")
    if record["source_ref"] != candidate.source_ref:
        raise HybridRetrievalError("one point_id cannot reference two source refs")
    if dict(record["payload"]) != dict(candidate.payload):
        raise HybridRetrievalError("dense and sparse payloads differ for one point")
    return record


def _group_ref(
    group_by: GroupingField,
    record: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> str:
    if group_by == "none":
        return str(record["point_id"])
    if group_by == "source_ref":
        return str(record["source_ref"])
    value = payload.get(group_by)
    if not isinstance(value, str) or not value:
        raise HybridRetrievalError(f"group field {group_by} is missing")
    _require_typed_ref(group_by, value)
    return value


def _named_vector(
    collection: QdrantCollectionProfile,
    vector_name: str,
    expected_kind: str,
) -> Any:
    for profile in collection.named_vectors:
        if profile.vector_name == vector_name:
            if profile.vector_kind != expected_kind:
                raise HybridRetrievalError(
                    f"{vector_name} is not a {expected_kind} vector"
                )
            return profile
    raise HybridRetrievalError(f"collection lacks named vector {vector_name}")


def _match(key: str, value: object) -> dict[str, object]:
    return {"key": key, "match": {"value": value}}


def _match_any(key: str, values: Sequence[str]) -> dict[str, object]:
    return {"key": key, "match": {"any": list(values)}}


def _normalize_identifiers(name: str, values: Sequence[str]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        _require_identifier(name, value)
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)


def _freeze_json_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise HybridRetrievalError("payload and metadata must be mappings")
    return MappingProxyType(
        {str(key): _freeze_json(item) for key, item in value.items()}
    )


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _freeze_json(item) for key, item in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    raise HybridRetrievalError("payload must contain JSON-compatible values")


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _require_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HybridRetrievalError(f"{name} must be a non-empty string")
    return value


def _require_typed_ref(name: str, value: object) -> str:
    text = _require_text(name, value)
    if _TYPED_REF_RE.fullmatch(text) is None:
        raise HybridRetrievalError(f"{name} must be a typed reference")
    return text


def _require_identifier(name: str, value: object) -> str:
    text = _require_text(name, value)
    if _IDENTIFIER_RE.fullmatch(text) is None:
        raise HybridRetrievalError(f"{name} must be a stable identifier")
    return text


def _sha256_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()
