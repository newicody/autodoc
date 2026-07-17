"""Controlled plan/readiness/creation for the installed hybrid Qdrant collection.

The module composes the canonical profile and an injected qdrant-client admin
port. It never imports qdrant-client, deletes resources or mutates aliases.
Creation is preview-first and requires an exact plan digest plus operator policy.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from types import MappingProxyType
from typing import Mapping, Protocol

from context.love_manual_runtime_configuration_0287 import (
    ManualInstalledRuntimeSettings,
)
from context.qdrant_canonical_profile_0287 import (
    QDRANT_COLLECTION_PROFILE_SCHEMA,
    QDRANT_NAMED_VECTOR_SCHEMA,
    QdrantCollectionProfile,
    QdrantNamedVectorProfile,
    build_canonical_payload_indexes,
)
from inference.qdrant_client_named_collection_admin_0287 import (
    QdrantNamedCollectionShape,
)


LOVE_QDRANT_NAMED_COLLECTION_PLAN_SCHEMA = (
    "missipy.love.qdrant_named_collection_plan.v1"
)
LOVE_QDRANT_NAMED_COLLECTION_READINESS_SCHEMA = (
    "missipy.love.qdrant_named_collection_readiness.v1"
)
LOVE_QDRANT_NAMED_COLLECTION_EXECUTION_SCHEMA = (
    "missipy.love.qdrant_named_collection_execution.v1"
)


class LoveQdrantNamedCollectionControlError(RuntimeError):
    """Fail-closed control-path error."""


class QdrantNamedCollectionAdminPort(Protocol):
    def read_collection(
        self,
        collection_name: str,
    ) -> QdrantNamedCollectionShape: ...

    def create_named_collection(
        self,
        *,
        collection_name: str,
        dense_vector_name: str,
        dense_dimension: int,
        dense_distance: str,
        sparse_vector_name: str,
    ) -> None: ...

    def create_payload_index(
        self,
        *,
        collection_name: str,
        field_name: str,
        index_kind: str,
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class LoveQdrantNamedCollectionPlan:
    schema: str
    profile: QdrantCollectionProfile
    plan_digest: str

    def __post_init__(self) -> None:
        if self.schema != LOVE_QDRANT_NAMED_COLLECTION_PLAN_SCHEMA:
            raise LoveQdrantNamedCollectionControlError(
                "unsupported named collection plan schema"
            )
        expected = _plan_digest(self.profile)
        if self.plan_digest != expected:
            raise LoveQdrantNamedCollectionControlError(
                "plan_digest differs from canonical profile"
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "plan_digest": self.plan_digest,
            "profile": self.profile.to_mapping(),
            "boundaries": {
                "preview_first": True,
                "delete_allowed": False,
                "alias_mutation_allowed": False,
                "point_write_performed": False,
                "sql_remains_authority": True,
            },
        }


@dataclass(frozen=True, slots=True)
class LoveQdrantNamedCollectionReadiness:
    schema: str
    valid: bool
    issues: tuple[str, ...]
    shape: QdrantNamedCollectionShape
    missing_payload_indexes: tuple[str, ...]
    plan_digest: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "issues": list(self.issues),
            "shape": self.shape.to_mapping(),
            "missing_payload_indexes": list(self.missing_payload_indexes),
            "plan_digest": self.plan_digest,
            "boundaries": {
                "read_only": True,
                "collection_write_performed": False,
                "payload_index_write_performed": False,
                "alias_mutated": False,
                "delete_performed": False,
            },
        }


@dataclass(frozen=True, slots=True)
class LoveQdrantNamedCollectionMutationGate:
    policy_decision_id: str
    operator_decision: str
    allow_create: bool
    confirm_plan_digest: str

    def __post_init__(self) -> None:
        if not self.policy_decision_id.startswith("policy:"):
            raise LoveQdrantNamedCollectionControlError(
                "policy_decision_id must be typed"
            )
        if self.operator_decision not in {"approve", "reject"}:
            raise LoveQdrantNamedCollectionControlError(
                "operator_decision must be approve or reject"
            )


@dataclass(frozen=True, slots=True)
class LoveQdrantNamedCollectionExecution:
    schema: str
    valid: bool
    created_collection: bool
    created_payload_indexes: tuple[str, ...]
    readiness: LoveQdrantNamedCollectionReadiness
    policy_decision_id: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "created_collection": self.created_collection,
            "created_payload_indexes": list(self.created_payload_indexes),
            "readiness": self.readiness.to_mapping(),
            "policy_decision_id": self.policy_decision_id,
            "boundaries": {
                "point_write_performed": False,
                "alias_mutated": False,
                "delete_performed": False,
                "destructive_mutation_performed": False,
                "sql_remains_authority": True,
            },
        }


def build_love_qdrant_named_collection_plan(
    settings: ManualInstalledRuntimeSettings,
) -> LoveQdrantNamedCollectionPlan:
    """Build the canonical physical collection plan from local settings."""

    cfg = settings.qdrant
    if not cfg.named_vectors_enabled:
        raise LoveQdrantNamedCollectionControlError(
            "named Qdrant vectors must be explicitly configured"
        )
    dense = QdrantNamedVectorProfile(
        schema=QDRANT_NAMED_VECTOR_SCHEMA,
        vector_name=cfg.dense_vector_name,
        vector_kind="dense",
        embedding_profile_ref="embedding-profile:multilingual-e5-small-passage",
        model_ref=settings.model_ref,
        model_revision=settings.model_revision,
        dimension=cfg.dimension,
        distance="Cosine",
        normalized=True,
        metadata={
            "backend_ref": settings.embedding_backend_ref,
            "role": "passage",
        },
    )
    sparse = QdrantNamedVectorProfile(
        schema=QDRANT_NAMED_VECTOR_SCHEMA,
        vector_name=cfg.sparse_vector_name,
        vector_kind="sparse",
        embedding_profile_ref="embedding-profile:sparse-lexical-v1",
        model_ref="model:sparse-lexical-v1",
        model_revision="v1",
        dimension=None,
        distance=None,
        normalized=None,
        hnsw_enabled=False,
        metadata={
            "backend_ref": "sparse:lexical-v1",
            "role": "passage",
        },
    )
    profile = QdrantCollectionProfile(
        schema=QDRANT_COLLECTION_PROFILE_SCHEMA,
        profile_ref="qdrant-profile:love-hybrid-v1",
        collection_name=cfg.physical_collection,
        collection_alias=cfg.collection_alias,
        point_identity_field="point_id",
        authority_ref_field="sql_ref",
        named_vectors=(dense, sparse),
        payload_indexes=build_canonical_payload_indexes(),
        metadata={
            "legacy_collection": cfg.collection,
            "alias_activation_deferred": True,
        },
    )
    return LoveQdrantNamedCollectionPlan(
        schema=LOVE_QDRANT_NAMED_COLLECTION_PLAN_SCHEMA,
        profile=profile,
        plan_digest=_plan_digest(profile),
    )


def inspect_love_qdrant_named_collection(
    admin: QdrantNamedCollectionAdminPort,
    plan: LoveQdrantNamedCollectionPlan,
) -> LoveQdrantNamedCollectionReadiness:
    """Read the physical collection and compare it with the locked profile."""

    shape = admin.read_collection(plan.profile.collection_name)
    issues: list[str] = []
    dense = next(
        item
        for item in plan.profile.named_vectors
        if item.vector_kind == "dense"
    )
    sparse = next(
        item
        for item in plan.profile.named_vectors
        if item.vector_kind == "sparse"
    )
    if not shape.exists:
        issues.append("physical Qdrant collection is missing")
    else:
        observed_dense = shape.dense_vectors.get(dense.vector_name)
        if observed_dense is None:
            issues.append("canonical named dense vector is missing")
        else:
            if int(observed_dense.get("size") or 0) != dense.dimension:
                issues.append("canonical dense vector dimension mismatch")
            if (
                str(observed_dense.get("distance") or "").casefold()
                != str(dense.distance).casefold()
            ):
                issues.append("canonical dense vector distance mismatch")
        if sparse.vector_name not in shape.sparse_vectors:
            issues.append("canonical named sparse vector is missing")
        if shape.status and shape.status != "green":
            issues.append("physical Qdrant collection status is not green")

    expected_indexes = {
        item.field_name: item.index_kind
        for item in plan.profile.payload_indexes
    }
    missing_indexes: list[str] = []
    for field_name, index_kind in expected_indexes.items():
        observed = shape.payload_indexes.get(field_name, "")
        if not observed:
            missing_indexes.append(field_name)
        elif observed.casefold() != index_kind.casefold():
            issues.append(
                f"payload index type mismatch for {field_name}"
            )
    if missing_indexes:
        issues.append("canonical payload indexes are incomplete")

    return LoveQdrantNamedCollectionReadiness(
        schema=LOVE_QDRANT_NAMED_COLLECTION_READINESS_SCHEMA,
        valid=not issues,
        issues=tuple(issues),
        shape=shape,
        missing_payload_indexes=tuple(sorted(missing_indexes)),
        plan_digest=plan.plan_digest,
    )


def execute_love_qdrant_named_collection_plan(
    admin: QdrantNamedCollectionAdminPort,
    plan: LoveQdrantNamedCollectionPlan,
    gate: LoveQdrantNamedCollectionMutationGate,
) -> LoveQdrantNamedCollectionExecution:
    """Create only missing additive resources, then require exact readback."""

    if gate.operator_decision != "approve":
        raise LoveQdrantNamedCollectionControlError(
            "operator decision did not approve collection creation"
        )
    if not gate.allow_create:
        raise LoveQdrantNamedCollectionControlError(
            "collection mutation is not allowed"
        )
    if gate.confirm_plan_digest != plan.plan_digest:
        raise LoveQdrantNamedCollectionControlError(
            "confirm-plan-digest mismatch"
        )

    initial = inspect_love_qdrant_named_collection(admin, plan)
    created_collection = False
    created_indexes: list[str] = []
    dense = next(
        item
        for item in plan.profile.named_vectors
        if item.vector_kind == "dense"
    )
    sparse = next(
        item
        for item in plan.profile.named_vectors
        if item.vector_kind == "sparse"
    )

    if initial.shape.exists:
        structural_issues = tuple(
            issue
            for issue in initial.issues
            if "payload index" not in issue
        )
        if structural_issues:
            raise LoveQdrantNamedCollectionControlError(
                "existing physical collection has incompatible structure: "
                + "; ".join(structural_issues)
            )
    else:
        admin.create_named_collection(
            collection_name=plan.profile.collection_name,
            dense_vector_name=dense.vector_name,
            dense_dimension=int(dense.dimension or 0),
            dense_distance=str(dense.distance),
            sparse_vector_name=sparse.vector_name,
        )
        created_collection = True

    current = inspect_love_qdrant_named_collection(admin, plan)
    expected_indexes = {
        item.field_name: item.index_kind
        for item in plan.profile.payload_indexes
    }
    for field_name in current.missing_payload_indexes:
        admin.create_payload_index(
            collection_name=plan.profile.collection_name,
            field_name=field_name,
            index_kind=expected_indexes[field_name],
        )
        created_indexes.append(field_name)

    final = inspect_love_qdrant_named_collection(admin, plan)
    if not final.valid:
        raise LoveQdrantNamedCollectionControlError(
            "Qdrant collection readback is not canonical: "
            + "; ".join(final.issues)
        )
    return LoveQdrantNamedCollectionExecution(
        schema=LOVE_QDRANT_NAMED_COLLECTION_EXECUTION_SCHEMA,
        valid=True,
        created_collection=created_collection,
        created_payload_indexes=tuple(sorted(created_indexes)),
        readiness=final,
        policy_decision_id=gate.policy_decision_id,
    )


def _plan_digest(profile: QdrantCollectionProfile) -> str:
    payload = {
        "schema": LOVE_QDRANT_NAMED_COLLECTION_PLAN_SCHEMA,
        "profile": profile.to_mapping(),
    }
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


__all__ = (
    "LOVE_QDRANT_NAMED_COLLECTION_EXECUTION_SCHEMA",
    "LOVE_QDRANT_NAMED_COLLECTION_PLAN_SCHEMA",
    "LOVE_QDRANT_NAMED_COLLECTION_READINESS_SCHEMA",
    "LoveQdrantNamedCollectionControlError",
    "LoveQdrantNamedCollectionExecution",
    "LoveQdrantNamedCollectionMutationGate",
    "LoveQdrantNamedCollectionPlan",
    "LoveQdrantNamedCollectionReadiness",
    "QdrantNamedCollectionAdminPort",
    "build_love_qdrant_named_collection_plan",
    "execute_love_qdrant_named_collection_plan",
    "inspect_love_qdrant_named_collection",
)
# r10-r1 does not change the controlled mutation boundary.
# r10-r2 changes readback normalization only; control effects remain unchanged.
