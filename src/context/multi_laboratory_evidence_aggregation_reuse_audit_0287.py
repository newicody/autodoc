"""Source-only reuse audit for multi-laboratory evidence aggregation.

Phase 0287-r1 inventories existing laboratory, specialist, evidence, operator,
durable-history and Projects closure surfaces before any aggregation contract
is introduced. The audit imports and executes none of the inspected modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

MULTI_LABORATORY_EVIDENCE_AGGREGATION_REUSE_AUDIT_SCHEMA = (
    "missipy.multi_laboratory.evidence_aggregation_reuse_audit.v1"
)
MULTI_LABORATORY_EVIDENCE_AGGREGATION_REUSE_AUDIT_VERSION = "0287.r1"


@dataclass(frozen=True, slots=True)
class AuditSurfaceRequirement:
    path: str
    role: str
    markers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DevelopmentPhase:
    patch_id: str
    requirements: tuple[AuditSurfaceRequirement, ...]


REQUIRED_REUSE_SURFACES: tuple[AuditSurfaceRequirement, ...] = (
    AuditSurfaceRequirement(
        path="src/context/laboratory_framework_contract_0273.py",
        role="laboratory visit/result evidence and provenance vocabulary",
        markers=(
            "class LaboratoryVisitRequest",
            "class LaboratoryVisitResult",
            "evidence_refs",
            "provenance_refs",
            "requested_laboratory_refs",
        ),
    ),
    AuditSurfaceRequirement(
        path="src/context/specialist_laboratory_message_contract_0284.py",
        role="immutable specialist/laboratory conversation continuity",
        markers=(
            "class SpecialistLaboratoryMessage",
            "class SpecialistLaboratoryConversation",
            "conversation_ref",
            "context_refs",
            "evidence_refs",
        ),
    ),
    AuditSurfaceRequirement(
        path="src/context/specialist_laboratory_transfer_contract_0284.py",
        role="cross-laboratory visit and transfer continuity",
        markers=(
            "class SpecialistTransferRequest",
            "class SpecialistTransferVisitPlan",
            "class SpecialistTransferResult",
            "origin_laboratory_ref",
            "target_laboratory_ref",
            "validate_specialist_transfer_chain",
        ),
    ),
    AuditSurfaceRequirement(
        path="src/context/specialist_capability_growth_proposal_contract_0285.py",
        role="digest-bound evidence references and claims",
        markers=(
            "class SpecialistCapabilityEvidenceRef",
            "class SpecialistCapabilityGrowthProposal",
            "digest_sha256",
            "source_ref",
            "operator_review",
        ),
    ),
    AuditSurfaceRequirement(
        path="src/context/specialist_capability_growth_operator_gate_0285.py",
        role="explicit approve/reject/defer operator authority",
        markers=(
            "class SpecialistCapabilityGrowthDecision",
            '"approve"',
            '"reject"',
            '"defer"',
            "revision_authorized",
        ),
    ),
    AuditSurfaceRequirement(
        path="src/context/specialist_capability_growth_durable_history_0285.py",
        role="append-only SQL-authority history pattern",
        markers=(
            "class SpecialistCapabilityGrowthHistoryEntry",
            "class SpecialistCapabilityGrowthHistoryPort",
            "sql_ref",
            "authority_contract",
        ),
    ),
    AuditSurfaceRequirement(
        path="src/context/specialist_capability_growth_observation_projection_0285.py",
        role="passive EventBus/read-model projection pattern",
        markers=(
            "class SpecialistCapabilityGrowthObservationProjection",
            "class SpecialistCapabilityGrowthPassiveReadModel",
            "eventbus_observation_only",
            "eventbus_observation_published",
        ),
    ),
    AuditSurfaceRequirement(
        path="src/context/specialist_capability_growth_projects_closed_loop_smoke_0286.py",
        role="closed Projects workflow and authority split",
        markers=(
            "class SpecialistCapabilityGrowthProjectsClosedLoopSmokeResult",
            "phase_0286_closed",
            "github_projects_authoritative",
            "sql_remains_durable_authority",
            "scheduler_remains_only_orchestrator",
        ),
    ),
    AuditSurfaceRequirement(
        path="templates/github/projects-repository/INSTALLATION.md",
        role="cumulative Projects installation guide",
        markers=(
            "Version du guide : `0286-r4`.",
            "newicody/projects",
            "Ne pas utiliser `--delete`",
        ),
    ),
)

DEVELOPMENT_PHASES: tuple[DevelopmentPhase, ...] = (
    DevelopmentPhase(
        patch_id="0287-r2-multi-laboratory-evidence-aggregation-contract",
        requirements=(
            AuditSurfaceRequirement(
                path=(
                    "src/context/"
                    "multi_laboratory_evidence_aggregation_contract_0287.py"
                ),
                role="canonical immutable evidence item and aggregate",
                markers=(
                    "class MultiLaboratoryEvidenceItem",
                    "class MultiLaboratoryEvidenceAggregate",
                    "aggregation_digest",
                ),
            ),
        ),
    ),
    DevelopmentPhase(
        patch_id="0287-r3-multi-laboratory-evidence-provenance-contract",
        requirements=(
            AuditSurfaceRequirement(
                path=(
                    "src/context/"
                    "multi_laboratory_evidence_provenance_contract_0287.py"
                ),
                role="laboratory/visit/specialist provenance chain",
                markers=(
                    "class MultiLaboratoryEvidenceProvenance",
                    "laboratory_ref",
                    "visit_ref",
                    "specialist_ref",
                    "source_ref",
                ),
            ),
        ),
    ),
    DevelopmentPhase(
        patch_id="0287-r4-multi-laboratory-evidence-digest-deduplication",
        requirements=(
            AuditSurfaceRequirement(
                path=(
                    "src/context/"
                    "multi_laboratory_evidence_digest_deduplication_0287.py"
                ),
                role="content and source digest deduplication",
                markers=(
                    "class MultiLaboratoryEvidenceDeduplicationResult",
                    "duplicate_evidence_refs",
                    "canonical_evidence_refs",
                ),
            ),
        ),
    ),
    DevelopmentPhase(
        patch_id="0287-r5-multi-laboratory-evidence-contradiction-detection",
        requirements=(
            AuditSurfaceRequirement(
                path=(
                    "src/context/"
                    "multi_laboratory_evidence_contradiction_detection_0287.py"
                ),
                role="explicit incompatible-claim detection",
                markers=(
                    "class MultiLaboratoryEvidenceContradiction",
                    "contradiction_refs",
                    "unresolved_contradictions",
                ),
            ),
        ),
    ),
    DevelopmentPhase(
        patch_id="0287-r6-multi-laboratory-evidence-operator-weighting-policy",
        requirements=(
            AuditSurfaceRequirement(
                path=(
                    "src/context/"
                    "multi_laboratory_evidence_operator_weighting_policy_0287.py"
                ),
                role="operator-authorized evidence weighting",
                markers=(
                    "class MultiLaboratoryEvidenceWeightingDecision",
                    "operator_ref",
                    "approve",
                    "weighting_digest",
                ),
            ),
        ),
    ),
    DevelopmentPhase(
        patch_id="0287-r7-multi-laboratory-evidence-durable-history",
        requirements=(
            AuditSurfaceRequirement(
                path=(
                    "src/context/"
                    "multi_laboratory_evidence_durable_history_0287.py"
                ),
                role="append-only SQL-authority aggregation history",
                markers=(
                    "class MultiLaboratoryEvidenceHistoryEntry",
                    "class MultiLaboratoryEvidenceHistoryPort",
                    "sql_ref",
                    "append",
                ),
            ),
        ),
    ),
    DevelopmentPhase(
        patch_id=(
            "0287-r8-multi-laboratory-evidence-"
            "scheduler-selection-constraints"
        ),
        requirements=(
            AuditSurfaceRequirement(
                path=(
                    "src/context/"
                    "multi_laboratory_evidence_scheduler_selection_0287.py"
                ),
                role="Scheduler-owned selection constraints",
                markers=(
                    "class MultiLaboratoryEvidenceSelectionCommand",
                    "scheduler_selection_performed",
                    "unresolved_contradictions",
                ),
            ),
        ),
    ),
    DevelopmentPhase(
        patch_id="0287-r9-multi-laboratory-evidence-observation-projection",
        requirements=(
            AuditSurfaceRequirement(
                path=(
                    "src/context/"
                    "multi_laboratory_evidence_observation_projection_0287.py"
                ),
                role="passive EventBus/PassiveSupervisor projection",
                markers=(
                    "class MultiLaboratoryEvidenceObservationProjection",
                    "eventbus_observation_published",
                    "scheduler_remains_only_orchestrator",
                ),
            ),
        ),
    ),
    DevelopmentPhase(
        patch_id="0287-r10-multi-laboratory-evidence-closed-loop-smoke",
        requirements=(
            AuditSurfaceRequirement(
                path=(
                    "src/context/"
                    "multi_laboratory_evidence_closed_loop_smoke_0287.py"
                ),
                role="multi-laboratory aggregation closed-loop proof",
                markers=(
                    "class MultiLaboratoryEvidenceClosedLoopSmokeResult",
                    "phase_0287_closed",
                    "sql_remains_durable_authority",
                ),
            ),
        ),
    ),
)


@dataclass(frozen=True, slots=True)
class MultiLaboratoryEvidenceAggregationReuseAuditResult:
    schema: str
    valid: bool
    issues: tuple[str, ...]
    scanned_file_count: int
    missing_reuse_surfaces: tuple[str, ...]
    incomplete_reuse_surfaces: tuple[str, ...]
    completed_phases: tuple[str, ...]
    next_recommended_patch: str
    visit_evidence_vocabulary_reusable: bool
    transfer_continuity_reusable: bool
    digest_bound_evidence_reusable: bool
    operator_gate_reusable: bool
    sql_history_pattern_reusable: bool
    passive_observation_pattern_reusable: bool
    projects_closed_loop_reusable: bool
    canonical_multi_laboratory_aggregate_missing: bool
    contradiction_policy_missing: bool
    weighting_policy_missing: bool
    scheduler_remains_only_orchestrator: bool = True
    sql_remains_durable_authority: bool = True
    qdrant_remains_projection_and_recall: bool = True
    eventbus_remains_observation_only: bool = True
    github_projects_remains_workflow_projection: bool = True
    laboratory_self_authorization_allowed: bool = False
    specialist_self_authorization_allowed: bool = False
    new_scheduler_required: bool = False
    new_laboratory_manager_required: bool = False
    new_global_evidence_registry_required: bool = False

    def to_mapping(self) -> dict[str, object]:
        return {
            name: (
                list(value)
                if isinstance(value := getattr(self, name), tuple)
                else value
            )
            for name in self.__dataclass_fields__
        }


def load_audit_sources(root: Path) -> dict[str, str]:
    paths = {item.path for item in REQUIRED_REUSE_SURFACES}
    for phase in DEVELOPMENT_PHASES:
        paths.update(item.path for item in phase.requirements)
    sources: dict[str, str] = {}
    for relative in sorted(paths):
        path = root / relative
        if path.is_file():
            sources[relative] = path.read_text(encoding="utf-8")
    return sources


def audit_multi_laboratory_evidence_aggregation_reuse(
    sources: Mapping[str, str],
) -> MultiLaboratoryEvidenceAggregationReuseAuditResult:
    missing: list[str] = []
    incomplete: list[str] = []
    issues: list[str] = []

    for requirement in REQUIRED_REUSE_SURFACES:
        text = sources.get(requirement.path)
        if text is None:
            missing.append(requirement.path)
            issues.append(f"missing reuse surface: {requirement.path}")
            continue
        absent = tuple(
            marker for marker in requirement.markers if marker not in text
        )
        if absent:
            incomplete.append(requirement.path)
            issues.append(
                f"incomplete reuse surface: {requirement.path}: "
                + ", ".join(absent)
            )

    completed: list[str] = []
    for phase in DEVELOPMENT_PHASES:
        if all(
            _surface_complete(requirement, sources)
            for requirement in phase.requirements
        ):
            completed.append(phase.patch_id)
        else:
            break

    next_patch = (
        "0287-complete"
        if len(completed) == len(DEVELOPMENT_PHASES)
        else DEVELOPMENT_PHASES[len(completed)].patch_id
    )

    return MultiLaboratoryEvidenceAggregationReuseAuditResult(
        schema=MULTI_LABORATORY_EVIDENCE_AGGREGATION_REUSE_AUDIT_SCHEMA,
        valid=not issues,
        issues=tuple(issues),
        scanned_file_count=len(sources),
        missing_reuse_surfaces=tuple(missing),
        incomplete_reuse_surfaces=tuple(incomplete),
        completed_phases=tuple(completed),
        next_recommended_patch=next_patch,
        visit_evidence_vocabulary_reusable=_surface_complete(
            REQUIRED_REUSE_SURFACES[0], sources
        ),
        transfer_continuity_reusable=_surface_complete(
            REQUIRED_REUSE_SURFACES[2], sources
        ),
        digest_bound_evidence_reusable=_surface_complete(
            REQUIRED_REUSE_SURFACES[3], sources
        ),
        operator_gate_reusable=_surface_complete(
            REQUIRED_REUSE_SURFACES[4], sources
        ),
        sql_history_pattern_reusable=_surface_complete(
            REQUIRED_REUSE_SURFACES[5], sources
        ),
        passive_observation_pattern_reusable=_surface_complete(
            REQUIRED_REUSE_SURFACES[6], sources
        ),
        projects_closed_loop_reusable=_surface_complete(
            REQUIRED_REUSE_SURFACES[7], sources
        ),
        canonical_multi_laboratory_aggregate_missing=(
            DEVELOPMENT_PHASES[0].patch_id not in completed
        ),
        contradiction_policy_missing=(
            DEVELOPMENT_PHASES[3].patch_id not in completed
        ),
        weighting_policy_missing=(
            DEVELOPMENT_PHASES[4].patch_id not in completed
        ),
    )


def _surface_complete(
    requirement: AuditSurfaceRequirement,
    sources: Mapping[str, str],
) -> bool:
    text = sources.get(requirement.path)
    return text is not None and all(
        marker in text for marker in requirement.markers
    )


__all__ = (
    "DEVELOPMENT_PHASES",
    "MULTI_LABORATORY_EVIDENCE_AGGREGATION_REUSE_AUDIT_SCHEMA",
    "MULTI_LABORATORY_EVIDENCE_AGGREGATION_REUSE_AUDIT_VERSION",
    "REQUIRED_REUSE_SURFACES",
    "AuditSurfaceRequirement",
    "DevelopmentPhase",
    "MultiLaboratoryEvidenceAggregationReuseAuditResult",
    "audit_multi_laboratory_evidence_aggregation_reuse",
    "load_audit_sources",
)
