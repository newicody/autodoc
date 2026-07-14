"""Source-only reuse audit for controlled portable-specialist capability growth.

The audit deliberately reads source text instead of importing runtime modules.  It
proves which existing contracts must be extended and detects future phase
surfaces without constructing a Scheduler, laboratory, EventBus, SQL adapter,
vector backend, or remote client.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Mapping


SPECIALIST_CAPABILITY_GROWTH_REUSE_AUDIT_SCHEMA = (
    "missipy.specialist.capability_growth_reuse_audit.v1"
)


@dataclass(frozen=True, slots=True)
class RequiredReuseSurface:
    """One existing source surface and the stable markers expected within it."""

    path: str
    markers: tuple[str, ...] = ()


REQUIRED_REUSE_SURFACES: tuple[RequiredReuseSurface, ...] = (
    RequiredReuseSurface(
        "src/context/portable_specialist_contract_0284.py",
        (
            "class SpecialistCapabilityContract",
            "class PortableSpecialistDescriptor",
            "specialist_version",
            "capabilities",
        ),
    ),
    RequiredReuseSurface(
        "src/context/context_variation_core.py",
        ("class ContextTrajectoryStep", "capability_hint", "max_specialist_calls"),
    ),
    RequiredReuseSurface(
        "src/context/scheduler_deliberation_route_contract.py",
        ("class SpecialistDispatchCommand", "class SpecialistDemandFrame"),
    ),
    RequiredReuseSurface(
        "src/context/laboratory_framework_contract_0273.py",
        ("class LaboratoryDescriptor", "capabilities"),
    ),
    RequiredReuseSurface(
        "src/context/specialist_laboratory_message_contract_0284.py",
        ("class SpecialistLaboratoryMessage", "evidence_refs", "return_route_ref"),
    ),
    RequiredReuseSurface(
        "src/context/specialist_laboratory_transfer_contract_0284.py",
        ("class SpecialistTransferRequest", "parent_transfer_ref", "evidence_refs"),
    ),
    RequiredReuseSurface(
        "src/context/portable_specialist_real_memory_closure_0284.py",
        (
            "class PortableSpecialistRealMemoryClosureResult",
            "real_sql_authority_used",
            "qdrant_returns_references_only",
        ),
    ),
    RequiredReuseSurface(
        "src/context/specialists_laboratories_live_path_evidence_0284.py",
        (
            "class SpecialistsLaboratoriesLivePathEvidenceResult",
            "phase_0284_closed",
            "evidence_digest",
        ),
    ),
    RequiredReuseSurface("src/context/closed_result_frame_eventbus_observation_0265.py"),
    RequiredReuseSurface(
        "src/context/passive_supervisor_closed_result_frame_observation_0266.py"
    ),
    RequiredReuseSurface("src/context/event_bus_cell_lens_live_bridge_0284.py"),
    RequiredReuseSurface(
        "src/context/github_operator_laboratory_advisory_projection_0281.py"
    ),
    RequiredReuseSurface(
        "src/context/github_project_v2_append_only_cycle_history_0282.py"
    ),
)


@dataclass(frozen=True, slots=True)
class CapabilityGrowthPhase:
    """One planned phase and the class surfaces that make it complete."""

    patch_id: str
    label: str
    required_classes: tuple[str, ...]


CAPABILITY_GROWTH_PHASES: tuple[CapabilityGrowthPhase, ...] = (
    CapabilityGrowthPhase(
        "0285-r2-specialist-capability-growth-proposal-contract",
        "immutable evidence-backed proposal",
        ("SpecialistCapabilityEvidenceRef", "SpecialistCapabilityGrowthProposal"),
    ),
    CapabilityGrowthPhase(
        "0285-r3-portable-specialist-revision-lineage-contract",
        "stable identity and immutable revision lineage",
        ("PortableSpecialistRevision", "SpecialistRevisionLineage"),
    ),
    CapabilityGrowthPhase(
        "0285-r4-specialist-capability-growth-operator-gate",
        "explicit operator decision boundary",
        (
            "SpecialistCapabilityGrowthDecision",
            "SpecialistCapabilityGrowthOperatorGate",
        ),
    ),
    CapabilityGrowthPhase(
        "0285-r5-specialist-capability-growth-durable-history",
        "SQL-authoritative append-only history port",
        (
            "SpecialistCapabilityGrowthHistoryEntry",
            "SpecialistCapabilityGrowthHistoryStorePort",
        ),
    ),
    CapabilityGrowthPhase(
        "0285-r6-scheduler-approved-specialist-revision-selection",
        "Scheduler selection of approved revisions only",
        (
            "ApprovedSpecialistRevisionSelection",
            "SchedulerApprovedSpecialistRevisionSelector",
        ),
    ),
    CapabilityGrowthPhase(
        "0285-r7-specialist-capability-growth-observation-projection",
        "observation-only EventBus, PassiveSupervisor, and Cell Lens projection",
        (
            "SpecialistCapabilityGrowthObservedEvent",
            "SpecialistCapabilityGrowthObservationProjection",
        ),
    ),
    CapabilityGrowthPhase(
        "0285-r8-specialist-capability-growth-closed-loop-smoke",
        "controlled proposal-to-approved-revision closed loop",
        ("SpecialistCapabilityGrowthClosedLoopSmokeResult",),
    ),
)


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthReuseAuditResult:
    """Deterministic outcome of the source-only 0285-r1 audit."""

    valid: bool
    issues: tuple[str, ...]
    inspected_paths: tuple[str, ...]
    source_digest: str
    discovered_classes: tuple[str, ...]
    completed_patch_ids: tuple[str, ...]
    next_recommended_patch: str
    findings: tuple[str, ...]
    installation_reviewed: bool = True
    installation_modified: bool = False
    schema: str = SPECIALIST_CAPABILITY_GROWTH_REUSE_AUDIT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != SPECIALIST_CAPABILITY_GROWTH_REUSE_AUDIT_SCHEMA:
            raise ValueError("unsupported specialist capability growth audit schema")
        if self.valid != (not self.issues):
            raise ValueError("valid must match the absence of audit issues")

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "issues": list(self.issues),
            "inspected_paths": list(self.inspected_paths),
            "source_digest": self.source_digest,
            "discovered_classes": list(self.discovered_classes),
            "completed_patch_ids": list(self.completed_patch_ids),
            "next_recommended_patch": self.next_recommended_patch,
            "findings": list(self.findings),
            "installation_reviewed": self.installation_reviewed,
            "installation_modified": self.installation_modified,
            "existing_portable_descriptor_reused": True,
            "existing_scheduler_remains_only_orchestrator": True,
            "sql_remains_durable_authority": True,
            "qdrant_remains_projection_and_recall_only": True,
            "eventbus_remains_observation_only": True,
            "github_remains_review_and_workflow_surface": True,
            "specialist_self_authorization_allowed": False,
            "laboratory_self_authorization_allowed": False,
            "copilot_self_authorization_allowed": False,
            "automatic_capability_learning_enabled": False,
            "new_scheduler_added": False,
            "new_laboratory_manager_added": False,
            "new_global_specialist_registry_added": False,
        }


def _source_digest(sources: Mapping[str, str]) -> str:
    payload = json.dumps(
        {path: sources[path] for path in sorted(sources)},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return sha256(payload).hexdigest()


def _class_names(source: str) -> tuple[str, ...]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return ()
    return tuple(
        sorted(
            {
                node.name
                for node in ast.walk(tree)
                if isinstance(node, (ast.ClassDef, ast.AsyncFunctionDef))
                and isinstance(node, ast.ClassDef)
            }
        )
    )


def _findings() -> tuple[str, ...]:
    return (
        "PortableSpecialistDescriptor already owns stable specialist identity, version, capabilities, contracts, and laboratory bindings.",
        "ContextTrajectoryStep already carries capability_hint and the exploration budget already limits specialist calls.",
        "Scheduler deliberation and dispatch contracts already provide the only orchestration boundary.",
        "Laboratory descriptors already advertise capabilities; laboratories must not authorize specialist growth.",
        "Specialist/laboratory messages and transfers already preserve evidence and continuity references.",
        "Phase 0284 already proves SQL authority, Qdrant reference-only recall, and correlated real-path evidence.",
        "EventBus, PassiveSupervisor, and Cell Lens surfaces already support observation without command authority.",
        "GitHub Projects and Copilot remain review/advisory surfaces and cannot approve a capability revision.",
        "The missing chain is proposal, evidence, operator decision, immutable revision, durable history, approved selection, observation, and smoke.",
    )


def audit_specialist_capability_growth_reuse(
    sources: Mapping[str, str],
) -> SpecialistCapabilityGrowthReuseAuditResult:
    """Audit existing sources and identify the first missing 0285 growth phase.

    The function never imports inspected sources.  A caller may pass additional
    source files so future phase classes can be detected as the roadmap advances.
    """

    if not isinstance(sources, Mapping):
        raise TypeError("sources must be a mapping")

    normalized: dict[str, str] = {}
    issues: list[str] = []
    for path, source in sources.items():
        if not isinstance(path, str) or not path.strip():
            raise ValueError("source paths must be non-empty strings")
        if not isinstance(source, str):
            raise TypeError(f"source for {path!r} must be text")
        normalized[path] = source

    for surface in REQUIRED_REUSE_SURFACES:
        source = normalized.get(surface.path)
        if source is None:
            issues.append(f"missing required reuse surface: {surface.path}")
            continue
        for marker in surface.markers:
            if marker not in source:
                issues.append(f"missing marker {marker!r} in {surface.path}")

    discovered_classes = tuple(
        sorted(
            {
                class_name
                for source in normalized.values()
                for class_name in _class_names(source)
            }
        )
    )
    discovered_set = set(discovered_classes)

    completed: list[str] = []
    next_patch = "0285-complete"
    for phase in CAPABILITY_GROWTH_PHASES:
        if all(name in discovered_set for name in phase.required_classes):
            completed.append(phase.patch_id)
            continue
        next_patch = phase.patch_id
        break

    inspected = tuple(sorted(normalized))
    return SpecialistCapabilityGrowthReuseAuditResult(
        valid=not issues,
        issues=tuple(sorted(set(issues))),
        inspected_paths=inspected,
        source_digest=_source_digest(normalized),
        discovered_classes=discovered_classes,
        completed_patch_ids=tuple(completed),
        next_recommended_patch=next_patch,
        findings=_findings(),
    )
