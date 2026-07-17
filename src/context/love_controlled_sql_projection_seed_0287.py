"""Controlled SQL-only seed for the first live projection probe.

The seed creates one immutable authority object and one accepted child revision
whose parent is the installed ``context-revision:love-base`` root.  The root
revision is never modified.  PostgreSQL remains the sole durable authority.

This module is a transitional operator use-case.  It imports no Scheduler,
Qdrant, OpenVINO, GitHub or database driver.  The authority store is injected.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
import hashlib
import json
from types import MappingProxyType
from typing import Literal, Protocol, runtime_checkable

from context.context_revision_sql_authority_0287 import (
    CONTEXT_AUTHORITY_OBJECT_SCHEMA,
    CONTEXT_REVISION_MEMBERSHIP_SCHEMA,
    CONTEXT_REVISION_SCHEMA,
    ContextAuthorityObject,
    ContextRevision,
    ContextRevisionMembership,
    ContextSqlWriteResult,
)

LOVE_CONTROLLED_SQL_SEED_PLAN_SCHEMA = (
    "missipy.love.controlled_sql_projection_seed_plan.v1"
)
LOVE_CONTROLLED_SQL_SEED_READINESS_SCHEMA = (
    "missipy.love.controlled_sql_projection_seed_readiness.v1"
)
LOVE_CONTROLLED_SQL_SEED_GATE_SCHEMA = (
    "missipy.love.controlled_sql_projection_seed_gate.v1"
)
LOVE_CONTROLLED_SQL_SEED_RECEIPT_SCHEMA = (
    "missipy.love.controlled_sql_projection_seed_receipt.v1"
)

DEFAULT_OBJECT_REF = "context-object:love-live-projection-probe-v1"
DEFAULT_REVISION_REF = "context-revision:love-live-projection-probe-v1"
DEFAULT_TITLE = "Analyse de validation du rappel hybride"
DEFAULT_CREATED_AT = "2026-07-17T00:00:00Z"
DEFAULT_BODY = """Cette analyse contrôlée sert de première preuve de projection réelle. Elle distingue l’objet autoritatif conservé dans PostgreSQL de ses représentations reconstructibles dans Qdrant.

Le test est réussi lorsque le texte est vectorisé avec le préfixe passage:, projeté dans les espaces dense_e5_v1 et sparse_lexical_v1, relu sans vecteurs puis réhydraté depuis SQL avec un digest identique. Aucun contenu autoritatif complet ne doit être stocké dans le payload Qdrant."""

OperatorDecision = Literal["approve", "reject"]


class LoveControlledSqlProjectionSeedError(RuntimeError):
    """Raised when the controlled SQL seed cannot be applied safely."""


@runtime_checkable
class ControlledSqlSeedAuthorityStore(Protocol):
    """Minimal existing SQL-authority surface reused by the seed."""

    def get_object(self, object_ref: str) -> ContextAuthorityObject | None: ...

    def put_object(
        self,
        item: ContextAuthorityObject,
    ) -> ContextSqlWriteResult: ...

    def get_revision(self, revision_ref: str) -> ContextRevision | None: ...

    def put_revision(self, item: ContextRevision) -> ContextSqlWriteResult: ...


@dataclass(frozen=True, slots=True)
class LoveControlledSqlProjectionSeedPlan:
    """Deterministic immutable object and child revision to seed."""

    schema: str
    parent_revision_ref: str
    authority_object: ContextAuthorityObject
    revision: ContextRevision
    plan_digest: str = field(init=False)
    boundaries: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.schema != LOVE_CONTROLLED_SQL_SEED_PLAN_SCHEMA:
            raise LoveControlledSqlProjectionSeedError(
                "unsupported controlled SQL seed plan schema"
            )
        if not self.parent_revision_ref.startswith("context-revision:"):
            raise LoveControlledSqlProjectionSeedError(
                "parent_revision_ref must start with context-revision:"
            )
        if self.revision.parent_revision_refs != (self.parent_revision_ref,):
            raise LoveControlledSqlProjectionSeedError(
                "seed revision must have exactly the installed base revision as parent"
            )
        active_refs = tuple(
            membership.object_ref
            for membership in self.revision.memberships
            if membership.state == "active"
        )
        if active_refs != (self.authority_object.object_ref,):
            raise LoveControlledSqlProjectionSeedError(
                "seed revision must contain exactly the seeded object as active"
            )
        if self.revision.validation_status != "accepted":
            raise LoveControlledSqlProjectionSeedError(
                "seed revision must be accepted"
            )
        frozen_boundaries = MappingProxyType(dict(self.boundaries))
        object.__setattr__(self, "boundaries", frozen_boundaries)
        object.__setattr__(self, "plan_digest", _plan_digest(self))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "plan_digest": self.plan_digest,
            "parent_revision_ref": self.parent_revision_ref,
            "authority_object": self.authority_object.to_mapping(),
            "revision": self.revision.to_mapping(),
            "boundaries": dict(self.boundaries),
        }


@dataclass(frozen=True, slots=True)
class LoveControlledSqlProjectionSeedReadiness:
    """Read-only comparison of the deterministic seed with SQL authority."""

    schema: str
    plan_digest: str
    ready: bool
    issues: tuple[str, ...]
    parent_exists: bool
    object_state: str
    revision_state: str
    boundaries: Mapping[str, object]

    def __post_init__(self) -> None:
        if self.schema != LOVE_CONTROLLED_SQL_SEED_READINESS_SCHEMA:
            raise LoveControlledSqlProjectionSeedError(
                "unsupported controlled SQL seed readiness schema"
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
            "parent_exists": self.parent_exists,
            "object_state": self.object_state,
            "revision_state": self.revision_state,
            "boundaries": dict(self.boundaries),
        }


@dataclass(frozen=True, slots=True)
class LoveControlledSqlProjectionSeedGate:
    """Explicit operator, environment and digest gate for SQL writes."""

    schema: str = LOVE_CONTROLLED_SQL_SEED_GATE_SCHEMA
    policy_decision_id: str = "policy:love-controlled-sql-seed"
    operator_decision: OperatorDecision = "reject"
    allow_write: bool = False
    confirm_plan_digest: str = ""

    def __post_init__(self) -> None:
        if self.schema != LOVE_CONTROLLED_SQL_SEED_GATE_SCHEMA:
            raise LoveControlledSqlProjectionSeedError(
                "unsupported controlled SQL seed gate schema"
            )
        if not self.policy_decision_id.startswith("policy:"):
            raise LoveControlledSqlProjectionSeedError(
                "policy_decision_id must start with policy:"
            )
        if self.operator_decision not in {"approve", "reject"}:
            raise LoveControlledSqlProjectionSeedError(
                "operator_decision must be approve or reject"
            )

    def require_allows(self, plan: LoveControlledSqlProjectionSeedPlan) -> None:
        if self.operator_decision != "approve":
            raise LoveControlledSqlProjectionSeedError(
                "controlled SQL seed requires operator approval"
            )
        if not self.allow_write:
            raise LoveControlledSqlProjectionSeedError(
                "controlled SQL seed write environment gate is closed"
            )
        if self.confirm_plan_digest != plan.plan_digest:
            raise LoveControlledSqlProjectionSeedError(
                "confirmed plan digest does not match controlled SQL seed plan"
            )


@dataclass(frozen=True, slots=True)
class LoveControlledSqlProjectionSeedReceipt:
    """Stable evidence for one inserted or idempotently replayed SQL seed."""

    schema: str
    plan_digest: str
    object_ref: str
    revision_ref: str
    parent_revision_ref: str
    object_inserted: bool
    object_idempotent_replay: bool
    revision_inserted: bool
    revision_idempotent_replay: bool
    checks: Mapping[str, bool]
    boundaries: Mapping[str, object]

    def __post_init__(self) -> None:
        if self.schema != LOVE_CONTROLLED_SQL_SEED_RECEIPT_SCHEMA:
            raise LoveControlledSqlProjectionSeedError(
                "unsupported controlled SQL seed receipt schema"
            )
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
            "object_ref": self.object_ref,
            "revision_ref": self.revision_ref,
            "parent_revision_ref": self.parent_revision_ref,
            "object_inserted": self.object_inserted,
            "object_idempotent_replay": self.object_idempotent_replay,
            "revision_inserted": self.revision_inserted,
            "revision_idempotent_replay": self.revision_idempotent_replay,
            "checks": dict(self.checks),
            "boundaries": dict(self.boundaries),
        }


def build_love_controlled_sql_projection_seed_plan(
    *,
    parent_revision_ref: str,
) -> LoveControlledSqlProjectionSeedPlan:
    """Build the fixed first-projection seed without consulting a backend."""

    if not parent_revision_ref.startswith("context-revision:"):
        raise LoveControlledSqlProjectionSeedError(
            "parent_revision_ref must start with context-revision:"
        )
    context_suffix = parent_revision_ref.removeprefix("context-revision:")
    if not context_suffix:
        raise LoveControlledSqlProjectionSeedError(
            "parent_revision_ref requires a non-empty identity"
        )
    body_bytes = DEFAULT_BODY.encode("utf-8")
    content_digest = "sha256:" + hashlib.sha256(body_bytes).hexdigest()
    authority_object = ContextAuthorityObject(
        schema=CONTEXT_AUTHORITY_OBJECT_SCHEMA,
        object_ref=DEFAULT_OBJECT_REF,
        object_kind="specialist-analysis",
        content_schema_ref="missipy.love.live_projection_probe_seed.v1",
        content_digest=content_digest,
        title=DEFAULT_TITLE,
        body=DEFAULT_BODY,
        media_type="text/plain; charset=utf-8",
        byte_count=len(body_bytes),
        metadata={
            "controlled_seed": True,
            "projection_probe": True,
            "source_kind": "operator-bootstrap",
        },
    )
    revision = ContextRevision(
        schema=CONTEXT_REVISION_SCHEMA,
        revision_ref=DEFAULT_REVISION_REF,
        context_ref=f"context:{context_suffix}",
        parent_revision_refs=(parent_revision_ref,),
        memberships=(
            ContextRevisionMembership(
                schema=CONTEXT_REVISION_MEMBERSHIP_SCHEMA,
                object_ref=authority_object.object_ref,
                state="active",
            ),
        ),
        validation_status="accepted",
        significance="minor",
        evidence_refs=(authority_object.object_ref,),
        created_at=DEFAULT_CREATED_AT,
        metadata={
            "controlled_seed": True,
            "purpose": "first-live-sql-openvino-qdrant-projection",
        },
    )
    return LoveControlledSqlProjectionSeedPlan(
        schema=LOVE_CONTROLLED_SQL_SEED_PLAN_SCHEMA,
        parent_revision_ref=parent_revision_ref,
        authority_object=authority_object,
        revision=revision,
        boundaries={
            "preview_first": True,
            "sql_only": True,
            "base_revision_mutated": False,
            "qdrant_write_performed": False,
            "openvino_inference_performed": False,
            "scheduler_constructed": False,
            "restart_safe": True,
        },
    )


def inspect_love_controlled_sql_projection_seed(
    authority_store: ControlledSqlSeedAuthorityStore,
    plan: LoveControlledSqlProjectionSeedPlan,
) -> LoveControlledSqlProjectionSeedReadiness:
    """Inspect parent and immutable collisions without performing writes."""

    if not isinstance(authority_store, ControlledSqlSeedAuthorityStore):
        raise LoveControlledSqlProjectionSeedError(
            "authority_store does not expose the controlled SQL seed contract"
        )
    parent = authority_store.get_revision(plan.parent_revision_ref)
    existing_object = authority_store.get_object(plan.authority_object.object_ref)
    existing_revision = authority_store.get_revision(plan.revision.revision_ref)

    issues: list[str] = []
    if parent is None:
        issues.append("installed base revision does not exist")
    else:
        if parent.validation_status != "accepted":
            issues.append("installed base revision is not accepted")
        if parent.context_ref != plan.revision.context_ref:
            issues.append("seed child context_ref differs from installed base revision")

    object_state = _immutable_state(existing_object, plan.authority_object)
    revision_state = _immutable_state(existing_revision, plan.revision)
    if object_state == "collision":
        issues.append("immutable authority object collision")
    if revision_state == "collision":
        issues.append("immutable child revision collision")
    if existing_revision is not None and existing_object is None:
        issues.append("child revision exists without its authority object")

    return LoveControlledSqlProjectionSeedReadiness(
        schema=LOVE_CONTROLLED_SQL_SEED_READINESS_SCHEMA,
        plan_digest=plan.plan_digest,
        ready=not issues,
        issues=tuple(issues),
        parent_exists=parent is not None,
        object_state=object_state,
        revision_state=revision_state,
        boundaries={
            "read_only": True,
            "sql_write_performed": False,
            "qdrant_client_constructed": False,
            "qdrant_write_performed": False,
            "openvino_constructed": False,
            "scheduler_constructed": False,
        },
    )


def execute_love_controlled_sql_projection_seed(
    authority_store: ControlledSqlSeedAuthorityStore,
    plan: LoveControlledSqlProjectionSeedPlan,
    gate: LoveControlledSqlProjectionSeedGate,
) -> LoveControlledSqlProjectionSeedReceipt:
    """Insert or idempotently replay the object and accepted child revision."""

    gate.require_allows(plan)
    readiness = inspect_love_controlled_sql_projection_seed(authority_store, plan)
    if not readiness.ready:
        raise LoveControlledSqlProjectionSeedError(
            "controlled SQL seed readiness failed: " + "; ".join(readiness.issues)
        )

    object_write = authority_store.put_object(plan.authority_object)
    revision_write = authority_store.put_revision(plan.revision)

    rehydrated_object = authority_store.get_object(plan.authority_object.object_ref)
    rehydrated_revision = authority_store.get_revision(plan.revision.revision_ref)
    if rehydrated_object is None or (
        rehydrated_object.to_mapping() != plan.authority_object.to_mapping()
    ):
        raise LoveControlledSqlProjectionSeedError(
            "seeded authority object did not rehydrate identically"
        )
    if rehydrated_revision is None or (
        rehydrated_revision.to_mapping() != plan.revision.to_mapping()
    ):
        raise LoveControlledSqlProjectionSeedError(
            "seeded child revision did not rehydrate identically"
        )

    return LoveControlledSqlProjectionSeedReceipt(
        schema=LOVE_CONTROLLED_SQL_SEED_RECEIPT_SCHEMA,
        plan_digest=plan.plan_digest,
        object_ref=plan.authority_object.object_ref,
        revision_ref=plan.revision.revision_ref,
        parent_revision_ref=plan.parent_revision_ref,
        object_inserted=object_write.inserted,
        object_idempotent_replay=object_write.idempotent_replay,
        revision_inserted=revision_write.inserted,
        revision_idempotent_replay=revision_write.idempotent_replay,
        checks={
            "parent_revision_preserved": True,
            "object_rehydrated": True,
            "object_digest_matches": True,
            "child_revision_rehydrated": True,
            "child_revision_accepted": True,
            "membership_active": True,
        },
        boundaries={
            "sql_write_performed": True,
            "base_revision_mutated": False,
            "qdrant_client_constructed": False,
            "qdrant_write_performed": False,
            "openvino_constructed": False,
            "openvino_inference_performed": False,
            "scheduler_constructed": False,
            "authoritative_body_serialized_in_receipt": False,
            "secret_value_serialized": False,
            "sql_remains_authority": True,
        },
    )


def _immutable_state(existing: object | None, expected: object) -> str:
    if existing is None:
        return "missing"
    existing_mapping = getattr(existing, "to_mapping", None)
    expected_mapping = getattr(expected, "to_mapping", None)
    if not callable(existing_mapping) or not callable(expected_mapping):
        return "collision"
    return "identical" if existing_mapping() == expected_mapping() else "collision"


def _plan_digest(plan: LoveControlledSqlProjectionSeedPlan) -> str:
    payload = {
        "schema": plan.schema,
        "parent_revision_ref": plan.parent_revision_ref,
        "authority_object": plan.authority_object.to_mapping(),
        "revision": plan.revision.to_mapping(),
        "boundaries": dict(plan.boundaries),
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(canonical).hexdigest()


__all__ = (
    "DEFAULT_OBJECT_REF",
    "DEFAULT_REVISION_REF",
    "LOVE_CONTROLLED_SQL_SEED_GATE_SCHEMA",
    "LOVE_CONTROLLED_SQL_SEED_PLAN_SCHEMA",
    "LOVE_CONTROLLED_SQL_SEED_READINESS_SCHEMA",
    "LOVE_CONTROLLED_SQL_SEED_RECEIPT_SCHEMA",
    "ControlledSqlSeedAuthorityStore",
    "LoveControlledSqlProjectionSeedError",
    "LoveControlledSqlProjectionSeedGate",
    "LoveControlledSqlProjectionSeedPlan",
    "LoveControlledSqlProjectionSeedReadiness",
    "LoveControlledSqlProjectionSeedReceipt",
    "build_love_controlled_sql_projection_seed_plan",
    "execute_love_controlled_sql_projection_seed",
    "inspect_love_controlled_sql_projection_seed",
)
