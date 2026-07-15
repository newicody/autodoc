from __future__ import annotations

from dataclasses import replace
import hashlib

import pytest

from context.portable_specialist_contract_0284 import (
    PORTABLE_SPECIALIST_DESCRIPTOR_SCHEMA,
    SPECIALIST_CAPABILITY_SCHEMA,
    SPECIALIST_EXECUTION_PROFILE_SCHEMA,
    SPECIALIST_LABORATORY_BINDING_SCHEMA,
    PortableSpecialistDescriptor,
    SpecialistCapabilityContract,
    SpecialistExecutionProfile,
    SpecialistLaboratoryBinding,
)
from context.specialist_deep_analysis_contract_0287 import (
    DEEP_ANALYSIS_CONTRIBUTION_SCHEMA,
    DEEP_ANALYSIS_FINDING_SCHEMA,
    DEEP_ANALYSIS_REQUEST_SCHEMA,
    DeepAnalysisContribution,
    DeepAnalysisFinding,
    DeepAnalysisRequest,
)
from context.specialist_laboratory_message_v2_0287 import (
    SPECIALIST_ARTIFACT_REFERENCE_SCHEMA,
    SpecialistArtifactReference,
)
from context.specialist_multitask_model_0287 import (
    EXTENSIBLE_MULTITASK_SPECIALIST_SCHEMA,
    SPECIALIST_FOLLOWUP_TASK_PROPOSAL_SCHEMA,
    SPECIALIST_TASK_DEPENDENCY_SCHEMA,
    SPECIALIST_TASK_EXECUTION_BINDING_SCHEMA,
    SPECIALIST_TASK_PLAN_SCHEMA,
    SPECIALIST_TASK_REQUEST_SCHEMA,
    SPECIALIST_TASK_RESULT_SCHEMA,
    SPECIALIST_TASK_TYPE_SCHEMA,
    ExtensibleMultitaskSpecialistDefinition,
    SpecialistFollowupTaskProposal,
    SpecialistMultitaskContractError,
    SpecialistTaskDependency,
    SpecialistTaskExecutionBinding,
    SpecialistTaskPlan,
    SpecialistTaskRequest,
    SpecialistTaskResult,
    SpecialistTaskType,
    build_stable_task_idempotency_key,
    deep_analysis_task_type,
    project_deep_analysis_contribution_to_task_result,
    project_deep_analysis_request_to_task,
)


SPECIALIST_REF = "specialist:love-multitask-analyst"
PLAN_REF = "specialist-task-plan:love-study"
MISSION_REF = "mission:love-study"
INPUT_CONTRACT = "contract:missipy.research.correlated_work_package.v1"
ANALYSIS_OUTPUT = "contract:missipy.love.affect_analysis.v1"
CRITIQUE_OUTPUT = "contract:missipy.love.analysis_critique.v1"


def _capability(
    capability: str,
    output_contract: str,
) -> SpecialistCapabilityContract:
    return SpecialistCapabilityContract(
        schema=SPECIALIST_CAPABILITY_SCHEMA,
        capability=capability,
        description=f"Capability {capability}",
        accepted_input_contract_refs=(INPUT_CONTRACT,),
        produced_output_contract_refs=(output_contract,),
    )


def _descriptor() -> PortableSpecialistDescriptor:
    capabilities = (
        _capability("analysis.deep", ANALYSIS_OUTPUT),
        _capability("analysis.critique", CRITIQUE_OUTPUT),
    )
    return PortableSpecialistDescriptor(
        schema=PORTABLE_SPECIALIST_DESCRIPTOR_SCHEMA,
        specialist_ref=SPECIALIST_REF,
        display_name="Love multitask analyst",
        specialist_version="1.0.0",
        capabilities=capabilities,
        accepted_input_contract_refs=(INPUT_CONTRACT,),
        produced_output_contract_refs=(ANALYSIS_OUTPUT, CRITIQUE_OUTPUT),
        execution_profile=SpecialistExecutionProfile(
            schema=SPECIALIST_EXECUTION_PROFILE_SCHEMA,
            preferred_execution_boundaries=("in_process",),
            determinism_preference="preferred",
            max_parallel_visits=2,
            network_allowed=False,
        ),
        laboratory_bindings=(
            SpecialistLaboratoryBinding(
                schema=SPECIALIST_LABORATORY_BINDING_SCHEMA,
                specialist_ref=SPECIALIST_REF,
                laboratory_ref="laboratory:love-studies-local",
                visit_modes=("resident", "visitor"),
                required_laboratory_capabilities=(
                    "specialist.multitask.execution",
                ),
            ),
        ),
        availability="declared",
    )


def _task_type(
    task_type_ref: str,
    capability: str,
    output_contract: str,
) -> SpecialistTaskType:
    return SpecialistTaskType(
        schema=SPECIALIST_TASK_TYPE_SCHEMA,
        task_type_ref=task_type_ref,
        capability=capability,
        description=f"Task type {task_type_ref}",
        accepted_input_contract_refs=(INPUT_CONTRACT,),
        produced_output_contract_refs=(output_contract,),
        contribution_kinds=("domain_analysis",),
        supports_resume=True,
        supports_review=True,
        deterministic=True,
    )


def _binding() -> SpecialistTaskExecutionBinding:
    return SpecialistTaskExecutionBinding(
        schema=SPECIALIST_TASK_EXECUTION_BINDING_SCHEMA,
        backend_ref="openvino:genai.local",
        operation="generate",
        runtime_contract_ref="contract:missipy.inference.openvino_runtime.v1",
        model_ref="model:qwen2.5-love-analysis",
        tokenizer_ref="tokenizer:qwen2.5-love-analysis",
        model_sha256=hashlib.sha256(b"model").hexdigest(),
        device_refs=("device:CPU", "openvino:GPU"),
        parameters={"max_new_tokens": 512, "temperature": 0.2},
    )


def _task(
    *,
    suffix: str,
    task_type_ref: str,
    capability: str,
    output_contract: str,
) -> SpecialistTaskRequest:
    task_ref = f"specialist-task:{suffix}"
    return SpecialistTaskRequest(
        schema=SPECIALIST_TASK_REQUEST_SCHEMA,
        task_ref=task_ref,
        plan_ref=PLAN_REF,
        mission_ref=MISSION_REF,
        specialist_ref=SPECIALIST_REF,
        task_type_ref=task_type_ref,
        capability=capability,
        objective=f"Execute {suffix}",
        input_contract_ref=INPUT_CONTRACT,
        expected_output_contract_ref=output_contract,
        conversation_ref="laboratory-conversation:love-study",
        return_route_ref="route:github-issue:42",
        constraints=("Do not invent absent evidence",),
        success_criteria=("Return evidence-linked findings",),
        context_refs=("ctx:issue:42",),
        evidence_refs=("ctx:source:42",),
        priority=100,
        idempotency_key=build_stable_task_idempotency_key(
            PLAN_REF,
            task_ref,
        ),
        execution_binding=_binding(),
    )


def _deep_request() -> DeepAnalysisRequest:
    return DeepAnalysisRequest(
        schema=DEEP_ANALYSIS_REQUEST_SCHEMA,
        request_ref="analysis-request:love-affect",
        mission_ref=MISSION_REF,
        work_package_ref="research-work-package:love-42",
        conversation_ref="laboratory-conversation:love-study",
        return_route_ref="route:github-issue:42",
        specialist_ref=SPECIALIST_REF,
        domain_ref="domain:love-affects",
        objective="Analyse affective concepts",
        input_contract_ref=INPUT_CONTRACT,
        expected_output_contract_ref=ANALYSIS_OUTPUT,
        requested_contribution_kind="domain_analysis",
        depth="deep",
        constraints=("Do not infer absent intentions",),
        success_criteria=("Link observations to evidence",),
        context_refs=("ctx:issue:42",),
        evidence_refs=("ctx:source:42",),
    )


def _artifact() -> SpecialistArtifactReference:
    return SpecialistArtifactReference(
        schema=SPECIALIST_ARTIFACT_REFERENCE_SCHEMA,
        artifact_ref="artifact:love-affect-analysis",
        artifact_schema=DEEP_ANALYSIS_CONTRIBUTION_SCHEMA,
        producer_ref=SPECIALIST_REF,
        producer_visit_ref="laboratory-visit:love-1",
        storage_ref="sql:artifact:love-affect-analysis",
        content_sha256=hashlib.sha256(b"analysis").hexdigest(),
        media_type="application/json",
        byte_count=512,
        evidence_refs=("ctx:source:42",),
    )


def _deep_contribution(request: DeepAnalysisRequest) -> DeepAnalysisContribution:
    finding = DeepAnalysisFinding(
        schema=DEEP_ANALYSIS_FINDING_SCHEMA,
        finding_ref="finding:affection-present",
        status="observed",
        statement="Affection is explicitly expressed",
        confidence=0.8,
        evidence_refs=("ctx:source:42",),
    )
    return DeepAnalysisContribution(
        schema=DEEP_ANALYSIS_CONTRIBUTION_SCHEMA,
        contribution_ref="specialist-contribution:love-affect",
        request_ref=request.request_ref,
        specialist_ref=request.specialist_ref,
        visit_ref="laboratory-visit:love-1",
        domain_ref=request.domain_ref,
        contribution_kind=request.requested_contribution_kind,
        output_contract_ref=request.expected_output_contract_ref,
        findings=(finding,),
        human_representation="Affection is present; reciprocity is unresolved.",
        machine_payload={"affection": 0.8},
        recommendations=("Request relational-dynamics review",),
        requested_specialist_refs=(
            "specialist:love-relational-dynamics-analyst",
        ),
        evidence_refs=("ctx:source:42",),
        artifact_refs=(_artifact(),),
    )


def test_definition_declares_multiple_extensible_task_types() -> None:
    definition = ExtensibleMultitaskSpecialistDefinition(
        schema=EXTENSIBLE_MULTITASK_SPECIALIST_SCHEMA,
        descriptor=_descriptor(),
        task_types=(
            _task_type(
                "specialist-task-type:analysis.deep",
                "analysis.deep",
                ANALYSIS_OUTPUT,
            ),
            _task_type(
                "specialist-task-type:analysis.critique",
                "analysis.critique",
                CRITIQUE_OUTPUT,
            ),
        ),
    )
    mapping = definition.to_mapping()
    assert mapping["multitask"] is True
    assert mapping["extensible_by_versioned_task_types"] is True
    assert mapping["global_registry_created"] is False
    assert definition.task_type(
        "specialist-task-type:analysis.critique"
    ).capability == "analysis.critique"


def test_openvino_binding_reuses_existing_backend_without_implementation() -> None:
    mapping = _binding().to_mapping()
    assert mapping["reuses_existing_openvino_backend"] is True
    assert mapping["backend_implementation_created"] is False
    assert mapping["openvino_reimplemented"] is False
    assert mapping["parameters"]["max_new_tokens"] == 512


def test_multitask_plan_exposes_dependency_ready_tasks_without_scheduling() -> None:
    analysis = _task(
        suffix="analysis",
        task_type_ref="specialist-task-type:analysis.deep",
        capability="analysis.deep",
        output_contract=ANALYSIS_OUTPUT,
    )
    critique = _task(
        suffix="critique",
        task_type_ref="specialist-task-type:analysis.critique",
        capability="analysis.critique",
        output_contract=CRITIQUE_OUTPUT,
    )
    dependency = SpecialistTaskDependency(
        schema=SPECIALIST_TASK_DEPENDENCY_SCHEMA,
        task_ref=critique.task_ref,
        depends_on_task_ref=analysis.task_ref,
        kind="reviews",
    )
    plan = SpecialistTaskPlan(
        schema=SPECIALIST_TASK_PLAN_SCHEMA,
        plan_ref=PLAN_REF,
        mission_ref=MISSION_REF,
        specialist_ref=SPECIALIST_REF,
        tasks=(analysis, critique),
        dependencies=(dependency,),
        requested_parallelism=2,
    )
    assert plan.ready_task_refs() == (analysis.task_ref,)
    assert plan.ready_task_refs((analysis.task_ref,)) == (critique.task_ref,)
    mapping = plan.to_mapping()
    assert mapping["scheduler_owned"] is True
    assert mapping["scheduler_execution_started"] is False
    assert mapping["specialist_self_scheduling"] is False


def test_task_plan_rejects_dependency_cycles() -> None:
    first = _task(
        suffix="analysis",
        task_type_ref="specialist-task-type:analysis.deep",
        capability="analysis.deep",
        output_contract=ANALYSIS_OUTPUT,
    )
    second = _task(
        suffix="critique",
        task_type_ref="specialist-task-type:analysis.critique",
        capability="analysis.critique",
        output_contract=CRITIQUE_OUTPUT,
    )
    with pytest.raises(SpecialistMultitaskContractError, match="acyclic"):
        SpecialistTaskPlan(
            schema=SPECIALIST_TASK_PLAN_SCHEMA,
            plan_ref=PLAN_REF,
            mission_ref=MISSION_REF,
            specialist_ref=SPECIALIST_REF,
            tasks=(first, second),
            dependencies=(
                SpecialistTaskDependency(
                    schema=SPECIALIST_TASK_DEPENDENCY_SCHEMA,
                    task_ref=first.task_ref,
                    depends_on_task_ref=second.task_ref,
                    kind="after",
                ),
                SpecialistTaskDependency(
                    schema=SPECIALIST_TASK_DEPENDENCY_SCHEMA,
                    task_ref=second.task_ref,
                    depends_on_task_ref=first.task_ref,
                    kind="after",
                ),
            ),
            requested_parallelism=1,
        )


def test_followup_is_a_scheduler_proposal_not_a_launched_task() -> None:
    task = _task(
        suffix="analysis",
        task_type_ref="specialist-task-type:analysis.deep",
        capability="analysis.deep",
        output_contract=ANALYSIS_OUTPUT,
    )
    proposal = SpecialistFollowupTaskProposal(
        schema=SPECIALIST_FOLLOWUP_TASK_PROPOSAL_SCHEMA,
        proposal_ref="specialist-task-proposal:relational-review",
        source_task_ref=task.task_ref,
        task_type_ref="specialist-task-type:analysis.critique",
        capability="analysis.critique",
        objective="Critique the affect analysis from a relational perspective",
        expected_output_contract_ref=CRITIQUE_OUTPUT,
        reason="A second domain view is required",
        requested_specialist_ref=(
            "specialist:love-relational-dynamics-analyst"
        ),
        required_context_refs=("ctx:issue:42",),
    )
    result = SpecialistTaskResult(
        schema=SPECIALIST_TASK_RESULT_SCHEMA,
        task_ref=task.task_ref,
        plan_ref=task.plan_ref,
        specialist_ref=task.specialist_ref,
        task_type_ref=task.task_type_ref,
        capability=task.capability,
        status="partial",
        output_contract_ref=task.expected_output_contract_ref,
        human_representation="Affect analysis completed; review requested.",
        machine_payload={"analysis": "partial"},
        followup_proposals=(proposal,),
        requested_specialist_refs=(proposal.requested_specialist_ref,),
    )
    mapping = result.to_mapping()
    assert mapping["followup_proposals"][0]["scheduler_approval_required"] is True
    assert mapping["followup_proposals"][0]["task_created"] is False
    assert mapping["followups_executed"] is False
    assert mapping["scheduler_command_emitted"] is False


def test_deep_analysis_is_wrapped_as_one_generic_task_type() -> None:
    request = _deep_request()
    task_type = deep_analysis_task_type(
        output_contract_ref=request.expected_output_contract_ref
    )
    task = project_deep_analysis_request_to_task(
        request,
        plan_ref=PLAN_REF,
        execution_binding=_binding(),
    )
    contribution = _deep_contribution(request)
    result = project_deep_analysis_contribution_to_task_result(
        request,
        contribution,
        task=task,
    )
    assert task_type.task_type_ref == "specialist-task-type:analysis.deep"
    assert task.capability == "analysis.deep"
    assert task.metadata["deep_analysis_request_ref"] == request.request_ref
    assert result.status == "completed"
    assert result.machine_payload["analysis_preserved_for_later_synthesis"] is True
    assert result.requested_specialist_refs == (
        "specialist:love-relational-dynamics-analyst",
    )
    assert result.to_mapping()["durable_write_performed"] is False


def test_definition_rejects_task_type_outside_declared_capabilities() -> None:
    task_type = _task_type(
        "specialist-task-type:analysis.compare",
        "analysis.compare",
        ANALYSIS_OUTPUT,
    )
    with pytest.raises(
        SpecialistMultitaskContractError,
        match="capability is not declared",
    ):
        ExtensibleMultitaskSpecialistDefinition(
            schema=EXTENSIBLE_MULTITASK_SPECIALIST_SCHEMA,
            descriptor=_descriptor(),
            task_types=(task_type,),
        )


def test_request_validation_detects_capability_and_contract_drift() -> None:
    definition = ExtensibleMultitaskSpecialistDefinition(
        schema=EXTENSIBLE_MULTITASK_SPECIALIST_SCHEMA,
        descriptor=_descriptor(),
        task_types=(
            _task_type(
                "specialist-task-type:analysis.deep",
                "analysis.deep",
                ANALYSIS_OUTPUT,
            ),
        ),
    )
    request = _task(
        suffix="analysis",
        task_type_ref="specialist-task-type:analysis.deep",
        capability="analysis.deep",
        output_contract=ANALYSIS_OUTPUT,
    )
    assert definition.validate_request(request) == ()
    drifted = replace(request, capability="analysis.critique")
    assert definition.validate_request(drifted) == (
        "request capability does not match task type",
    )
