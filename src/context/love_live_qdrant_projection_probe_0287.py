"""Controlled one-object SQL -> OpenVINO -> Qdrant projection probe.

The module contains no resource construction.  It coordinates already-opened
ports, persists only reconstructible projection metadata in SQL, reads the
Qdrant point back without vectors and proves that SQL can rehydrate the source.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import hashlib
import json
from types import MappingProxyType
from typing import Any, Protocol, runtime_checkable

from context.context_revision_sql_authority_0287 import (
    ContextAuthorityObject,
    ContextRevision,
    ContextSqlWriteResult,
    VectorProjectionMetadata,
)

LOVE_LIVE_QDRANT_PROJECTION_PROBE_SCHEMA = (
    "missipy.love.live_qdrant_projection_probe.v1"
)
LOVE_LIVE_QDRANT_PROJECTION_PLAN_SCHEMA = (
    "missipy.love.live_qdrant_projection_plan.v1"
)
LOVE_LIVE_QDRANT_PROJECTION_READINESS_SCHEMA = (
    "missipy.love.live_qdrant_projection_readiness.v1"
)
LOVE_LIVE_QDRANT_PROJECTION_RECEIPT_SCHEMA = (
    "missipy.love.live_qdrant_projection_receipt.v1"
)


class LoveLiveQdrantProjectionProbeError(RuntimeError):
    """Raised when the controlled live projection probe cannot fail closed."""


@runtime_checkable
class ProjectionAuthorityStore(Protocol):
    """Narrow subset of the existing SQL authority store used by the probe."""

    def get_object(self, object_ref: str) -> ContextAuthorityObject | None: ...

    def get_revision(self, revision_ref: str) -> ContextRevision | None: ...

    def put_projection(
        self,
        item: VectorProjectionMetadata,
    ) -> ContextSqlWriteResult: ...

    def get_projection(
        self,
        projection_ref: str,
    ) -> VectorProjectionMetadata | None: ...


@runtime_checkable
class LiveAnalysisProjectionPort(Protocol):
    """Existing asynchronous projection operation supplied by r11."""

    async def project(
        self,
        authority_object: ContextAuthorityObject,
        *,
        revision: ContextRevision,
        branch_ref: str,
        project_ref: str,
        conversation_ref: str,
        specialist_ref: str,
        laboratory_ref: str,
        security_scope: str,
        projected_at: str | None = None,
    ) -> Any: ...


@runtime_checkable
class ReferencePointReader(Protocol):
    """Qdrant readback port returning references only and no vectors."""

    def read_named_reference_point(
        self,
        *,
        collection_name: str,
        point_id: str,
    ) -> object | None: ...


@dataclass(frozen=True, slots=True)
class LoveLiveProjectionProbeRequest:
    """Stable identities for one operator-selected authority object."""

    object_ref: str
    revision_ref: str
    branch_ref: str
    project_ref: str
    conversation_ref: str
    specialist_ref: str
    laboratory_ref: str
    security_scope: str
    projected_at: str = ""

    def __post_init__(self) -> None:
        for name in (
            "object_ref",
            "revision_ref",
            "branch_ref",
            "project_ref",
            "conversation_ref",
            "specialist_ref",
            "laboratory_ref",
            "security_scope",
        ):
            _require_typed_ref(name, getattr(self, name))
        if not self.revision_ref.startswith("context-revision:"):
            raise LoveLiveQdrantProjectionProbeError(
                "revision_ref must start with context-revision:"
            )
        if self.projected_at and not self.projected_at.strip():
            raise LoveLiveQdrantProjectionProbeError(
                "projected_at must be empty or non-blank"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "object_ref": self.object_ref,
            "revision_ref": self.revision_ref,
            "branch_ref": self.branch_ref,
            "project_ref": self.project_ref,
            "conversation_ref": self.conversation_ref,
            "specialist_ref": self.specialist_ref,
            "laboratory_ref": self.laboratory_ref,
            "security_scope": self.security_scope,
            "projected_at": self.projected_at,
        }


@dataclass(frozen=True, slots=True)
class LoveLiveProjectionProbePlan:
    """Digest-confirmed plan for one live named-vector projection."""

    schema: str
    request: LoveLiveProjectionProbeRequest
    collection_name: str
    dense_vector_name: str
    sparse_vector_name: str
    model_ref: str
    model_revision: str
    dimension: int = 384

    def __post_init__(self) -> None:
        if self.schema != LOVE_LIVE_QDRANT_PROJECTION_PLAN_SCHEMA:
            raise LoveLiveQdrantProjectionProbeError(
                "unsupported live projection plan schema"
            )
        for name in (
            "collection_name",
            "dense_vector_name",
            "sparse_vector_name",
            "model_ref",
            "model_revision",
        ):
            if not str(getattr(self, name)).strip():
                raise LoveLiveQdrantProjectionProbeError(
                    f"{name} must be non-empty"
                )
        if self.dense_vector_name == self.sparse_vector_name:
            raise LoveLiveQdrantProjectionProbeError(
                "dense and sparse vector names must differ"
            )
        if self.dimension != 384:
            raise LoveLiveQdrantProjectionProbeError(
                "multilingual-e5-small dimension must be 384"
            )

    @property
    def plan_digest(self) -> str:
        encoded = json.dumps(
            self._unsigned_mapping(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return "sha256:" + hashlib.sha256(encoded).hexdigest()

    def _unsigned_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "request": self.request.to_mapping(),
            "collection_name": self.collection_name,
            "dense_vector_name": self.dense_vector_name,
            "sparse_vector_name": self.sparse_vector_name,
            "model_ref": self.model_ref,
            "model_revision": self.model_revision,
            "dimension": self.dimension,
            "boundaries": {
                "one_object_only": True,
                "reference_only_qdrant_payload": True,
                "qdrant_vectors_omitted_from_readback": True,
                "sql_remains_authority": True,
                "delete_allowed": False,
                "alias_mutation_allowed": False,
            },
        }

    def to_mapping(self) -> dict[str, object]:
        return {
            **self._unsigned_mapping(),
            "plan_digest": self.plan_digest,
        }


@dataclass(frozen=True, slots=True)
class LoveLiveProjectionProbeGate:
    """Three-part operator gate for a single Qdrant point mutation."""

    policy_decision_id: str
    operator_decision: str
    allow_write: bool
    confirm_plan_digest: str

    def __post_init__(self) -> None:
        if not self.policy_decision_id.startswith("policy:"):
            raise LoveLiveQdrantProjectionProbeError(
                "policy_decision_id must start with policy:"
            )
        if self.operator_decision not in {"approve", "reject"}:
            raise LoveLiveQdrantProjectionProbeError(
                "operator_decision must be approve or reject"
            )

    def require_allows(self, plan: LoveLiveProjectionProbePlan) -> None:
        if not self.allow_write:
            raise LoveLiveQdrantProjectionProbeError(
                "live Qdrant point write is not enabled"
            )
        if self.operator_decision != "approve":
            raise LoveLiveQdrantProjectionProbeError(
                "operator did not approve live projection"
            )
        if self.confirm_plan_digest != plan.plan_digest:
            raise LoveLiveQdrantProjectionProbeError(
                "confirmed plan digest differs from live projection plan"
            )


@dataclass(frozen=True, slots=True)
class LoveLiveProjectionProbeReadiness:
    """Read-only SQL validation performed before OpenVINO/Qdrant construction."""

    schema: str
    plan_digest: str
    ready: bool
    issues: tuple[str, ...]
    object_ref: str
    revision_ref: str
    object_content_digest: str
    boundaries: Mapping[str, bool] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema != LOVE_LIVE_QDRANT_PROJECTION_READINESS_SCHEMA:
            raise LoveLiveQdrantProjectionProbeError(
                "unsupported live projection readiness schema"
            )
        object.__setattr__(self, "issues", tuple(self.issues))
        object.__setattr__(
            self,
            "boundaries",
            MappingProxyType(dict(self.boundaries)),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "plan_digest": self.plan_digest,
            "ready": self.ready,
            "issues": list(self.issues),
            "object_ref": self.object_ref,
            "revision_ref": self.revision_ref,
            "object_content_digest": self.object_content_digest,
            "boundaries": dict(self.boundaries),
        }


@dataclass(frozen=True, slots=True)
class LoveLiveProjectionProbeReceipt:
    """Secret-free evidence for one complete live projection/readback cycle."""

    schema: str
    plan_digest: str
    projection_ref: str
    point_id: str
    object_ref: str
    revision_ref: str
    source_content_digest: str
    sql_projection_inserted: bool
    sql_projection_idempotent_replay: bool
    qdrant_payload: Mapping[str, object]
    checks: Mapping[str, bool]
    boundaries: Mapping[str, bool]

    def __post_init__(self) -> None:
        if self.schema != LOVE_LIVE_QDRANT_PROJECTION_RECEIPT_SCHEMA:
            raise LoveLiveQdrantProjectionProbeError(
                "unsupported live projection receipt schema"
            )
        for name in (
            "projection_ref",
            "point_id",
            "object_ref",
            "revision_ref",
        ):
            _require_typed_ref(name, getattr(self, name))
        _require_sha256("source_content_digest", self.source_content_digest)
        compact = _reference_only_mapping(self.qdrant_payload)
        object.__setattr__(self, "qdrant_payload", MappingProxyType(compact))
        object.__setattr__(self, "checks", MappingProxyType(dict(self.checks)))
        object.__setattr__(
            self,
            "boundaries",
            MappingProxyType(dict(self.boundaries)),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "plan_digest": self.plan_digest,
            "projection_ref": self.projection_ref,
            "point_id": self.point_id,
            "object_ref": self.object_ref,
            "revision_ref": self.revision_ref,
            "source_content_digest": self.source_content_digest,
            "sql_projection": {
                "inserted": self.sql_projection_inserted,
                "idempotent_replay": self.sql_projection_idempotent_replay,
            },
            "qdrant_payload": dict(self.qdrant_payload),
            "checks": dict(self.checks),
            "boundaries": dict(self.boundaries),
        }


def build_love_live_projection_probe_plan(
    request: LoveLiveProjectionProbeRequest,
    *,
    collection_name: str,
    dense_vector_name: str,
    sparse_vector_name: str,
    model_ref: str,
    model_revision: str,
    dimension: int = 384,
) -> LoveLiveProjectionProbePlan:
    """Build the immutable operator-confirmed projection plan."""

    return LoveLiveProjectionProbePlan(
        schema=LOVE_LIVE_QDRANT_PROJECTION_PLAN_SCHEMA,
        request=request,
        collection_name=collection_name,
        dense_vector_name=dense_vector_name,
        sparse_vector_name=sparse_vector_name,
        model_ref=model_ref,
        model_revision=model_revision,
        dimension=dimension,
    )


def inspect_love_live_projection_probe(
    authority_store: ProjectionAuthorityStore,
    plan: LoveLiveProjectionProbePlan,
) -> LoveLiveProjectionProbeReadiness:
    """Validate the selected SQL object and revision without external effects."""

    if not isinstance(authority_store, ProjectionAuthorityStore):
        raise LoveLiveQdrantProjectionProbeError(
            "authority_store does not expose the required SQL authority methods"
        )
    authority_object = authority_store.get_object(plan.request.object_ref)
    revision = authority_store.get_revision(plan.request.revision_ref)
    issues: list[str] = []
    if authority_object is None:
        issues.append("SQL authority object does not exist")
    elif not authority_object.body.strip():
        issues.append("SQL authority object has no inline body to project")
    if revision is None:
        issues.append("SQL context revision does not exist")
    elif authority_object is not None and not _is_active_member(
        authority_object,
        revision,
    ):
        issues.append("SQL authority object is not an active revision member")
    return LoveLiveProjectionProbeReadiness(
        schema=LOVE_LIVE_QDRANT_PROJECTION_READINESS_SCHEMA,
        plan_digest=plan.plan_digest,
        ready=not issues,
        issues=tuple(issues),
        object_ref=plan.request.object_ref,
        revision_ref=plan.request.revision_ref,
        object_content_digest=(
            authority_object.content_digest if authority_object is not None else ""
        ),
        boundaries={
            "read_only": True,
            "openvino_constructed": False,
            "openvino_inference_performed": False,
            "qdrant_client_constructed": False,
            "qdrant_write_performed": False,
            "qdrant_read_performed": False,
            "sql_write_performed": False,
        },
    )


async def execute_love_live_projection_probe(
    authority_store: ProjectionAuthorityStore,
    projector: LiveAnalysisProjectionPort,
    reader: ReferencePointReader,
    plan: LoveLiveProjectionProbePlan,
    gate: LoveLiveProjectionProbeGate,
) -> LoveLiveProjectionProbeReceipt:
    """Execute one projection, persist metadata, read back and rehydrate SQL."""

    gate.require_allows(plan)
    readiness = inspect_love_live_projection_probe(authority_store, plan)
    if not readiness.ready:
        raise LoveLiveQdrantProjectionProbeError(
            "live projection readiness failed: " + "; ".join(readiness.issues)
        )
    if not isinstance(projector, LiveAnalysisProjectionPort):
        raise LoveLiveQdrantProjectionProbeError(
            "projector does not expose async project()"
        )
    if not isinstance(reader, ReferencePointReader):
        raise LoveLiveQdrantProjectionProbeError(
            "reader does not expose reference-only point readback"
        )

    authority_object = authority_store.get_object(plan.request.object_ref)
    revision = authority_store.get_revision(plan.request.revision_ref)
    if authority_object is None or revision is None:
        raise LoveLiveQdrantProjectionProbeError(
            "SQL authority changed after readiness inspection"
        )

    projection_receipt = await projector.project(
        authority_object,
        revision=revision,
        branch_ref=plan.request.branch_ref,
        project_ref=plan.request.project_ref,
        conversation_ref=plan.request.conversation_ref,
        specialist_ref=plan.request.specialist_ref,
        laboratory_ref=plan.request.laboratory_ref,
        security_scope=plan.request.security_scope,
        projected_at=plan.request.projected_at or None,
    )
    projection = getattr(projection_receipt, "projection", None)
    if not isinstance(projection, VectorProjectionMetadata):
        raise LoveLiveQdrantProjectionProbeError(
            "projection port did not return VectorProjectionMetadata"
        )
    _require_projection_matches_plan(projection, plan, authority_object)

    sql_write = authority_store.put_projection(projection)
    readback = reader.read_named_reference_point(
        collection_name=plan.collection_name,
        point_id=projection.point_id,
    )
    if readback is None:
        raise LoveLiveQdrantProjectionProbeError(
            "Qdrant point was not found after acknowledged projection"
        )
    payload = _reference_only_mapping(getattr(readback, "payload", {}))
    _require_readback_matches_projection(readback, payload, projection, plan)

    rehydrated = authority_store.get_object(str(payload["sql_ref"]))
    if rehydrated is None:
        raise LoveLiveQdrantProjectionProbeError(
            "Qdrant sql_ref cannot be rehydrated from SQL authority"
        )
    if rehydrated.content_digest != projection.source_content_digest:
        raise LoveLiveQdrantProjectionProbeError(
            "rehydrated SQL content digest differs from Qdrant reference"
        )
    persisted_projection = authority_store.get_projection(
        projection.projection_ref
    )
    if persisted_projection is None:
        raise LoveLiveQdrantProjectionProbeError(
            "projection metadata was not rehydrated from SQL authority"
        )
    if persisted_projection.to_mapping() != projection.to_mapping():
        raise LoveLiveQdrantProjectionProbeError(
            "rehydrated SQL projection metadata differs from receipt"
        )

    return LoveLiveProjectionProbeReceipt(
        schema=LOVE_LIVE_QDRANT_PROJECTION_RECEIPT_SCHEMA,
        plan_digest=plan.plan_digest,
        projection_ref=projection.projection_ref,
        point_id=projection.point_id,
        object_ref=authority_object.object_ref,
        revision_ref=revision.revision_ref,
        source_content_digest=authority_object.content_digest,
        sql_projection_inserted=sql_write.inserted,
        sql_projection_idempotent_replay=sql_write.idempotent_replay,
        qdrant_payload=payload,
        checks={
            "qdrant_point_read_back": True,
            "qdrant_payload_reference_only": True,
            "sql_source_rehydrated": True,
            "sql_source_digest_matches": True,
            "sql_projection_metadata_rehydrated": True,
        },
        boundaries={
            "one_object_projected": True,
            "openvino_e5_used": True,
            "qdrant_write_performed": True,
            "qdrant_read_performed": True,
            "qdrant_vectors_serialized": False,
            "authoritative_body_serialized": False,
            "secret_value_serialized": False,
            "delete_performed": False,
            "alias_mutated": False,
            "sql_remains_authority": True,
        },
    )


def _require_projection_matches_plan(
    projection: VectorProjectionMetadata,
    plan: LoveLiveProjectionProbePlan,
    authority_object: ContextAuthorityObject,
) -> None:
    expected = {
        "source_ref": authority_object.object_ref,
        "source_content_digest": authority_object.content_digest,
        "collection_name": plan.collection_name,
        "vector_name": plan.dense_vector_name,
        "model_ref": plan.model_ref,
        "model_revision": plan.model_revision,
        "dimension": plan.dimension,
    }
    for name, value in expected.items():
        if getattr(projection, name) != value:
            raise LoveLiveQdrantProjectionProbeError(
                f"projection {name} differs from confirmed plan"
            )
    if projection.normalized is not True or projection.projection_state != "active":
        raise LoveLiveQdrantProjectionProbeError(
            "projection must be active and normalized"
        )


def _require_readback_matches_projection(
    readback: object,
    payload: Mapping[str, object],
    projection: VectorProjectionMetadata,
    plan: LoveLiveProjectionProbePlan,
) -> None:
    if getattr(readback, "point_id", "") != projection.point_id:
        raise LoveLiveQdrantProjectionProbeError(
            "Qdrant readback point_id differs from projection"
        )
    expected = {
        "point_id": projection.point_id,
        "sql_ref": projection.source_ref,
        "source_ref": projection.source_ref,
        "source_content_digest": projection.source_content_digest,
        "context_revision_ref": plan.request.revision_ref,
    }
    for name, value in expected.items():
        if payload.get(name) != value:
            raise LoveLiveQdrantProjectionProbeError(
                f"Qdrant readback {name} differs from projection"
            )


def _is_active_member(
    authority_object: ContextAuthorityObject,
    revision: ContextRevision,
) -> bool:
    return any(
        membership.object_ref == authority_object.object_ref
        and membership.state == "active"
        for membership in revision.memberships
    )


def _reference_only_mapping(value: object) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise LoveLiveQdrantProjectionProbeError(
            "Qdrant readback payload must be a mapping"
        )
    forbidden = {
        "body",
        "content",
        "vector",
        "vectors",
        "values",
        "embedding",
        "local_path",
    }.intersection(value)
    if forbidden:
        raise LoveLiveQdrantProjectionProbeError(
            "Qdrant readback contains forbidden authoritative/vector fields"
        )
    result: dict[str, object] = {}
    for key, item in value.items():
        if isinstance(item, (str, int, float, bool)) or item is None:
            result[str(key)] = item
    return result


def _require_typed_ref(name: str, value: object) -> None:
    if not isinstance(value, str) or ":" not in value:
        raise LoveLiveQdrantProjectionProbeError(
            f"{name} must be a typed reference"
        )
    prefix, suffix = value.split(":", 1)
    if not prefix or not suffix or not prefix[0].islower():
        raise LoveLiveQdrantProjectionProbeError(
            f"{name} must be a typed reference"
        )


def _require_sha256(name: str, value: object) -> None:
    if not isinstance(value, str) or len(value) != 71 or not value.startswith(
        "sha256:"
    ):
        raise LoveLiveQdrantProjectionProbeError(f"{name} must be sha256:*")
    try:
        int(value[7:], 16)
    except ValueError as exc:
        raise LoveLiveQdrantProjectionProbeError(
            f"{name} must be hexadecimal"
        ) from exc


__all__ = (
    "LOVE_LIVE_QDRANT_PROJECTION_PLAN_SCHEMA",
    "LOVE_LIVE_QDRANT_PROJECTION_PROBE_SCHEMA",
    "LOVE_LIVE_QDRANT_PROJECTION_READINESS_SCHEMA",
    "LOVE_LIVE_QDRANT_PROJECTION_RECEIPT_SCHEMA",
    "LiveAnalysisProjectionPort",
    "LoveLiveProjectionProbeGate",
    "LoveLiveProjectionProbePlan",
    "LoveLiveProjectionProbeReadiness",
    "LoveLiveProjectionProbeReceipt",
    "LoveLiveProjectionProbeRequest",
    "LoveLiveQdrantProjectionProbeError",
    "ProjectionAuthorityStore",
    "ReferencePointReader",
    "build_love_live_projection_probe_plan",
    "execute_love_live_projection_probe",
    "inspect_love_live_projection_probe",
)
