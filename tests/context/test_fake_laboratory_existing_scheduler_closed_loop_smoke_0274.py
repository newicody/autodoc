import asyncio
import json

import pytest

from context.fake_laboratory_closed_local_handoff_0274 import (
    FakeLaboratoryClosedHandoffCommand,
)
from context.fake_laboratory_deliberation_composition_0274 import (
    FAKE_LABORATORY_DELIBERATION_COMMAND_SCHEMA,
    FakeLaboratoryDeliberationCommand,
)
from context.fake_laboratory_existing_scheduler_closed_loop_smoke_0274 import (
    FakeLaboratoryClosedLoopSmokeCommand,
    FakeLaboratoryClosedLoopSmokeError,
    run_fake_laboratory_existing_scheduler_closed_loop_smoke,
)
from context.fake_laboratory_recall_closed_result_frame_0274 import (
    LaboratoryRecallClosureCommand,
)
from context.github_project_v2_source_candidate_vector_projection_0272 import (
    EmbeddingSpaceProfile,
)
from context.laboratory_framework_contract_0273 import (
    LaboratoryResourceBudget,
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
from context.sql_context_store import SQLiteSqlContextStore
from kernel.dispatcher import Dispatcher
from kernel.event_bus import EventBus
from kernel.queue import PriorityQueue
from kernel.registry import Registry
from kernel.scheduler import Scheduler


def orientation() -> ServerOrientation:
    return ServerOrientation(
        orientation_ref="orientation:laboratory-r5",
        artifact_ref="artifact:github-request:r5",
        source_ref="artifact:source-candidate:r5",
        sql_context_ref="sql:github_artifact:r5-parent",
        title="Smoke fermé laboratoire fictif",
        intent="Vérifier le chemin local complet r2-r4.",
        requested_specialist_refs=(
            "specialist:technical",
            "specialist:validator",
        ),
        requested_document_kinds=("analysis",),
        do_directives=("Conserver les preuves.",),
        avoid_directives=("Ne pas publier sans gate.",),
        context_refs=("ctx:project:r5",),
    )


def passage_profile() -> EmbeddingSpaceProfile:
    return EmbeddingSpaceProfile(
        backend_ref="openvino:model:multilingual-e5-small",
        model_ref="openvino.embedding.e5-small",
        model_revision="local-test",
        tokenizer_ref="transformers.multilingual-e5-small",
        role="passage",
        collection_name="laboratory_outputs_e5_384",
    )


def embedder(text, sql_ref, model_dir, device):
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


def command(
    *,
    scenarios: tuple[tuple[str, str], ...] = (),
    observations: bool = False,
    verify_sql_replay: bool = True,
) -> FakeLaboratoryClosedLoopSmokeCommand:
    deliberation = FakeLaboratoryDeliberationCommand(
        schema=FAKE_LABORATORY_DELIBERATION_COMMAND_SCHEMA,
        orientation=orientation(),
        artifact_ref="artifact:github-request:r5",
        source_candidate_ref="source-candidate:projectv2:r5",
        target_ref="github:issue:newicody/ideas/45",
        context_generation=6,
        resource_budget=LaboratoryResourceBudget(
            max_duration_ms=2_000,
            max_context_refs=16,
            max_evidence_refs=16,
            max_followup_requests=8,
        ),
        scenario_by_specialist=scenarios,
    )
    return FakeLaboratoryClosedLoopSmokeCommand(
        deliberation=deliberation,
        handoff=FakeLaboratoryClosedHandoffCommand(
            execute=True,
            policy_decision_id="policy:0274:r5:handoff",
            vector_execute=True,
            publish_observations=observations,
        ),
        recall=LaboratoryRecallClosureCommand(
            execute=True,
            policy_decision_id="policy:0274:r5:recall",
            publish_observations=observations,
        ),
        verify_sql_replay=verify_sql_replay,
        timeout_per_visit=1.0,
    )


async def execute_smoke(
    item: FakeLaboratoryClosedLoopSmokeCommand,
    *,
    event_bus: EventBus | None = None,
    recall_factory=None,
):
    observation_bus = event_bus or EventBus()
    dispatcher = Dispatcher(observation_bus)
    register_laboratory_visit_handler(dispatcher)
    scheduler = Scheduler(
        queue=PriorityQueue(),
        dispatcher=dispatcher,
        event_bus=observation_bus,
        registry=Registry(),
        context_interval=60.0,
    )
    run_task = asyncio.create_task(scheduler.run())
    try:
        return await run_fake_laboratory_existing_scheduler_closed_loop_smoke(
            scheduler,
            item,
            store=SQLiteSqlContextStore(),
            passage_profile=passage_profile(),
            embedder=embedder,
            projection_executor=DemoQdrantProjectionExecutor(),
            recall_executor_factory=(
                recall_factory
                or (
                    lambda sql_ref: DemoQdrantRecallExecutor(
                        sql_refs=(sql_ref,)
                    )
                )
            ),
            event_bus=observation_bus,
        )
    finally:
        await scheduler.shutdown()
        await asyncio.wait_for(run_task, timeout=1.0)


def test_complete_smoke_closes_r2_r3_r4_and_sql_replay() -> None:
    result = asyncio.run(execute_smoke(command()))
    payload = result.to_mapping()

    assert result.valid is True
    assert result.phase_trace == (
        "0274-r2-deliberation",
        "0274-r3-durable-passage-projection",
        "0274-r4-query-recall-result-frame",
    )
    assert result.closed_loop_complete is True
    assert result.sql_replay_verified is True
    assert result.specialist_output_verified is True
    assert result.visual_path_complete is True
    assert result.publication_preview_ready is True
    assert result.sql_ref.startswith("sql:specialist_output:")
    assert result.final_ref.startswith("artifact-final:laboratory:")
    assert result.passage_profile_ref
    assert result.query_profile_ref
    assert payload["scheduler_created"] is False
    assert payload["scheduler_run_owned"] is False
    assert payload["parallel_orchestrator_created"] is False
    assert payload["github_mutation_performed"] is False
    assert payload["publication_gate_required"] is True
    json.dumps(payload, sort_keys=True)


def test_smoke_publishes_r3_and_r4_facts_on_existing_eventbus() -> None:
    event_bus = EventBus()
    observer = event_bus.subscribe()
    result = asyncio.run(
        execute_smoke(
            command(observations=True),
            event_bus=event_bus,
        )
    )

    assert result.valid is True
    assert result.handoff["eventbus_publish_performed"] is True
    assert result.recall["eventbus_publish_performed"] is True
    assert observer.qsize() >= 7


def test_non_converged_deliberation_stops_before_durable_handoff() -> None:
    result = asyncio.run(
        execute_smoke(
            command(
                scenarios=(("specialist:technical", "needs_context"),)
            )
        )
    )

    assert result.valid is False
    assert "r2 deliberation is not locally publication-ready" in result.issues
    assert result.handoff == {}
    assert result.recall == {}
    assert result.closed_loop_complete is False


def test_wrong_recall_reference_breaks_semantic_closure() -> None:
    result = asyncio.run(
        execute_smoke(
            command(),
            recall_factory=lambda _sql_ref: DemoQdrantRecallExecutor(
                sql_refs=("sql:specialist_output:wrong-reference",)
            ),
        )
    )

    assert result.valid is False
    assert result.closed_loop_complete is False
    assert any(
        "exact r3 specialist_output" in issue
        or "r4 recall closure is invalid" in issue
        for issue in result.issues
    )


def test_smoke_can_skip_replay_verification_explicitly() -> None:
    result = asyncio.run(
        execute_smoke(command(verify_sql_replay=False))
    )

    assert result.valid is True
    assert result.sql_replay == {}
    assert result.sql_replay_verified is True


def test_command_requires_execute_projection_and_recall() -> None:
    base = command()

    with pytest.raises(
        FakeLaboratoryClosedLoopSmokeError,
        match="handoff execute mode",
    ):
        FakeLaboratoryClosedLoopSmokeCommand(
            deliberation=base.deliberation,
            handoff=FakeLaboratoryClosedHandoffCommand(),
            recall=base.recall,
        )

    with pytest.raises(
        FakeLaboratoryClosedLoopSmokeError,
        match="passage vector projection",
    ):
        FakeLaboratoryClosedLoopSmokeCommand(
            deliberation=base.deliberation,
            handoff=replace_handoff_without_vector(base),
            recall=base.recall,
        )

    with pytest.raises(
        FakeLaboratoryClosedLoopSmokeError,
        match="recall execute mode",
    ):
        FakeLaboratoryClosedLoopSmokeCommand(
            deliberation=base.deliberation,
            handoff=base.handoff,
            recall=LaboratoryRecallClosureCommand(),
        )


def replace_handoff_without_vector(
    base: FakeLaboratoryClosedLoopSmokeCommand,
) -> FakeLaboratoryClosedHandoffCommand:
    return FakeLaboratoryClosedHandoffCommand(
        execute=True,
        policy_decision_id=base.handoff.policy_decision_id,
        vector_execute=False,
    )
