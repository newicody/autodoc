"""SQL-authoritative context revision graph for phase 0287-r7-r8-r2.

The historical ``SqlContextRecord`` and ``DbApiSqlContextStore`` remain
unchanged.  This module adds a versioned DB-API authority boundary for context
objects, immutable revisions, DAG lineage, relations, external artifacts and
vector-projection metadata.

SQL stores identities, content digests, relations, revision membership and
projection provenance.  Heavy bytes remain in content-addressed storage and
vectors remain in Qdrant.  The ControlProxy, Scheduler, OpenVINO and Qdrant are
not imported or invoked here.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any, Literal, Protocol
import hashlib
import json
import re
import sqlite3

from context.sql_context_store import SqlContextRecord, SqlContextStorePolicy

CONTEXT_SQL_AUTHORITY_VERSION = "0287.r7.r8.r2"
CONTEXT_AUTHORITY_OBJECT_SCHEMA = "missipy.context.authority_object.v1"
CONTEXT_ARTIFACT_DESCRIPTOR_SCHEMA = "missipy.context.artifact_descriptor.v1"
CONTEXT_RELATION_SCHEMA = "missipy.context.relation.v1"
CONTEXT_REVISION_MEMBERSHIP_SCHEMA = (
    "missipy.context.revision_membership.v1"
)
CONTEXT_REVISION_SCHEMA = "missipy.context.revision.v1"
VECTOR_PROJECTION_METADATA_SCHEMA = (
    "missipy.context.vector_projection_metadata.v1"
)
CONTEXT_REVISION_BUNDLE_SCHEMA = "missipy.context.revision_bundle.v1"
CONTEXT_SQL_WRITE_RESULT_SCHEMA = "missipy.context.sql_write_result.v1"

ContextMembershipState = Literal["active", "superseded", "invalidated"]
ContextRevisionStatus = Literal[
    "proposed",
    "accepted",
    "rejected",
    "superseded",
]
ContextSignificance = Literal["minor", "material", "critical"]
VectorProjectionState = Literal[
    "pending",
    "active",
    "stale",
    "failed",
    "deleted",
]

_MEMBERSHIP_STATES = frozenset({"active", "superseded", "invalidated"})
_REVISION_STATUSES = frozenset(
    {"proposed", "accepted", "rejected", "superseded"}
)
_SIGNIFICANCE_VALUES = frozenset({"minor", "material", "critical"})
_PROJECTION_STATES = frozenset(
    {"pending", "active", "stale", "failed", "deleted"}
)
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_IDENTIFIER_RE = re.compile(r"^[a-z][a-z0-9_.-]*$")
_JSON_SCALAR_TYPES = (str, int, float, bool, type(None))
_MAX_ITEMS = 100_000
_MAX_TEXT_CHARS = 4_000_000


class ContextSqlAuthorityError(ValueError):
    """Raised when an authority contract or immutable SQL write is invalid."""


class _Cursor(Protocol):
    def execute(
        self,
        sql: str,
        parameters: Sequence[object] = (),
    ) -> object: ...

    def fetchone(self) -> Sequence[object] | None: ...

    def fetchall(self) -> Sequence[Sequence[object]]: ...

    def close(self) -> object: ...


class _Connection(Protocol):
    def cursor(self) -> _Cursor: ...

    def commit(self) -> object: ...

    def rollback(self) -> object: ...

    def close(self) -> object: ...


@dataclass(frozen=True, slots=True)
class ContextAuthorityObject:
    """One durable, digest-addressed context object.

    Small text and structured metadata may remain in SQL.  Heavy content is
    referenced through ``storage_ref`` and is not copied into Scheduler events
    or vector payloads.
    """

    schema: str
    object_ref: str
    object_kind: str
    content_schema_ref: str
    content_digest: str
    title: str
    body: str = ""
    storage_ref: str | None = None
    media_type: str = "application/json"
    byte_count: int = 0
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema != CONTEXT_AUTHORITY_OBJECT_SCHEMA:
            raise ContextSqlAuthorityError(
                "unsupported context authority object schema"
            )
        _require_typed_ref("object_ref", self.object_ref)
        _require_identifier("object_kind", self.object_kind)
        _require_text("content_schema_ref", self.content_schema_ref)
        _require_sha256("content_digest", self.content_digest)
        _require_text("title", self.title)
        _require_optional_text("body", self.body)
        if self.storage_ref is not None:
            _require_typed_ref("storage_ref", self.storage_ref)
        _require_text("media_type", self.media_type)
        if not isinstance(self.byte_count, int) or isinstance(
            self.byte_count,
            bool,
        ):
            raise ContextSqlAuthorityError("byte_count must be an integer")
        if self.byte_count < 0:
            raise ContextSqlAuthorityError("byte_count must be >= 0")
        if not self.body and self.storage_ref is None:
            raise ContextSqlAuthorityError(
                "an authority object requires body or storage_ref"
            )
        object.__setattr__(self, "metadata", _freeze_json_mapping(self.metadata))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "object_ref": self.object_ref,
            "object_kind": self.object_kind,
            "content_schema_ref": self.content_schema_ref,
            "content_digest": self.content_digest,
            "title": self.title,
            "body": self.body,
            "storage_ref": self.storage_ref,
            "media_type": self.media_type,
            "byte_count": self.byte_count,
            "metadata": _thaw_json(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ContextArtifactDescriptor:
    """Metadata for one heavy or independently addressable artifact."""

    schema: str
    artifact_ref: str
    content_schema_ref: str
    content_digest: str
    storage_ref: str
    media_type: str
    byte_count: int
    producer_task_ref: str | None = None
    producer_specialist_ref: str | None = None
    producer_laboratory_ref: str | None = None
    created_at: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema != CONTEXT_ARTIFACT_DESCRIPTOR_SCHEMA:
            raise ContextSqlAuthorityError(
                "unsupported context artifact descriptor schema"
            )
        _require_typed_ref("artifact_ref", self.artifact_ref)
        _require_text("content_schema_ref", self.content_schema_ref)
        _require_sha256("content_digest", self.content_digest)
        _require_typed_ref("storage_ref", self.storage_ref)
        _require_text("media_type", self.media_type)
        if not isinstance(self.byte_count, int) or isinstance(
            self.byte_count,
            bool,
        ):
            raise ContextSqlAuthorityError("byte_count must be an integer")
        if self.byte_count < 0:
            raise ContextSqlAuthorityError("byte_count must be >= 0")
        for name in (
            "producer_task_ref",
            "producer_specialist_ref",
            "producer_laboratory_ref",
        ):
            value = getattr(self, name)
            if value is not None:
                _require_typed_ref(name, value)
        _require_text("created_at", self.created_at)
        object.__setattr__(self, "metadata", _freeze_json_mapping(self.metadata))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "artifact_ref": self.artifact_ref,
            "content_schema_ref": self.content_schema_ref,
            "content_digest": self.content_digest,
            "storage_ref": self.storage_ref,
            "media_type": self.media_type,
            "byte_count": self.byte_count,
            "producer_task_ref": self.producer_task_ref,
            "producer_specialist_ref": self.producer_specialist_ref,
            "producer_laboratory_ref": self.producer_laboratory_ref,
            "created_at": self.created_at,
            "metadata": _thaw_json(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ContextRelation:
    """One immutable graph edge between durable typed references."""

    schema: str
    relation_ref: str
    source_ref: str
    target_ref: str
    relation_kind: str
    context_revision_ref: str | None = None
    evidence_refs: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema != CONTEXT_RELATION_SCHEMA:
            raise ContextSqlAuthorityError("unsupported context relation schema")
        _require_typed_ref("relation_ref", self.relation_ref)
        _require_typed_ref("source_ref", self.source_ref)
        _require_typed_ref("target_ref", self.target_ref)
        if self.source_ref == self.target_ref:
            raise ContextSqlAuthorityError(
                "a context relation cannot target its source"
            )
        _require_identifier("relation_kind", self.relation_kind)
        if self.context_revision_ref is not None:
            _require_typed_ref(
                "context_revision_ref",
                self.context_revision_ref,
                required_prefix="context-revision:",
            )
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_refs("evidence_refs", self.evidence_refs),
        )
        object.__setattr__(self, "metadata", _freeze_json_mapping(self.metadata))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "relation_ref": self.relation_ref,
            "source_ref": self.source_ref,
            "target_ref": self.target_ref,
            "relation_kind": self.relation_kind,
            "context_revision_ref": self.context_revision_ref,
            "evidence_refs": list(self.evidence_refs),
            "metadata": _thaw_json(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ContextRevisionMembership:
    """Membership state of one object or artifact in one revision snapshot."""

    schema: str
    object_ref: str
    state: ContextMembershipState
    replacement_ref: str | None = None

    def __post_init__(self) -> None:
        if self.schema != CONTEXT_REVISION_MEMBERSHIP_SCHEMA:
            raise ContextSqlAuthorityError(
                "unsupported context revision membership schema"
            )
        _require_typed_ref("object_ref", self.object_ref)
        if self.state not in _MEMBERSHIP_STATES:
            raise ContextSqlAuthorityError("unsupported membership state")
        if self.replacement_ref is not None:
            _require_typed_ref("replacement_ref", self.replacement_ref)
        if self.state == "superseded" and self.replacement_ref is None:
            raise ContextSqlAuthorityError(
                "superseded membership requires replacement_ref"
            )
        if self.state != "superseded" and self.replacement_ref is not None:
            raise ContextSqlAuthorityError(
                "replacement_ref is reserved for superseded membership"
            )
        if self.replacement_ref == self.object_ref:
            raise ContextSqlAuthorityError(
                "replacement_ref must differ from object_ref"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "object_ref": self.object_ref,
            "state": self.state,
            "replacement_ref": self.replacement_ref,
        }


@dataclass(frozen=True, slots=True)
class ContextRevision:
    """One immutable semantic revision of a context DAG."""

    schema: str
    revision_ref: str
    context_ref: str
    parent_revision_refs: tuple[str, ...]
    memberships: tuple[ContextRevisionMembership, ...]
    validation_status: ContextRevisionStatus
    significance: ContextSignificance
    evidence_refs: tuple[str, ...] = ()
    producer_task_ref: str | None = None
    producer_specialist_ref: str | None = None
    producer_laboratory_ref: str | None = None
    created_at: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema != CONTEXT_REVISION_SCHEMA:
            raise ContextSqlAuthorityError("unsupported context revision schema")
        _require_typed_ref(
            "revision_ref",
            self.revision_ref,
            required_prefix="context-revision:",
        )
        _require_typed_ref("context_ref", self.context_ref)
        parents = _normalize_refs(
            "parent_revision_refs",
            self.parent_revision_refs,
            required_prefix="context-revision:",
        )
        if self.revision_ref in parents:
            raise ContextSqlAuthorityError(
                "a context revision cannot be its own parent"
            )
        object.__setattr__(self, "parent_revision_refs", parents)
        memberships = tuple(self.memberships)
        if len(memberships) > _MAX_ITEMS:
            raise ContextSqlAuthorityError("too many revision memberships")
        member_refs = tuple(item.object_ref for item in memberships)
        if len(member_refs) != len(set(member_refs)):
            raise ContextSqlAuthorityError(
                "revision membership object_refs must be unique"
            )
        object.__setattr__(self, "memberships", memberships)
        if self.validation_status not in _REVISION_STATUSES:
            raise ContextSqlAuthorityError("unsupported revision status")
        if self.significance not in _SIGNIFICANCE_VALUES:
            raise ContextSqlAuthorityError("unsupported significance value")
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_refs("evidence_refs", self.evidence_refs),
        )
        for name in (
            "producer_task_ref",
            "producer_specialist_ref",
            "producer_laboratory_ref",
        ):
            value = getattr(self, name)
            if value is not None:
                _require_typed_ref(name, value)
        _require_text("created_at", self.created_at)
        object.__setattr__(self, "metadata", _freeze_json_mapping(self.metadata))

    @property
    def revision_digest(self) -> str:
        return _sha256_mapping(self.to_mapping())

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "revision_ref": self.revision_ref,
            "context_ref": self.context_ref,
            "parent_revision_refs": list(self.parent_revision_refs),
            "memberships": [item.to_mapping() for item in self.memberships],
            "validation_status": self.validation_status,
            "significance": self.significance,
            "evidence_refs": list(self.evidence_refs),
            "producer_task_ref": self.producer_task_ref,
            "producer_specialist_ref": self.producer_specialist_ref,
            "producer_laboratory_ref": self.producer_laboratory_ref,
            "created_at": self.created_at,
            "metadata": _thaw_json(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class VectorProjectionMetadata:
    """Reconstructible Qdrant projection metadata without vector values."""

    schema: str
    projection_ref: str
    source_ref: str
    source_content_digest: str
    embedding_profile_ref: str
    model_ref: str
    model_revision: str
    dimension: int
    normalized: bool
    vector_name: str
    collection_name: str
    point_id: str
    projection_state: VectorProjectionState
    projected_at: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema != VECTOR_PROJECTION_METADATA_SCHEMA:
            raise ContextSqlAuthorityError(
                "unsupported vector projection metadata schema"
            )
        for name in (
            "projection_ref",
            "source_ref",
            "embedding_profile_ref",
            "model_ref",
        ):
            _require_typed_ref(name, getattr(self, name))
        _require_sha256("source_content_digest", self.source_content_digest)
        _require_text("model_revision", self.model_revision)
        if not isinstance(self.dimension, int) or isinstance(self.dimension, bool):
            raise ContextSqlAuthorityError("dimension must be an integer")
        if self.dimension <= 0:
            raise ContextSqlAuthorityError("dimension must be > 0")
        if not isinstance(self.normalized, bool):
            raise ContextSqlAuthorityError("normalized must be a boolean")
        _require_identifier("vector_name", self.vector_name)
        _require_text("collection_name", self.collection_name)
        _require_text("point_id", self.point_id)
        if self.projection_state not in _PROJECTION_STATES:
            raise ContextSqlAuthorityError("unsupported projection state")
        if self.projected_at is not None:
            _require_text("projected_at", self.projected_at)
        forbidden = {"vector", "values", "embedding", "raw_vector"}
        if forbidden.intersection(str(key) for key in self.metadata):
            raise ContextSqlAuthorityError(
                "projection metadata must not contain vector values"
            )
        object.__setattr__(self, "metadata", _freeze_json_mapping(self.metadata))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "projection_ref": self.projection_ref,
            "source_ref": self.source_ref,
            "source_content_digest": self.source_content_digest,
            "embedding_profile_ref": self.embedding_profile_ref,
            "model_ref": self.model_ref,
            "model_revision": self.model_revision,
            "dimension": self.dimension,
            "normalized": self.normalized,
            "vector_name": self.vector_name,
            "collection_name": self.collection_name,
            "point_id": self.point_id,
            "projection_state": self.projection_state,
            "projected_at": self.projected_at,
            "metadata": _thaw_json(self.metadata),
            "vector_values_stored": False,
        }


@dataclass(frozen=True, slots=True)
class ContextSqlWriteResult:
    """Stable result for one immutable authority write."""

    entity_kind: str
    entity_ref: str
    inserted: bool
    idempotent_replay: bool

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": CONTEXT_SQL_WRITE_RESULT_SCHEMA,
            "entity_kind": self.entity_kind,
            "entity_ref": self.entity_ref,
            "inserted": self.inserted,
            "idempotent_replay": self.idempotent_replay,
        }


@dataclass(frozen=True, slots=True)
class ContextRevisionBundle:
    """Readback of one revision and its normalized authority references."""

    revision: ContextRevision
    objects: tuple[ContextAuthorityObject, ...]
    artifacts: tuple[ContextArtifactDescriptor, ...]
    relations: tuple[ContextRelation, ...]
    projections: tuple[VectorProjectionMetadata, ...]

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": CONTEXT_REVISION_BUNDLE_SCHEMA,
            "revision": self.revision.to_mapping(),
            "objects": [item.to_mapping() for item in self.objects],
            "artifacts": [item.to_mapping() for item in self.artifacts],
            "relations": [item.to_mapping() for item in self.relations],
            "projections": [item.to_mapping() for item in self.projections],
            "sql_is_authority": True,
            "qdrant_is_projection_only": True,
            "vector_values_stored_in_sql": False,
        }


class DbApiContextRevisionAuthorityStore:
    """DB-API context revision authority over an injected connection."""

    def __init__(
        self,
        connection: _Connection,
        policy: SqlContextStorePolicy | None = None,
    ) -> None:
        self._connection = connection
        self._policy = policy or SqlContextStorePolicy()

    @property
    def policy(self) -> SqlContextStorePolicy:
        return self._policy

    def initialize_schema(self) -> None:
        statements = (
            """
            CREATE TABLE IF NOT EXISTS context_authority_objects (
                object_ref TEXT PRIMARY KEY,
                object_kind TEXT NOT NULL,
                content_digest TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS context_artifact_descriptors (
                artifact_ref TEXT PRIMARY KEY,
                content_digest TEXT NOT NULL,
                storage_ref TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS context_revisions (
                revision_ref TEXT PRIMARY KEY,
                context_ref TEXT NOT NULL,
                revision_digest TEXT NOT NULL,
                validation_status TEXT NOT NULL,
                significance TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS context_revision_parents (
                revision_ref TEXT NOT NULL,
                ordinal INTEGER NOT NULL,
                parent_revision_ref TEXT NOT NULL,
                PRIMARY KEY (revision_ref, parent_revision_ref)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS context_revision_memberships (
                revision_ref TEXT NOT NULL,
                object_ref TEXT NOT NULL,
                state TEXT NOT NULL,
                replacement_ref TEXT,
                PRIMARY KEY (revision_ref, object_ref)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS context_relations (
                relation_ref TEXT PRIMARY KEY,
                source_ref TEXT NOT NULL,
                target_ref TEXT NOT NULL,
                relation_kind TEXT NOT NULL,
                context_revision_ref TEXT,
                payload_json TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS context_vector_projections (
                projection_ref TEXT PRIMARY KEY,
                source_ref TEXT NOT NULL,
                embedding_profile_ref TEXT NOT NULL,
                collection_name TEXT NOT NULL,
                vector_name TEXT NOT NULL,
                point_id TEXT NOT NULL,
                projection_state TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_context_revision_context
            ON context_revisions(context_ref)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_context_revision_parent
            ON context_revision_parents(parent_revision_ref)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_context_membership_object
            ON context_revision_memberships(object_ref)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_context_relation_revision
            ON context_relations(context_revision_ref)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_context_projection_source
            ON context_vector_projections(source_ref)
            """,
        )
        for statement in statements:
            self._execute(statement)
        self._commit_if_needed()

    def put_object(
        self,
        item: ContextAuthorityObject,
    ) -> ContextSqlWriteResult:
        return self._immutable_insert(
            table="context_authority_objects",
            key_column="object_ref",
            key_value=item.object_ref,
            entity_kind="context_object",
            columns={
                "object_ref": item.object_ref,
                "object_kind": item.object_kind,
                "content_digest": item.content_digest,
                "payload_json": _canonical_json(item.to_mapping()),
            },
        )

    def get_object(self, object_ref: str) -> ContextAuthorityObject | None:
        payload = self._get_payload(
            "context_authority_objects",
            "object_ref",
            object_ref,
        )
        return None if payload is None else _authority_object_from_mapping(payload)

    def put_artifact(
        self,
        item: ContextArtifactDescriptor,
    ) -> ContextSqlWriteResult:
        return self._immutable_insert(
            table="context_artifact_descriptors",
            key_column="artifact_ref",
            key_value=item.artifact_ref,
            entity_kind="artifact_descriptor",
            columns={
                "artifact_ref": item.artifact_ref,
                "content_digest": item.content_digest,
                "storage_ref": item.storage_ref,
                "payload_json": _canonical_json(item.to_mapping()),
            },
        )

    def get_artifact(
        self,
        artifact_ref: str,
    ) -> ContextArtifactDescriptor | None:
        payload = self._get_payload(
            "context_artifact_descriptors",
            "artifact_ref",
            artifact_ref,
        )
        return None if payload is None else _artifact_from_mapping(payload)

    def put_relation(self, item: ContextRelation) -> ContextSqlWriteResult:
        if item.context_revision_ref is not None:
            self._require_revision(item.context_revision_ref)
        return self._immutable_insert(
            table="context_relations",
            key_column="relation_ref",
            key_value=item.relation_ref,
            entity_kind="context_relation",
            columns={
                "relation_ref": item.relation_ref,
                "source_ref": item.source_ref,
                "target_ref": item.target_ref,
                "relation_kind": item.relation_kind,
                "context_revision_ref": item.context_revision_ref,
                "payload_json": _canonical_json(item.to_mapping()),
            },
        )

    def get_relation(self, relation_ref: str) -> ContextRelation | None:
        payload = self._get_payload(
            "context_relations",
            "relation_ref",
            relation_ref,
        )
        return None if payload is None else _relation_from_mapping(payload)

    def put_revision(self, item: ContextRevision) -> ContextSqlWriteResult:
        existing = self.get_revision(item.revision_ref)
        if existing is not None:
            if existing.to_mapping() != item.to_mapping():
                raise ContextSqlAuthorityError(
                    "immutable context revision collision"
                )
            return ContextSqlWriteResult(
                entity_kind="context_revision",
                entity_ref=item.revision_ref,
                inserted=False,
                idempotent_replay=True,
            )
        for parent_ref in item.parent_revision_refs:
            self._require_revision(parent_ref)
        for membership in item.memberships:
            self._require_authority_reference(membership.object_ref)
            if membership.replacement_ref is not None:
                self._require_authority_reference(membership.replacement_ref)
        payload_json = _canonical_json(item.to_mapping())
        try:
            self._insert_columns(
                "context_revisions",
                {
                    "revision_ref": item.revision_ref,
                    "context_ref": item.context_ref,
                    "revision_digest": item.revision_digest,
                    "validation_status": item.validation_status,
                    "significance": item.significance,
                    "created_at": item.created_at,
                    "payload_json": payload_json,
                },
            )
            for ordinal, parent_ref in enumerate(item.parent_revision_refs):
                self._insert_columns(
                    "context_revision_parents",
                    {
                        "revision_ref": item.revision_ref,
                        "ordinal": ordinal,
                        "parent_revision_ref": parent_ref,
                    },
                )
            for membership in item.memberships:
                self._insert_columns(
                    "context_revision_memberships",
                    {
                        "revision_ref": item.revision_ref,
                        "object_ref": membership.object_ref,
                        "state": membership.state,
                        "replacement_ref": membership.replacement_ref,
                    },
                )
            self._commit_if_needed()
        except Exception:
            self._rollback_if_possible()
            raise
        return ContextSqlWriteResult(
            entity_kind="context_revision",
            entity_ref=item.revision_ref,
            inserted=True,
            idempotent_replay=False,
        )

    def get_revision(self, revision_ref: str) -> ContextRevision | None:
        payload = self._get_payload(
            "context_revisions",
            "revision_ref",
            revision_ref,
        )
        return None if payload is None else _revision_from_mapping(payload)

    def list_context_revisions(
        self,
        context_ref: str,
    ) -> tuple[ContextRevision, ...]:
        _require_typed_ref("context_ref", context_ref)
        p = self._placeholder
        rows = self._fetchall(
            "SELECT payload_json FROM context_revisions "
            f"WHERE context_ref = {p} ORDER BY created_at, revision_ref",
            (context_ref,),
        )
        return tuple(
            _revision_from_mapping(_decode_payload(row[0])) for row in rows
        )

    def put_projection(
        self,
        item: VectorProjectionMetadata,
    ) -> ContextSqlWriteResult:
        self._require_authority_reference(item.source_ref)
        source_digest = self._authority_content_digest(item.source_ref)
        if source_digest != item.source_content_digest:
            raise ContextSqlAuthorityError(
                "projection source digest does not match SQL authority"
            )
        return self._immutable_insert(
            table="context_vector_projections",
            key_column="projection_ref",
            key_value=item.projection_ref,
            entity_kind="vector_projection_metadata",
            columns={
                "projection_ref": item.projection_ref,
                "source_ref": item.source_ref,
                "embedding_profile_ref": item.embedding_profile_ref,
                "collection_name": item.collection_name,
                "vector_name": item.vector_name,
                "point_id": item.point_id,
                "projection_state": item.projection_state,
                "payload_json": _canonical_json(item.to_mapping()),
            },
        )

    def get_projection(
        self,
        projection_ref: str,
    ) -> VectorProjectionMetadata | None:
        payload = self._get_payload(
            "context_vector_projections",
            "projection_ref",
            projection_ref,
        )
        return None if payload is None else _projection_from_mapping(payload)

    def read_revision_bundle(self, revision_ref: str) -> ContextRevisionBundle:
        revision = self.get_revision(revision_ref)
        if revision is None:
            raise ContextSqlAuthorityError("context revision does not exist")
        objects: list[ContextAuthorityObject] = []
        artifacts: list[ContextArtifactDescriptor] = []
        for membership in revision.memberships:
            authority_object = self.get_object(membership.object_ref)
            if authority_object is not None:
                objects.append(authority_object)
                continue
            artifact = self.get_artifact(membership.object_ref)
            if artifact is not None:
                artifacts.append(artifact)
                continue
            raise ContextSqlAuthorityError(
                "revision membership cannot be rehydrated"
            )
        p = self._placeholder
        relation_rows = self._fetchall(
            "SELECT payload_json FROM context_relations "
            f"WHERE context_revision_ref = {p} ORDER BY relation_ref",
            (revision_ref,),
        )
        relations = tuple(
            _relation_from_mapping(_decode_payload(row[0]))
            for row in relation_rows
        )
        member_refs = tuple(item.object_ref for item in revision.memberships)
        projections: list[VectorProjectionMetadata] = []
        for source_ref in member_refs:
            rows = self._fetchall(
                "SELECT payload_json FROM context_vector_projections "
                f"WHERE source_ref = {p} ORDER BY projection_ref",
                (source_ref,),
            )
            projections.extend(
                _projection_from_mapping(_decode_payload(row[0]))
                for row in rows
            )
        return ContextRevisionBundle(
            revision=revision,
            objects=tuple(sorted(objects, key=lambda item: item.object_ref)),
            artifacts=tuple(
                sorted(artifacts, key=lambda item: item.artifact_ref)
            ),
            relations=relations,
            projections=tuple(projections),
        )

    def close(self) -> None:
        self._connection.close()

    @property
    def _placeholder(self) -> str:
        return "?" if self._policy.paramstyle == "qmark" else "%s"

    def _immutable_insert(
        self,
        *,
        table: str,
        key_column: str,
        key_value: str,
        entity_kind: str,
        columns: Mapping[str, object],
    ) -> ContextSqlWriteResult:
        existing = self._get_payload(table, key_column, key_value)
        incoming = _decode_payload(str(columns["payload_json"]))
        if existing is not None:
            if existing != incoming:
                raise ContextSqlAuthorityError(
                    f"immutable {entity_kind} collision"
                )
            return ContextSqlWriteResult(
                entity_kind=entity_kind,
                entity_ref=key_value,
                inserted=False,
                idempotent_replay=True,
            )
        self._insert_columns(table, columns)
        self._commit_if_needed()
        return ContextSqlWriteResult(
            entity_kind=entity_kind,
            entity_ref=key_value,
            inserted=True,
            idempotent_replay=False,
        )

    def _insert_columns(
        self,
        table: str,
        columns: Mapping[str, object],
    ) -> None:
        names = tuple(columns)
        placeholders = ", ".join(self._placeholder for _ in names)
        sql = (
            f"INSERT INTO {table} ({', '.join(names)}) "
            f"VALUES ({placeholders})"
        )
        self._execute(sql, tuple(columns[name] for name in names))

    def _get_payload(
        self,
        table: str,
        key_column: str,
        key_value: str,
    ) -> Mapping[str, Any] | None:
        p = self._placeholder
        row = self._fetchone(
            f"SELECT payload_json FROM {table} WHERE {key_column} = {p}",
            (key_value,),
        )
        return None if row is None else _decode_payload(row[0])

    def _require_revision(self, revision_ref: str) -> None:
        if self.get_revision(revision_ref) is None:
            raise ContextSqlAuthorityError(
                f"unknown parent context revision: {revision_ref}"
            )

    def _require_authority_reference(self, item_ref: str) -> None:
        if self.get_object(item_ref) is None and self.get_artifact(item_ref) is None:
            raise ContextSqlAuthorityError(
                f"unknown SQL authority reference: {item_ref}"
            )

    def _authority_content_digest(self, item_ref: str) -> str:
        authority_object = self.get_object(item_ref)
        if authority_object is not None:
            return authority_object.content_digest
        artifact = self.get_artifact(item_ref)
        if artifact is not None:
            return artifact.content_digest
        raise ContextSqlAuthorityError(
            f"unknown SQL authority reference: {item_ref}"
        )

    def _execute(
        self,
        sql: str,
        parameters: Sequence[object] = (),
    ) -> None:
        cursor = self._connection.cursor()
        try:
            cursor.execute(sql, parameters)
        finally:
            cursor.close()

    def _fetchone(
        self,
        sql: str,
        parameters: Sequence[object],
    ) -> Sequence[object] | None:
        cursor = self._connection.cursor()
        try:
            cursor.execute(sql, parameters)
            return cursor.fetchone()
        finally:
            cursor.close()

    def _fetchall(
        self,
        sql: str,
        parameters: Sequence[object],
    ) -> Sequence[Sequence[object]]:
        cursor = self._connection.cursor()
        try:
            cursor.execute(sql, parameters)
            return cursor.fetchall()
        finally:
            cursor.close()

    def _commit_if_needed(self) -> None:
        if self._policy.auto_commit:
            self._connection.commit()

    def _rollback_if_possible(self) -> None:
        rollback = getattr(self._connection, "rollback", None)
        if callable(rollback):
            rollback()


class SQLiteContextRevisionAuthorityStore(DbApiContextRevisionAuthorityStore):
    """SQLite convenience authority for tests and local dry runs."""

    def __init__(self, path: str | Path = ":memory:") -> None:
        self.path = path
        connection = sqlite3.connect(str(path))
        super().__init__(
            connection,
            SqlContextStorePolicy(paramstyle="qmark", auto_commit=True),
        )


def build_authority_object_from_sql_context_record(
    record: SqlContextRecord,
) -> ContextAuthorityObject:
    """Bridge one historical v1 SQL record into the revision authority."""

    payload = record.to_mapping()
    body = str(payload["body"])
    return ContextAuthorityObject(
        schema=CONTEXT_AUTHORITY_OBJECT_SCHEMA,
        object_ref=record.context_ref,
        object_kind=record.kind,
        content_schema_ref=str(payload["schema"]),
        content_digest=_sha256_mapping(payload),
        title=record.title,
        body=body,
        media_type="application/json",
        byte_count=len(body.encode("utf-8")),
        metadata={
            "legacy_sql_context_store_schema": str(payload["schema"]),
            "legacy_parent_ref": record.parent_ref,
            "legacy_metadata": dict(record.metadata),
        },
    )


def build_context_revision_ref(
    *,
    context_ref: str,
    parent_revision_refs: Sequence[str],
    memberships: Sequence[ContextRevisionMembership],
    validation_status: ContextRevisionStatus,
    significance: ContextSignificance,
) -> str:
    """Build a deterministic revision reference from semantic identity."""

    _require_typed_ref("context_ref", context_ref)
    payload = {
        "context_ref": context_ref,
        "parent_revision_refs": list(parent_revision_refs),
        "memberships": [item.to_mapping() for item in memberships],
        "validation_status": validation_status,
        "significance": significance,
    }
    digest = hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()
    return f"context-revision:{digest[:32]}"


def _authority_object_from_mapping(
    payload: Mapping[str, Any],
) -> ContextAuthorityObject:
    return ContextAuthorityObject(
        schema=str(payload.get("schema", "")),
        object_ref=str(payload.get("object_ref", "")),
        object_kind=str(payload.get("object_kind", "")),
        content_schema_ref=str(payload.get("content_schema_ref", "")),
        content_digest=str(payload.get("content_digest", "")),
        title=str(payload.get("title", "")),
        body=str(payload.get("body", "")),
        storage_ref=_optional_str(payload.get("storage_ref")),
        media_type=str(payload.get("media_type", "")),
        byte_count=_as_int(payload.get("byte_count"), "byte_count"),
        metadata=_mapping(payload.get("metadata")),
    )


def _artifact_from_mapping(
    payload: Mapping[str, Any],
) -> ContextArtifactDescriptor:
    return ContextArtifactDescriptor(
        schema=str(payload.get("schema", "")),
        artifact_ref=str(payload.get("artifact_ref", "")),
        content_schema_ref=str(payload.get("content_schema_ref", "")),
        content_digest=str(payload.get("content_digest", "")),
        storage_ref=str(payload.get("storage_ref", "")),
        media_type=str(payload.get("media_type", "")),
        byte_count=_as_int(payload.get("byte_count"), "byte_count"),
        producer_task_ref=_optional_str(payload.get("producer_task_ref")),
        producer_specialist_ref=_optional_str(
            payload.get("producer_specialist_ref")
        ),
        producer_laboratory_ref=_optional_str(
            payload.get("producer_laboratory_ref")
        ),
        created_at=str(payload.get("created_at", "")),
        metadata=_mapping(payload.get("metadata")),
    )


def _relation_from_mapping(payload: Mapping[str, Any]) -> ContextRelation:
    return ContextRelation(
        schema=str(payload.get("schema", "")),
        relation_ref=str(payload.get("relation_ref", "")),
        source_ref=str(payload.get("source_ref", "")),
        target_ref=str(payload.get("target_ref", "")),
        relation_kind=str(payload.get("relation_kind", "")),
        context_revision_ref=_optional_str(
            payload.get("context_revision_ref")
        ),
        evidence_refs=_string_tuple(payload.get("evidence_refs")),
        metadata=_mapping(payload.get("metadata")),
    )


def _membership_from_mapping(
    payload: Mapping[str, Any],
) -> ContextRevisionMembership:
    return ContextRevisionMembership(
        schema=str(payload.get("schema", "")),
        object_ref=str(payload.get("object_ref", "")),
        state=str(payload.get("state", "")),
        replacement_ref=_optional_str(payload.get("replacement_ref")),
    )


def _revision_from_mapping(payload: Mapping[str, Any]) -> ContextRevision:
    memberships_raw = payload.get("memberships")
    if not isinstance(memberships_raw, list):
        raise ContextSqlAuthorityError("revision memberships must be a list")
    return ContextRevision(
        schema=str(payload.get("schema", "")),
        revision_ref=str(payload.get("revision_ref", "")),
        context_ref=str(payload.get("context_ref", "")),
        parent_revision_refs=_string_tuple(
            payload.get("parent_revision_refs")
        ),
        memberships=tuple(
            _membership_from_mapping(_mapping(item)) for item in memberships_raw
        ),
        validation_status=str(payload.get("validation_status", "")),
        significance=str(payload.get("significance", "")),
        evidence_refs=_string_tuple(payload.get("evidence_refs")),
        producer_task_ref=_optional_str(payload.get("producer_task_ref")),
        producer_specialist_ref=_optional_str(
            payload.get("producer_specialist_ref")
        ),
        producer_laboratory_ref=_optional_str(
            payload.get("producer_laboratory_ref")
        ),
        created_at=str(payload.get("created_at", "")),
        metadata=_mapping(payload.get("metadata")),
    )


def _projection_from_mapping(
    payload: Mapping[str, Any],
) -> VectorProjectionMetadata:
    return VectorProjectionMetadata(
        schema=str(payload.get("schema", "")),
        projection_ref=str(payload.get("projection_ref", "")),
        source_ref=str(payload.get("source_ref", "")),
        source_content_digest=str(
            payload.get("source_content_digest", "")
        ),
        embedding_profile_ref=str(payload.get("embedding_profile_ref", "")),
        model_ref=str(payload.get("model_ref", "")),
        model_revision=str(payload.get("model_revision", "")),
        dimension=_as_int(payload.get("dimension"), "dimension"),
        normalized=_as_bool(payload.get("normalized"), "normalized"),
        vector_name=str(payload.get("vector_name", "")),
        collection_name=str(payload.get("collection_name", "")),
        point_id=str(payload.get("point_id", "")),
        projection_state=str(payload.get("projection_state", "")),
        projected_at=_optional_str(payload.get("projected_at")),
        metadata=_mapping(payload.get("metadata")),
    )


def _normalize_refs(
    name: str,
    values: Sequence[str],
    *,
    required_prefix: str | None = None,
) -> tuple[str, ...]:
    normalized = tuple(str(value) for value in values)
    if len(normalized) > _MAX_ITEMS:
        raise ContextSqlAuthorityError(f"{name} contains too many values")
    if len(normalized) != len(set(normalized)):
        raise ContextSqlAuthorityError(f"{name} must contain unique values")
    for value in normalized:
        _require_typed_ref(name, value, required_prefix=required_prefix)
    return normalized


def _freeze_json_mapping(value: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ContextSqlAuthorityError("metadata must be a mapping")
    return MappingProxyType(
        {
            str(key): _freeze_json(item)
            for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))
        }
    )


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _freeze_json_mapping(value)
    if isinstance(value, (list, tuple)):
        if len(value) > _MAX_ITEMS:
            raise ContextSqlAuthorityError("JSON sequence contains too many values")
        return tuple(_freeze_json(item) for item in value)
    if isinstance(value, _JSON_SCALAR_TYPES):
        return value
    raise ContextSqlAuthorityError("metadata must be JSON-compatible")


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _decode_payload(value: object) -> Mapping[str, Any]:
    if not isinstance(value, str):
        raise ContextSqlAuthorityError("SQL payload_json must be text")
    decoded = json.loads(value)
    if not isinstance(decoded, dict):
        raise ContextSqlAuthorityError("SQL payload_json must decode to an object")
    return decoded


def _mapping(value: object) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ContextSqlAuthorityError("value must be a mapping")
    return value


def _string_tuple(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise ContextSqlAuthorityError("value must be a list of strings")
    if not all(isinstance(item, str) for item in value):
        raise ContextSqlAuthorityError("value must be a list of strings")
    return tuple(value)


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ContextSqlAuthorityError("optional value must be text")
    return value


def _as_int(value: object, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ContextSqlAuthorityError(f"{name} must be an integer")
    return value


def _as_bool(value: object, name: str) -> bool:
    if not isinstance(value, bool):
        raise ContextSqlAuthorityError(f"{name} must be a boolean")
    return value


def _require_typed_ref(
    name: str,
    value: str,
    *,
    required_prefix: str | None = None,
) -> None:
    _require_text(name, value)
    if required_prefix is not None and not value.startswith(required_prefix):
        raise ContextSqlAuthorityError(
            f"{name} must start with {required_prefix}"
        )
    if not _TYPED_REF_RE.match(value):
        raise ContextSqlAuthorityError(f"{name} must be a typed reference")


def _require_identifier(name: str, value: str) -> None:
    _require_text(name, value)
    if not _IDENTIFIER_RE.match(value):
        raise ContextSqlAuthorityError(f"{name} must be a stable identifier")


def _require_sha256(name: str, value: str) -> None:
    if not _SHA256_RE.match(value):
        raise ContextSqlAuthorityError(f"{name} must be sha256:<64 lowercase hex>")


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ContextSqlAuthorityError(f"{name} must not be empty")
    if len(value) > _MAX_TEXT_CHARS:
        raise ContextSqlAuthorityError(f"{name} is too large")


def _require_optional_text(name: str, value: str) -> None:
    if not isinstance(value, str):
        raise ContextSqlAuthorityError(f"{name} must be text")
    if len(value) > _MAX_TEXT_CHARS:
        raise ContextSqlAuthorityError(f"{name} is too large")


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        _thaw_json(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256_mapping(value: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()
    return f"sha256:{digest}"
