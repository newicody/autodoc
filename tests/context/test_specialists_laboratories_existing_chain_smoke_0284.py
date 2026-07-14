import asyncio
import json

import pytest

from context.fake_laboratory_closed_local_handoff_0274 import (
    FakeLaboratoryClosedHandoffCommand,
)
from context.fake_laboratory_deliberation_composition_0274 import (
    FakeLaboratoryDeliberationCommand,
)
from context.fake_laboratory_existing_scheduler_closed_loop_smoke_0274 import (
    FakeLaboratoryClosedLoopSmokeCommand,
)
from context.fake_laboratory_recall_closed_result_frame_0274 import (
    LaboratoryRecallClosureCommand,
)
from context.github_project_v2_source_candidate_vector_projection_0272 import (
    EmbeddingSpaceProfile,
)
from context.laboratory_framework_contract_0273 import LaboratoryResourceBudget
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
from context.scheduler_laboratory_visit_binding_0274 import (
    register_laboratory_visit_handler,
)
from context.scheduler_managed_embedding_qdrant_projection_usage_0262 import (
    DemoQdrantProjectionExecutor,
)
from context.scheduler_managed_qdrant_recall_sql_rehydrate_usage_0263 import (
    DemoQdrantRecallExecutor,
)
from context.scheduler_managed_sql_ref_openvino_embedding_usage_0261 import (
    build_embedding_mapping,
)
from context.server_oriented_deliberation_cycle import ServerOrientation
from context.specialists_laboratories_existing_chain_smoke_0284 import (
    PortableSpecialistExistingChainSmokeCommand,
    PortableSpecialistExistingChainSmokeError,
    run_portable_specialist_existing_chain_smoke,
)
from context.sql_context_store import SQLiteSqlContextStore
from kernel.dispatcher import Dispatcher
from kernel.event_bus import EventBus
from kernel.queue import PriorityQueue
from kernel.registry import Registry
from kernel.scheduler import Scheduler


def _descriptor(
    specialist_ref: str = "specialist:technical",
) -> PortableSpecialistDescriptor:
    input_ref = "contract:missipy.specialist.demand.v1"
    output_ref = "contract:missipy.laboratory.visit_result.v1"
    return PortableSpecialistDescriptor(
        schema=PORTABLE_SPECIALIST_DESCRIPTOR_SCHEMA,
        specialist_ref=specialist_ref,
        display_name="Portable deterministic technical specialist",
        specialist_version="1.0.0",
        capabilities=(
            SpecialistCapabilityContract(
                schema=SPECIALIST_CAPABILITY_SCHEMA,
                capability="laboratory.analysis",
                description="Produce one deterministic bounded laboratory analysis.",
                accepted_input_contract_refs=(input_ref,),
                produced_output_contract_refs=(output_ref,),
            ),
        ),
        accepted_input_contract_refs=(input_ref,),
        produced_output_contract_refs=(output_ref,),
        execution_profile=SpecialistExecutionProfile(
            schema=SPECIALIST_EXECUTION_PROFILE_SCHEMA,
            preferred_execution_boundaries=("in_process",),
            determinism_preference="required",
        ),
        laboratory_bindings=(
            SpecialistLaboratoryBinding(
                schema=SPECIALIST_LABORATORY_BINDING_SCHEMA,
                specialist_ref=specialist_ref,
                laboratory_ref="laboratory:local-fake",
                visit_modes=("resident", "visitor"),
                required_laboratory_capabilities=(
                    "laboratory.visit.execute",
                    "laboratory.specialist.simulate",
                ),
            ),
        ),
        availability="ready",
    )


def _orientation() -> ServerOrientation:
    return ServerOrientation(
        orientation_ref="orientation:portable-specialist-r5",
        artifact_ref="artifact:github-request:portable-r5",
        source_ref="artifact:source-candidate:portable-r5",
        sql_context_ref="sql:github_artifact:portable-r5-parent",
        title="Portable fake specialist existing-chain smoke",
        intent="Run one portable specialist through the existing Scheduler.",
        requested_specialist_refs=(
            "specialist:technical",
            "specialist:validator",
        ),
        requested_document_kinds=("analysis",),
        do_directives=("Preserve typed evidence.",),
        avoid_directives=("Do not publish without a gate.",),
        context_refs=("ctx:project:portable-r5",),
    )


def _profile() -> EmbeddingSpaceProfile:
    return EmbeddingSpaceProfile(
        backend_ref="openvino:model:multilingual-e5-small",
        model_ref="openvino.embedding.e5-small",
        model_revision="local-test",
        tokenizer_ref="transformers.multilingual-e5-small",
        role="passage",
        collection_name="laboratory_outputs_e5_384",
    )


def _embedder(text, sql_ref, model_dir, device):
    vector = [0.0] * 384
    vector[0] = 1.0
    role = "query" if text.startswith("query:") else "passage"
    return build_embedding_mapping(
        sql_ref=sql_ref,
        role=role,
        text=text,
        vector=vector,
        backend_ref="openvino:model:multilingual-e5-small",
        model="openvino.embedding.e5-small",
        tokenizer="transformers.multilingual-e5-small",
        model_path=model_dir or "",
        device=device,
    )


def _closed_loop_command(
    *,
    scenarios: tuple[tuple[str, str], ...] = (),
) -> FakeLaboratoryClosedLoopSmokeCommand:
    deliberation = FakeLaboratoryDeliberationCommand(
        orientation=_orientation(),
        artifact_ref="artifact:github-request:portable-r5",
        source_candidate_ref="source-candidate:projectv2:portable-r5",
        target_ref="github:issue:newicody/projects/51",
        context_generation=7,
        resource_budget=LaboratoryResourceBudget(
            max_duration_ms=2_000,
            max_context_refs=16,
            max_evidence_refs=16,
            max_followup_requests=8,
        ),
        scenario_by_specialist=scenarios,
        priority=9,
    )
    return FakeLaboratoryClosedLoopSmokeCommand(
        deliberation=deliberation,
        handoff=FakeLaboratoryClosedHandoffCommand(
            execute=True,
            policy_decision_id="policy:0284:r5:handoff",
            vector_execute=True,
        ),
        recall=LaboratoryRecallClosureCommand(
            execute=True,
            policy_decision_id="policy:0284:r5:recall",
        ),
        verify_sql_replay=True,
        timeout_per_visit=1.0,
    )


async def _execute(command: PortableSpecialistExistingChainSmokeCommand):
    event_bus = EventBus()
    dispatcher = Dispatcher(event_bus)
    register_laboratory_visit_handler(dispatcher)
    scheduler = Scheduler(
        queue=PriorityQueue(),
        dispatcher=dispatcher,
        event_bus=event_bus,
        registry=Registry(),
        context_interval=60.0,
    )
    run_task = asyncio.create_task(scheduler.run())
    try:
        return await run_portable_specialist_existing_chain_smoke(
            scheduler,
            command,
            store=SQLiteSqlContextStore(),
            passage_profile=_profile(),
            embedder=_embedder,
            projection_executor=DemoQdrantProjectionExecutor(),
            recall_executor_factory=lambda sql_ref: DemoQdrantRecallExecutor(
                sql_refs=(sql_ref,)
            ),
            event_bus=event_bus,
        )
    finally:
        await scheduler.shutdown()
        await asyncio.wait_for(run_task, timeout=1.0)


def test_portable_fake_specialist_uses_existing_scheduler_and_closes_messages() -> None:
    command = PortableSpecialistExistingChainSmokeCommand(
        descriptor=_descriptor(),
        smoke=_closed_loop_command(),
        specialist_ref="specialist:technical",
    )
    result = asyncio.run(_execute(command))
    payload = result.to_mapping()

    assert result.valid is True
    assert result.fake_specialist_executed is True
    assert result.portable_identity_preserved is True
    assert result.existing_scheduler_path_verified is True
    assert result.message_contract_closed is True
    assert result.durable_closed_loop_preserved is True
    assert result.conversation is not None
    assert len(result.conversation.messages) == 2
    assert result.conversation.messages[0].kind == "demand"
    assert result.conversation.messages[1].kind == "opinion"
    assert result.provider_ref == "laboratory:local-fake"
    assert payload["live_path_status"] == "transition"
    assert payload["real_specialist_backend_used"] is False
    assert payload["transfer_execution_performed"] is False
    json.dumps(payload, sort_keys=True)


def test_non_converged_existing_smoke_does_not_claim_portable_closure() -> None:
    command = PortableSpecialistExistingChainSmokeCommand(
        descriptor=_descriptor(),
        smoke=_closed_loop_command(
            scenarios=(("specialist:technical", "needs_context"),)
        ),
        specialist_ref="specialist:technical",
    )
    result = asyncio.run(_execute(command))

    assert result.valid is False
    assert result.conversation is None
    assert result.fake_specialist_executed is False
    assert result.durable_closed_loop_preserved is False


def test_command_rejects_descriptor_not_requested_by_orientation() -> None:
    with pytest.raises(
        PortableSpecialistExistingChainSmokeError,
        match="requested by deliberation orientation",
    ):
        PortableSpecialistExistingChainSmokeCommand(
            descriptor=_descriptor("specialist:not-requested"),
            smoke=_closed_loop_command(),
            specialist_ref="specialist:not-requested",
        )
