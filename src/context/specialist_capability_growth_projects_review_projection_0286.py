"""Immutable GitHub Projects review projection for specialist capability growth.

Phase 0286-r2 consumes the already-closed 0285 capability-growth evidence and
builds one deterministic, non-authoritative review projection.  The contract
performs no GitHub, ProjectV2, SQL, Qdrant, EventBus, Scheduler or laboratory
mutation.  Later phases may publish the projection only through the existing
operator-authorized GitHub boundaries.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from hashlib import sha256
import json
import re
from typing import Protocol


SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REVIEW_PROJECTION_SCHEMA = (
    "missipy.specialist.capability_growth.projects_review_projection.v1"
)
SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REVIEW_PROJECTION_VERSION = "0286.r2"

_PROJECTS_REVIEW_REF_PREFIXES = ("projects-review:",)
_SPECIALIST_REF_PREFIXES = ("specialist:", "llm:")
_REVISION_REF_PREFIXES = ("revision:",)
_PROPOSAL_REF_PREFIXES = ("proposal:",)
_DECISION_REF_PREFIXES = ("decision:",)
_HISTORY_REF_PREFIXES = ("history:",)
_HISTORY_ENTRY_REF_PREFIXES = ("history-entry:",)
_SQL_REF_PREFIXES = ("sql:",)
_SELECTION_REF_PREFIXES = ("selection:",)
_SCHEDULER_REF_PREFIXES = ("scheduler:",)
_LABORATORY_REF_PREFIXES = ("laboratory:",)
_CONVERSATION_REF_PREFIXES = ("conversation:",)
_CONTEXT_REF_PREFIXES = ("context:", "sql:")
_EVIDENCE_REF_PREFIXES = ("evidence:",)

_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){2,}$")

_PROJECTV2_FIELD_NAMES = (
    "Spécialiste",
    "Révision spécialiste",
    "Capacité proposée",
    "Action capacité",
    "Décision capacité",
    "Statut révision",
    "Référence SQL",
    "Digest décision",
    "Laboratoire",
)


class SpecialistCapabilityGrowthProjectsReviewProjectionError(ValueError):
    """Raised when the closed-loop evidence cannot form a safe review projection."""


class SpecialistCapabilityGrowthClosedLoopReviewSource(Protocol):
    """Structural boundary implemented by the 0285 closed-loop smoke result."""

    @property
    def smoke_digest(self) -> str:
        """Return the deterministic 0285 closed-loop evidence digest."""

    def to_mapping(self, *, include_digest: bool = True) -> Mapping[str, object]:
        """Return the complete closed-loop evidence mapping."""


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthProjectsReviewProjection:
    """One immutable, non-authoritative review projection for GitHub Projects."""

    schema: str
    review_ref: str
    source_smoke_ref: str
    source_smoke_digest_sha256: str
    proposal_ref: str
    proposal_digest_sha256: str
    specialist_ref: str
    specialist_version: str
    revision_ref: str
    revision_digest_sha256: str
    capability: str
    action: str
    evidence_refs: tuple[str, ...]
    decision_ref: str
    decision_digest_sha256: str
    decision_outcome: str
    operator_ref: str
    decision_reason: str
    history_ref: str
    history_entry_ref: str
    history_entry_digest_sha256: str
    history_snapshot_digest_sha256: str
    sql_ref: str
    selection_ref: str
    selection_digest_sha256: str
    scheduler_ref: str
    laboratory_ref: str
    visit_mode: str
    execution_boundary: str
    observation_event_id: str
    conversation_ref: str
    context_refs: tuple[str, ...]
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    review_status: str = field(
        default="approved_selected_observed",
        init=False,
    )
    review_only: bool = field(default=True, init=False)
    github_projects_authoritative: bool = field(default=False, init=False)
    publication_performed: bool = field(default=False, init=False)
    projectv2_mutation_performed: bool = field(default=False, init=False)
    issue_comment_published: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REVIEW_PROJECTION_SCHEMA:
            raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
                "unsupported specialist capability-growth Projects review schema"
            )
        _require_ref(
            "review_ref",
            self.review_ref,
            prefixes=_PROJECTS_REVIEW_REF_PREFIXES,
        )
        _require_ref("source_smoke_ref", self.source_smoke_ref, prefixes=("smoke:",))
        _require_sha256(
            "source_smoke_digest_sha256",
            self.source_smoke_digest_sha256,
        )
        _require_ref("proposal_ref", self.proposal_ref, prefixes=_PROPOSAL_REF_PREFIXES)
        _require_sha256("proposal_digest_sha256", self.proposal_digest_sha256)
        _require_ref(
            "specialist_ref",
            self.specialist_ref,
            prefixes=_SPECIALIST_REF_PREFIXES,
        )
        if not isinstance(self.specialist_version, str) or not _VERSION_RE.fullmatch(
            self.specialist_version
        ):
            raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
                "specialist_version must be a dotted numeric version"
            )
        _require_ref("revision_ref", self.revision_ref, prefixes=_REVISION_REF_PREFIXES)
        _require_sha256("revision_digest_sha256", self.revision_digest_sha256)
        _require_non_empty("capability", self.capability)
        if self.action not in {"add", "refine", "deprecate", "restore"}:
            raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
                "unsupported capability-growth action"
            )
        object.__setattr__(
            self,
            "evidence_refs",
            _normalize_refs(
                "evidence_refs",
                self.evidence_refs,
                prefixes=_EVIDENCE_REF_PREFIXES,
            ),
        )
        _require_ref("decision_ref", self.decision_ref, prefixes=_DECISION_REF_PREFIXES)
        _require_sha256("decision_digest_sha256", self.decision_digest_sha256)
        if self.decision_outcome != "approve":
            raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
                "Projects review projection requires an approved decision"
            )
        _require_ref("operator_ref", self.operator_ref, prefixes=("operator:",))
        _require_non_empty("decision_reason", self.decision_reason)
        _require_ref("history_ref", self.history_ref, prefixes=_HISTORY_REF_PREFIXES)
        _require_ref(
            "history_entry_ref",
            self.history_entry_ref,
            prefixes=_HISTORY_ENTRY_REF_PREFIXES,
        )
        _require_sha256(
            "history_entry_digest_sha256",
            self.history_entry_digest_sha256,
        )
        _require_sha256(
            "history_snapshot_digest_sha256",
            self.history_snapshot_digest_sha256,
        )
        _require_ref("sql_ref", self.sql_ref, prefixes=_SQL_REF_PREFIXES)
        _require_ref("selection_ref", self.selection_ref, prefixes=_SELECTION_REF_PREFIXES)
        _require_sha256("selection_digest_sha256", self.selection_digest_sha256)
        _require_ref("scheduler_ref", self.scheduler_ref, prefixes=_SCHEDULER_REF_PREFIXES)
        _require_ref("laboratory_ref", self.laboratory_ref, prefixes=_LABORATORY_REF_PREFIXES)
        _require_non_empty("visit_mode", self.visit_mode)
        _require_non_empty("execution_boundary", self.execution_boundary)
        _require_non_empty("observation_event_id", self.observation_event_id)
        _require_ref(
            "conversation_ref",
            self.conversation_ref,
            prefixes=_CONVERSATION_REF_PREFIXES,
        )
        object.__setattr__(
            self,
            "context_refs",
            _normalize_refs(
                "context_refs",
                self.context_refs,
                prefixes=_CONTEXT_REF_PREFIXES,
            ),
        )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @property
    def projectv2_field_values(self) -> tuple[tuple[str, str], ...]:
        """Return the future ProjectV2 field values without performing a mutation."""

        values = (
            ("Spécialiste", self.specialist_ref),
            ("Révision spécialiste", self.revision_ref),
            ("Capacité proposée", self.capability),
            ("Action capacité", self.action),
            ("Décision capacité", self.decision_outcome),
            ("Statut révision", self.review_status),
            ("Référence SQL", self.sql_ref),
            ("Digest décision", self.decision_digest_sha256),
            ("Laboratoire", self.laboratory_ref),
        )
        if tuple(name for name, _value in values) != _PROJECTV2_FIELD_NAMES:
            raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
                "ProjectV2 field order drifted from the review contract"
            )
        return values

    @property
    def projection_digest(self) -> str:
        """Return a deterministic digest of the complete review projection."""

        payload = json.dumps(
            self.to_mapping(include_digest=False),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return sha256(payload).hexdigest()

    def to_mapping(self, *, include_digest: bool = True) -> dict[str, object]:
        mapping: dict[str, object] = {
            "schema": self.schema,
            "review_ref": self.review_ref,
            "source_smoke_ref": self.source_smoke_ref,
            "source_smoke_digest_sha256": self.source_smoke_digest_sha256,
            "proposal_ref": self.proposal_ref,
            "proposal_digest_sha256": self.proposal_digest_sha256,
            "specialist_ref": self.specialist_ref,
            "specialist_version": self.specialist_version,
            "revision_ref": self.revision_ref,
            "revision_digest_sha256": self.revision_digest_sha256,
            "capability": self.capability,
            "action": self.action,
            "evidence_refs": list(self.evidence_refs),
            "decision_ref": self.decision_ref,
            "decision_digest_sha256": self.decision_digest_sha256,
            "decision_outcome": self.decision_outcome,
            "operator_ref": self.operator_ref,
            "decision_reason": self.decision_reason,
            "history_ref": self.history_ref,
            "history_entry_ref": self.history_entry_ref,
            "history_entry_digest_sha256": self.history_entry_digest_sha256,
            "history_snapshot_digest_sha256": self.history_snapshot_digest_sha256,
            "sql_ref": self.sql_ref,
            "selection_ref": self.selection_ref,
            "selection_digest_sha256": self.selection_digest_sha256,
            "scheduler_ref": self.scheduler_ref,
            "laboratory_ref": self.laboratory_ref,
            "visit_mode": self.visit_mode,
            "execution_boundary": self.execution_boundary,
            "observation_event_id": self.observation_event_id,
            "conversation_ref": self.conversation_ref,
            "context_refs": list(self.context_refs),
            "metadata": dict(self.metadata),
            "review_status": self.review_status,
            "projectv2_field_values": dict(self.projectv2_field_values),
            "review_only": self.review_only,
            "github_projects_authoritative": self.github_projects_authoritative,
            "publication_performed": self.publication_performed,
            "projectv2_mutation_performed": self.projectv2_mutation_performed,
            "issue_comment_published": self.issue_comment_published,
            "phase_0285_closed_required": True,
            "operator_decision_preserved": True,
            "sql_remains_durable_authority": True,
            "scheduler_remains_only_orchestrator": True,
            "qdrant_authoritative": False,
            "eventbus_observation_reused": True,
            "copilot_authoritative": False,
            "new_scheduler_created": False,
            "new_global_specialist_registry_created": False,
            "new_http_client_created": False,
        }
        if include_digest:
            mapping["projection_digest"] = self.projection_digest
        return mapping


def build_specialist_capability_growth_projects_review_projection(
    source: SpecialistCapabilityGrowthClosedLoopReviewSource,
    *,
    review_ref: str,
    metadata: Sequence[tuple[str, str]] = (),
) -> SpecialistCapabilityGrowthProjectsReviewProjection:
    """Build a deterministic review projection from the closed 0285 evidence."""

    try:
        mapping = source.to_mapping()
        smoke_digest = source.smoke_digest
    except AttributeError as exc:
        raise TypeError(
            "source must implement the 0285 closed-loop review source contract"
        ) from exc
    if not isinstance(mapping, Mapping):
        raise TypeError("closed-loop source to_mapping() must return a mapping")

    _require_closed_loop_boundaries(mapping)

    command = _require_mapping(mapping, "command")
    proposal = _require_mapping(command, "proposal")
    candidate_revision = _require_mapping(command, "candidate_revision")
    decision = _require_mapping(mapping, "decision")
    history_result = _require_mapping(mapping, "history_result")
    history_entry = _require_mapping(history_result, "entry")
    history_snapshot = _require_mapping(history_result, "snapshot")
    selection = _require_mapping(mapping, "selection")
    selected_revision = _require_mapping(selection, "selected_revision")
    observation_publication = _require_mapping(mapping, "observation_publication")
    observation_projection = _require_mapping(observation_publication, "projection")
    passive_read_model = _require_mapping(mapping, "passive_read_model")

    proposal_ref = _require_string(proposal, "proposal_ref")
    proposal_digest = _require_digest(proposal, "proposal_digest")
    specialist_ref = _require_string(proposal, "specialist_ref")
    revision_ref = _require_string(candidate_revision, "revision_ref")
    revision_digest = _require_digest(candidate_revision, "revision_digest")
    decision_ref = _require_string(decision, "decision_ref")
    decision_digest = _require_digest(decision, "decision_digest")
    history_entry_ref = _require_string(history_entry, "entry_ref")
    history_entry_digest = _require_digest(history_entry, "entry_digest")
    sql_ref = _require_string(history_entry, "sql_ref")
    selection_ref = _require_string(selection, "selection_ref")
    selection_digest = _require_digest(selection, "selection_digest")

    correlation_checks = (
        (_require_string(candidate_revision, "source_proposal_ref"), proposal_ref),
        (_require_string(decision, "proposal_ref"), proposal_ref),
        (_require_string(decision, "candidate_revision_ref"), revision_ref),
        (_require_string(history_entry, "entry_ref"), history_entry_ref),
        (_require_string(history_entry, "specialist_ref"), specialist_ref),
        (_require_string(selection, "specialist_ref"), specialist_ref),
        (_require_string(selection, "decision_ref"), decision_ref),
        (_require_string(selection, "history_entry_ref"), history_entry_ref),
        (_require_string(selection, "sql_ref"), sql_ref),
        (_require_string(selected_revision, "revision_ref"), revision_ref),
        (_require_string(observation_projection, "selection_ref"), selection_ref),
        (_require_string(observation_projection, "specialist_ref"), specialist_ref),
        (_require_string(observation_projection, "revision_ref"), revision_ref),
        (_require_string(observation_projection, "proposal_ref"), proposal_ref),
        (_require_string(observation_projection, "decision_ref"), decision_ref),
        (
            _require_string(observation_projection, "history_entry_ref"),
            history_entry_ref,
        ),
        (_require_string(observation_projection, "sql_ref"), sql_ref),
        (_require_string(passive_read_model, "selection_ref"), selection_ref),
        (_require_string(passive_read_model, "specialist_ref"), specialist_ref),
        (_require_string(passive_read_model, "revision_ref"), revision_ref),
        (_require_string(passive_read_model, "proposal_ref"), proposal_ref),
        (_require_string(passive_read_model, "decision_ref"), decision_ref),
        (
            _require_string(passive_read_model, "history_entry_ref"),
            history_entry_ref,
        ),
        (_require_string(passive_read_model, "sql_ref"), sql_ref),
    )
    if any(actual != expected for actual, expected in correlation_checks):
        raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
            "closed-loop review evidence contains a correlation drift"
        )

    digest_checks = (
        (
            _require_digest(candidate_revision, "source_proposal_digest_sha256"),
            proposal_digest,
        ),
        (_require_digest(decision, "proposal_digest_sha256"), proposal_digest),
        (
            _require_digest(decision, "candidate_revision_digest_sha256"),
            revision_digest,
        ),
        (
            _require_digest(selection, "history_entry_digest_sha256"),
            history_entry_digest,
        ),
        (
            _require_digest(observation_projection, "selection_digest_sha256"),
            selection_digest,
        ),
    )
    if any(actual != expected for actual, expected in digest_checks):
        raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
            "closed-loop review evidence contains a digest drift"
        )

    capability = _require_string(proposal, "capability")
    if _require_string(selection, "capability") != capability:
        raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
            "selected capability must match the approved proposal"
        )
    conversation_ref = _require_string(proposal, "conversation_ref")
    if _require_string(selection, "conversation_ref") != conversation_ref:
        raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
            "selection must preserve proposal conversation_ref"
        )
    context_refs = _require_string_tuple(proposal, "context_refs")
    if _require_string_tuple(selection, "context_refs") != context_refs:
        raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
            "selection must preserve proposal context_refs"
        )

    evidence_refs = tuple(
        _require_string(item, "evidence_ref")
        for item in _require_mapping_sequence(proposal, "evidence_refs")
    )

    return SpecialistCapabilityGrowthProjectsReviewProjection(
        schema=SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REVIEW_PROJECTION_SCHEMA,
        review_ref=review_ref,
        source_smoke_ref=_require_string(command, "smoke_ref"),
        source_smoke_digest_sha256=_validated_digest(
            "source smoke digest",
            smoke_digest,
        ),
        proposal_ref=proposal_ref,
        proposal_digest_sha256=proposal_digest,
        specialist_ref=specialist_ref,
        specialist_version=_require_string(candidate_revision, "specialist_version"),
        revision_ref=revision_ref,
        revision_digest_sha256=revision_digest,
        capability=capability,
        action=_require_string(proposal, "action"),
        evidence_refs=evidence_refs,
        decision_ref=decision_ref,
        decision_digest_sha256=decision_digest,
        decision_outcome=_require_string(decision, "outcome"),
        operator_ref=_require_string(decision, "operator_ref"),
        decision_reason=_require_string(decision, "reason"),
        history_ref=_require_string(history_entry, "history_ref"),
        history_entry_ref=history_entry_ref,
        history_entry_digest_sha256=history_entry_digest,
        history_snapshot_digest_sha256=_require_digest(
            history_snapshot,
            "snapshot_digest",
        ),
        sql_ref=sql_ref,
        selection_ref=selection_ref,
        selection_digest_sha256=selection_digest,
        scheduler_ref=_require_string(selection, "scheduler_ref"),
        laboratory_ref=_require_string(selection, "laboratory_ref"),
        visit_mode=_require_string(selection, "visit_mode"),
        execution_boundary=_require_string(selection, "execution_boundary"),
        observation_event_id=_require_string(observation_publication, "event_id"),
        conversation_ref=conversation_ref,
        context_refs=context_refs,
        metadata=tuple(metadata),
    )


def _require_closed_loop_boundaries(mapping: Mapping[str, object]) -> None:
    required_true = (
        "phase_0285_closed",
        "operator_gate_closed",
        "durable_sql_history_recorded",
        "scheduler_selection_performed",
        "laboratory_execution_performed",
        "eventbus_observation_published",
        "passive_supervisor_read_model_valid",
    )
    for key in required_true:
        if mapping.get(key) is not True:
            raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
                f"closed-loop review source requires {key}=true"
            )
    if mapping.get("github_mutation_performed") is not False:
        raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
            "0285 source evidence must not contain a GitHub mutation"
        )
    if mapping.get("qdrant_authoritative") is not False:
        raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
            "Qdrant must remain non-authoritative"
        )
    issues = mapping.get("issues")
    if not isinstance(issues, Sequence) or isinstance(issues, (str, bytes)):
        raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
            "closed-loop issues must be a sequence"
        )
    if tuple(issues):
        raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
            "closed-loop review source must not contain unresolved issues"
        )


def _require_mapping(mapping: Mapping[str, object], key: str) -> Mapping[str, object]:
    value = mapping.get(key)
    if not isinstance(value, Mapping):
        raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
            f"{key} must be a mapping"
        )
    return value


def _require_mapping_sequence(
    mapping: Mapping[str, object],
    key: str,
) -> tuple[Mapping[str, object], ...]:
    value = mapping.get(key)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
            f"{key} must be a sequence of mappings"
        )
    items = tuple(value)
    if not items or not all(isinstance(item, Mapping) for item in items):
        raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
            f"{key} must contain at least one mapping"
        )
    return items  # type: ignore[return-value]


def _require_string(mapping: Mapping[str, object], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
            f"{key} must be a non-empty string"
        )
    return value.strip()


def _require_digest(mapping: Mapping[str, object], key: str) -> str:
    return _validated_digest(key, _require_string(mapping, key))


def _validated_digest(name: str, value: str) -> str:
    if not _SHA256_RE.fullmatch(value):
        raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
            f"{name} must be a lowercase SHA-256 digest"
        )
    return value


def _require_string_tuple(mapping: Mapping[str, object], key: str) -> tuple[str, ...]:
    value = mapping.get(key)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
            f"{key} must be a sequence"
        )
    items = tuple(value)
    if not items or not all(isinstance(item, str) and item.strip() for item in items):
        raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
            f"{key} must contain non-empty strings"
        )
    return tuple(item.strip() for item in items)


def _require_ref(name: str, value: str, *, prefixes: tuple[str, ...]) -> None:
    if not isinstance(value, str) or not _TYPED_REF_RE.fullmatch(value):
        raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
            f"{name} must be a typed reference"
        )
    if not value.startswith(prefixes):
        raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
            f"{name} uses an unsupported reference prefix"
        )


def _require_sha256(name: str, value: str) -> None:
    _validated_digest(name, value)


def _require_non_empty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
            f"{name} must be non-empty"
        )


def _normalize_refs(
    name: str,
    values: Sequence[str],
    *,
    prefixes: tuple[str, ...],
) -> tuple[str, ...]:
    normalized = tuple(sorted(dict.fromkeys(values)))
    if not normalized:
        raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
            f"{name} must not be empty"
        )
    for value in normalized:
        _require_ref(name, value, prefixes=prefixes)
    return normalized


def _normalize_metadata(
    values: Sequence[tuple[str, str]],
) -> tuple[tuple[str, str], ...]:
    normalized: dict[str, str] = {}
    for key, value in values:
        if not isinstance(key, str) or not key.strip():
            raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
                "metadata keys must be non-empty strings"
            )
        if not isinstance(value, str):
            raise SpecialistCapabilityGrowthProjectsReviewProjectionError(
                "metadata values must be strings"
            )
        normalized[key.strip()] = value.strip()
    return tuple(sorted(normalized.items()))


__all__ = (
    "SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REVIEW_PROJECTION_SCHEMA",
    "SPECIALIST_CAPABILITY_GROWTH_PROJECTS_REVIEW_PROJECTION_VERSION",
    "SpecialistCapabilityGrowthClosedLoopReviewSource",
    "SpecialistCapabilityGrowthProjectsReviewProjection",
    "SpecialistCapabilityGrowthProjectsReviewProjectionError",
    "build_specialist_capability_growth_projects_review_projection",
)
