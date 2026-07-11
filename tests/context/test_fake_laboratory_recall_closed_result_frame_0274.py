import asyncio
import json

import pytest

from context.fake_laboratory_closed_local_handoff_0274 import (
    FakeLaboratoryClosedHandoffCommand,
    run_fake_laboratory_closed_local_handoff,
)
from context.fake_laboratory_deliberation_composition_0274 import (
    FAKE_LABORATORY_DELIBERATION_COMMAND_SCHEMA,
    FakeLaboratoryDeliberationCommand,
    run_fake_laboratory_deliberation,
)
from context.fake_laboratory_recall_closed_result_frame_0274 import (
    LaboratoryRecallClosureCommand,
    run_fake_laboratory_recall_closure,
)
from context.github_project_v2_source_candidate_vector_projection_0272 import (
    EmbeddingSpaceProfile,
)
from context.laboratory_framework_contract_0273 import LaboratoryResourceBudget
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
        orientation_ref='orientation:laboratory-r4',
        artifact_ref='artifact:github-request:r4',
        source_ref='artifact:source-candidate:r4',
        sql_context_ref='sql:github_artifact:r4-parent',
        title='Recall laboratoire fictif',
        intent='Vérifier le résultat spécialiste par recall et SQL.',
        requested_specialist_refs=(
            'specialist:technical',
            'specialist:validator',
        ),
        requested_document_kinds=('analysis',),
        do_directives=('Conserver les preuves.',),
        avoid_directives=('Ne pas publier sans gate.',),
        context_refs=('ctx:project:r4',),
    )


def deliberation_command() -> FakeLaboratoryDeliberationCommand:
    return FakeLaboratoryDeliberationCommand(
        schema=FAKE_LABORATORY_DELIBERATION_COMMAND_SCHEMA,
        orientation=orientation(),
        artifact_ref='artifact:github-request:r4',
        source_candidate_ref='source-candidate:projectv2:r4',
        target_ref='github:issue:newicody/ideas/44',
        context_generation=5,
        resource_budget=LaboratoryResourceBudget(
            max_duration_ms=2_000,
            max_context_refs=16,
            max_evidence_refs=16,
            max_followup_requests=8,
        ),
    )


def passage_profile() -> EmbeddingSpaceProfile:
    return EmbeddingSpaceProfile(
        backend_ref='openvino:model:multilingual-e5-small',
        model_ref='openvino.embedding.e5-small',
        model_revision='local-test',
        tokenizer_ref='transformers.multilingual-e5-small',
        role='passage',
        collection_name='laboratory_outputs_e5_384',
    )


def embedder(text, sql_ref, model_dir, device):
    vector = [0.0] * 384
    vector[0] = 1.0
    role = 'query' if text.startswith('query:') else 'passage'
    return build_embedding_mapping(
        sql_ref=sql_ref,
        role=role,
        text=text,
        vector=vector,
        backend_ref='openvino:model:multilingual-e5-small',
        model='openvino.embedding.e5-small',
        tokenizer='transformers.multilingual-e5-small',
        model_path=model_dir or '',
        device=device,
    )


async def build_r3_handoff():
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
    store = SQLiteSqlContextStore()
    try:
        deliberation = await run_fake_laboratory_deliberation(
            scheduler,
            deliberation_command(),
            timeout_per_visit=1.0,
        )
        handoff = await run_fake_laboratory_closed_local_handoff(
            deliberation,
            FakeLaboratoryClosedHandoffCommand(
                execute=True,
                policy_decision_id='policy:0274:r4:r3',
                vector_execute=True,
            ),
            store=store,
            profile=passage_profile(),
            embedder=embedder,
            qdrant_executor=DemoQdrantProjectionExecutor(),
        )
        return handoff, store
    finally:
        await scheduler.shutdown()
        await asyncio.wait_for(run_task, timeout=1.0)


def test_dry_run_validates_plan_without_recall_effects() -> None:
    handoff, store = asyncio.run(build_r3_handoff())
    result = asyncio.run(
        run_fake_laboratory_recall_closure(
            handoff,
            LaboratoryRecallClosureCommand(),
            store=store,
            passage_profile=passage_profile(),
        )
    )

    assert result.valid is True
    assert result.query_profile['role'] == 'query'
    assert result.query_openvino_call_performed is False
    assert result.qdrant_recall_performed is False
    assert result.sql_rehydrate_performed is False
    assert result.closed_result_frame_built is False


def test_execute_recalls_rehydrates_and_builds_closed_frame() -> None:
    handoff, store = asyncio.run(build_r3_handoff())
    sql_ref = handoff.sql_record['context_ref']
    result = asyncio.run(
        run_fake_laboratory_recall_closure(
            handoff,
            LaboratoryRecallClosureCommand(
                execute=True,
                policy_decision_id='policy:0274:r4:recall',
            ),
            store=store,
            passage_profile=passage_profile(),
            embedder=embedder,
            recall_executor=DemoQdrantRecallExecutor(sql_refs=(sql_ref,)),
        )
    )

    assert result.valid is True
    assert result.query_embedding['embedding']['role'] == 'query'
    assert result.query_compatibility['compatible'] is True
    assert result.recall_rehydrate['sql_refs'] == [sql_ref]
    assert result.recall_rehydrate['hydrated_count'] == 1
    assert result.recall_rehydrate['missing_count'] == 0
    assert result.closed_frame['valid'] is True
    assert result.closed_frame['laboratory_ref'] == 'laboratory:local-fake'
    assert result.closed_frame['specialist_output_verified'] is True
    assert result.closed_frame['passage_embedding_ref'].startswith(
        'embedding:passage:'
    )
    assert result.closed_frame['query_embedding_ref'].startswith(
        'embedding:query:'
    )
    assert result.passive_supervisor['valid'] is True
    assert result.visual_read_model['node_count'] == 5
    assert result.visual_layout['node_count'] == 5
    assert result.github_preview['publication_gate_required'] is True
    assert result.github_mutation_performed is False
    assert result.scheduler_created is False
    json.dumps(result.to_mapping(), sort_keys=True)


def test_observation_publication_uses_existing_eventbus() -> None:
    handoff, store = asyncio.run(build_r3_handoff())
    sql_ref = handoff.sql_record['context_ref']
    event_bus = EventBus()
    observer = event_bus.subscribe()
    result = asyncio.run(
        run_fake_laboratory_recall_closure(
            handoff,
            LaboratoryRecallClosureCommand(
                execute=True,
                policy_decision_id='policy:0274:r4:observe',
                publish_observations=True,
            ),
            store=store,
            passage_profile=passage_profile(),
            embedder=embedder,
            recall_executor=DemoQdrantRecallExecutor(sql_refs=(sql_ref,)),
            event_bus=event_bus,
        )
    )

    assert result.valid is True
    assert result.eventbus_publish_performed is True
    assert len(result.published_event_ids) == 3
    assert observer.qsize() == 3
    assert all(
        fact['observation_only'] is True
        and fact['command'] is False
        for fact in result.observation_report['facts']
    )


def test_missing_specialist_output_hit_blocks_frame() -> None:
    handoff, store = asyncio.run(build_r3_handoff())
    result = asyncio.run(
        run_fake_laboratory_recall_closure(
            handoff,
            LaboratoryRecallClosureCommand(
                execute=True,
                policy_decision_id='policy:0274:r4:missing',
            ),
            store=store,
            passage_profile=passage_profile(),
            embedder=embedder,
            recall_executor=DemoQdrantRecallExecutor(
                sql_refs=('sql:specialist_output:missing0000000000',)
            ),
        )
    )

    assert result.valid is False
    assert result.sql_rehydrate_performed is False
    assert result.closed_result_frame_built is False
    assert any('exact r3 specialist_output' in issue for issue in result.issues)


def test_query_profile_mismatch_blocks_before_recall() -> None:
    handoff, store = asyncio.run(build_r3_handoff())
    mismatched = EmbeddingSpaceProfile(
        backend_ref='openvino:model:multilingual-e5-small',
        model_ref='openvino.embedding.e5-small',
        model_revision='other-revision',
        tokenizer_ref='transformers.multilingual-e5-small',
        role='query',
        collection_name='laboratory_outputs_e5_384',
    )
    result = asyncio.run(
        run_fake_laboratory_recall_closure(
            handoff,
            LaboratoryRecallClosureCommand(
                execute=True,
                policy_decision_id='policy:0274:r4:mismatch',
            ),
            store=store,
            passage_profile=passage_profile(),
            query_profile=mismatched,
            embedder=embedder,
            recall_executor=DemoQdrantRecallExecutor(sql_refs=()),
        )
    )

    assert result.valid is False
    assert result.query_openvino_call_performed is False
    assert result.qdrant_recall_performed is False
    assert 'query and passage profiles must share one vector space' in result.issues


def test_command_rejects_uncontrolled_effects() -> None:
    with pytest.raises(Exception, match='execute requires policy_decision_id'):
        LaboratoryRecallClosureCommand(execute=True)
    with pytest.raises(Exception, match='publish_observations requires execute'):
        LaboratoryRecallClosureCommand(publish_observations=True)
