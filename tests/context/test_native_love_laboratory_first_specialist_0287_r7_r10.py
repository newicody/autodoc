from __future__ import annotations

import pytest

from context.laboratory_framework_contract_0273 import (
    LABORATORY_RESOURCE_BUDGET_SCHEMA,
    LABORATORY_VISIT_REQUEST_SCHEMA,
    LaboratoryResourceBudget,
    LaboratoryVisitRequest,
)
from context.love_study_contracts_0287 import (
    LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,
    LOVE_CONCEPT_AFFECT_ANALYSIS_SCHEMA,
    LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
    LOVE_STUDIES_LABORATORY_REF,
    LOVE_STUDY_REQUEST_CONTRACT_REF,
    LOVE_STUDY_REQUEST_SCHEMA,
    SPECIALIST_TASK_RESULT_CONTRACT_REF,
    LoveStudyRequest,
)
from context.native_love_laboratory_first_specialist_0287 import (
    NATIVE_LOVE_LABORATORY_COMPONENT_ID,
    InMemoryLoveLaboratoryInputResolver,
    NativeLoveLaboratoryError,
    bind_native_love_laboratory_registration,
    build_native_love_laboratory_descriptor,
    build_native_love_laboratory_provider,
    build_native_love_laboratory_registration,
    execute_native_love_laboratory_visit,
)
from context.scheduler_owned_runtime_registry_0257 import (
    build_scheduler_owned_runtime_registry,
)
from context.specialist_multitask_model_0287 import (
    SPECIALIST_TASK_REQUEST_SCHEMA,
    SpecialistTaskRequest,
)


def _study(text: str, suffix: str = "one") -> LoveStudyRequest:
    return LoveStudyRequest(
        schema=LOVE_STUDY_REQUEST_SCHEMA,
        study_ref=f"love-study:{suffix}",
        source_issue_ref="github-issue:newicody-projects-1",
        objective="Analyser les concepts et affects exprimés.",
        subject_text=text,
        constraints=("Ne pas inférer les intentions absentes.",),
        success_criteria=("Citer les éléments du texte.",),
        context_refs=("ctx:love:source",),
        evidence_refs=("artifact:love-source",),
    )


def _task(
    *,
    suffix: str = "one",
    capability: str = "love.concept_analysis",
    output_contract: str = LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,
) -> SpecialistTaskRequest:
    return SpecialistTaskRequest(
        schema=SPECIALIST_TASK_REQUEST_SCHEMA,
        task_ref=f"specialist-task:{suffix}",
        plan_ref="specialist-task-plan:love-one",
        mission_ref="mission:love-one",
        specialist_ref=LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
        task_type_ref=f"task-type:{capability}",
        capability=capability,
        objective="Produire une analyse attribuable du texte fourni.",
        input_contract_ref=LOVE_STUDY_REQUEST_CONTRACT_REF,
        expected_output_contract_ref=output_contract,
        conversation_ref="laboratory-conversation:love-one",
        return_route_ref="route:love-return",
        constraints=("Ne pas diagnostiquer les personnes.",),
        success_criteria=("Retourner un résultat structuré.",),
        context_refs=("ctx:love:source",),
        evidence_refs=("artifact:love-source",),
        idempotency_key=f"love-task-{suffix}-{capability}",
        metadata={"context_revision_ref": "context-revision:love-r1"},
    )


def _visit(
    task: SpecialistTaskRequest,
    study: LoveStudyRequest,
    *,
    specialist_ref: str = LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
) -> LaboratoryVisitRequest:
    return LaboratoryVisitRequest(
        schema=LABORATORY_VISIT_REQUEST_SCHEMA,
        visit_ref=f"laboratory-visit:{task.task_ref.split(':', 1)[1]}",
        laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        specialist_ref=specialist_ref,
        objective_ref=task.task_ref,
        source_candidate_ref=study.study_ref,
        context_generation=1,
        input_contract_ref=task.input_contract_ref,
        expected_output_contract_ref=task.expected_output_contract_ref,
        resource_budget=LaboratoryResourceBudget(
            schema=LABORATORY_RESOURCE_BUDGET_SCHEMA,
            max_duration_ms=5_000,
            max_output_chars=32_768,
            max_context_refs=8,
            max_evidence_refs=64,
            max_followup_requests=4,
            max_specialist_messages=16,
            max_external_calls=0,
            allow_network=False,
        ),
        return_route_ref=task.return_route_ref,
        context_refs=task.context_refs,
        evidence_refs=task.evidence_refs,
        conversation_ref=task.conversation_ref,
    )


def _provider(study: LoveStudyRequest, task: SpecialistTaskRequest):
    resolver = InMemoryLoveLaboratoryInputResolver(
        studies={study.study_ref: study},
        tasks={task.task_ref: task},
    )
    return build_native_love_laboratory_provider(resolver)


def test_descriptor_is_ready_native_and_network_closed() -> None:
    descriptor = build_native_love_laboratory_descriptor()

    assert descriptor.laboratory_ref == LOVE_STUDIES_LABORATORY_REF
    assert descriptor.provider_kind == "autodoc_native"
    assert descriptor.availability == "ready"
    assert descriptor.enabled is True
    assert descriptor.execution_boundary == "in_process"
    assert descriptor.network_allowed is False
    assert dict(descriptor.metadata)["first_specialist_real"] == "true"


def test_registration_extends_existing_scheduler_owned_registry() -> None:
    registry = build_scheduler_owned_runtime_registry()
    updated = bind_native_love_laboratory_registration(registry)
    registration = build_native_love_laboratory_registration()

    assert registration.component_id == NATIVE_LOVE_LABORATORY_COMPONENT_ID
    assert updated.owner == "scheduler"
    assert updated.registrations[-1] == registration
    assert bind_native_love_laboratory_registration(updated) is updated
    assert updated.creates_runtime_manager is False
    assert updated.instantiates_components is False


def test_concept_analysis_depends_on_supplied_text() -> None:
    first = _study(
        "Je ressens beaucoup de tendresse et de confiance. "
        "Nous parlons de notre avenir ensemble.",
        "first",
    )
    second = _study(
        "La distance et la jalousie créent un doute. "
        "Nous évitons la discussion.",
        "second",
    )
    first_task = _task(suffix="first")
    second_task = _task(suffix="second")

    first_record = execute_native_love_laboratory_visit(
        _visit(first_task, first),
        provider=_provider(first, first_task),
    )
    second_record = execute_native_love_laboratory_visit(
        _visit(second_task, second),
        provider=_provider(second, second_task),
    )

    first_payload = first_record.result.machine_result
    second_payload = second_record.result.machine_result
    assert first_payload["schema"] == LOVE_CONCEPT_AFFECT_ANALYSIS_SCHEMA
    assert second_payload["schema"] == LOVE_CONCEPT_AFFECT_ANALYSIS_SCHEMA
    assert first_payload["analysis_ref"] != second_payload["analysis_ref"]
    assert "trust" in first_payload["concepts"]
    assert "separation" in second_payload["concepts"]
    assert first_record.real_specialist_executed is True
    assert first_record.content_dependent_result is True
    assert first_record.openvino_used is False


def test_evidence_extraction_is_a_real_multitask_capability() -> None:
    study = _study(
        "Je l'aime. Nous devons parler de nos limites et de notre avenir.",
        "evidence",
    )
    task = _task(
        suffix="evidence",
        capability="love.evidence_extraction",
        output_contract=SPECIALIST_TASK_RESULT_CONTRACT_REF,
    )

    record = execute_native_love_laboratory_visit(
        _visit(task, study),
        provider=_provider(study, task),
    )

    payload = record.result.machine_result
    assert payload["schema"] == "missipy.specialist.task_result.v1"
    assert payload["capability"] == "love.evidence_extraction"
    assert len(payload["machine_payload"]["sentences"]) == 2
    assert payload["artifact_refs"][0]["inline_bytes_present"] is False


def test_local_synthesis_requires_explicit_task_capability() -> None:
    study = _study(
        "Il y a de la tendresse et du doute, mais nous parlons avec respect.",
        "synthesis",
    )
    task = _task(
        suffix="synthesis",
        capability="analysis.local_synthesis",
    )

    record = execute_native_love_laboratory_visit(
        _visit(task, study),
        provider=_provider(study, task),
    )

    payload = record.result.machine_result
    assert payload["contribution_kind"] == "local_synthesis"
    assert payload["local_synthesis"]
    assert payload["global_synthesis_claimed"] is False


def test_second_specialist_is_not_silently_enabled_in_r10() -> None:
    study = _study("Nous parlons avec confiance.", "second-refused")
    task = _task(suffix="second-refused")
    visit = _visit(
        task,
        study,
        specialist_ref="specialist:love-relational-dynamics-analyst",
    )

    with pytest.raises(NativeLoveLaboratoryError, match="first love specialist"):
        _provider(study, task).execute(visit)


def test_resolver_rejects_unknown_authoritative_inputs() -> None:
    study = _study("Nous parlons.", "known")
    task = _task(suffix="known")
    resolver = InMemoryLoveLaboratoryInputResolver(
        studies={study.study_ref: study},
        tasks={task.task_ref: task},
    )
    provider = build_native_love_laboratory_provider(resolver)
    unknown = _study("Autre texte.", "unknown")

    with pytest.raises(NativeLoveLaboratoryError, match="source_candidate_ref"):
        provider.execute(_visit(task, unknown))


@pytest.mark.asyncio
async def test_existing_scheduler_path_executes_native_provider() -> None:
    from contracts.event import Event
    from contracts.scheduler import SchedulerContract
    from context.native_love_laboratory_scheduler_binding_0287 import (
        NativeLoveLaboratoryVisitRequestHandler,
        register_native_love_laboratory_visit_handler,
        submit_native_love_laboratory_visit,
    )

    study = _study(
        "Je ressens de la tendresse et nous parlons avec confiance.",
        "scheduler",
    )
    task = _task(suffix="scheduler")
    provider = _provider(study, task)

    class Dispatcher:
        def __init__(self) -> None:
            self.handler: NativeLoveLaboratoryVisitRequestHandler | None = None

        def register(self, event_type, handler) -> None:
            self.event_type = event_type
            self.handler = handler

    dispatcher = Dispatcher()
    handler = register_native_love_laboratory_visit_handler(
        dispatcher,
        provider=provider,
    )

    class InlineScheduler(SchedulerContract):
        async def emit(self, event: Event) -> None:
            receipt = await handler.handle(event)
            assert event.request is not None
            assert event.request.reply is not None
            event.request.reply.set_result(receipt)

        async def shutdown(self) -> None:
            return None

    receipt = await submit_native_love_laboratory_visit(
        InlineScheduler(),
        _visit(task, study),
    )

    assert receipt.existing_scheduler_used is True
    assert receipt.scheduler_created is False
    assert receipt.parallel_registry_created is False
    assert receipt.execution.real_specialist_executed is True
    assert receipt.execution.result.machine_result["schema"] == (
        LOVE_CONCEPT_AFFECT_ANALYSIS_SCHEMA
    )
