"""Source-only reuse audit for the 0286 GitHub Projects operator workflow.

The audit reads source text.  It never imports the inspected modules, contacts
GitHub, mutates ProjectV2, writes SQL/Qdrant, or dispatches the Scheduler.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
from typing import Mapping

SPECIALIST_CAPABILITY_GROWTH_PROJECTS_OPERATOR_WORKFLOW_REUSE_AUDIT_SCHEMA = (
    "missipy.specialist.capability_growth.projects_operator_workflow_reuse_audit.v1"
)
SPECIALIST_CAPABILITY_GROWTH_PROJECTS_OPERATOR_WORKFLOW_REUSE_AUDIT_VERSION = "0286.r1"


@dataclass(frozen=True, slots=True)
class SourceRequirement:
    path: str
    role: str
    markers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PhaseMarker:
    path: str
    markers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ProjectsOperatorWorkflowPhase:
    patch_id: str
    label: str
    requirements: tuple[PhaseMarker, ...]


@dataclass(frozen=True, slots=True)
class SpecialistCapabilityGrowthProjectsOperatorWorkflowReuseAuditResult:
    schema: str
    valid: bool
    missing_reuse_surfaces: tuple[str, ...]
    incomplete_reuse_surfaces: tuple[str, ...]
    completed_phases: tuple[str, ...]
    next_recommended_patch: str
    dedicated_growth_issue_form_present: bool
    specialist_revision_fields_present: bool
    operator_decision_view_present: bool
    workflow_is_read_only_for_issues: bool
    installation_reviewed: bool
    installation_update_required: bool
    findings: tuple[str, ...]
    source_digest: str

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "missing_reuse_surfaces": list(self.missing_reuse_surfaces),
            "incomplete_reuse_surfaces": list(self.incomplete_reuse_surfaces),
            "completed_phases": list(self.completed_phases),
            "next_recommended_patch": self.next_recommended_patch,
            "dedicated_growth_issue_form_present": self.dedicated_growth_issue_form_present,
            "specialist_revision_fields_present": self.specialist_revision_fields_present,
            "operator_decision_view_present": self.operator_decision_view_present,
            "workflow_is_read_only_for_issues": self.workflow_is_read_only_for_issues,
            "installation_reviewed": self.installation_reviewed,
            "installation_update_required": self.installation_update_required,
            "findings": list(self.findings),
            "source_digest": self.source_digest,
            "github_projects_authoritative": False,
            "operator_gate_reused": True,
            "sql_remains_durable_authority": True,
            "scheduler_remains_only_orchestrator": True,
            "qdrant_remains_projection_and_recall_only": True,
            "copilot_remains_advisory": True,
            "new_scheduler_required": False,
            "new_global_specialist_registry_required": False,
            "new_http_client_required": False,
        }


REQUIRED_REUSE_SURFACES: tuple[SourceRequirement, ...] = (
    SourceRequirement(
        "src/context/specialist_capability_growth_proposal_contract_0285.py",
        "non-authoritative evidence-backed proposal",
        ("SpecialistCapabilityGrowthProposal", "authoritative"),
    ),
    SourceRequirement(
        "src/context/portable_specialist_revision_lineage_contract_0285.py",
        "immutable portable revision lineage",
        ("PortableSpecialistRevision", "SpecialistRevisionLineage"),
    ),
    SourceRequirement(
        "src/context/specialist_capability_growth_operator_gate_0285.py",
        "explicit operator authorization gate",
        ("SpecialistCapabilityGrowthDecision", "revision_authorized"),
    ),
    SourceRequirement(
        "src/context/specialist_capability_growth_durable_history_0285.py",
        "SQL-authoritative append-only history port",
        ("SpecialistCapabilityGrowthHistoryEntry", "SpecialistCapabilityGrowthHistoryPort", "sql_ref"),
    ),
    SourceRequirement(
        "src/context/scheduler_approved_specialist_revision_selection_0285.py",
        "selection through the existing Scheduler/Dispatcher path",
        ("SPECIALIST_REVISION_SELECTION", "scheduler_selection_performed"),
    ),
    SourceRequirement(
        "src/context/specialist_capability_growth_observation_projection_0285.py",
        "EventBus and passive observation projection",
        ("SPECIALIST_REVISION_SELECTION_RESULT", "eventbus_observation_published"),
    ),
    SourceRequirement(
        "src/context/specialist_capability_growth_closed_loop_smoke_0285.py",
        "closed generic capability-growth proof",
        ("phase_0285_closed", "run_specialist_capability_growth_closed_loop_smoke"),
    ),
    SourceRequirement(
        "src/context/github_operator_laboratory_advisory_projection_0281.py",
        "existing operator/laboratory GitHub projection pattern",
        ("operator", "laboratory", "advisory"),
    ),
    SourceRequirement(
        "src/context/github_controlled_advisory_issue_publication_0281.py",
        "controlled idempotent Issue publication pattern",
        ("plan_digest", "idempot"),
    ),
    SourceRequirement(
        "src/context/github_project_v2_append_only_cycle_history_0282.py",
        "append-only ProjectV2 cycle/history pattern",
        ("append", "ProjectV2"),
    ),
    SourceRequirement(
        "tools/apply_github_project_v2_operator_authorized_mutations_0282.py",
        "operator-authorized mutation adapter using the established gh boundary",
        ("--execute", "confirm-plan-digest", "gh"),
    ),
    SourceRequirement(
        "tools/publish_github_advisory_issue_comment_0281.py",
        "operator-confirmed Issue comment CLI",
        ("--execute", "confirm-plan-digest"),
    ),
    SourceRequirement(
        "templates/github/projects-repository/.github/workflows/autodoc-controlled-research.yml",
        "controlled request artifact workflow",
        ("workflow_dispatch", "permissions", "issues: read", "actions: read"),
    ),
    SourceRequirement(
        "templates/github/projects-repository/.github/ISSUE_TEMPLATE/research.yml",
        "existing generic research form",
        ("name:",),
    ),
    SourceRequirement(
        "templates/github/projects-repository/.github/ISSUE_TEMPLATE/update.yml",
        "existing append-only update form",
        ("name:",),
    ),
    SourceRequirement(
        "templates/github/projects-repository/.github/ISSUE_TEMPLATE/theme.yml",
        "existing theme/group form",
        ("name:",),
    ),
    SourceRequirement(
        "templates/github/projects-repository/projectv2_views.json",
        "versioned ProjectV2 field and view declaration",
        ('"Thème"', '"Affichage"', '"Copilot"'),
    ),
    SourceRequirement(
        "templates/github/projects-repository/PROJECT_BOARD_TEMPLATE.md",
        "board workflow/read-surface contract",
        ("ProjectV2", "workflow"),
    ),
    SourceRequirement(
        "templates/github/projects-repository/RESULT_UPDATE_PRESENTATION_CONTRACT.md",
        "result/update presentation contract",
        ("Résultat / UPDATE", "validation opérateur"),
    ),
    SourceRequirement(
        "templates/github/projects-repository/INSTALLATION.md",
        "cumulative newicody/projects installation guide",
        ("0284-r9", "AUTODOC_COPILOT_ADVISORY_ENABLED=false", "--delete"),
    ),
)


DEVELOPMENT_PHASES: tuple[ProjectsOperatorWorkflowPhase, ...] = (
    ProjectsOperatorWorkflowPhase(
        "0286-r2-specialist-capability-growth-projects-review-projection-contract",
        "immutable non-authoritative review projection",
        (
            PhaseMarker(
                "src/context/specialist_capability_growth_projects_review_projection_0286.py",
                ("SpecialistCapabilityGrowthProjectsReviewProjection", "github_projects_authoritative"),
            ),
        ),
    ),
    ProjectsOperatorWorkflowPhase(
        "0286-r3-specialist-capability-growth-projects-request-form-contract",
        "dedicated request form and normalized local intake",
        (
            PhaseMarker(
                "templates/github/projects-repository/.github/ISSUE_TEMPLATE/specialist-capability-growth.yml",
                ("specialist_ref", "capability", "operator decision remains local"),
            ),
            PhaseMarker(
                "src/context/github_specialist_capability_growth_issue_contract_0286.py",
                ("GitHubSpecialistCapabilityGrowthIssueRequest",),
            ),
            PhaseMarker(
                "templates/github/projects-repository/INSTALLATION.md",
                ("0286-r3", "specialist-capability-growth.yml"),
            ),
        ),
    ),
    ProjectsOperatorWorkflowPhase(
        "0286-r4-specialist-capability-growth-projectv2-fields-views",
        "specialist revision fields and review views",
        (
            PhaseMarker(
                "templates/github/projects-repository/projectv2_views.json",
                ("Révision spécialiste", "Décision capacité", "Révisions spécialistes"),
            ),
            PhaseMarker(
                "templates/github/projects-repository/INSTALLATION.md",
                ("0286-r4", "Révision spécialiste", "Décision capacité"),
            ),
        ),
    ),
    ProjectsOperatorWorkflowPhase(
        "0286-r5-specialist-capability-growth-projects-publication-plan",
        "digest-bound comment and field publication plan",
        (
            PhaseMarker(
                "src/context/specialist_capability_growth_projects_publication_plan_0286.py",
                ("SpecialistCapabilityGrowthProjectsPublicationPlan", "plan_digest"),
            ),
        ),
    ),
    ProjectsOperatorWorkflowPhase(
        "0286-r6-specialist-capability-growth-projects-operator-authorized-adapter",
        "preview-first operator-authorized GitHub adapter",
        (
            PhaseMarker(
                "tools/apply_specialist_capability_growth_projects_projection_0286.py",
                ("--execute", "--confirm-plan-digest", "gh api"),
            ),
        ),
    ),
    ProjectsOperatorWorkflowPhase(
        "0286-r7-specialist-capability-growth-projects-readback-readiness",
        "query-only readback and deployment readiness evidence",
        (
            PhaseMarker(
                "src/context/specialist_capability_growth_projects_readback_readiness_0286.py",
                ("SpecialistCapabilityGrowthProjectsReadbackEvidence", "remote_mutation_allowed"),
            ),
        ),
    ),
    ProjectsOperatorWorkflowPhase(
        "0286-r8-specialist-capability-growth-projects-closed-loop-smoke",
        "real controlled publish/readback closure",
        (
            PhaseMarker(
                "src/context/specialist_capability_growth_projects_closed_loop_smoke_0286.py",
                ("SpecialistCapabilityGrowthProjectsClosedLoopSmokeResult", "phase_0286_closed"),
            ),
        ),
    ),
)


def all_audit_paths() -> tuple[str, ...]:
    paths = {item.path for item in REQUIRED_REUSE_SURFACES}
    for phase in DEVELOPMENT_PHASES:
        paths.update(item.path for item in phase.requirements)
    return tuple(sorted(paths))


def load_audit_sources(root: Path) -> dict[str, str]:
    root = Path(root)
    sources: dict[str, str] = {}
    for relative in all_audit_paths():
        path = root / relative
        if path.is_file():
            sources[relative] = path.read_text(encoding="utf-8")
    return sources


def audit_specialist_capability_growth_projects_operator_workflow_reuse(
    sources: Mapping[str, str],
) -> SpecialistCapabilityGrowthProjectsOperatorWorkflowReuseAuditResult:
    normalized = {str(path): str(text) for path, text in sources.items()}
    missing: list[str] = []
    incomplete: list[str] = []
    for requirement in REQUIRED_REUSE_SURFACES:
        text = normalized.get(requirement.path)
        if text is None:
            missing.append(requirement.path)
            continue
        if not all(marker in text for marker in requirement.markers):
            incomplete.append(requirement.path)

    completed: list[str] = []
    next_patch = "0286-complete"
    for phase in DEVELOPMENT_PHASES:
        phase_complete = all(
            requirement.path in normalized
            and all(marker in normalized[requirement.path] for marker in requirement.markers)
            for requirement in phase.requirements
        )
        if phase_complete:
            completed.append(phase.patch_id)
        elif next_patch == "0286-complete":
            next_patch = phase.patch_id

    issue_form_path = (
        "templates/github/projects-repository/.github/ISSUE_TEMPLATE/"
        "specialist-capability-growth.yml"
    )
    project_configuration = normalized.get(
        "templates/github/projects-repository/projectv2_views.json", ""
    )
    workflow = normalized.get(
        "templates/github/projects-repository/.github/workflows/"
        "autodoc-controlled-research.yml",
        "",
    )
    installation = normalized.get(
        "templates/github/projects-repository/INSTALLATION.md", ""
    )
    workflow_is_read_only = (
        "issues: read" in workflow
        and "actions: read" in workflow
        and "issues: write" not in workflow
    )
    findings = (
        "reuse the complete 0285 proposal/revision/operator-gate/history/selection chain",
        "reuse the existing controlled Issue publication and ProjectV2 mutation boundaries",
        "keep GitHub Projects as a workflow and review surface, never as durable authority",
        "add one dedicated capability-growth request form instead of overloading generic research forms",
        "add specialist revision and operator decision fields/views to the versioned Projects bundle",
        "require preview, exact plan digest, explicit operator authorization and query-only readback",
        "keep Scheduler as the only orchestrator, SQL as durable authority and Qdrant as projection/recall",
        "do not create a global specialist registry, another HTTP client or a LaboratoryManager",
    )
    digest_payload = json.dumps(
        {key: normalized[key] for key in sorted(normalized)},
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return SpecialistCapabilityGrowthProjectsOperatorWorkflowReuseAuditResult(
        schema=SPECIALIST_CAPABILITY_GROWTH_PROJECTS_OPERATOR_WORKFLOW_REUSE_AUDIT_SCHEMA,
        valid=not missing and not incomplete,
        missing_reuse_surfaces=tuple(sorted(missing)),
        incomplete_reuse_surfaces=tuple(sorted(incomplete)),
        completed_phases=tuple(completed),
        next_recommended_patch=next_patch,
        dedicated_growth_issue_form_present=issue_form_path in normalized,
        specialist_revision_fields_present=all(
            marker in project_configuration
            for marker in ("Révision spécialiste", "Décision capacité")
        ),
        operator_decision_view_present="Révisions spécialistes" in project_configuration,
        workflow_is_read_only_for_issues=workflow_is_read_only,
        installation_reviewed=all(
            marker in installation
            for marker in (
                "0284-r9",
                "AUTODOC_COPILOT_ADVISORY_ENABLED=false",
                "--delete",
            )
        ),
        installation_update_required=False,
        findings=findings,
        source_digest=sha256(digest_payload).hexdigest(),
    )


__all__ = (
    "DEVELOPMENT_PHASES",
    "REQUIRED_REUSE_SURFACES",
    "SPECIALIST_CAPABILITY_GROWTH_PROJECTS_OPERATOR_WORKFLOW_REUSE_AUDIT_SCHEMA",
    "SPECIALIST_CAPABILITY_GROWTH_PROJECTS_OPERATOR_WORKFLOW_REUSE_AUDIT_VERSION",
    "PhaseMarker",
    "ProjectsOperatorWorkflowPhase",
    "SourceRequirement",
    "SpecialistCapabilityGrowthProjectsOperatorWorkflowReuseAuditResult",
    "all_audit_paths",
    "audit_specialist_capability_growth_projects_operator_workflow_reuse",
    "load_audit_sources",
)
