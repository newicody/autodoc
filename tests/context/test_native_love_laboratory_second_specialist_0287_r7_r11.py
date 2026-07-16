from __future__ import annotations

import asyncio
from dataclasses import replace
from typing import Any

import pytest

from contracts.event import Event, EventType
from contracts.scheduler import SchedulerContract
from context.laboratory_framework_contract_0273 import (
    LABORATORY_VISIT_REQUEST_SCHEMA,
    LaboratoryResourceBudget,
    LaboratoryVisitRequest,
)
from context.love_study_contracts_0287 import (
    LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,
    LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
    LOVE_RELATIONAL_DYNAMICS_ANALYSIS_CONTRACT_REF,
    LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF,
    LOVE_STUDIES_LABORATORY_REF,
    LOVE_STUDY_REQUEST_CONTRACT_REF,
    LOVE_STUDY_REQUEST_SCHEMA,
    LoveStudyRequest,
)
from context.native_love_laboratory_collaboration_scheduler_binding_0287 import (
    NativeLoveCollaborationSchedulerVisitReceipt,
    register_native_love_collaboration_visit_handler,
    submit_native_love_collaboration_visit,
)
from context.native_love_laboratory_first_specialist_0287 import (
    NativeLoveLaboratoryError,
    bind_native_love_laboratory_registration,
    build_native_love_laboratory_provider,
)
from context.native_love_laboratory_second_specialist_0287 import (
    InMemoryCollaborativeLoveLaboratoryInputResolver,
    NativeLoveCollaborationError,
    build_completed_collaboration_record,
    build_native_love_collaborative_descriptor,
    build_native_love_collaborative_provider,
    build_native_love_collaborative_registration,
    concept_analysis_from_visit_result,
    prepare_second_specialist_collaboration,
    relational_analysis_from_visit_result,
    upgrade_native_love_collaborative_registration,
)
from context.scheduler_owned_runtime_registry_0257 import (
    build_scheduler_owned_runtime_registry,
)
from context.specialist_laboratory_message_v2_0287 import (
    SpecialistArtifactReference,
)
from context.specialist_multitask_model_0287 import (
    SPECIALIST_TASK_REQUEST_SCHEMA,
    SpecialistTaskRequest,
)


class _Dispatcher:
    def __init__(self) -> None:
        self.handlers: dict[EventType, Any] = {}

    def register(self, event_type: EventType, handler: object) -> None:
        self.handlers[event_type] = handler


class _Scheduler(SchedulerContract):
    def __init__(self, dispatcher: _Dispatcher) -> None:
        self.dispatcher = dispatcher
        self.events: list[Event] = []
        self.shutdown_called = False

    async def emit(self, event: Event) -> None:
        self.events.append(event)
        handler = self.dispatcher.handlers[event.type]
        result = await handler.handle(event)
        assert event.request is not None
        assert event.request.reply is not None
        event.request.reply.set_result(result)

    async def shutdown(self) -> None:
        self.shutdown_called = True


def _fixture(
    text: str = (
        "Je l'aime et nous parlons souvent. "
        "Mais j'ai l'impression de faire toujours plus que lui. "
        "Nous évitons de parler d'engagement."
    ),
) -> tuple[
    LoveStudyRequest,
    SpecialistTaskRequest,
    LaboratoryVisitRequest,
    InMemoryCollaborativeLoveLaboratoryInputResolver,
]:
    study = LoveStudyRequest(
        schema=LOVE_STUDY_REQUEST_SCHEMA,
        study_ref="love-study:collaboration-1",
        source_issue_ref="github-issue:newicody/projects#41",
        objective="Analyser la relation décrite.",
        subject_text=text,
        constraints=("Ne pas produire de diagnostic psychologique.",),
        success_criteria=("Produire deux analyses attribuées.",),
        context_refs=("context-revision:love-r1",),
    )
    task = SpecialistTaskRequest(
        schema=SPECIALIST_TASK_REQUEST_SCHEMA,
        task_ref="specialist-task:love-first",
        plan_ref="specialist-task-plan:love-collaboration",
        mission_ref="mission:love-study-41",
        specialist_ref=LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
        task_type_ref="task-type:love.concept_analysis",
        capability="love.concept_analysis",
        objective="Analyser les concepts et affects présents.",
        input_contract_ref=LOVE_STUDY_REQUEST_CONTRACT_REF,
        expected_output_contract_ref=LOVE_CONCEPT_AFFECT_ANALYSIS_CONTRACT_REF,
        conversation_ref="laboratory-conversation:love-study-41",
        return_route_ref="route:love-study-41",
        constraints=(),
        success_criteria=("Fournir des constats et preuves.",),
        context_refs=("ctx:love-study-41",),
        idempotency_key="idempotency:love-first-0001",
        metadata={"context_revision_ref": "context-revision:love-r1"},
    )
    visit = LaboratoryVisitRequest(
        schema=LABORATORY_VISIT_REQUEST_SCHEMA,
        visit_ref="laboratory-visit:love-first",
        laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        specialist_ref=LOVE_CONCEPT_AFFECT_SPECIALIST_REF,
        objective_ref=task.task_ref,
        source_candidate_ref=study.study_ref,
        context_generation=1,
        input_contract_ref=task.input_contract_ref,
        expected_output_contract_ref=task.expected_output_contract_ref,
        resource_budget=LaboratoryResourceBudget(),
        return_route_ref=task.return_route_ref,
        context_refs=task.context_refs,
        origin_laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        target_laboratory_ref=LOVE_STUDIES_LABORATORY_REF,
        conversation_ref=task.conversation_ref,
    )
    resolver = InMemoryCollaborativeLoveLaboratoryInputResolver(
        studies={study.study_ref: study},
        tasks={task.task_ref: task},
    )
    return study, task, visit, resolver


def _prepare(
    text: str = (
        "Je l'aime et nous parlons souvent. "
        "Mais j'ai l'impression de faire toujours plus que lui. "
        "Nous évitons de parler d'engagement."
    ),
):
    study, task, visit, resolver = _fixture(text)
    provider = build_native_love_collaborative_provider(resolver)
    first_result = provider.execute(visit)
    preparation = prepare_second_specialist_collaboration(
        first_visit=visit,
        first_result=first_result,
        second_task_ref="specialist-task:love-second",
        second_visit_ref="laboratory-visit:love-second",
    )
    return study, task, visit, resolver, provider, first_result, preparation


def test_collaborative_descriptor_activates_two_real_specialists() -> None:
    descriptor = build_native_love_collaborative_descriptor()
    metadata = dict(descriptor.metadata)

    assert descriptor.enabled is True
    assert descriptor.provider_kind == "autodoc_native"
    assert metadata["runtime_phase"] == "0287-r7-r11"
    assert metadata["first_specialist_real"] == "true"
    assert metadata["second_specialist_real"] == "true"
    assert metadata["direct_followup_execution"] == "false"
    assert metadata["global_synthesis"] == "later_liaison_step"


def test_collaborative_registration_upgrades_one_existing_component() -> None:
    registry = bind_native_love_laboratory_registration(
        build_scheduler_owned_runtime_registry()
    )
    upgraded = upgrade_native_love_collaborative_registration(registry)
    expected = build_native_love_collaborative_registration()
    matching = tuple(
        item
        for item in upgraded.registrations
        if item.component_id == expected.component_id
    )

    assert matching == (expected,)
    assert len(upgraded.registrations) == len(registry.registrations)
    assert any(
        path.endswith("native_love_laboratory_second_specialist_0287.py")
        for path in expected.source_paths
    )
    assert upgraded.creates_runtime_manager is False


def test_collaborative_provider_reuses_the_r10_first_specialist() -> None:
    _, _, visit, resolver = _fixture()
    provider = build_native_love_collaborative_provider(resolver)

    result = provider.execute(visit)
    analysis = concept_analysis_from_visit_result(result)

    assert provider.first_provider.resolver is resolver
    assert result.specialist_ref == LOVE_CONCEPT_AFFECT_SPECIALIST_REF
    assert analysis.study_ref == "love-study:collaboration-1"
    assert analysis.findings


def test_preparation_does_not_execute_second_specialist() -> None:
    *_, preparation = _prepare()

    mapping = preparation.to_mapping()
    assert preparation.scheduler_submission_required is True
    assert preparation.second_visit_executed is False
    assert preparation.direct_specialist_invocation is False
    assert mapping["task_created_by_scheduler"] is False
    assert preparation.second_task.specialist_ref == (
        LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF
    )
    assert preparation.first_artifact in (
        preparation.second_task.input_artifact_refs
    )


def test_second_specialist_requires_registered_source_artifact() -> None:
    *_, resolver, provider, _, preparation = _prepare()
    resolver.register_task(preparation.second_task)

    with pytest.raises(
        NativeLoveCollaborationError,
        match="artifact is unavailable",
    ):
        provider.execute(preparation.second_visit)


def test_second_specialist_rejects_digest_mismatch() -> None:
    *_, resolver, _, _, preparation = _prepare()
    artifact = preparation.first_artifact
    altered = replace(artifact, content_sha256="0" * 64)

    with pytest.raises(
        NativeLoveCollaborationError,
        match="digest does not match",
    ):
        resolver.register_concept_analysis(preparation.first_analysis, altered)


def test_second_specialist_consumes_first_analysis_and_source_text() -> None:
    *_, resolver, provider, _, preparation = _prepare()
    resolver.register_concept_analysis(
        preparation.first_analysis,
        preparation.first_artifact,
    )
    resolver.register_task(preparation.second_task)

    result = provider.execute(preparation.second_visit)
    analysis = relational_analysis_from_visit_result(result)

    assert analysis.source_analysis_refs == (
        preparation.first_analysis.analysis_ref,
    )
    assert "communication" in analysis.dynamics
    assert "asymmetry" in analysis.dynamics
    assert analysis.specialist_ref == LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF
    assert "synthèse globale" in result.human_representation.lower()


def test_second_result_changes_when_relationship_text_changes() -> None:
    left = _prepare(
        "Nous discutons avec confiance et nos projets sont mutuels."
    )
    right = _prepare(
        "Le silence crée une distance et je fais toujours plus que lui."
    )
    analyses = []
    for values in (left, right):
        resolver = values[3]
        provider = values[4]
        preparation = values[6]
        resolver.register_concept_analysis(
            preparation.first_analysis,
            preparation.first_artifact,
        )
        resolver.register_task(preparation.second_task)
        result = provider.execute(preparation.second_visit)
        analyses.append(relational_analysis_from_visit_result(result))

    assert analyses[0].dynamics != analyses[1].dynamics
    assert analyses[0].analysis_ref != analyses[1].analysis_ref


def test_old_r10_provider_still_refuses_second_specialist() -> None:
    *_, resolver, _, _, preparation = _prepare()
    resolver.register_concept_analysis(
        preparation.first_analysis,
        preparation.first_artifact,
    )
    resolver.register_task(preparation.second_task)
    r10_provider = build_native_love_laboratory_provider(resolver)

    with pytest.raises(
        NativeLoveLaboratoryError,
        match="only the first love specialist",
    ):
        r10_provider.execute(preparation.second_visit)


def test_two_visits_use_same_scheduler_and_close_v2_conversation() -> None:
    async def run() -> None:
        _, _, first_visit, resolver = _fixture()
        provider = build_native_love_collaborative_provider(resolver)
        dispatcher = _Dispatcher()
        register_native_love_collaboration_visit_handler(
            dispatcher,
            provider=provider,
        )
        scheduler = _Scheduler(dispatcher)

        first_receipt = await submit_native_love_collaboration_visit(
            scheduler,
            first_visit,
        )
        assert isinstance(
            first_receipt,
            NativeLoveCollaborationSchedulerVisitReceipt,
        )
        preparation = prepare_second_specialist_collaboration(
            first_visit=first_visit,
            first_result=first_receipt.execution.result,
            second_task_ref="specialist-task:love-second",
            second_visit_ref="laboratory-visit:love-second",
        )
        resolver.register_concept_analysis(
            preparation.first_analysis,
            preparation.first_artifact,
        )
        resolver.register_task(preparation.second_task)
        second_receipt = await submit_native_love_collaboration_visit(
            scheduler,
            preparation.second_visit,
        )
        record = build_completed_collaboration_record(
            preparation=preparation,
            first_execution=first_receipt.execution,
            second_execution=second_receipt.execution,
            first_scheduler_receipt_ref=first_receipt.receipt_ref,
            second_scheduler_receipt_ref=second_receipt.receipt_ref,
        )

        assert len(scheduler.events) == 2
        assert all(
            event.dest == "scheduler" for event in scheduler.events
        )
        assert record.conversation.closed is True
        assert tuple(
            message.sequence_no for message in record.conversation.messages
        ) == (0, 1, 2, 3)
        assert len(record.conversation.to_mapping()["visit_refs"]) == 2
        assert record.direct_specialist_invocation is False
        assert record.global_synthesis_created is False
        assert record.second_analysis.source_analysis_refs == (
            preparation.first_analysis.analysis_ref,
        )

    asyncio.run(run())


def test_second_task_artifact_must_match_registered_metadata() -> None:
    *_, resolver, provider, _, preparation = _prepare()
    resolver.register_concept_analysis(
        preparation.first_analysis,
        preparation.first_artifact,
    )
    tampered_artifact = SpecialistArtifactReference(
        schema=preparation.first_artifact.schema,
        artifact_ref=preparation.first_artifact.artifact_ref,
        artifact_schema=preparation.first_artifact.artifact_schema,
        producer_ref=preparation.first_artifact.producer_ref,
        producer_visit_ref=preparation.first_artifact.producer_visit_ref,
        storage_ref=preparation.first_artifact.storage_ref,
        content_sha256=preparation.first_artifact.content_sha256,
        media_type="application/problem+json",
        byte_count=preparation.first_artifact.byte_count,
        evidence_refs=preparation.first_artifact.evidence_refs,
        provenance_refs=preparation.first_artifact.provenance_refs,
    )
    task = replace(
        preparation.second_task,
        input_artifact_refs=(tampered_artifact,),
    )
    resolver.register_task(task)

    with pytest.raises(
        NativeLoveCollaborationError,
        match="metadata differs",
    ):
        provider.execute(preparation.second_visit)
