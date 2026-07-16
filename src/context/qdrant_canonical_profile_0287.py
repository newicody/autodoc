"""Canonical Qdrant projection profile for semantic context revisions.

Phase 0287-r7-r8-r3 does not execute Qdrant operations.  It defines the
immutable profile that connects SQL-authoritative context objects and vector
projection metadata to reconstructible Qdrant points, named-vector spaces,
payload indexes and model-migration plans.

SQL remains the authority.  Qdrant stores projections and reference payloads.
The ControlProxy, Scheduler, EventBus, OpenVINO and qdrant-client are not
imported or invoked here.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal, Protocol
import hashlib
import json
import re

QDRANT_CANONICAL_PROFILE_VERSION = "0287.r7.r8.r3"
QDRANT_NAMED_VECTOR_SCHEMA = "missipy.qdrant.named_vector_profile.v1"
QDRANT_PAYLOAD_INDEX_SCHEMA = "missipy.qdrant.payload_index_profile.v1"
QDRANT_COLLECTION_PROFILE_SCHEMA = "missipy.qdrant.collection_profile.v1"
QDRANT_POINT_PROJECTION_SCHEMA = "missipy.qdrant.point_projection.v1"
QDRANT_MODEL_MIGRATION_SCHEMA = "missipy.qdrant.model_migration_plan.v1"
QDRANT_PROFILE_REPORT_SCHEMA = "missipy.qdrant.canonical_profile_report.v1"

VECTOR_PROJECTION_METADATA_SCHEMA = (
    "missipy.context.vector_projection_metadata.v1"
)
EMBEDDING_SPACE_PROFILE_SCHEMA = "missipy.embedding_space_profile.v1"

VectorKind = Literal["dense", "sparse", "multivector"]
DistanceMetric = Literal["Cosine", "Dot", "Euclid", "Manhattan"]
PayloadIndexKind = Literal[
    "keyword",
    "integer",
    "float",
    "bool",
    "datetime",
    "uuid",
    "text",
    "geo",
]
MigrationStrategy = Literal["named_vector", "alias_swap"]

_VECTOR_KINDS = frozenset({"dense", "sparse", "multivector"})
_DISTANCE_METRICS = frozenset({"Cosine", "Dot", "Euclid", "Manhattan"})
_PAYLOAD_INDEX_KINDS = frozenset(
    {"keyword", "integer", "float", "bool", "datetime", "uuid", "text", "geo"}
)
_MIGRATION_STRATEGIES = frozenset({"named_vector", "alias_swap"})
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_.-]*$")
_COLLECTION_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

CANONICAL_PAYLOAD_INDEXES: tuple[tuple[str, PayloadIndexKind], ...] = (
    ("sql_ref", "keyword"),
    ("source_ref", "keyword"),
    ("source_content_digest", "keyword"),
    ("context_revision_ref", "keyword"),
    ("branch_ref", "keyword"),
    ("project_ref", "keyword"),
    ("conversation_ref", "keyword"),
    ("artifact_kind", "keyword"),
    ("contribution_kind", "keyword"),
    ("specialist_ref", "keyword"),
    ("laboratory_ref", "keyword"),
    ("security_scope", "keyword"),
    ("valid", "bool"),
    ("superseded_by", "keyword"),
)


class QdrantCanonicalProfileError(ValueError):
    """Raised when a Qdrant projection contract is inconsistent."""


class _ToMapping(Protocol):
    def to_mapping(self) -> Mapping[str, Any]: ...


def _mapping(value: Mapping[str, Any] | _ToMapping) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    to_mapping = getattr(value, "to_mapping", None)
    if not callable(to_mapping):
        raise QdrantCanonicalProfileError("value must be a mapping or expose to_mapping()")
    result = to_mapping()
    if not isinstance(result, Mapping):
        raise QdrantCanonicalProfileError("to_mapping() must return a mapping")
    return dict(result)


def _require_text(name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise QdrantCanonicalProfileError(f"{name} must be a non-empty string")
    return value


def _require_typed_ref(name: str, value: object, *, optional: bool = False) -> str:
    if optional and value in (None, ""):
        return ""
    text = _require_text(name, value)
    if _TYPED_REF_RE.fullmatch(text) is None:
        raise QdrantCanonicalProfileError(f"{name} must be a typed reference")
    return text


def _require_identifier(name: str, value: object) -> str:
    text = _require_text(name, value)
    if _IDENTIFIER_RE.fullmatch(text) is None:
        raise QdrantCanonicalProfileError(f"{name} must be a stable identifier")
    return text


def _require_collection_name(name: str, value: object) -> str:
    text = _require_text(name, value)
    if _COLLECTION_RE.fullmatch(text) is None:
        raise QdrantCanonicalProfileError(f"{name} must be a safe Qdrant name")
    return text


def _require_sha256(name: str, value: object) -> str:
    text = _require_text(name, value)
    if _SHA256_RE.fullmatch(text) is None:
        raise QdrantCanonicalProfileError(f"{name} must use sha256:<64 lowercase hex>")
    return text


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze_json(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    if isinstance(value, (str, int, float, bool, type(None))):
        return value
    raise QdrantCanonicalProfileError("metadata must contain JSON-compatible values")


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _stable_digest(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class QdrantNamedVectorProfile:
    """One named vector space attached to a shared Qdrant point identity."""

    schema: str
    vector_name: str
    vector_kind: VectorKind
    embedding_profile_ref: str
    model_ref: str
    model_revision: str
    dimension: int | None
    distance: DistanceMetric | None
    normalized: bool | None
    model_artifact_digest: str = ""
    hnsw_enabled: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema != QDRANT_NAMED_VECTOR_SCHEMA:
            raise QdrantCanonicalProfileError("unsupported named vector schema")
        _require_identifier("vector_name", self.vector_name)
        if self.vector_kind not in _VECTOR_KINDS:
            raise QdrantCanonicalProfileError("unsupported vector_kind")
        _require_typed_ref("embedding_profile_ref", self.embedding_profile_ref)
        _require_typed_ref("model_ref", self.model_ref)
        _require_text("model_revision", self.model_revision)
        if self.vector_kind == "sparse":
            if self.dimension is not None or self.distance is not None:
                raise QdrantCanonicalProfileError(
                    "sparse vectors must not declare fixed dimension or distance"
                )
            if self.normalized is not None:
                raise QdrantCanonicalProfileError(
                    "sparse vectors must not declare dense normalization"
                )
        else:
            if not isinstance(self.dimension, int) or isinstance(self.dimension, bool):
                raise QdrantCanonicalProfileError("dense/multivector dimension must be int")
            if self.dimension <= 0:
                raise QdrantCanonicalProfileError("dimension must be > 0")
            if self.distance not in _DISTANCE_METRICS:
                raise QdrantCanonicalProfileError("unsupported distance metric")
            if not isinstance(self.normalized, bool):
                raise QdrantCanonicalProfileError("normalized must be a boolean")
        if self.model_artifact_digest:
            _require_sha256("model_artifact_digest", self.model_artifact_digest)
        if not isinstance(self.hnsw_enabled, bool):
            raise QdrantCanonicalProfileError("hnsw_enabled must be a boolean")
        object.__setattr__(self, "metadata", _freeze_json(self.metadata))

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "vector_name": self.vector_name,
            "vector_kind": self.vector_kind,
            "embedding_profile_ref": self.embedding_profile_ref,
            "model_ref": self.model_ref,
            "model_revision": self.model_revision,
            "dimension": self.dimension,
            "distance": self.distance,
            "normalized": self.normalized,
            "model_artifact_digest": self.model_artifact_digest,
            "hnsw_enabled": self.hnsw_enabled,
            "metadata": _thaw_json(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class QdrantPayloadIndexProfile:
    """One indexed payload field used for authority and scope filtering."""

    schema: str
    field_name: str
    index_kind: PayloadIndexKind
    required: bool = True
    tenant_key: bool = False
    principal_key: bool = False

    def __post_init__(self) -> None:
        if self.schema != QDRANT_PAYLOAD_INDEX_SCHEMA:
            raise QdrantCanonicalProfileError("unsupported payload index schema")
        _require_identifier("field_name", self.field_name)
        if self.index_kind not in _PAYLOAD_INDEX_KINDS:
            raise QdrantCanonicalProfileError("unsupported payload index kind")
        for name in ("required", "tenant_key", "principal_key"):
            if not isinstance(getattr(self, name), bool):
                raise QdrantCanonicalProfileError(f"{name} must be a boolean")
        if self.tenant_key and self.index_kind != "keyword":
            raise QdrantCanonicalProfileError("tenant_key must use a keyword index")
        if self.principal_key and self.index_kind != "keyword":
            raise QdrantCanonicalProfileError("principal_key must use a keyword index")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "field_name": self.field_name,
            "index_kind": self.index_kind,
            "required": self.required,
            "tenant_key": self.tenant_key,
            "principal_key": self.principal_key,
        }


@dataclass(frozen=True, slots=True)
class QdrantCollectionProfile:
    """A bounded collection profile sharing one point/payload identity."""

    schema: str
    profile_ref: str
    collection_name: str
    collection_alias: str
    point_identity_field: str
    authority_ref_field: str
    named_vectors: tuple[QdrantNamedVectorProfile, ...]
    payload_indexes: tuple[QdrantPayloadIndexProfile, ...]
    multitenancy_mode: Literal["payload_partitioning"] = "payload_partitioning"
    create_indexes_before_ingest: bool = True
    raw_content_in_payload_allowed: bool = False
    vectors_reconstructible: bool = True
    one_collection_per_task_allowed: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema != QDRANT_COLLECTION_PROFILE_SCHEMA:
            raise QdrantCanonicalProfileError("unsupported collection profile schema")
        _require_typed_ref("profile_ref", self.profile_ref)
        _require_collection_name("collection_name", self.collection_name)
        _require_collection_name("collection_alias", self.collection_alias)
        _require_identifier("point_identity_field", self.point_identity_field)
        _require_identifier("authority_ref_field", self.authority_ref_field)
        if self.multitenancy_mode != "payload_partitioning":
            raise QdrantCanonicalProfileError("only payload_partitioning is supported")
        if not self.named_vectors:
            raise QdrantCanonicalProfileError("at least one named vector is required")
        vector_names = [item.vector_name for item in self.named_vectors]
        if len(vector_names) != len(set(vector_names)):
            raise QdrantCanonicalProfileError("named vector names must be unique")
        field_names = [item.field_name for item in self.payload_indexes]
        if len(field_names) != len(set(field_names)):
            raise QdrantCanonicalProfileError("payload index names must be unique")
        canonical = {name: kind for name, kind in CANONICAL_PAYLOAD_INDEXES}
        observed = {item.field_name: item.index_kind for item in self.payload_indexes}
        missing = sorted(name for name in canonical if name not in observed)
        mismatched = sorted(
            name for name, kind in canonical.items() if observed.get(name) not in (None, kind)
        )
        if missing:
            raise QdrantCanonicalProfileError(
                "missing canonical payload indexes: " + ", ".join(missing)
            )
        if mismatched:
            raise QdrantCanonicalProfileError(
                "canonical payload index type mismatch: " + ", ".join(mismatched)
            )
        booleans = (
            "create_indexes_before_ingest",
            "raw_content_in_payload_allowed",
            "vectors_reconstructible",
            "one_collection_per_task_allowed",
        )
        for name in booleans:
            if not isinstance(getattr(self, name), bool):
                raise QdrantCanonicalProfileError(f"{name} must be a boolean")
        if not self.create_indexes_before_ingest:
            raise QdrantCanonicalProfileError(
                "payload indexes must be created before first ingestion"
            )
        if self.raw_content_in_payload_allowed:
            raise QdrantCanonicalProfileError("raw authoritative content is forbidden")
        if not self.vectors_reconstructible:
            raise QdrantCanonicalProfileError("Qdrant vectors must be reconstructible")
        if self.one_collection_per_task_allowed:
            raise QdrantCanonicalProfileError("one collection per task is forbidden")
        object.__setattr__(self, "metadata", _freeze_json(self.metadata))

    def vector(self, vector_name: str) -> QdrantNamedVectorProfile:
        for item in self.named_vectors:
            if item.vector_name == vector_name:
                return item
        raise QdrantCanonicalProfileError(f"unknown named vector: {vector_name}")

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "profile_ref": self.profile_ref,
            "collection_name": self.collection_name,
            "collection_alias": self.collection_alias,
            "point_identity_field": self.point_identity_field,
            "authority_ref_field": self.authority_ref_field,
            "named_vectors": [item.to_mapping() for item in self.named_vectors],
            "payload_indexes": [item.to_mapping() for item in self.payload_indexes],
            "multitenancy_mode": self.multitenancy_mode,
            "create_indexes_before_ingest": self.create_indexes_before_ingest,
            "raw_content_in_payload_allowed": self.raw_content_in_payload_allowed,
            "vectors_reconstructible": self.vectors_reconstructible,
            "one_collection_per_task_allowed": self.one_collection_per_task_allowed,
            "metadata": _thaw_json(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class QdrantPointProjection:
    """Reference-only Qdrant point payload validated against SQL metadata."""

    schema: str
    point_id: str
    collection_profile_ref: str
    vector_name: str
    source_ref: str
    source_content_digest: str
    projection_ref: str
    context_revision_ref: str
    branch_ref: str
    project_ref: str
    conversation_ref: str
    artifact_kind: str
    contribution_kind: str
    specialist_ref: str = ""
    laboratory_ref: str = ""
    security_scope: str = "scope:default"
    valid: bool = True
    superseded_by: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema != QDRANT_POINT_PROJECTION_SCHEMA:
            raise QdrantCanonicalProfileError("unsupported point projection schema")
        _require_text("point_id", self.point_id)
        for name in (
            "collection_profile_ref",
            "source_ref",
            "projection_ref",
            "context_revision_ref",
            "branch_ref",
            "project_ref",
            "conversation_ref",
            "security_scope",
        ):
            _require_typed_ref(name, getattr(self, name))
        _require_sha256("source_content_digest", self.source_content_digest)
        _require_identifier("vector_name", self.vector_name)
        _require_identifier("artifact_kind", self.artifact_kind)
        _require_identifier("contribution_kind", self.contribution_kind)
        for name in ("specialist_ref", "laboratory_ref", "superseded_by"):
            _require_typed_ref(name, getattr(self, name), optional=True)
        if not isinstance(self.valid, bool):
            raise QdrantCanonicalProfileError("valid must be a boolean")
        if self.valid and self.superseded_by:
            raise QdrantCanonicalProfileError(
                "a valid point must not declare superseded_by"
            )
        object.__setattr__(self, "metadata", _freeze_json(self.metadata))

    def qdrant_payload(self) -> dict[str, Any]:
        payload = {
            "sql_ref": self.source_ref,
            "source_ref": self.source_ref,
            "source_content_digest": self.source_content_digest,
            "context_revision_ref": self.context_revision_ref,
            "branch_ref": self.branch_ref,
            "project_ref": self.project_ref,
            "conversation_ref": self.conversation_ref,
            "artifact_kind": self.artifact_kind,
            "contribution_kind": self.contribution_kind,
            "specialist_ref": self.specialist_ref,
            "laboratory_ref": self.laboratory_ref,
            "security_scope": self.security_scope,
            "valid": self.valid,
            "superseded_by": self.superseded_by,
            "projection_ref": self.projection_ref,
        }
        payload.update(_thaw_json(self.metadata))
        forbidden = {"content", "body", "text", "vector", "embedding", "local_path"}
        collisions = sorted(forbidden.intersection(payload))
        if collisions:
            raise QdrantCanonicalProfileError(
                "raw or runtime payload fields are forbidden: " + ", ".join(collisions)
            )
        return payload

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "point_id": self.point_id,
            "collection_profile_ref": self.collection_profile_ref,
            "vector_name": self.vector_name,
            "payload": self.qdrant_payload(),
        }


@dataclass(frozen=True, slots=True)
class QdrantModelMigrationPlan:
    """A no-mutation plan for changing an embedding model or vector space."""

    schema: str
    migration_ref: str
    strategy: MigrationStrategy
    source_collection_profile_ref: str
    target_collection_profile_ref: str
    source_vector_name: str
    target_vector_name: str
    source_model_ref: str
    target_model_ref: str
    reembed_required: bool
    background_backfill_required: bool
    validation_required: bool
    operator_approval_required: bool
    alias_swap_required: bool
    delete_source_after_validation: bool = False

    def __post_init__(self) -> None:
        if self.schema != QDRANT_MODEL_MIGRATION_SCHEMA:
            raise QdrantCanonicalProfileError("unsupported migration schema")
        _require_typed_ref("migration_ref", self.migration_ref)
        if self.strategy not in _MIGRATION_STRATEGIES:
            raise QdrantCanonicalProfileError("unsupported migration strategy")
        for name in (
            "source_collection_profile_ref",
            "target_collection_profile_ref",
            "source_model_ref",
            "target_model_ref",
        ):
            _require_typed_ref(name, getattr(self, name))
        _require_identifier("source_vector_name", self.source_vector_name)
        _require_identifier("target_vector_name", self.target_vector_name)
        for name in (
            "reembed_required",
            "background_backfill_required",
            "validation_required",
            "operator_approval_required",
            "alias_swap_required",
            "delete_source_after_validation",
        ):
            if not isinstance(getattr(self, name), bool):
                raise QdrantCanonicalProfileError(f"{name} must be a boolean")
        if not self.reembed_required:
            raise QdrantCanonicalProfileError("model migration requires re-embedding")
        if not self.background_backfill_required:
            raise QdrantCanonicalProfileError("migration requires background backfill")
        if not self.validation_required or not self.operator_approval_required:
            raise QdrantCanonicalProfileError(
                "migration requires validation and operator approval"
            )
        if self.strategy == "named_vector" and self.alias_swap_required:
            raise QdrantCanonicalProfileError(
                "named-vector migration must not require an alias swap"
            )
        if self.strategy == "alias_swap" and not self.alias_swap_required:
            raise QdrantCanonicalProfileError(
                "alias-swap migration must require an alias swap"
            )
        if self.delete_source_after_validation:
            raise QdrantCanonicalProfileError(
                "source deletion is not part of the initial migration plan"
            )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "migration_ref": self.migration_ref,
            "strategy": self.strategy,
            "source_collection_profile_ref": self.source_collection_profile_ref,
            "target_collection_profile_ref": self.target_collection_profile_ref,
            "source_vector_name": self.source_vector_name,
            "target_vector_name": self.target_vector_name,
            "source_model_ref": self.source_model_ref,
            "target_model_ref": self.target_model_ref,
            "reembed_required": self.reembed_required,
            "background_backfill_required": self.background_backfill_required,
            "validation_required": self.validation_required,
            "operator_approval_required": self.operator_approval_required,
            "alias_swap_required": self.alias_swap_required,
            "delete_source_after_validation": self.delete_source_after_validation,
        }


def build_canonical_payload_indexes() -> tuple[QdrantPayloadIndexProfile, ...]:
    """Return the minimum payload indexes required before ingestion."""

    result = []
    for field_name, index_kind in CANONICAL_PAYLOAD_INDEXES:
        result.append(
            QdrantPayloadIndexProfile(
                schema=QDRANT_PAYLOAD_INDEX_SCHEMA,
                field_name=field_name,
                index_kind=index_kind,
                tenant_key=field_name == "project_ref",
                principal_key=field_name == "security_scope",
            )
        )
    return tuple(result)


def build_named_vector_from_embedding_profile(
    profile: Mapping[str, Any] | _ToMapping,
    *,
    vector_name: str,
    vector_kind: VectorKind = "dense",
) -> QdrantNamedVectorProfile:
    """Bridge the historical embedding-space profile into a named vector."""

    payload = _mapping(profile)
    if payload.get("schema") != EMBEDDING_SPACE_PROFILE_SCHEMA:
        raise QdrantCanonicalProfileError("unsupported embedding space profile")
    distance = payload.get("distance")
    return QdrantNamedVectorProfile(
        schema=QDRANT_NAMED_VECTOR_SCHEMA,
        vector_name=vector_name,
        vector_kind=vector_kind,
        embedding_profile_ref=_require_typed_ref("profile_ref", payload.get("profile_ref")),
        model_ref=_require_typed_ref("model_ref", payload.get("model_ref")),
        model_revision=_require_text("model_revision", payload.get("model_revision")),
        dimension=payload.get("dimension") if vector_kind != "sparse" else None,
        distance=distance if vector_kind != "sparse" else None,
        normalized=payload.get("normalized") if vector_kind != "sparse" else None,
        model_artifact_digest=str(payload.get("model_artifact_digest", "")),
        hnsw_enabled=vector_kind != "sparse",
        metadata={
            "backend_ref": payload.get("backend_ref", ""),
            "tokenizer_ref": payload.get("tokenizer_ref", ""),
            "role": payload.get("role", ""),
        },
    )


def build_point_projection_from_sql_metadata(
    projection: Mapping[str, Any] | _ToMapping,
    *,
    collection: QdrantCollectionProfile,
    context_revision_ref: str,
    branch_ref: str,
    project_ref: str,
    conversation_ref: str,
    artifact_kind: str,
    contribution_kind: str,
    specialist_ref: str = "",
    laboratory_ref: str = "",
    security_scope: str = "scope:default",
    valid: bool = True,
    superseded_by: str = "",
) -> QdrantPointProjection:
    """Create a reference-only point from SQL projection metadata."""

    payload = _mapping(projection)
    if payload.get("schema") != VECTOR_PROJECTION_METADATA_SCHEMA:
        raise QdrantCanonicalProfileError("unsupported SQL vector projection metadata")
    if payload.get("collection_name") != collection.collection_name:
        raise QdrantCanonicalProfileError("SQL projection collection does not match profile")
    vector_name = _require_identifier("vector_name", payload.get("vector_name"))
    vector = collection.vector(vector_name)
    if payload.get("embedding_profile_ref") != vector.embedding_profile_ref:
        raise QdrantCanonicalProfileError("embedding profile does not match named vector")
    if payload.get("model_ref") != vector.model_ref:
        raise QdrantCanonicalProfileError("model_ref does not match named vector")
    if payload.get("model_revision") != vector.model_revision:
        raise QdrantCanonicalProfileError("model_revision does not match named vector")
    if payload.get("dimension") != vector.dimension:
        raise QdrantCanonicalProfileError("dimension does not match named vector")
    if payload.get("normalized") != vector.normalized:
        raise QdrantCanonicalProfileError("normalization does not match named vector")
    return QdrantPointProjection(
        schema=QDRANT_POINT_PROJECTION_SCHEMA,
        point_id=_require_text("point_id", payload.get("point_id")),
        collection_profile_ref=collection.profile_ref,
        vector_name=vector_name,
        source_ref=_require_typed_ref("source_ref", payload.get("source_ref")),
        source_content_digest=_require_sha256(
            "source_content_digest", payload.get("source_content_digest")
        ),
        projection_ref=_require_typed_ref("projection_ref", payload.get("projection_ref")),
        context_revision_ref=context_revision_ref,
        branch_ref=branch_ref,
        project_ref=project_ref,
        conversation_ref=conversation_ref,
        artifact_kind=artifact_kind,
        contribution_kind=contribution_kind,
        specialist_ref=specialist_ref,
        laboratory_ref=laboratory_ref,
        security_scope=security_scope,
        valid=valid,
        superseded_by=superseded_by,
        metadata={
            "projection_state": payload.get("projection_state"),
            "projected_at": payload.get("projected_at"),
        },
    )


def choose_model_migration_strategy(
    source: QdrantCollectionProfile,
    target: QdrantCollectionProfile,
    *,
    source_vector_name: str,
    target_vector_name: str,
    migration_ref: str,
) -> QdrantModelMigrationPlan:
    """Select named-vector backfill or collection-alias swap deterministically."""

    source_vector = source.vector(source_vector_name)
    target_vector = target.vector(target_vector_name)
    shared_identity = (
        source.collection_name == target.collection_name
        and source.point_identity_field == target.point_identity_field
        and source.authority_ref_field == target.authority_ref_field
    )
    strategy: MigrationStrategy = "named_vector" if shared_identity else "alias_swap"
    return QdrantModelMigrationPlan(
        schema=QDRANT_MODEL_MIGRATION_SCHEMA,
        migration_ref=migration_ref,
        strategy=strategy,
        source_collection_profile_ref=source.profile_ref,
        target_collection_profile_ref=target.profile_ref,
        source_vector_name=source_vector.vector_name,
        target_vector_name=target_vector.vector_name,
        source_model_ref=source_vector.model_ref,
        target_model_ref=target_vector.model_ref,
        reembed_required=True,
        background_backfill_required=True,
        validation_required=True,
        operator_approval_required=True,
        alias_swap_required=strategy == "alias_swap",
    )


def build_canonical_profile_report(
    collection: QdrantCollectionProfile,
    *,
    migration_plans: Sequence[QdrantModelMigrationPlan] = (),
) -> dict[str, Any]:
    """Return a deterministic, inspection-only report for rules and tooling."""

    report = {
        "schema": QDRANT_PROFILE_REPORT_SCHEMA,
        "version": QDRANT_CANONICAL_PROFILE_VERSION,
        "collection_profile": collection.to_mapping(),
        "migration_plans": [item.to_mapping() for item in migration_plans],
        "boundaries": {
            "sql_remains_authority": True,
            "qdrant_is_reconstructible_projection": True,
            "raw_authoritative_content_in_payload": False,
            "qdrant_client_imported": False,
            "qdrant_write_performed": False,
            "openvino_call_performed": False,
            "scheduler_modified": False,
            "control_proxy_modified": False,
            "one_collection_per_task": False,
        },
    }
    report["profile_digest"] = _stable_digest(report)
    return report
