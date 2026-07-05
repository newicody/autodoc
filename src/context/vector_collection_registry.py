"""Vector collection registry contract.

0127 turns the 0126 vector collection roles into a local registry/reconcile plan.
One Qdrant instance owns multiple role-oriented collections; it is not one
Qdrant database per specialist.  The registry is a contract layer only: SQL is
still durable authority, E5/OpenVINO is embedding only behind adapter, Qdrant
is projection/recall only, and Scheduler remains the orchestrator.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

from context.vector_contract_indexing_plan import VectorCollectionRole, build_default_vector_collection_roles

_REGISTRY_SCHEMA = "missipy.vector.collection_registry.v1"
_ENSURE_ITEM_SCHEMA = "missipy.vector.collection_ensure_item.v1"
_ENSURE_PLAN_SCHEMA = "missipy.vector.collection_ensure_plan.v1"
_POINT_ROUTING_SCHEMA = "missipy.vector.point_routing_plan.v1"

_ALLOWED_REF_PREFIXES = (
    "sql:",
    "qdrant:",
    "collection:",
    "contract:",
    "specialist:",
    "specialist-output:",
    "ctx-result:",
    "ctx-fragment:",
    "route:",
    "route-frame:",
    "artifact:",
    "github:",
    "bus:",
    "specialist-path:",
    "scheduler-trace:",
    "vector-plan:",
    "vector-registry:",
    "vector-point:",
    "embedding-model:",
    "openvino:",
    "e5:",
)
_COLLECTION_ROLE_TO_KIND = {
    "context_chunks": ("sql:chunk", "sql:document", "ctx-fragment:"),
    "contracts": ("contract:", "sql:contract/"),
    "specialist_outputs": ("specialist-output:", "sql:specialist-output/"),
    "deliberation_signals": ("bus:", "specialist-path:", "scheduler-trace:"),
    "synthesis_candidates": ("ctx-result:", "sql:synthesis/", "vector-plan:"),
}


@dataclass(frozen=True, slots=True)
class VectorCollectionEnsureItem:
    """Creation/reconcile spec for one role-oriented Qdrant collection."""

    collection_role: VectorCollectionRole
    create_if_missing: bool = True
    recreate_if_dimension_mismatch: bool = False
    durable_authority_ref: str = "sql:context-store"

    def __post_init__(self) -> None:
        _require_typed_ref("durable_authority_ref", self.durable_authority_ref, required_prefixes=("sql:",))
        if self.collection_role.authority_ref != self.durable_authority_ref:
            raise ValueError("collection role authority_ref must match durable_authority_ref")

    def to_mapping(self) -> dict[str, object]:
        role = self.collection_role
        return {
            "schema": _ENSURE_ITEM_SCHEMA,
            "role": role.role,
            "collection_ref": role.collection_ref,
            "collection_name": role.collection_name,
            "vector_dimension": role.vector_dimension,
            "distance": role.distance,
            "embedding_model_ref": role.embedding_model_ref,
            "create_if_missing": self.create_if_missing,
            "recreate_if_dimension_mismatch": self.recreate_if_dimension_mismatch,
            "durable_authority_ref": self.durable_authority_ref,
            "qdrant_runtime_client": False,
            "qdrant_projection_only": True,
            "sql_is_authority": True,
        }


@dataclass(frozen=True, slots=True)
class VectorCollectionRegistry:
    """Registry for role-oriented vector collections in one Qdrant instance."""

    registry_ref: str
    qdrant_instance_ref: str
    collection_roles: tuple[VectorCollectionRole, ...]
    embedding_model_ref: str = "openvino:e5-small"
    durable_authority_ref: str = "sql:context-store"

    def __post_init__(self) -> None:
        _require_typed_ref("registry_ref", self.registry_ref, required_prefixes=("vector-registry:",))
        _require_typed_ref("qdrant_instance_ref", self.qdrant_instance_ref, required_prefixes=("qdrant:",))
        _require_typed_ref("embedding_model_ref", self.embedding_model_ref, required_prefixes=("openvino:", "e5:", "embedding-model:"))
        _require_typed_ref("durable_authority_ref", self.durable_authority_ref, required_prefixes=("sql:",))
        roles = tuple(self.collection_roles)
        if not roles:
            raise ValueError("collection_roles must not be empty")
        seen: set[str] = set()
        names: set[str] = set()
        for role in roles:
            if role.role in seen:
                raise ValueError("collection roles must be unique")
            if role.collection_name in names:
                raise ValueError("collection names must be unique")
            if role.embedding_model_ref != self.embedding_model_ref:
                raise ValueError("all collection roles must use the registry embedding_model_ref")
            if role.authority_ref != self.durable_authority_ref:
                raise ValueError("all collection roles must use the registry durable_authority_ref")
            if "specialist" in role.collection_name and role.role != "specialist_outputs":
                raise ValueError("do not create per-specialist collection names")
            seen.add(role.role)
            names.add(role.collection_name)
        object.__setattr__(self, "collection_roles", roles)

    @property
    def role_names(self) -> tuple[str, ...]:
        return tuple(role.role for role in self.collection_roles)

    def role(self, role_name: str) -> VectorCollectionRole:
        for role in self.collection_roles:
            if role.role == role_name:
                return role
        raise ValueError(f"unknown collection role: {role_name}")

    def ensure_plan(self) -> "VectorCollectionEnsurePlan":
        items = tuple(VectorCollectionEnsureItem(role, durable_authority_ref=self.durable_authority_ref) for role in self.collection_roles)
        return VectorCollectionEnsurePlan(
            plan_ref=f"vector-plan:ensure-collections-{_stable_suffix(self.registry_ref + self.qdrant_instance_ref)}",
            registry_ref=self.registry_ref,
            qdrant_instance_ref=self.qdrant_instance_ref,
            items=items,
        )

    def route_point(self, *, source_ref: str, output_kind: str, specialist_ref: str | None = None) -> "VectorPointRoutingPlan":
        _require_typed_ref("source_ref", source_ref)
        if specialist_ref is not None:
            _require_typed_ref("specialist_ref", specialist_ref, required_prefixes=("specialist:",))
        role_name = _role_for_source(source_ref, output_kind)
        role = self.role(role_name)
        seed = f"{self.registry_ref}|{source_ref}|{output_kind}|{specialist_ref or ''}|{role.collection_ref}"
        return VectorPointRoutingPlan(
            point_ref=f"vector-point:{_stable_suffix(seed)}",
            source_ref=source_ref,
            output_kind=output_kind,
            collection_role=role,
            specialist_ref=specialist_ref,
            payload_refs=(source_ref,) if specialist_ref is None else (source_ref, specialist_ref),
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _REGISTRY_SCHEMA,
            "registry_ref": self.registry_ref,
            "qdrant_instance_ref": self.qdrant_instance_ref,
            "embedding_model_ref": self.embedding_model_ref,
            "durable_authority_ref": self.durable_authority_ref,
            "collection_roles": [role.to_mapping() for role in self.collection_roles],
            "role_names": list(self.role_names),
            "one_qdrant_instance_multiple_role_collections": True,
            "per_specialist_database": False,
            "scheduler_orchestrates": True,
            "e5_openvino_role": "embedding only behind adapter",
            "qdrant_role": "projection and recall only",
            "sql_is_authority": True,
        }


@dataclass(frozen=True, slots=True)
class VectorCollectionEnsurePlan:
    """Plan an adapter can execute later to ensure Qdrant collections exist."""

    plan_ref: str
    registry_ref: str
    qdrant_instance_ref: str
    items: tuple[VectorCollectionEnsureItem, ...]

    def __post_init__(self) -> None:
        _require_typed_ref("plan_ref", self.plan_ref, required_prefixes=("vector-plan:",))
        _require_typed_ref("registry_ref", self.registry_ref, required_prefixes=("vector-registry:",))
        _require_typed_ref("qdrant_instance_ref", self.qdrant_instance_ref, required_prefixes=("qdrant:",))
        if not self.items:
            raise ValueError("items must not be empty")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _ENSURE_PLAN_SCHEMA,
            "plan_ref": self.plan_ref,
            "registry_ref": self.registry_ref,
            "qdrant_instance_ref": self.qdrant_instance_ref,
            "items": [item.to_mapping() for item in self.items],
            "runtime_client_required_here": False,
            "adapter_executes_later": True,
        }


@dataclass(frozen=True, slots=True)
class VectorPointRoutingPlan:
    """Route one embedded point to the proper role collection."""

    point_ref: str
    source_ref: str
    output_kind: str
    collection_role: VectorCollectionRole
    specialist_ref: str | None = None
    payload_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_typed_ref("point_ref", self.point_ref, required_prefixes=("vector-point:",))
        _require_typed_ref("source_ref", self.source_ref)
        _require_non_empty("output_kind", self.output_kind)
        if self.specialist_ref is not None:
            _require_typed_ref("specialist_ref", self.specialist_ref, required_prefixes=("specialist:",))
        object.__setattr__(self, "payload_refs", _normalize_refs("payload_refs", self.payload_refs, allow_empty=False))

    def to_mapping(self) -> dict[str, object | None]:
        return {
            "schema": _POINT_ROUTING_SCHEMA,
            "point_ref": self.point_ref,
            "source_ref": self.source_ref,
            "output_kind": self.output_kind,
            "collection_ref": self.collection_role.collection_ref,
            "collection_role": self.collection_role.role,
            "collection_name": self.collection_role.collection_name,
            "specialist_ref": self.specialist_ref,
            "payload_refs": list(self.payload_refs),
            "content_hydrated_from_sql": self.source_ref.startswith("sql:"),
            "qdrant_payload_is_lightweight": True,
            "qdrant_decides": False,
        }


def build_default_vector_collection_registry(
    *,
    qdrant_instance_ref: str = "qdrant:local-autodoc",
    embedding_model_ref: str = "openvino:e5-small",
    durable_authority_ref: str = "sql:context-store",
) -> VectorCollectionRegistry:
    roles = build_default_vector_collection_roles(embedding_model_ref=embedding_model_ref)
    return VectorCollectionRegistry(
        registry_ref="vector-registry:autodoc-e5-384-role-collections",
        qdrant_instance_ref=qdrant_instance_ref,
        collection_roles=roles,
        embedding_model_ref=embedding_model_ref,
        durable_authority_ref=durable_authority_ref,
    )


def _role_for_source(source_ref: str, output_kind: str) -> str:
    if output_kind in {"contract", "instruction_contract", "human_representation_contract"}:
        return "contracts"
    if output_kind in {"preliminary_opinion", "feasibility_review", "context_patch_proposal", "work_product"}:
        return "specialist_outputs"
    if output_kind in {"analysis_signal", "bus_fact", "scheduler_trace", "specialist_path"}:
        return "deliberation_signals"
    if output_kind in {"final_synthesis_candidate", "synthesis_candidate"}:
        return "synthesis_candidates"
    for role, prefixes in _COLLECTION_ROLE_TO_KIND.items():
        if source_ref.startswith(prefixes):
            return role
    raise ValueError("cannot route source_ref/output_kind to a locked vector collection role")


def _require_typed_ref(name: str, value: str, *, required_prefixes: tuple[str, ...] = _ALLOWED_REF_PREFIXES) -> None:
    _require_non_empty(name, value)
    if ":" not in value:
        raise ValueError(f"{name} must be a typed ref")
    if required_prefixes and not value.startswith(required_prefixes):
        raise ValueError(f"{name} must start with one of {required_prefixes}")


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _normalize_refs(
    name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool,
    required_prefixes: tuple[str, ...] = _ALLOWED_REF_PREFIXES,
) -> tuple[str, ...]:
    normalized = tuple(dict.fromkeys(values))
    if not allow_empty and not normalized:
        raise ValueError(f"{name} must not be empty")
    for value in normalized:
        _require_typed_ref(name, value, required_prefixes=required_prefixes)
    return normalized


def _stable_suffix(seed: str) -> str:
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]
