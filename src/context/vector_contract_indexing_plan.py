"""Vector contract indexing plan.

0126 locks vectorized contracts without making Qdrant or E5/OpenVINO authority.
SQLContextStore keeps the durable contracts and specialist outputs.  E5/OpenVINO
embeds contracts, requests, and specialist outputs behind adapter.  Qdrant stores projection collections by role, not one database per specialist.  Scheduler
orchestrates the deliberation cycle; vector recall only proposes nearby
contracts, context, opinions, signals, and synthesis candidates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import re

_VECTOR_COLLECTION_SCHEMA = "missipy.vector.collection_role.v1"
_SPECIALIST_CONTRACT_SCHEMA = "missipy.vector.specialist_instruction_contract.v1"
_HUMAN_REPRESENTATION_SCHEMA = "missipy.vector.human_representation_contract.v1"
_EMBEDDED_CONTRACT_SCHEMA = "missipy.vector.embedded_contract_descriptor.v1"
_OUTPUT_INDEX_SCHEMA = "missipy.vector.specialist_output_indexing_descriptor.v1"
_RETRIEVAL_PLAN_SCHEMA = "missipy.vector.retrieval_plan.v1"
_PACKET_SCHEMA = "missipy.vector.contract_instruction_packet.v1"

_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9._/-]*$")
_ALLOWED_COLLECTION_ROLES = (
    "context_chunks",
    "contracts",
    "specialist_outputs",
    "deliberation_signals",
    "synthesis_candidates",
)
_ALLOWED_DISTANCE = ("Cosine", "Dot", "Euclid")
_ALLOWED_EMBEDDING_ROLES = ("query", "passage")
_ALLOWED_OUTPUT_TYPES = (
    "preliminary_opinion",
    "feasibility_review",
    "context_patch_proposal",
    "peer_review_request",
    "impossibility_report",
    "analysis_signal",
    "work_product",
    "final_synthesis_candidate",
)
_ALLOWED_REF_PREFIXES = (
    "sql:",
    "ctx:",
    "ctx-result:",
    "ctx-fragment:",
    "qdrant:",
    "collection:",
    "contract:",
    "specialist:",
    "route:",
    "route-frame:",
    "artifact:",
    "github:",
    "bus:",
    "specialist-path:",
    "scheduler-trace:",
    "openvino:",
    "e5:",
    "embedding-model:",
    "human-representation:",
    "vector-plan:",
    "vector-packet:",
    "vector-descriptor:",
)


@dataclass(frozen=True, slots=True)
class VectorCollectionRole:
    """A Qdrant collection role, not a Qdrant authority boundary.

    Collections are split by use, not by specialist.  Specialist identity is a
    payload/filter dimension so the system can still recall across specialists
    when the Scheduler asks for synthesis or contradiction search.
    """

    role: str
    collection_ref: str
    collection_name: str
    vector_dimension: int = 384
    distance: str = "Cosine"
    embedding_model_ref: str = "openvino:e5-small"
    authority_ref: str = "sql:context-store"
    description: str = ""

    def __post_init__(self) -> None:
        if self.role not in _ALLOWED_COLLECTION_ROLES:
            raise ValueError("role must be one of the locked vector collection roles")
        _require_typed_ref("collection_ref", self.collection_ref, required_prefixes=("qdrant:", "collection:"))
        _require_slug("collection_name", self.collection_name)
        if self.vector_dimension <= 0:
            raise ValueError("vector_dimension must be > 0")
        if self.distance not in _ALLOWED_DISTANCE:
            raise ValueError("distance must be Cosine, Dot, or Euclid")
        _require_typed_ref("embedding_model_ref", self.embedding_model_ref, required_prefixes=("openvino:", "e5:", "embedding-model:"))
        _require_typed_ref("authority_ref", self.authority_ref, required_prefixes=("sql:",))
        if self.description:
            _require_non_empty("description", self.description)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _VECTOR_COLLECTION_SCHEMA,
            "role": self.role,
            "collection_ref": self.collection_ref,
            "collection_name": self.collection_name,
            "vector_dimension": self.vector_dimension,
            "distance": self.distance,
            "embedding_model_ref": self.embedding_model_ref,
            "authority_ref": self.authority_ref,
            "description": self.description,
            "qdrant_role": "projection only",
            "per_specialist_database": False,
            "sql_is_authority": True,
        }


@dataclass(frozen=True, slots=True)
class HumanRepresentationContract:
    """Human-facing output shape proposed by a specialist contract."""

    representation_ref: str
    document_kind: str
    audience: str = "end_user"
    sections: tuple[str, ...] = ()
    style_hints: tuple[str, ...] = ()
    hide_specialist_provenance_by_default: bool = True

    def __post_init__(self) -> None:
        _require_typed_ref("representation_ref", self.representation_ref, required_prefixes=("human-representation:", "contract:"))
        _require_slug("document_kind", self.document_kind)
        _require_slug("audience", self.audience)
        object.__setattr__(self, "sections", _normalize_slugs("sections", self.sections, allow_empty=False))
        object.__setattr__(self, "style_hints", _normalize_slugs("style_hints", self.style_hints, allow_empty=True))

    def to_embedding_passage(self) -> str:
        section_text = ", ".join(self.sections)
        style_text = ", ".join(self.style_hints) if self.style_hints else "neutral"
        return f"passage: human representation {self.document_kind} for {self.audience}; sections {section_text}; style {style_text}"

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _HUMAN_REPRESENTATION_SCHEMA,
            "representation_ref": self.representation_ref,
            "document_kind": self.document_kind,
            "audience": self.audience,
            "sections": list(self.sections),
            "style_hints": list(self.style_hints),
            "hide_specialist_provenance_by_default": self.hide_specialist_provenance_by_default,
        }


@dataclass(frozen=True, slots=True)
class SpecialistInstructionContract:
    """SQL-owned contract that can be embedded to instruct specialist work."""

    contract_ref: str
    sql_contract_ref: str
    title: str
    domain: str
    objective: str
    output_type: str
    human_representation: HumanRepresentationContract
    specialist_refs: tuple[str, ...] = ()
    context_refs: tuple[str, ...] = ()
    required_evidence_refs: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_typed_ref("contract_ref", self.contract_ref, required_prefixes=("contract:",))
        _require_typed_ref("sql_contract_ref", self.sql_contract_ref, required_prefixes=("sql:",))
        _require_non_empty("title", self.title)
        _require_slug("domain", self.domain)
        _require_non_empty("objective", self.objective)
        if self.output_type not in _ALLOWED_OUTPUT_TYPES:
            raise ValueError("output_type must be one of the allowed specialist output types")
        object.__setattr__(self, "specialist_refs", _normalize_refs("specialist_refs", self.specialist_refs, allow_empty=True, required_prefixes=("specialist:",)))
        object.__setattr__(self, "context_refs", _normalize_refs("context_refs", self.context_refs, allow_empty=True))
        object.__setattr__(self, "required_evidence_refs", _normalize_refs("required_evidence_refs", self.required_evidence_refs, allow_empty=True))
        object.__setattr__(self, "tags", _normalize_slugs("tags", self.tags, allow_empty=True))

    def to_embedding_passage(self) -> str:
        specialists = ", ".join(self.specialist_refs) if self.specialist_refs else "any-specialist"
        tags = ", ".join(self.tags) if self.tags else "untagged"
        sections = ", ".join(self.human_representation.sections)
        return (
            "passage: specialist instruction contract; "
            f"title {self.title}; domain {self.domain}; objective {self.objective}; "
            f"output {self.output_type}; specialists {specialists}; sections {sections}; tags {tags}"
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _SPECIALIST_CONTRACT_SCHEMA,
            "contract_ref": self.contract_ref,
            "sql_contract_ref": self.sql_contract_ref,
            "title": self.title,
            "domain": self.domain,
            "objective": self.objective,
            "output_type": self.output_type,
            "human_representation": self.human_representation.to_mapping(),
            "specialist_refs": list(self.specialist_refs),
            "context_refs": list(self.context_refs),
            "required_evidence_refs": list(self.required_evidence_refs),
            "tags": list(self.tags),
            "sql_is_authority": True,
            "embedding_role": "passage",
        }


@dataclass(frozen=True, slots=True)
class EmbeddedContractDescriptor:
    """Embedding work descriptor for a SQL-owned specialist contract."""

    descriptor_ref: str
    contract_ref: str
    sql_contract_ref: str
    qdrant_collection_ref: str
    embedding_model_ref: str
    embedding_role: str
    text_for_embedding: str
    vector_dimension: int = 384
    payload_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_typed_ref("descriptor_ref", self.descriptor_ref, required_prefixes=("vector-descriptor:",))
        _require_typed_ref("contract_ref", self.contract_ref, required_prefixes=("contract:",))
        _require_typed_ref("sql_contract_ref", self.sql_contract_ref, required_prefixes=("sql:",))
        _require_typed_ref("qdrant_collection_ref", self.qdrant_collection_ref, required_prefixes=("qdrant:", "collection:"))
        _require_typed_ref("embedding_model_ref", self.embedding_model_ref, required_prefixes=("openvino:", "e5:", "embedding-model:"))
        if self.embedding_role not in _ALLOWED_EMBEDDING_ROLES:
            raise ValueError("embedding_role must be query or passage")
        _require_non_empty("text_for_embedding", self.text_for_embedding)
        if not self.text_for_embedding.startswith(f"{self.embedding_role}:"):
            raise ValueError("text_for_embedding must start with the E5 embedding role prefix")
        if self.vector_dimension <= 0:
            raise ValueError("vector_dimension must be > 0")
        object.__setattr__(self, "payload_refs", _normalize_refs("payload_refs", self.payload_refs, allow_empty=True))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _EMBEDDED_CONTRACT_SCHEMA,
            "descriptor_ref": self.descriptor_ref,
            "contract_ref": self.contract_ref,
            "sql_contract_ref": self.sql_contract_ref,
            "qdrant_collection_ref": self.qdrant_collection_ref,
            "embedding_model_ref": self.embedding_model_ref,
            "embedding_role": self.embedding_role,
            "text_for_embedding": self.text_for_embedding,
            "vector_dimension": self.vector_dimension,
            "payload_refs": list(self.payload_refs),
            "e5_openvino_role": "embedding only behind adapter",
            "decision_maker": False,
        }


@dataclass(frozen=True, slots=True)
class SpecialistOutputIndexingDescriptor:
    """Descriptor for indexing specialist outputs after SQL persistence."""

    descriptor_ref: str
    output_ref: str
    sql_output_ref: str
    specialist_ref: str
    output_type: str
    machine_summary: str
    human_representation_ref: str
    qdrant_collection_ref: str = "qdrant:specialist_outputs_e5_384"
    embedding_model_ref: str = "openvino:e5-small"
    evidence_refs: tuple[str, ...] = ()
    bus_fact_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_typed_ref("descriptor_ref", self.descriptor_ref, required_prefixes=("vector-descriptor:",))
        _require_typed_ref("output_ref", self.output_ref, required_prefixes=("specialist-output:", "specialist-opinion:", "ctx-result:"))
        _require_typed_ref("sql_output_ref", self.sql_output_ref, required_prefixes=("sql:",))
        _require_typed_ref("specialist_ref", self.specialist_ref, required_prefixes=("specialist:",))
        if self.output_type not in _ALLOWED_OUTPUT_TYPES:
            raise ValueError("output_type must be one of the allowed specialist output types")
        _require_non_empty("machine_summary", self.machine_summary)
        _require_typed_ref("human_representation_ref", self.human_representation_ref, required_prefixes=("human-representation:", "contract:"))
        _require_typed_ref("qdrant_collection_ref", self.qdrant_collection_ref, required_prefixes=("qdrant:", "collection:"))
        _require_typed_ref("embedding_model_ref", self.embedding_model_ref, required_prefixes=("openvino:", "e5:", "embedding-model:"))
        object.__setattr__(self, "evidence_refs", _normalize_refs("evidence_refs", self.evidence_refs, allow_empty=True))
        object.__setattr__(self, "bus_fact_refs", _normalize_refs("bus_fact_refs", self.bus_fact_refs, allow_empty=True, required_prefixes=("bus:", "specialist-path:", "scheduler-trace:")))

    def to_embedding_passage(self) -> str:
        evidence = ", ".join(self.evidence_refs) if self.evidence_refs else "no-evidence-ref"
        return (
            "passage: specialist output; "
            f"specialist {self.specialist_ref}; output {self.output_type}; "
            f"summary {self.machine_summary}; evidence {evidence}"
        )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _OUTPUT_INDEX_SCHEMA,
            "descriptor_ref": self.descriptor_ref,
            "output_ref": self.output_ref,
            "sql_output_ref": self.sql_output_ref,
            "specialist_ref": self.specialist_ref,
            "output_type": self.output_type,
            "machine_summary": self.machine_summary,
            "human_representation_ref": self.human_representation_ref,
            "qdrant_collection_ref": self.qdrant_collection_ref,
            "embedding_model_ref": self.embedding_model_ref,
            "evidence_refs": list(self.evidence_refs),
            "bus_fact_refs": list(self.bus_fact_refs),
            "text_for_embedding": self.to_embedding_passage(),
            "sql_is_authority": True,
        }


@dataclass(frozen=True, slots=True)
class VectorRetrievalPlan:
    """Bounded plan for recalling contracts and outputs by semantic query."""

    plan_ref: str
    query_text: str
    query_context_refs: tuple[str, ...]
    collection_roles: tuple[VectorCollectionRole, ...]
    embedding_model_ref: str = "openvino:e5-small"
    top_k_per_collection: int = 8
    embedding_role: str = "query"
    filter_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_typed_ref("plan_ref", self.plan_ref, required_prefixes=("vector-plan:",))
        _require_non_empty("query_text", self.query_text)
        object.__setattr__(self, "query_context_refs", _normalize_refs("query_context_refs", self.query_context_refs, allow_empty=True))
        object.__setattr__(self, "collection_roles", tuple(self.collection_roles))
        if not self.collection_roles:
            raise ValueError("collection_roles must not be empty")
        _require_typed_ref("embedding_model_ref", self.embedding_model_ref, required_prefixes=("openvino:", "e5:", "embedding-model:"))
        if self.top_k_per_collection <= 0:
            raise ValueError("top_k_per_collection must be > 0")
        if self.embedding_role != "query":
            raise ValueError("VectorRetrievalPlan embedding_role must be query")
        object.__setattr__(self, "filter_refs", _normalize_refs("filter_refs", self.filter_refs, allow_empty=True))

    @property
    def text_for_embedding(self) -> str:
        return f"query: {self.query_text}"

    @property
    def collection_refs(self) -> tuple[str, ...]:
        return tuple(role.collection_ref for role in self.collection_roles)

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _RETRIEVAL_PLAN_SCHEMA,
            "plan_ref": self.plan_ref,
            "query_text": self.query_text,
            "text_for_embedding": self.text_for_embedding,
            "query_context_refs": list(self.query_context_refs),
            "collection_refs": list(self.collection_refs),
            "collection_roles": [role.to_mapping() for role in self.collection_roles],
            "embedding_model_ref": self.embedding_model_ref,
            "top_k_per_collection": self.top_k_per_collection,
            "embedding_role": self.embedding_role,
            "filter_refs": list(self.filter_refs),
            "qdrant_decides": False,
            "scheduler_orchestrates": True,
        }


@dataclass(frozen=True, slots=True)
class VectorContractInstructionPacket:
    """Packet that can enrich a Scheduler-dispatched specialist demand frame."""

    packet_ref: str
    demand_frame_ref: str
    retrieval_plan: VectorRetrievalPlan
    contract_descriptors: tuple[EmbeddedContractDescriptor, ...]
    output_indexing_targets: tuple[VectorCollectionRole, ...]

    def __post_init__(self) -> None:
        _require_typed_ref("packet_ref", self.packet_ref, required_prefixes=("vector-packet:",))
        _require_typed_ref("demand_frame_ref", self.demand_frame_ref, required_prefixes=("route-frame:",))
        object.__setattr__(self, "contract_descriptors", tuple(self.contract_descriptors))
        object.__setattr__(self, "output_indexing_targets", tuple(self.output_indexing_targets))
        if not self.contract_descriptors:
            raise ValueError("contract_descriptors must not be empty")
        if not self.output_indexing_targets:
            raise ValueError("output_indexing_targets must not be empty")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _PACKET_SCHEMA,
            "packet_ref": self.packet_ref,
            "demand_frame_ref": self.demand_frame_ref,
            "retrieval_plan": self.retrieval_plan.to_mapping(),
            "contract_descriptors": [descriptor.to_mapping() for descriptor in self.contract_descriptors],
            "output_indexing_targets": [target.to_mapping() for target in self.output_indexing_targets],
            "specialist_receives_machine_and_human_contracts": True,
            "github_exchange_only": True,
            "event_bus_observation_only": True,
        }


def build_default_vector_collection_roles(*, embedding_model_ref: str = "openvino:e5-small") -> tuple[VectorCollectionRole, ...]:
    """Return the locked initial Qdrant collection roles for E5 384 vectors."""

    specs = (
        ("context_chunks", "qdrant:context_chunks_e5_384", "context_chunks_e5_384", "Fragments SQL/documents réhydratables."),
        ("contracts", "qdrant:contracts_e5_384", "contracts_e5_384", "Contrats d'instruction et formats de sortie."),
        ("specialist_outputs", "qdrant:specialist_outputs_e5_384", "specialist_outputs_e5_384", "Avis, productions et contradictions spécialistes."),
        ("deliberation_signals", "qdrant:deliberation_signals_e5_384", "deliberation_signals_e5_384", "Signaux sémantiques des chemins et statistiques bus."),
        ("synthesis_candidates", "qdrant:synthesis_candidates_e5_384", "synthesis_candidates_e5_384", "Morceaux candidats pour synthèse finale."),
    )
    return tuple(
        VectorCollectionRole(
            role=role,
            collection_ref=collection_ref,
            collection_name=collection_name,
            embedding_model_ref=embedding_model_ref,
            description=description,
        )
        for role, collection_ref, collection_name, description in specs
    )


def collection_role_by_name(roles: tuple[VectorCollectionRole, ...], role: str) -> VectorCollectionRole:
    for collection_role in roles:
        if collection_role.role == role:
            return collection_role
    raise ValueError(f"missing vector collection role: {role}")


def build_embedded_contract_descriptor(
    contract: SpecialistInstructionContract,
    *,
    collection_role: VectorCollectionRole | None = None,
    embedding_model_ref: str = "openvino:e5-small",
) -> EmbeddedContractDescriptor:
    role = collection_role or collection_role_by_name(build_default_vector_collection_roles(embedding_model_ref=embedding_model_ref), "contracts")
    if role.role != "contracts":
        raise ValueError("contract descriptors must target the contracts collection role")
    seed = f"{contract.contract_ref}|{contract.sql_contract_ref}|{role.collection_ref}"
    descriptor_ref = f"vector-descriptor:contract-{_stable_suffix(seed)}"
    payload_refs = (contract.sql_contract_ref, contract.human_representation.representation_ref, *contract.specialist_refs)
    return EmbeddedContractDescriptor(
        descriptor_ref=descriptor_ref,
        contract_ref=contract.contract_ref,
        sql_contract_ref=contract.sql_contract_ref,
        qdrant_collection_ref=role.collection_ref,
        embedding_model_ref=role.embedding_model_ref,
        embedding_role="passage",
        text_for_embedding=contract.to_embedding_passage(),
        vector_dimension=role.vector_dimension,
        payload_refs=payload_refs,
    )


def build_vector_retrieval_plan_for_specialist_request(
    *,
    query_text: str,
    query_context_refs: tuple[str, ...] = (),
    include_roles: tuple[str, ...] = ("contracts", "context_chunks", "specialist_outputs", "deliberation_signals", "synthesis_candidates"),
    embedding_model_ref: str = "openvino:e5-small",
    top_k_per_collection: int = 8,
    filter_refs: tuple[str, ...] = (),
) -> VectorRetrievalPlan:
    roles = build_default_vector_collection_roles(embedding_model_ref=embedding_model_ref)
    selected = tuple(collection_role_by_name(roles, role) for role in include_roles)
    seed = f"{query_text}|{','.join(include_roles)}|{','.join(query_context_refs)}"
    return VectorRetrievalPlan(
        plan_ref=f"vector-plan:specialist-request-{_stable_suffix(seed)}",
        query_text=query_text,
        query_context_refs=query_context_refs,
        collection_roles=selected,
        embedding_model_ref=embedding_model_ref,
        top_k_per_collection=top_k_per_collection,
        filter_refs=filter_refs,
    )


def build_vector_contract_instruction_packet(
    *,
    demand_frame_ref: str,
    query_text: str,
    contracts: tuple[SpecialistInstructionContract, ...],
    query_context_refs: tuple[str, ...] = (),
    embedding_model_ref: str = "openvino:e5-small",
) -> VectorContractInstructionPacket:
    if not contracts:
        raise ValueError("contracts must not be empty")
    roles = build_default_vector_collection_roles(embedding_model_ref=embedding_model_ref)
    contract_role = collection_role_by_name(roles, "contracts")
    descriptors = tuple(build_embedded_contract_descriptor(contract, collection_role=contract_role) for contract in contracts)
    retrieval_plan = build_vector_retrieval_plan_for_specialist_request(
        query_text=query_text,
        query_context_refs=query_context_refs,
        embedding_model_ref=embedding_model_ref,
    )
    output_targets = (
        collection_role_by_name(roles, "specialist_outputs"),
        collection_role_by_name(roles, "deliberation_signals"),
        collection_role_by_name(roles, "synthesis_candidates"),
    )
    seed = f"{demand_frame_ref}|{retrieval_plan.plan_ref}|{','.join(descriptor.contract_ref for descriptor in descriptors)}"
    return VectorContractInstructionPacket(
        packet_ref=f"vector-packet:contract-instruction-{_stable_suffix(seed)}",
        demand_frame_ref=demand_frame_ref,
        retrieval_plan=retrieval_plan,
        contract_descriptors=descriptors,
        output_indexing_targets=output_targets,
    )


def _require_typed_ref(name: str, value: str, *, required_prefixes: tuple[str, ...] = _ALLOWED_REF_PREFIXES) -> None:
    _require_non_empty(name, value)
    if not _TYPED_REF_RE.match(value):
        raise ValueError(f"{name} must be a typed ref")
    if required_prefixes and not value.startswith(required_prefixes):
        raise ValueError(f"{name} must start with one of {required_prefixes}")


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _require_slug(name: str, value: str) -> None:
    _require_non_empty(name, value)
    if not _SLUG_RE.match(value):
        raise ValueError(f"{name} must be a lowercase slug")


def _normalize_slugs(name: str, values: tuple[str, ...], *, allow_empty: bool) -> tuple[str, ...]:
    normalized = tuple(dict.fromkeys(values))
    if not allow_empty and not normalized:
        raise ValueError(f"{name} must not be empty")
    for value in normalized:
        _require_slug(name, value)
    return normalized


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
