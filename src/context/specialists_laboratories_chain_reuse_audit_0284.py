"""Pure reuse audit for the specialists/laboratories chain.

0284-r1 reads source text supplied by an IO adapter. It inventories the
existing laboratory contracts, deterministic provider, existing-Scheduler
binding, specialist route frames, local handoff, recall/ResultFrame closure,
GitHub bridges and the real SQL/E5/Qdrant chain.

The audit imports and executes none of the inspected modules. It performs no
network access, SQL/Qdrant effect, Scheduler mutation, EventBus publication,
shared-memory write or laboratory execution.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from typing import Any, Mapping

AUDIT_SCHEMA = (
    "missipy.specialists_laboratories.chain_reuse_audit.v1"
)

REQUIRED_SURFACES: tuple[str, ...] = (
    "src/context/laboratory_framework_contract_0273.py",
    "src/context/deterministic_fake_laboratory_provider_0273.py",
    "src/context/scheduler_owned_runtime_registry_0257.py",
    "src/context/scheduler_laboratory_visit_binding_0274.py",
    "src/context/scheduler_deliberation_route_contract.py",
    "src/context/fake_laboratory_deliberation_composition_0274.py",
    "src/context/fake_laboratory_closed_local_handoff_0274.py",
    "src/context/fake_laboratory_recall_closed_result_frame_0274.py",
    "src/context/fake_laboratory_existing_scheduler_closed_loop_smoke_0274.py",
    "src/context/github_dual_artifact_laboratory_smoke_0275.py",
    "src/context/github_operator_laboratory_advisory_projection_0281.py",
    "src/context/scheduler_managed_qdrant_projection_binding_0283.py",
    "src/context/scheduler_managed_qdrant_recall_binding_0283.py",
    "tools/run_qdrant_real_closed_loop_smoke_0283.py",
)

_REQUIRED_LABORATORY_REFS = (
    "laboratory_ref",
    "origin_laboratory_ref",
    "target_laboratory_ref",
    "visit_ref",
    "specialist_ref",
    "conversation_ref",
    "context_refs",
    "return_route_ref",
)

_FIRST_CLASS_SPECIALIST_CLASS_NAMES = frozenset(
    {
        "SpecialistDescriptor",
        "PortableSpecialistDescriptor",
        "SpecialistCapabilityContract",
        "SpecialistExecutionProfile",
        "SpecialistLaboratoryBinding",
    }
)

_LABORATORY_MESSAGE_CLASS_NAMES = frozenset(
    {
        "LaboratoryMessage",
        "LaboratoryConversationMessage",
        "SpecialistLaboratoryMessage",
    }
)

_LABORATORY_TRANSFER_CLASS_NAMES = frozenset(
    {
        "LaboratoryTransferRequest",
        "LaboratoryTransferResult",
        "SpecialistTransferRequest",
        "SpecialistTransferResult",
    }
)


@dataclass(frozen=True, slots=True)
class ReusedSurfaceFinding:
    """One existing implementation surface selected for reuse."""

    path: str
    role: str
    markers: tuple[str, ...]
    complete: bool

    def to_mapping(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "role": self.role,
            "markers": list(self.markers),
            "complete": self.complete,
        }


@dataclass(frozen=True, slots=True)
class SpecialistsLaboratoriesChainReuseAuditResult:
    """Immutable result of the 0284-r1 source-only audit."""

    valid: bool
    issues: tuple[str, ...]
    scanned_file_count: int
    required_surfaces_present: tuple[str, ...]
    missing_required_surfaces: tuple[str, ...]
    reused_surfaces: tuple[ReusedSurfaceFinding, ...]
    laboratory_contract_complete: bool
    required_reference_fields_present: bool
    deterministic_fake_provider_complete: bool
    scheduler_visit_binding_complete: bool
    specialist_route_frames_complete: bool
    deliberation_composition_complete: bool
    local_handoff_complete: bool
    recall_result_frame_complete: bool
    existing_scheduler_smoke_complete: bool
    github_laboratory_bridges_complete: bool
    real_qdrant_chain_available: bool
    first_class_portable_specialist_contract_found: bool
    laboratory_message_contract_found: bool
    laboratory_transfer_contract_found: bool
    laboratory_framework_must_be_reused: bool = True
    fake_provider_must_be_reused: bool = True
    scheduler_route_frames_must_be_reused: bool = True
    existing_scheduler_must_remain_orchestrator: bool = True
    eventbus_observation_only: bool = True
    sql_remains_authority: bool = True
    qdrant_remains_projection_recall_only: bool = True
    dev_shm_remains_fast_route_plane: bool = True
    control_proxy_remains_lateral: bool = True
    new_laboratory_manager_justified: bool = False
    new_scheduler_justified: bool = False
    network_used: bool = False
    sql_or_qdrant_called: bool = False
    audited_module_imported: bool = False
    scheduler_run_modified: bool = False

    @property
    def portable_specialist_contract_needed(self) -> bool:
        return self.valid and not (
            self.first_class_portable_specialist_contract_found
        )

    @property
    def laboratory_message_contract_needed(self) -> bool:
        return self.valid and not self.laboratory_message_contract_found

    @property
    def laboratory_transfer_contract_needed(self) -> bool:
        return self.valid and not self.laboratory_transfer_contract_found

    @property
    def new_specialist_contract_module_justified(self) -> bool:
        return self.portable_specialist_contract_needed

    @property
    def next_recommended_patch(self) -> str:
        if self.portable_specialist_contract_needed:
            return "0284-r2-portable-specialist-contract"
        if self.laboratory_message_contract_needed:
            return "0284-r3-specialist-laboratory-message-contract"
        if self.laboratory_transfer_contract_needed:
            return "0284-r4-specialist-laboratory-transfer-contract"
        return "0284-r5-specialists-laboratories-existing-chain-smoke"

    def to_mapping(self) -> dict[str, Any]:
        return {
            "schema": AUDIT_SCHEMA,
            "specialists_laboratories_chain_reuse_audit": True,
            "valid": self.valid,
            "issues": list(self.issues),
            "scanned_file_count": self.scanned_file_count,
            "required_surfaces_present": list(
                self.required_surfaces_present
            ),
            "missing_required_surfaces": list(
                self.missing_required_surfaces
            ),
            "reused_surfaces": [
                item.to_mapping() for item in self.reused_surfaces
            ],
            "laboratory_contract_complete": (
                self.laboratory_contract_complete
            ),
            "required_reference_fields_present": (
                self.required_reference_fields_present
            ),
            "deterministic_fake_provider_complete": (
                self.deterministic_fake_provider_complete
            ),
            "scheduler_visit_binding_complete": (
                self.scheduler_visit_binding_complete
            ),
            "specialist_route_frames_complete": (
                self.specialist_route_frames_complete
            ),
            "deliberation_composition_complete": (
                self.deliberation_composition_complete
            ),
            "local_handoff_complete": self.local_handoff_complete,
            "recall_result_frame_complete": (
                self.recall_result_frame_complete
            ),
            "existing_scheduler_smoke_complete": (
                self.existing_scheduler_smoke_complete
            ),
            "github_laboratory_bridges_complete": (
                self.github_laboratory_bridges_complete
            ),
            "real_qdrant_chain_available": (
                self.real_qdrant_chain_available
            ),
            "first_class_portable_specialist_contract_found": (
                self.first_class_portable_specialist_contract_found
            ),
            "laboratory_message_contract_found": (
                self.laboratory_message_contract_found
            ),
            "laboratory_transfer_contract_found": (
                self.laboratory_transfer_contract_found
            ),
            "portable_specialist_contract_needed": (
                self.portable_specialist_contract_needed
            ),
            "laboratory_message_contract_needed": (
                self.laboratory_message_contract_needed
            ),
            "laboratory_transfer_contract_needed": (
                self.laboratory_transfer_contract_needed
            ),
            "new_specialist_contract_module_justified": (
                self.new_specialist_contract_module_justified
            ),
            "next_recommended_patch": self.next_recommended_patch,
            "laboratory_framework_must_be_reused": (
                self.laboratory_framework_must_be_reused
            ),
            "fake_provider_must_be_reused": (
                self.fake_provider_must_be_reused
            ),
            "scheduler_route_frames_must_be_reused": (
                self.scheduler_route_frames_must_be_reused
            ),
            "existing_scheduler_must_remain_orchestrator": (
                self.existing_scheduler_must_remain_orchestrator
            ),
            "eventbus_observation_only": (
                self.eventbus_observation_only
            ),
            "sql_remains_authority": self.sql_remains_authority,
            "qdrant_remains_projection_recall_only": (
                self.qdrant_remains_projection_recall_only
            ),
            "dev_shm_remains_fast_route_plane": (
                self.dev_shm_remains_fast_route_plane
            ),
            "control_proxy_remains_lateral": (
                self.control_proxy_remains_lateral
            ),
            "new_laboratory_manager_justified": (
                self.new_laboratory_manager_justified
            ),
            "new_scheduler_justified": self.new_scheduler_justified,
            "network_used": self.network_used,
            "sql_or_qdrant_called": self.sql_or_qdrant_called,
            "audited_module_imported": self.audited_module_imported,
            "scheduler_run_modified": self.scheduler_run_modified,
        }


def audit_specialists_laboratories_chain_reuse(
    sources: Mapping[str, str],
) -> SpecialistsLaboratoriesChainReuseAuditResult:
    """Audit supplied source text without importing or executing it."""

    normalized = {
        str(path): str(text) for path, text in sources.items()
    }
    present = tuple(
        path for path in REQUIRED_SURFACES if path in normalized
    )
    missing = tuple(
        path for path in REQUIRED_SURFACES if path not in normalized
    )
    issues: list[str] = [
        f"missing required surface: {path}" for path in missing
    ]

    laboratory_contract = normalized.get(
        "src/context/laboratory_framework_contract_0273.py",
        "",
    )
    fake_provider = normalized.get(
        "src/context/deterministic_fake_laboratory_provider_0273.py",
        "",
    )
    runtime_registry = normalized.get(
        "src/context/scheduler_owned_runtime_registry_0257.py",
        "",
    )
    scheduler_binding = normalized.get(
        "src/context/scheduler_laboratory_visit_binding_0274.py",
        "",
    )
    specialist_routes = normalized.get(
        "src/context/scheduler_deliberation_route_contract.py",
        "",
    )
    deliberation = normalized.get(
        "src/context/fake_laboratory_deliberation_composition_0274.py",
        "",
    )
    handoff = normalized.get(
        "src/context/fake_laboratory_closed_local_handoff_0274.py",
        "",
    )
    recall = normalized.get(
        "src/context/fake_laboratory_recall_closed_result_frame_0274.py",
        "",
    )
    smoke = normalized.get(
        (
            "src/context/"
            "fake_laboratory_existing_scheduler_closed_loop_smoke_0274.py"
        ),
        "",
    )
    github_smoke = normalized.get(
        "src/context/github_dual_artifact_laboratory_smoke_0275.py",
        "",
    )
    github_projection = normalized.get(
        (
            "src/context/"
            "github_operator_laboratory_advisory_projection_0281.py"
        ),
        "",
    )
    qdrant_projection = normalized.get(
        (
            "src/context/"
            "scheduler_managed_qdrant_projection_binding_0283.py"
        ),
        "",
    )
    qdrant_recall = normalized.get(
        (
            "src/context/"
            "scheduler_managed_qdrant_recall_binding_0283.py"
        ),
        "",
    )
    qdrant_smoke = normalized.get(
        "tools/run_qdrant_real_closed_loop_smoke_0283.py",
        "",
    )

    findings = (
        _finding(
            "src/context/laboratory_framework_contract_0273.py",
            "versioned laboratory and visit contracts",
            laboratory_contract,
            (
                "class LaboratoryDescriptor",
                "class LaboratoryVisitRequest",
                "class LaboratoryVisitResult",
                "class LaboratoryResourceBudget",
                "class LaboratoryRegistryBindingPlan",
                "validate_laboratory_visit_result",
            ),
        ),
        _finding(
            (
                "src/context/"
                "deterministic_fake_laboratory_provider_0273.py"
            ),
            "deterministic provider membrane",
            fake_provider,
            (
                "class LaboratoryProvider(Protocol)",
                "class DeterministicFakeLaboratoryProvider",
                "build_deterministic_fake_laboratory_registration",
                "execute_deterministic_fake_laboratory_visit",
            ),
        ),
        _finding(
            "src/context/scheduler_owned_runtime_registry_0257.py",
            "existing Scheduler-owned registry",
            runtime_registry,
            (
                "class SchedulerOwnedRuntimeComponentRegistration",
                "class SchedulerOwnedRuntimeRegistry",
                'owner: str = "scheduler"',
                "creates_runtime_manager: bool = False",
            ),
        ),
        _finding(
            "src/context/scheduler_laboratory_visit_binding_0274.py",
            "existing Scheduler visit command path",
            scheduler_binding,
            (
                "class LaboratoryVisitRequestHandler",
                "build_laboratory_visit_event",
                "register_laboratory_visit_handler",
                "submit_laboratory_visit",
                '"Scheduler.run()"',
            ),
        ),
        _finding(
            "src/context/scheduler_deliberation_route_contract.py",
            "specialist dispatch and /dev/shm frame contracts",
            specialist_routes,
            (
                "class SpecialistDispatchCommand",
                "class SpecialistDemandFrame",
                "class SpecialistOpinionFrame",
                "class SchedulerDeliberationRouteBridge",
                "/dev/shm/autodoc/routes/deliberation/",
            ),
        ),
        _finding(
            (
                "src/context/"
                "fake_laboratory_deliberation_composition_0274.py"
            ),
            "multi-specialist fake deliberation composition",
            deliberation,
            (
                "class FakeLaboratoryDeliberationCommand",
                "class FakeLaboratoryDeliberationResult",
                "run_fake_laboratory_deliberation",
                "_build_visit_request",
            ),
        ),
        _finding(
            "src/context/fake_laboratory_closed_local_handoff_0274.py",
            "SQL/EventBus/passive-view local handoff",
            handoff,
            (
                "class FakeLaboratoryClosedHandoffCommand",
                "class FakeLaboratoryClosedHandoffResult",
                "run_fake_laboratory_closed_local_handoff",
                "class LaboratoryGitHubPublicationPreview",
            ),
        ),
        _finding(
            (
                "src/context/"
                "fake_laboratory_recall_closed_result_frame_0274.py"
            ),
            "recall and closed ResultFrame",
            recall,
            (
                "class LaboratoryRecallClosureCommand",
                "class LaboratoryClosedResultFrame",
                "class LaboratoryRecallClosureResult",
                "run_fake_laboratory_recall_closure",
            ),
        ),
        _finding(
            (
                "src/context/"
                "fake_laboratory_existing_scheduler_closed_loop_smoke_0274.py"
            ),
            "existing-Scheduler laboratory smoke",
            smoke,
            (
                "class FakeLaboratoryClosedLoopSmokeCommand",
                "class FakeLaboratoryClosedLoopSmokeResult",
                (
                    "run_fake_laboratory_existing_scheduler_"
                    "closed_loop_smoke"
                ),
            ),
        ),
        _finding(
            (
                "src/context/"
                "github_dual_artifact_laboratory_smoke_0275.py"
            ),
            "GitHub dual-artifact laboratory bridge",
            github_smoke,
            (
                "class GitHubDualArtifactLaboratorySmokeCommand",
                "run_github_dual_artifact_laboratory_smoke",
            ),
        ),
        _finding(
            (
                "src/context/"
                "github_operator_laboratory_advisory_projection_0281.py"
            ),
            "operator advisory to laboratory projection",
            github_projection,
            (
                "class GitHubOperatorLaboratoryAdvisoryProjectionCommand",
                "build_copilot_advisory_laboratory_projection",
                "run_github_operator_laboratory_advisory_projection",
            ),
        ),
        _finding(
            (
                "src/context/"
                "scheduler_managed_qdrant_projection_binding_0283.py"
            ),
            "real controlled Qdrant projection",
            qdrant_projection,
            (
                "QdrantControlledSchedulerProjectionCommand",
                "run_qdrant_controlled_scheduler_projection_binding",
            ),
        ),
        _finding(
            (
                "src/context/"
                "scheduler_managed_qdrant_recall_binding_0283.py"
            ),
            "real controlled Qdrant recall and SQL rehydrate",
            qdrant_recall,
            (
                "QdrantControlledSchedulerRecallCommand",
                "run_qdrant_controlled_scheduler_recall_binding",
            ),
        ),
        _finding(
            "tools/run_qdrant_real_closed_loop_smoke_0283.py",
            "real SQL/E5/Qdrant closed-loop smoke",
            qdrant_smoke,
            (
                "SMOKE_REPORT_SCHEMA",
                "run_smoke",
                "real_openvino_e5_used_on_execute",
                "sql_rehydration_verified",
            ),
        ),
    )

    for finding in findings:
        if not finding.complete:
            issues.append(
                f"incomplete reused surface: {finding.path}"
            )

    required_reference_fields_present = all(
        marker in laboratory_contract
        for marker in _REQUIRED_LABORATORY_REFS
    )
    if not required_reference_fields_present:
        issues.append(
            "laboratory visit contract is missing required future refs"
        )

    first_class_names = _class_names(normalized)
    first_class_specialist_found = bool(
        first_class_names.intersection(
            _FIRST_CLASS_SPECIALIST_CLASS_NAMES
        )
    )
    message_contract_found = bool(
        first_class_names.intersection(
            _LABORATORY_MESSAGE_CLASS_NAMES
        )
    )
    transfer_contract_found = bool(
        first_class_names.intersection(
            _LABORATORY_TRANSFER_CLASS_NAMES
        )
    )

    return SpecialistsLaboratoriesChainReuseAuditResult(
        valid=not issues,
        issues=tuple(issues),
        scanned_file_count=len(normalized),
        required_surfaces_present=present,
        missing_required_surfaces=missing,
        reused_surfaces=findings,
        laboratory_contract_complete=findings[0].complete,
        required_reference_fields_present=(
            required_reference_fields_present
        ),
        deterministic_fake_provider_complete=findings[1].complete,
        scheduler_visit_binding_complete=findings[3].complete,
        specialist_route_frames_complete=findings[4].complete,
        deliberation_composition_complete=findings[5].complete,
        local_handoff_complete=findings[6].complete,
        recall_result_frame_complete=findings[7].complete,
        existing_scheduler_smoke_complete=findings[8].complete,
        github_laboratory_bridges_complete=(
            findings[9].complete and findings[10].complete
        ),
        real_qdrant_chain_available=(
            findings[11].complete
            and findings[12].complete
            and findings[13].complete
        ),
        first_class_portable_specialist_contract_found=(
            first_class_specialist_found
        ),
        laboratory_message_contract_found=message_contract_found,
        laboratory_transfer_contract_found=transfer_contract_found,
    )


def _finding(
    path: str,
    role: str,
    source: str,
    markers: tuple[str, ...],
) -> ReusedSurfaceFinding:
    return ReusedSurfaceFinding(
        path=path,
        role=role,
        markers=markers,
        complete=bool(source) and all(
            marker in source for marker in markers
        ),
    )


def _class_names(
    sources: Mapping[str, str],
) -> frozenset[str]:
    names: set[str] = set()
    for path, source in sources.items():
        try:
            tree = ast.parse(source, filename=path)
        except SyntaxError:
            continue
        names.update(
            node.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ClassDef)
        )
    return frozenset(names)


__all__ = (
    "AUDIT_SCHEMA",
    "REQUIRED_SURFACES",
    "ReusedSurfaceFinding",
    "SpecialistsLaboratoriesChainReuseAuditResult",
    "audit_specialists_laboratories_chain_reuse",
)
