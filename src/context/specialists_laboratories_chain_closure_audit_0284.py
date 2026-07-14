"""Source-only closure audit for the phase 0284 specialist chain.

The audit distinguishes implementation completeness from operational closure.
It reads source text supplied by an IO adapter and optional immutable runtime
evidence.  It imports and executes none of the inspected specialist, Scheduler,
SQL, OpenVINO, Qdrant, GitHub or ProjectV2 modules.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

PHASE0284_CLOSURE_AUDIT_VERSION = "0284.r8"
PHASE0284_CLOSURE_AUDIT_SCHEMA = (
    "missipy.specialists_laboratories.chain_closure_audit.v1"
)


@dataclass(frozen=True, slots=True)
class ClosureSurfaceRequirement:
    """One source surface and the markers required for phase closure."""

    path: str
    role: str
    markers: tuple[str, ...]


REQUIRED_CHAIN_SURFACES: tuple[ClosureSurfaceRequirement, ...] = (
    ClosureSurfaceRequirement(
        path="src/context/specialists_laboratories_chain_reuse_audit_0284.py",
        role="reuse-first phase entry audit",
        markers=(
            "class SpecialistsLaboratoriesChainReuseAuditResult",
            'return "0284-r5-specialists-laboratories-existing-chain-smoke"',
            "existing_scheduler_must_remain_orchestrator",
        ),
    ),
    ClosureSurfaceRequirement(
        path="src/context/portable_specialist_contract_0284.py",
        role="portable specialist identity and capability contract",
        markers=(
            "class PortableSpecialistDescriptor",
            "class SpecialistCapabilityContract",
            "class SpecialistExecutionProfile",
            "class SpecialistLaboratoryBinding",
            "def validate_portable_specialist_visit_contract",
        ),
    ),
    ClosureSurfaceRequirement(
        path="src/context/specialist_laboratory_message_contract_0284.py",
        role="specialist/laboratory conversation contract",
        markers=(
            "class SpecialistLaboratoryMessage",
            "class SpecialistLaboratoryConversation",
            "def build_specialist_demand_message",
            "def build_specialist_opinion_message",
            "def validate_specialist_laboratory_conversation",
        ),
    ),
    ClosureSurfaceRequirement(
        path="src/context/specialist_laboratory_transfer_contract_0284.py",
        role="visit and transfer continuity contract",
        markers=(
            "class SpecialistTransferRequest",
            "class SpecialistTransferVisitPlan",
            "class SpecialistTransferResult",
            "def validate_specialist_transfer_chain",
        ),
    ),
    ClosureSurfaceRequirement(
        path="src/context/specialists_laboratories_existing_chain_smoke_0284.py",
        role="existing-Scheduler fake specialist smoke",
        markers=(
            "class PortableSpecialistExistingChainSmokeCommand",
            "class PortableSpecialistExistingChainSmokeResult",
            "run_portable_specialist_existing_chain_smoke",
            '"Scheduler.run()"',
            "fake_specialist_executed",
        ),
    ),
    ClosureSurfaceRequirement(
        path="src/context/portable_specialist_real_memory_closure_0284.py",
        role="real SQL/OpenVINO/Qdrant memory composition",
        markers=(
            "class PortableSpecialistRealMemoryClosureCommand",
            "class PortableSpecialistRealMemoryClosureResult",
            "run_portable_specialist_real_memory_closure",
            "real_openvino_e5_used",
            "real_qdrant_projection_used",
            "real_qdrant_recall_used",
            "sql_rehydration_verified",
        ),
    ),
    ClosureSurfaceRequirement(
        path="src/context/projects_copilot_specialist_integrated_smoke_0284.py",
        role="Projects/Copilot/specialist integrated composition",
        markers=(
            "class ProjectsCopilotSpecialistIntegratedSmokeCommand",
            "class ProjectsCopilotSpecialistIntegratedSmokeResult",
            "run_projects_copilot_specialist_integrated_smoke",
            "advisory_context_injected",
            "source_candidate_injected",
            "integrated_closed_loop_complete",
        ),
    ),
)

REQUIRED_SUPPORT_SURFACES: tuple[ClosureSurfaceRequirement, ...] = (
    ClosureSurfaceRequirement(
        path="src/context/event_bus_cell_lens_live_bridge_0284.py",
        role="passive EventBus to VisPy live observation bridge",
        markers=(
            "class EventBusCellLensLiveBridge",
            "event_to_cell_observation_event",
            "EventBusCellLensLiveBridgeStats",
        ),
    ),
    ClosureSurfaceRequirement(
        path="templates/github/projects-repository/projectv2_views.json",
        role="Projects-owned organized view configuration",
        markers=(
            '"autodoc.github.projects_repository_configuration.v1"',
            '"Recherches"',
            '"Résultats"',
            '"Copilot"',
            '"Connaissances serveur"',
            '"Historique"',
        ),
    ),
    ClosureSurfaceRequirement(
        path=(
            "templates/github/projects-repository/scripts/"
            "project_copilot_advisory_fields.py"
        ),
        role="Projects-owned controlled Copilot field projection",
        markers=(
            "class CopilotFieldProjectionCommand",
            "def plan_copilot_field_projection",
            "def execute_copilot_field_projection",
        ),
    ),
    ClosureSurfaceRequirement(
        path=(
            "templates/github/projects-repository/scripts/"
            "reconcile_projectv2_configuration.py"
        ),
        role="Projects-owned view and field reconciliation",
        markers=(
            "class ProjectConfigurationCommand",
            "def plan_projectv2_configuration",
            "def execute_projectv2_configuration",
        ),
    ),
    ClosureSurfaceRequirement(
        path="templates/github/projects-repository/INSTALLATION.md",
        role="cumulative Projects repository installation guide",
        markers=(
            "newicody/projects",
            "AUTODOC_PROJECT_TOKEN",
            "projectv2_views.json",
        ),
    ),
    ClosureSurfaceRequirement(
        path="config/github_projects_workflow_dispatch.example.ini",
        role="outbound workflow dispatch configuration",
        markers=(
            "[workflow_dispatch]",
            "allow_workflow_dispatch = false",
            "allow_remote_mutation = false",
            "newicody/projects",
        ),
    ),
)

FORBIDDEN_ACTIVE_AUTODOC_PROJECT_SURFACES: tuple[str, ...] = (
    ".github/workflows/autodoc-controlled-research.yml",
    ".github/ISSUE_TEMPLATE/research.yml",
    ".github/ISSUE_TEMPLATE/theme.yml",
    ".github/ISSUE_TEMPLATE/transversal-event.yml",
)


@dataclass(frozen=True, slots=True)
class Phase0284OperationalEvidence:
    """Evidence required to close the integrated capability as green."""

    fake_specialist_scheduler_closed: bool
    existing_scheduler_path_verified: bool
    real_sql_authority_used: bool
    real_openvino_e5_used: bool
    real_qdrant_projection_used: bool
    real_qdrant_recall_used: bool
    qdrant_returns_references_only: bool
    sql_rehydration_verified: bool
    portable_identity_preserved: bool
    artifact_correlation_verified: bool
    advisory_context_injected: bool
    source_candidate_injected: bool
    integrated_closed_loop_complete: bool
    publication_plan_ready: bool
    projects_projection_ready: bool
    github_mutation_performed: bool = False
    projectv2_mutation_performed: bool = False

    @property
    def green(self) -> bool:
        required = (
            self.fake_specialist_scheduler_closed,
            self.existing_scheduler_path_verified,
            self.real_sql_authority_used,
            self.real_openvino_e5_used,
            self.real_qdrant_projection_used,
            self.real_qdrant_recall_used,
            self.qdrant_returns_references_only,
            self.sql_rehydration_verified,
            self.portable_identity_preserved,
            self.artifact_correlation_verified,
            self.advisory_context_injected,
            self.source_candidate_injected,
            self.integrated_closed_loop_complete,
            self.publication_plan_ready,
            self.projects_projection_ready,
        )
        return (
            all(required)
            and not self.github_mutation_performed
            and not self.projectv2_mutation_performed
        )

    def to_mapping(self) -> dict[str, bool]:
        return {
            name: bool(getattr(self, name))
            for name in self.__dataclass_fields__
        } | {"green": self.green}


@dataclass(frozen=True, slots=True)
class Phase0284ClosureAuditResult:
    """Immutable closure decision for implementation and live evidence."""

    valid: bool
    issues: tuple[str, ...]
    scanned_file_count: int
    missing_required_surfaces: tuple[str, ...]
    incomplete_required_surfaces: tuple[str, ...]
    forbidden_active_surfaces: tuple[str, ...]
    contract_chain_complete: bool
    existing_scheduler_smoke_complete: bool
    real_memory_composition_complete: bool
    projects_copilot_composition_complete: bool
    passive_vispy_observation_available: bool
    projects_repository_bundle_complete: bool
    implementation_complete: bool
    operational_evidence_supplied: bool
    operationally_green: bool
    phase_0284_closed: bool
    next_recommended_patch: str
    existing_scheduler_remains_orchestrator: bool = True
    new_scheduler_added: bool = False
    new_laboratory_manager_added: bool = False
    eventbus_observation_only: bool = True
    sql_remains_authority: bool = True
    qdrant_projection_recall_only: bool = True
    projects_configuration_owned_by: str = "newicody/projects"
    schema: str = PHASE0284_CLOSURE_AUDIT_SCHEMA

    @property
    def live_path_status(self) -> str:
        if not self.valid:
            return "red"
        if self.operationally_green:
            return "green"
        return "transition"

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "issues": list(self.issues),
            "scanned_file_count": self.scanned_file_count,
            "missing_required_surfaces": list(self.missing_required_surfaces),
            "incomplete_required_surfaces": list(
                self.incomplete_required_surfaces
            ),
            "forbidden_active_surfaces": list(self.forbidden_active_surfaces),
            "contract_chain_complete": self.contract_chain_complete,
            "existing_scheduler_smoke_complete": (
                self.existing_scheduler_smoke_complete
            ),
            "real_memory_composition_complete": (
                self.real_memory_composition_complete
            ),
            "projects_copilot_composition_complete": (
                self.projects_copilot_composition_complete
            ),
            "passive_vispy_observation_available": (
                self.passive_vispy_observation_available
            ),
            "projects_repository_bundle_complete": (
                self.projects_repository_bundle_complete
            ),
            "implementation_complete": self.implementation_complete,
            "operational_evidence_supplied": self.operational_evidence_supplied,
            "operationally_green": self.operationally_green,
            "phase_0284_closed": self.phase_0284_closed,
            "next_recommended_patch": self.next_recommended_patch,
            "existing_scheduler_remains_orchestrator": True,
            "new_scheduler_added": False,
            "new_laboratory_manager_added": False,
            "eventbus_observation_only": True,
            "sql_remains_authority": True,
            "qdrant_projection_recall_only": True,
            "projects_configuration_owned_by": "newicody/projects",
            "live_path_status": self.live_path_status,
            "live_path_uses_real_backend": (
                True if self.operationally_green else False
            ),
        }


def audit_specialists_laboratories_chain_closure(
    sources: Mapping[str, str],
    operational_evidence: Phase0284OperationalEvidence | None = None,
) -> Phase0284ClosureAuditResult:
    """Audit supplied repository text and optional real execution evidence."""

    normalized = {str(path): str(text) for path, text in sources.items()}
    requirements = REQUIRED_CHAIN_SURFACES + REQUIRED_SUPPORT_SURFACES
    missing = tuple(req.path for req in requirements if req.path not in normalized)
    incomplete = tuple(
        req.path
        for req in requirements
        if req.path in normalized
        and not all(marker in normalized[req.path] for marker in req.markers)
    )
    forbidden = tuple(
        path for path in FORBIDDEN_ACTIVE_AUTODOC_PROJECT_SURFACES
        if path in normalized
    )
    issues = tuple(
        [f"missing required surface: {path}" for path in missing]
        + [f"incomplete required surface: {path}" for path in incomplete]
        + [f"forbidden active Autodoc project surface: {path}" for path in forbidden]
    )

    complete_paths = {
        req.path
        for req in requirements
        if req.path in normalized
        and all(marker in normalized[req.path] for marker in req.markers)
    }
    contract_paths = {req.path for req in REQUIRED_CHAIN_SURFACES[:4]}
    support_paths = {req.path for req in REQUIRED_SUPPORT_SURFACES}
    contract_chain_complete = contract_paths.issubset(complete_paths)
    existing_smoke = REQUIRED_CHAIN_SURFACES[4].path in complete_paths
    real_memory = REQUIRED_CHAIN_SURFACES[5].path in complete_paths
    projects_copilot = REQUIRED_CHAIN_SURFACES[6].path in complete_paths
    vispy = REQUIRED_SUPPORT_SURFACES[0].path in complete_paths
    projects_bundle = support_paths.difference(
        {REQUIRED_SUPPORT_SURFACES[0].path}
    ).issubset(complete_paths)
    implementation_complete = (
        not issues
        and contract_chain_complete
        and existing_smoke
        and real_memory
        and projects_copilot
        and vispy
        and projects_bundle
    )
    evidence_supplied = operational_evidence is not None
    operationally_green = bool(
        implementation_complete
        and operational_evidence is not None
        and operational_evidence.green
    )
    if operationally_green:
        next_patch = "0285-r1-specialist-capability-growth-reuse-audit"
    else:
        next_patch = "0284-r9-specialists-laboratories-live-path-evidence"

    return Phase0284ClosureAuditResult(
        valid=not issues,
        issues=issues,
        scanned_file_count=len(normalized),
        missing_required_surfaces=missing,
        incomplete_required_surfaces=incomplete,
        forbidden_active_surfaces=forbidden,
        contract_chain_complete=contract_chain_complete,
        existing_scheduler_smoke_complete=existing_smoke,
        real_memory_composition_complete=real_memory,
        projects_copilot_composition_complete=projects_copilot,
        passive_vispy_observation_available=vispy,
        projects_repository_bundle_complete=projects_bundle,
        implementation_complete=implementation_complete,
        operational_evidence_supplied=evidence_supplied,
        operationally_green=operationally_green,
        phase_0284_closed=operationally_green,
        next_recommended_patch=next_patch,
    )


__all__ = (
    "PHASE0284_CLOSURE_AUDIT_VERSION",
    "PHASE0284_CLOSURE_AUDIT_SCHEMA",
    "ClosureSurfaceRequirement",
    "REQUIRED_CHAIN_SURFACES",
    "REQUIRED_SUPPORT_SURFACES",
    "FORBIDDEN_ACTIVE_AUTODOC_PROJECT_SURFACES",
    "Phase0284OperationalEvidence",
    "Phase0284ClosureAuditResult",
    "audit_specialists_laboratories_chain_closure",
)
