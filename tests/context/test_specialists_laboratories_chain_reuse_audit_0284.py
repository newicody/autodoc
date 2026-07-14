from __future__ import annotations

from context.specialists_laboratories_chain_reuse_audit_0284 import (
    REQUIRED_SURFACES,
    audit_specialists_laboratories_chain_reuse,
)


def _sources(
    *,
    include_specialist_contract: bool = False,
    include_message_contract: bool = False,
    include_transfer_contract: bool = False,
):
    values = {
        path: "# required surface\n"
        for path in REQUIRED_SURFACES
    }
    values[
        "src/context/laboratory_framework_contract_0273.py"
    ] = """
class LaboratoryDescriptor: pass
class LaboratoryVisitRequest: pass
class LaboratoryVisitResult: pass
class LaboratoryResourceBudget: pass
class LaboratoryRegistryBindingPlan: pass
def validate_laboratory_visit_result(): pass
laboratory_ref = origin_laboratory_ref = target_laboratory_ref = ""
visit_ref = specialist_ref = conversation_ref = ""
context_refs = return_route_ref = ""
"""
    values[
        (
            "src/context/"
            "deterministic_fake_laboratory_provider_0273.py"
        )
    ] = """
class LaboratoryProvider(Protocol): pass
class DeterministicFakeLaboratoryProvider: pass
def build_deterministic_fake_laboratory_registration(): pass
def execute_deterministic_fake_laboratory_visit(): pass
"""
    values[
        "src/context/scheduler_owned_runtime_registry_0257.py"
    ] = """
class SchedulerOwnedRuntimeComponentRegistration: pass
class SchedulerOwnedRuntimeRegistry: pass
owner: str = "scheduler"
creates_runtime_manager: bool = False
"""
    values[
        "src/context/scheduler_laboratory_visit_binding_0274.py"
    ] = """
class LaboratoryVisitRequestHandler: pass
def build_laboratory_visit_event(): pass
def register_laboratory_visit_handler(): pass
def submit_laboratory_visit(): pass
path = "Scheduler.run()"
"""
    values[
        "src/context/scheduler_deliberation_route_contract.py"
    ] = """
class SpecialistDispatchCommand: pass
class SpecialistDemandFrame: pass
class SpecialistOpinionFrame: pass
class SchedulerDeliberationRouteBridge: pass
path = "/dev/shm/autodoc/routes/deliberation/"
"""
    values[
        (
            "src/context/"
            "fake_laboratory_deliberation_composition_0274.py"
        )
    ] = """
class FakeLaboratoryDeliberationCommand: pass
class FakeLaboratoryDeliberationResult: pass
def run_fake_laboratory_deliberation(): pass
def _build_visit_request(): pass
"""
    values[
        "src/context/fake_laboratory_closed_local_handoff_0274.py"
    ] = """
class FakeLaboratoryClosedHandoffCommand: pass
class FakeLaboratoryClosedHandoffResult: pass
class LaboratoryGitHubPublicationPreview: pass
def run_fake_laboratory_closed_local_handoff(): pass
"""
    values[
        (
            "src/context/"
            "fake_laboratory_recall_closed_result_frame_0274.py"
        )
    ] = """
class LaboratoryRecallClosureCommand: pass
class LaboratoryClosedResultFrame: pass
class LaboratoryRecallClosureResult: pass
def run_fake_laboratory_recall_closure(): pass
"""
    values[
        (
            "src/context/"
            "fake_laboratory_existing_scheduler_closed_loop_smoke_0274.py"
        )
    ] = """
class FakeLaboratoryClosedLoopSmokeCommand: pass
class FakeLaboratoryClosedLoopSmokeResult: pass
def run_fake_laboratory_existing_scheduler_closed_loop_smoke(): pass
"""
    values[
        (
            "src/context/"
            "github_dual_artifact_laboratory_smoke_0275.py"
        )
    ] = """
class GitHubDualArtifactLaboratorySmokeCommand: pass
def run_github_dual_artifact_laboratory_smoke(): pass
"""
    values[
        (
            "src/context/"
            "github_operator_laboratory_advisory_projection_0281.py"
        )
    ] = """
class GitHubOperatorLaboratoryAdvisoryProjectionCommand: pass
def build_copilot_advisory_laboratory_projection(): pass
def run_github_operator_laboratory_advisory_projection(): pass
"""
    values[
        (
            "src/context/"
            "scheduler_managed_qdrant_projection_binding_0283.py"
        )
    ] = """
class QdrantControlledSchedulerProjectionCommand: pass
def run_qdrant_controlled_scheduler_projection_binding(): pass
"""
    values[
        (
            "src/context/"
            "scheduler_managed_qdrant_recall_binding_0283.py"
        )
    ] = """
class QdrantControlledSchedulerRecallCommand: pass
def run_qdrant_controlled_scheduler_recall_binding(): pass
"""
    values[
        "tools/run_qdrant_real_closed_loop_smoke_0283.py"
    ] = """
SMOKE_REPORT_SCHEMA = "smoke"
def run_smoke(): pass
real_openvino_e5_used_on_execute = True
sql_rehydration_verified = True
"""
    additions = []
    if include_specialist_contract:
        additions.append("class PortableSpecialistDescriptor: pass")
    if include_message_contract:
        additions.append("class LaboratoryConversationMessage: pass")
    if include_transfer_contract:
        additions.append("class LaboratoryTransferRequest: pass")
    if additions:
        values[
            "src/context/scheduler_deliberation_route_contract.py"
        ] += "\n" + "\n".join(additions)
    return values


def test_existing_chain_is_complete_but_portable_contract_is_missing():
    result = audit_specialists_laboratories_chain_reuse(
        _sources()
    )

    assert result.valid is True
    assert result.laboratory_contract_complete is True
    assert result.required_reference_fields_present is True
    assert result.deterministic_fake_provider_complete is True
    assert result.scheduler_visit_binding_complete is True
    assert result.specialist_route_frames_complete is True
    assert result.deliberation_composition_complete is True
    assert result.local_handoff_complete is True
    assert result.recall_result_frame_complete is True
    assert result.existing_scheduler_smoke_complete is True
    assert result.github_laboratory_bridges_complete is True
    assert result.real_qdrant_chain_available is True
    assert (
        result.first_class_portable_specialist_contract_found
        is False
    )
    assert result.portable_specialist_contract_needed is True
    assert result.new_specialist_contract_module_justified is True
    assert result.next_recommended_patch == (
        "0284-r2-portable-specialist-contract"
    )


def test_first_class_specialist_advances_to_message_contract():
    result = audit_specialists_laboratories_chain_reuse(
        _sources(include_specialist_contract=True)
    )

    assert result.valid is True
    assert result.portable_specialist_contract_needed is False
    assert result.laboratory_message_contract_needed is True
    assert result.next_recommended_patch == (
        "0284-r3-specialist-laboratory-message-contract"
    )


def test_message_and_transfer_detection_advance_roadmap():
    result = audit_specialists_laboratories_chain_reuse(
        _sources(
            include_specialist_contract=True,
            include_message_contract=True,
            include_transfer_contract=True,
        )
    )

    assert result.valid is True
    assert result.laboratory_message_contract_needed is False
    assert result.laboratory_transfer_contract_needed is False
    assert result.next_recommended_patch == (
        "0284-r5-specialists-laboratories-existing-chain-smoke"
    )


def test_missing_existing_surface_invalidates_audit():
    sources = _sources()
    sources.pop(
        "src/context/scheduler_laboratory_visit_binding_0274.py"
    )

    result = audit_specialists_laboratories_chain_reuse(
        sources
    )

    assert result.valid is False
    assert (
        "src/context/scheduler_laboratory_visit_binding_0274.py"
        in result.missing_required_surfaces
    )
    assert any(
        issue.startswith("missing required surface:")
        for issue in result.issues
    )


def test_audit_never_claims_parallel_or_effectful_runtime():
    result = audit_specialists_laboratories_chain_reuse(
        _sources()
    )

    assert result.laboratory_framework_must_be_reused is True
    assert result.fake_provider_must_be_reused is True
    assert result.scheduler_route_frames_must_be_reused is True
    assert result.existing_scheduler_must_remain_orchestrator is True
    assert result.eventbus_observation_only is True
    assert result.sql_remains_authority is True
    assert result.qdrant_remains_projection_recall_only is True
    assert result.dev_shm_remains_fast_route_plane is True
    assert result.control_proxy_remains_lateral is True
    assert result.new_laboratory_manager_justified is False
    assert result.new_scheduler_justified is False
    assert result.network_used is False
    assert result.sql_or_qdrant_called is False
    assert result.audited_module_imported is False
    assert result.scheduler_run_modified is False
