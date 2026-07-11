import asyncio
import json

import pytest

from contracts.event import EventType

from context.fake_laboratory_closed_local_handoff_0274 import (
    FakeLaboratoryClosedHandoffCommand,
    run_fake_laboratory_closed_local_handoff,
)
from context.fake_laboratory_deliberation_composition_0274 import (
    FAKE_LABORATORY_DELIBERATION_COMMAND_SCHEMA,
    FakeLaboratoryDeliberationCommand,
    run_fake_laboratory_deliberation,
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
        orientation_ref="orientation:laboratory-r3",
        artifact_ref="artifact:github-request:r3",
        source_ref="artifact:source-candidate:r3",
        sql_context_ref="sql:github_artifact:r3-parent",
        title="Fermeture locale laboratoire",
        intent="Persister, projeter et observer le résultat local.",
        requested_specialist_refs=(
            "specialist:technical",
            "specialist:validator",
        ),
        requested_document_kinds=("analysis",),
        do_directives=("Conserver les preuves.",),
        avoid_directives=("Ne pas publier sans gate.",),
        context_refs=("ctx:project:r3",),
    )


def deliberation_command(
    *,
    scenarios: tuple[tuple[str, str], ...] = (),
) -> FakeLaboratoryDeliberationCommand:
    return FakeLaboratoryDeliberationCommand(
        schema=FAKE_LABORATORY_DELIBERATION_COMMAND_SCHEMA,
        orientation=orientation(),
        artifact_ref="artifact:github-request:r3",
        source_candidate_ref="source-candidate:projectv2:r3",
        target_ref="github:issue:newicody/ideas/43",
        context_generation=4,
        resource_budget=LaboratoryResourceBudget(
            max_duration_ms=2_000,
            max_context_refs=16,
            max_evidence_refs=16,
            max_followup_requests=8,
        ),
        scenario_by_specialist=scenarios,
    )


async def build_deliberation(
    *,
    scenarios: tuple[tuple[str, str], ...] = (),
):
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
        return await run_fake_laboratory_deliberation(
            scheduler,
            deliberation_command(scenarios=scenarios),
            timeout_per_visit=1.0,
        )
    finally:
        await scheduler.shutdown()
        await asyncio.wait_for(run_task, timeout=1.0)


def profile() -> EmbeddingSpaceProfile:
    return EmbeddingSpaceProfile(
        backend_ref="openvino:model:multilingual-e5-small",
        model_ref="openvino.embedding.e5-small",
        model_revision="local-test",
        tokenizer_ref="transformers.multilingual-e5-small",
        collection_name="laboratory_outputs_e5_384",
    )


def embedder(text, sql_ref, model_dir, device):
    vector = [0.0] * 384
    vector[0] = 1.0
    return build_embedding_mapping(
        sql_ref=sql_ref,
        role="passage",
        text=text,
        vector=vector,
        backend_ref="openvino:model:multilingual-e5-small",
        model="openvino.embedding.e5-small",
        tokenizer="transformers.multilingual-e5-small",
        model_path=model_dir or "",
        device=device,
    )


def test_dry_run_builds_local_preview_and_visual_models_without_effects() -> None:
    deliberation = asyncio.run(build_deliberation())
    result = asyncio.run(
        run_fake_laboratory_closed_local_handoff(
            deliberation,
            FakeLaboratoryClosedHandoffCommand(),
        )
    )

    assert result.valid is True
    assert result.sql_record["kind"] == "specialist_output"
    assert result.sql_write_performed is False
    assert result.qdrant_write_performed is False
    assert result.eventbus_publish_performed is False
    assert result.github_preview["publication_gate_required"] is True
    assert result.github_preview["remote_mutation_allowed"] is False
    assert result.passive_supervisor["valid"] is True
    assert result.visual_read_model["node_count"] >= 7
    assert result.visual_layout["node_count"] >= 7
    json.dumps(result.to_mapping(), sort_keys=True)


def test_execute_persists_projects_observes_and_keeps_github_closed() -> None:
    deliberation = asyncio.run(build_deliberation())
    store = SQLiteSqlContextStore()
    event_bus = EventBus()
    observed = event_bus.subscribe(EventType.LABORATORY_VISIT_RESULT)

    result = asyncio.run(
        run_fake_laboratory_closed_local_handoff(
            deliberation,
            FakeLaboratoryClosedHandoffCommand(
                execute=True,
                policy_decision_id="policy:0274:r3:test",
                vector_execute=True,
                publish_observations=True,
            ),
            store=store,
            profile=profile(),
            embedder=embedder,
            qdrant_executor=DemoQdrantProjectionExecutor(),
            event_bus=event_bus,
        )
    )

    assert result.valid is True
    assert result.sql_write_performed is True
    assert result.sql_readback_performed is True
    assert result.openvino_call_performed is True
    assert result.qdrant_write_performed is True
    assert result.eventbus_publish_performed is True
    assert len(result.published_event_ids) == 4
    assert observed.qsize() == 4
    assert result.github_mutation_performed is False
    assert result.github_preview["status"] == "pending"
    assert result.visual_read_model["authority_boundary"]["writes_sql"] is False
    assert result.visual_layout["authority_boundary"]["writes_qdrant"] is False
    assert any(
        node["zone"] == "laboratory"
        for node in result.visual_read_model["nodes"]
    )


def test_replay_is_idempotent_and_does_not_replace_record() -> None:
    deliberation = asyncio.run(build_deliberation())
    store = SQLiteSqlContextStore()
    command = FakeLaboratoryClosedHandoffCommand(
        execute=True,
        policy_decision_id="policy:0274:r3:replay",
    )

    first = asyncio.run(
        run_fake_laboratory_closed_local_handoff(
            deliberation,
            command,
            store=store,
        )
    )
    second = asyncio.run(
        run_fake_laboratory_closed_local_handoff(
            deliberation,
            command,
            store=store,
        )
    )

    assert first.valid is True
    assert first.sql_write["inserted"] is True
    assert second.valid is True
    assert second.sql_write["idempotent_replay"] is True
    assert second.sql_write["replaced"] is False
    assert first.sql_record == second.sql_record


def test_non_converged_deliberation_is_refused_before_sql() -> None:
    deliberation = asyncio.run(
        build_deliberation(
            scenarios=(("specialist:technical", "needs_context"),)
        )
    )
    result = asyncio.run(
        run_fake_laboratory_closed_local_handoff(
            deliberation,
            FakeLaboratoryClosedHandoffCommand(
                execute=True,
                policy_decision_id="policy:0274:r3:blocked",
            ),
            store=SQLiteSqlContextStore(),
        )
    )

    assert result.valid is False
    assert "deliberation must be locally publication-ready" in result.issues
    assert result.sql_write_performed is False
    assert result.qdrant_write_performed is False


def test_incompatible_embedding_blocks_qdrant_write() -> None:
    deliberation = asyncio.run(build_deliberation())

    def incompatible(text, sql_ref, model_dir, device):
        vector = [0.0] * 384
        vector[0] = 1.0
        return build_embedding_mapping(
            sql_ref=sql_ref,
            role="passage",
            text=text,
            vector=vector,
            model="other.embedding.model",
            tokenizer="other.tokenizer",
            device=device,
        )

    result = asyncio.run(
        run_fake_laboratory_closed_local_handoff(
            deliberation,
            FakeLaboratoryClosedHandoffCommand(
                execute=True,
                policy_decision_id="policy:0274:r3:incompatible",
                vector_execute=True,
            ),
            store=SQLiteSqlContextStore(),
            profile=profile(),
            embedder=incompatible,
            qdrant_executor=DemoQdrantProjectionExecutor(),
        )
    )

    assert result.valid is False
    assert result.openvino_call_performed is True
    assert result.qdrant_write_performed is False
    assert any("model" in issue for issue in result.issues)


def test_command_rejects_effects_without_execute() -> None:
    with pytest.raises(Exception, match="vector_execute requires execute"):
        FakeLaboratoryClosedHandoffCommand(vector_execute=True)
    with pytest.raises(Exception, match="publish_observations requires execute"):
        FakeLaboratoryClosedHandoffCommand(publish_observations=True)
