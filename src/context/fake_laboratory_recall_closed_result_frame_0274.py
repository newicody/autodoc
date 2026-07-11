"""Recall, SQL rehydration and closed ResultFrame for laboratory output.

0274-r4 reuses the existing 0261 query embedding, 0263 Qdrant recall/SQL
rehydration, 0264 closed ResultFrame, 0265 EventBus observation and 0266
PassiveSupervisor surfaces around the converged local handoff produced by
0274-r3.

The passage embedding projected by r3 and the query embedding used by r4 are
kept distinct while being required to share the same E5 vector space.  The
module creates no Scheduler, queue, EventBus, registry, SQL authority, Qdrant
authority, laboratory orchestrator, renderer or GitHub client.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
import hashlib
import json
from typing import Any, Callable, Protocol

from context.closed_result_frame_eventbus_observation_0265 import (
    build_closed_result_frame_eventbus_observation_report,
    publish_closed_result_frame_observation_facts,
)
from context.fake_laboratory_closed_local_handoff_0274 import (
    FakeLaboratoryClosedHandoffResult,
)
from context.github_project_v2_source_candidate_vector_projection_0272 import (
    EmbeddingSpaceProfile,
    attach_profile_to_embedding,
    validate_embedding_against_profile,
)
from context.passive_supervisor_closed_result_frame_observation_0266 import (
    build_passive_supervisor_closed_frame_observation_report,
)
from context.passive_supervisor_visual_layout_model import (
    build_passive_supervisor_visual_layout_model,
)
from context.passive_supervisor_visual_read_model import build_visual_read_model
from context.scheduler_managed_closed_result_frame_0264 import (
    ClosedResultFrameReportRefs,
    SchedulerManagedClosedResultFrame,
    compose_scheduler_managed_closed_result_frame,
)
from context.scheduler_managed_qdrant_recall_sql_rehydrate_usage_0263 import (
    SchedulerManagedQdrantRecallSqlRehydrateRequest,
    default_query_ref_from_embedding_report,
    run_scheduler_managed_qdrant_recall_sql_rehydrate_usage,
)
from context.scheduler_managed_sql_ref_openvino_embedding_usage_0261 import (
    SchedulerManagedSqlRefOpenVinoEmbeddingRequest,
    run_scheduler_managed_sql_ref_openvino_embedding_usage,
)

LABORATORY_RECALL_COMMAND_SCHEMA = (
    'missipy.laboratory.recall_closure_command.v1'
)
LABORATORY_CLOSED_RESULT_FRAME_SCHEMA = (
    'missipy.laboratory.closed_result_frame.v1'
)
LABORATORY_RECALL_CLOSURE_RESULT_SCHEMA = (
    'missipy.laboratory.recall_closure_result.v1'
)
LABORATORY_RECALL_CLOSURE_VERSION = '0274.r4'

EmbeddingCallable = Callable[[str, str, str | None, str], Mapping[str, Any]]


class ExistingObservationBus(Protocol):
    """Existing EventBus surface accepted by the 0265 publisher."""

    async def publish(self, event: object) -> None:
        """Publish one immutable fact event."""


class LaboratoryRecallClosureError(RuntimeError):
    """Raised when recall closure would violate an authority boundary."""


@dataclass(frozen=True, slots=True)
class LaboratoryRecallClosureCommand:
    """Explicit command for query embedding, recall and passive observation."""

    execute: bool = False
    policy_decision_id: str = ''
    publish_observations: bool = False
    model_dir: str | None = None
    device: str = 'CPU'
    recall_limit: int = 8
    frame_ref: str = 'laboratory-frame:0274-r4'
    schema: str = LABORATORY_RECALL_COMMAND_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != LABORATORY_RECALL_COMMAND_SCHEMA:
            raise LaboratoryRecallClosureError(
                'unsupported laboratory recall command schema'
            )
        if self.execute and not self.policy_decision_id.strip():
            raise LaboratoryRecallClosureError(
                'execute requires policy_decision_id'
            )
        if self.publish_observations and not self.execute:
            raise LaboratoryRecallClosureError(
                'publish_observations requires execute'
            )
        if isinstance(self.recall_limit, bool) or not isinstance(
            self.recall_limit, int
        ):
            raise LaboratoryRecallClosureError(
                'recall_limit must be an integer'
            )
        if not 1 <= self.recall_limit <= 128:
            raise LaboratoryRecallClosureError(
                'recall_limit must be between 1 and 128'
            )
        if not self.frame_ref.startswith('laboratory-frame:'):
            raise LaboratoryRecallClosureError(
                'frame_ref must start with laboratory-frame:'
            )

    def to_mapping(self) -> dict[str, object]:
        return {
            'schema': self.schema,
            'execute': self.execute,
            'policy_decision_id': self.policy_decision_id,
            'publish_observations': self.publish_observations,
            'model_dir': self.model_dir,
            'device': self.device,
            'recall_limit': self.recall_limit,
            'frame_ref': self.frame_ref,
        }


@dataclass(frozen=True, slots=True)
class LaboratoryClosedResultFrame:
    """Laboratory provenance around the reused 0264 closed frame."""

    base_frame: SchedulerManagedClosedResultFrame
    laboratory_ref: str
    final_ref: str
    synthesis_ref: str
    passage_profile_ref: str
    query_profile_ref: str
    passage_embedding_ref: str
    query_embedding_ref: str
    recall_query_ref: str
    specialist_output_verified: bool
    existing_scheduler_used_upstream: bool = True
    scheduler_created: bool = False
    scheduler_modified: bool = False
    github_mutation_performed: bool = False

    def __post_init__(self) -> None:
        if not self.base_frame.valid:
            raise LaboratoryRecallClosureError(
                'laboratory frame requires a valid 0264 base frame'
            )
        if self.laboratory_ref != 'laboratory:local-fake':
            raise LaboratoryRecallClosureError(
                'r4 supports only laboratory:local-fake'
            )
        for name in (
            'final_ref',
            'synthesis_ref',
            'passage_profile_ref',
            'query_profile_ref',
            'passage_embedding_ref',
            'query_embedding_ref',
            'recall_query_ref',
        ):
            if not str(getattr(self, name)).strip():
                raise LaboratoryRecallClosureError(
                    f'{name} must be non-empty'
                )
        if not self.specialist_output_verified:
            raise LaboratoryRecallClosureError(
                'closed frame requires verified specialist_output rehydration'
            )
        if (
            not self.existing_scheduler_used_upstream
            or self.scheduler_created
            or self.scheduler_modified
            or self.github_mutation_performed
        ):
            raise LaboratoryRecallClosureError(
                'laboratory frame must preserve authority boundaries'
            )

    def to_mapping(self) -> dict[str, object]:
        payload = self.base_frame.to_mapping()
        payload.update(
            {
                'schema': LABORATORY_CLOSED_RESULT_FRAME_SCHEMA,
                'laboratory_closed_result_frame': True,
                'base_frame_schema': (
                    'missipy.scheduler_managed_closed_result_frame.v1'
                ),
                'laboratory_ref': self.laboratory_ref,
                'final_ref': self.final_ref,
                'synthesis_ref': self.synthesis_ref,
                'passage_profile_ref': self.passage_profile_ref,
                'query_profile_ref': self.query_profile_ref,
                'passage_embedding_ref': self.passage_embedding_ref,
                'query_embedding_ref': self.query_embedding_ref,
                'recall_query_ref': self.recall_query_ref,
                'specialist_output_verified': self.specialist_output_verified,
                'existing_scheduler_used_upstream': (
                    self.existing_scheduler_used_upstream
                ),
                'scheduler_created': self.scheduler_created,
                'scheduler_modified': self.scheduler_modified,
                'github_mutation_performed': (
                    self.github_mutation_performed
                ),
                'publication_gate_required': True,
            }
        )
        trace = dict(payload.get('trace', {}))
        trace['0274-r4-query'] = {
            'kind': 'query_embedding_qdrant_recall',
            'sql_ref': self.base_frame.sql_ref,
            'query_embedding_ref': self.query_embedding_ref,
            'query_profile_ref': self.query_profile_ref,
            'recall_query_ref': self.recall_query_ref,
        }
        payload['trace'] = trace
        return payload


@dataclass(frozen=True, slots=True)
class LaboratoryRecallClosureResult:
    """Serializable result of the r4 recall and passive closure."""

    valid: bool
    issues: tuple[str, ...]
    command: LaboratoryRecallClosureCommand
    sql_ref: str
    passage_profile: Mapping[str, Any]
    query_profile: Mapping[str, Any]
    query_embedding: Mapping[str, Any] = field(default_factory=dict)
    query_compatibility: Mapping[str, Any] = field(default_factory=dict)
    recall_rehydrate: Mapping[str, Any] = field(default_factory=dict)
    closed_frame: Mapping[str, Any] = field(default_factory=dict)
    observation_report: Mapping[str, Any] = field(default_factory=dict)
    published_event_ids: tuple[str, ...] = ()
    passive_supervisor: Mapping[str, Any] = field(default_factory=dict)
    visual_read_model: Mapping[str, Any] = field(default_factory=dict)
    visual_layout: Mapping[str, Any] = field(default_factory=dict)
    github_preview: Mapping[str, Any] = field(default_factory=dict)
    query_openvino_call_performed: bool = False
    qdrant_recall_performed: bool = False
    sql_rehydrate_performed: bool = False
    closed_result_frame_built: bool = False
    eventbus_publish_performed: bool = False
    existing_scheduler_used_upstream: bool = True
    scheduler_created: bool = False
    scheduler_modified: bool = False
    parallel_orchestrator_created: bool = False
    parallel_eventbus_created: bool = False
    parallel_registry_created: bool = False
    sql_write_performed: bool = False
    qdrant_write_performed: bool = False
    github_mutation_performed: bool = False
    schema: str = LABORATORY_RECALL_CLOSURE_RESULT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != LABORATORY_RECALL_CLOSURE_RESULT_SCHEMA:
            raise LaboratoryRecallClosureError(
                'unsupported laboratory recall result schema'
            )
        forbidden = (
            not self.existing_scheduler_used_upstream,
            self.scheduler_created,
            self.scheduler_modified,
            self.parallel_orchestrator_created,
            self.parallel_eventbus_created,
            self.parallel_registry_created,
            self.sql_write_performed,
            self.qdrant_write_performed,
            self.github_mutation_performed,
        )
        if any(forbidden):
            raise LaboratoryRecallClosureError(
                'r4 must remain read/recall/observation only'
            )
        if self.command.execute and self.valid:
            required = (
                self.query_openvino_call_performed,
                self.qdrant_recall_performed,
                self.sql_rehydrate_performed,
                self.closed_result_frame_built,
            )
            if not all(required):
                raise LaboratoryRecallClosureError(
                    'successful execute mode requires complete recall closure'
                )
        if self.command.publish_observations and self.valid:
            if not self.eventbus_publish_performed:
                raise LaboratoryRecallClosureError(
                    'observation mode requires existing EventBus publication'
                )

    def to_mapping(self) -> dict[str, object]:
        return {
            'schema': self.schema,
            'valid': self.valid,
            'issues': list(self.issues),
            'command': self.command.to_mapping(),
            'sql_ref': self.sql_ref,
            'passage_profile': dict(self.passage_profile),
            'query_profile': dict(self.query_profile),
            'query_embedding': dict(self.query_embedding),
            'query_compatibility': dict(self.query_compatibility),
            'recall_rehydrate': dict(self.recall_rehydrate),
            'closed_frame': dict(self.closed_frame),
            'observation_report': dict(self.observation_report),
            'published_event_ids': list(self.published_event_ids),
            'passive_supervisor': dict(self.passive_supervisor),
            'visual_read_model': dict(self.visual_read_model),
            'visual_layout': dict(self.visual_layout),
            'github_preview': dict(self.github_preview),
            'query_openvino_call_performed': (
                self.query_openvino_call_performed
            ),
            'qdrant_recall_performed': self.qdrant_recall_performed,
            'sql_rehydrate_performed': self.sql_rehydrate_performed,
            'closed_result_frame_built': self.closed_result_frame_built,
            'eventbus_publish_performed': self.eventbus_publish_performed,
            'existing_scheduler_used_upstream': (
                self.existing_scheduler_used_upstream
            ),
            'scheduler_created': self.scheduler_created,
            'scheduler_modified': self.scheduler_modified,
            'parallel_orchestrator_created': (
                self.parallel_orchestrator_created
            ),
            'parallel_eventbus_created': self.parallel_eventbus_created,
            'parallel_registry_created': self.parallel_registry_created,
            'sql_write_performed': self.sql_write_performed,
            'qdrant_write_performed': self.qdrant_write_performed,
            'github_mutation_performed': self.github_mutation_performed,
            'sql_remains_authority': True,
            'qdrant_recall_refs_only': True,
            'eventbus_observation_only': True,
            'passive_supervisor_observation_only': True,
            'vispy_passive': True,
            'publication_gate_required': True,
        }


async def run_fake_laboratory_recall_closure(
    handoff: FakeLaboratoryClosedHandoffResult,
    command: LaboratoryRecallClosureCommand,
    *,
    store: Any | None = None,
    passage_profile: EmbeddingSpaceProfile | None = None,
    query_profile: EmbeddingSpaceProfile | None = None,
    embedder: EmbeddingCallable | None = None,
    recall_executor: Any | None = None,
    event_bus: ExistingObservationBus | None = None,
) -> LaboratoryRecallClosureResult:
    """Recall the r3 specialist output and build the closed passive frame."""

    effective_passage = passage_profile or EmbeddingSpaceProfile()
    effective_query = query_profile or replace(
        effective_passage,
        role='query',
    )
    issues = list(
        _validate_inputs(
            handoff,
            command,
            passage_profile=effective_passage,
            query_profile=effective_query,
            store=store,
            recall_executor=recall_executor,
            event_bus=event_bus,
        )
    )
    sql_ref = str(handoff.sql_record.get('context_ref', ''))

    if issues or not command.execute:
        return _result(
            issues=issues,
            command=command,
            sql_ref=sql_ref,
            passage_profile=effective_passage,
            query_profile=effective_query,
            github_preview=handoff.github_preview,
        )

    query_request = SchedulerManagedSqlRefOpenVinoEmbeddingRequest(
        sql_ref=sql_ref,
        role='query',
        policy_decision_id=command.policy_decision_id,
        model_dir=command.model_dir,
        device=command.device,
    )
    query_result = run_scheduler_managed_sql_ref_openvino_embedding_usage(
        store,
        query_request,
        execute=True,
        embedder=embedder,
    )
    query_report = query_result.to_mapping()
    if not query_result.valid:
        issues.extend(query_result.issues)
        return _result(
            issues=issues,
            command=command,
            sql_ref=sql_ref,
            passage_profile=effective_passage,
            query_profile=effective_query,
            query_embedding=query_report,
            github_preview=handoff.github_preview,
            query_openvino_call_performed=True,
        )

    query_embedding = _mapping(query_report.get('embedding'))
    compatibility = validate_embedding_against_profile(
        query_embedding,
        effective_query,
        expected_sql_ref=sql_ref,
    )
    if not compatibility.compatible:
        issues.extend(compatibility.issues)
        return _result(
            issues=issues,
            command=command,
            sql_ref=sql_ref,
            passage_profile=effective_passage,
            query_profile=effective_query,
            query_embedding=query_report,
            query_compatibility=compatibility.to_mapping(),
            github_preview=handoff.github_preview,
            query_openvino_call_performed=True,
        )

    profiled_query_report = dict(query_report)
    profiled_query_report['embedding'] = attach_profile_to_embedding(
        query_embedding,
        effective_query,
    )
    recall_request = SchedulerManagedQdrantRecallSqlRehydrateRequest(
        query_ref=default_query_ref_from_embedding_report(
            profiled_query_report
        ),
        policy_decision_id=command.policy_decision_id,
        collection_name=effective_passage.collection_name,
        vector_dimension=effective_passage.dimension,
        limit=command.recall_limit,
    )
    recall_result = run_scheduler_managed_qdrant_recall_sql_rehydrate_usage(
        profiled_query_report,
        store,
        recall_request,
        execute=True,
        executor=recall_executor,
    )
    recall_mapping = recall_result.to_mapping()
    if not recall_result.valid:
        issues.extend(recall_result.issues)
    verified_record = _verify_rehydrated_specialist_output(
        handoff,
        recall_mapping,
    )
    if not verified_record:
        issues.append(
            'recall must rehydrate the exact r3 specialist_output record'
        )

    base_frame: SchedulerManagedClosedResultFrame | None = None
    laboratory_frame: LaboratoryClosedResultFrame | None = None
    if not issues:
        base_frame = compose_scheduler_managed_closed_result_frame(
            sql_write_report={
                'sql_ref': sql_ref,
                'result': dict(handoff.sql_write),
            },
            embedding_report=handoff.embedding,
            projection_report=handoff.projection,
            recall_rehydrate_report=recall_mapping,
            report_refs=ClosedResultFrameReportRefs(
                sql_write_report='memory:0274-r3:sql-write',
                embedding_report='memory:0274-r3:passage-embedding',
                projection_report='memory:0274-r3:qdrant-projection',
                recall_rehydrate_report='memory:0274-r4:recall-rehydrate',
            ),
        )
        if not base_frame.valid:
            issues.extend(base_frame.issues)
        else:
            final_ref = str(
                handoff.github_preview.get('final_ref', '')
            )
            synthesis_ref = str(
                handoff.github_preview.get('synthesis_ref', '')
            )
            passage_embedding = _mapping(
                handoff.embedding.get('embedding')
            )
            laboratory_frame = LaboratoryClosedResultFrame(
                base_frame=base_frame,
                laboratory_ref='laboratory:local-fake',
                final_ref=final_ref,
                synthesis_ref=synthesis_ref,
                passage_profile_ref=effective_passage.profile_ref,
                query_profile_ref=effective_query.profile_ref,
                passage_embedding_ref=str(
                    passage_embedding.get('embedding_ref', '')
                ),
                query_embedding_ref=str(
                    query_embedding.get('embedding_ref', '')
                ),
                recall_query_ref=recall_request.query_ref,
                specialist_output_verified=True,
            )

    observation_mapping: dict[str, Any] = {}
    passive_mapping: dict[str, Any] = {}
    visual_mapping: dict[str, Any] = {}
    layout_mapping: dict[str, Any] = {}
    published_ids: tuple[str, ...] = ()

    if not issues and laboratory_frame is not None:
        frame_mapping = laboratory_frame.to_mapping()
        observation = build_closed_result_frame_eventbus_observation_report(
            frame_mapping,
            frame_ref=command.frame_ref,
        )
        observation_mapping = observation.to_mapping()
        if not observation.valid:
            issues.extend(observation.issues)
        else:
            passive = build_passive_supervisor_closed_frame_observation_report(
                observation_mapping,
                source_observation_ref=(
                    'laboratory-recall-observation:' + _digest(sql_ref)
                ),
            )
            passive_mapping = passive.to_mapping()
            if not passive.valid:
                issues.extend(passive.issues)
            snapshot = _build_visual_snapshot(
                handoff,
                laboratory_frame,
                recall_mapping,
            )
            visual_mapping = build_visual_read_model(
                snapshot,
                layout_kind='laboratory-recall-cellular',
            ).to_dict()
            layout_mapping = build_passive_supervisor_visual_layout_model(
                visual_mapping
            )
            if command.publish_observations and not issues:
                published = await publish_closed_result_frame_observation_facts(
                    event_bus,
                    observation.facts,
                )
                published_ids = tuple(event.id for event in published)

    return _result(
        issues=issues,
        command=command,
        sql_ref=sql_ref,
        passage_profile=effective_passage,
        query_profile=effective_query,
        query_embedding=profiled_query_report,
        query_compatibility=compatibility.to_mapping(),
        recall_rehydrate=recall_mapping,
        closed_frame=(
            {} if laboratory_frame is None else laboratory_frame.to_mapping()
        ),
        observation_report=observation_mapping,
        published_event_ids=published_ids,
        passive_supervisor=passive_mapping,
        visual_read_model=visual_mapping,
        visual_layout=layout_mapping,
        github_preview=handoff.github_preview,
        query_openvino_call_performed=True,
        qdrant_recall_performed=bool(recall_mapping),
        sql_rehydrate_performed=verified_record,
        closed_result_frame_built=laboratory_frame is not None,
        eventbus_publish_performed=bool(published_ids),
    )


def _validate_inputs(
    handoff: FakeLaboratoryClosedHandoffResult,
    command: LaboratoryRecallClosureCommand,
    *,
    passage_profile: EmbeddingSpaceProfile,
    query_profile: EmbeddingSpaceProfile,
    store: Any | None,
    recall_executor: Any | None,
    event_bus: ExistingObservationBus | None,
) -> tuple[str, ...]:
    issues: list[str] = []
    if not isinstance(handoff, FakeLaboratoryClosedHandoffResult):
        return ('handoff must be FakeLaboratoryClosedHandoffResult',)
    if not handoff.valid:
        issues.append('r3 handoff must be valid')
    if not handoff.command.execute:
        issues.append('r3 handoff must come from execute mode')
    if not handoff.sql_write_performed or not handoff.sql_readback_performed:
        issues.append('r3 handoff must have durable SQL write/readback')
    if not handoff.qdrant_write_performed:
        issues.append('r3 handoff must have an acknowledged passage projection')
    sql_ref = str(handoff.sql_record.get('context_ref', ''))
    if not sql_ref.startswith('sql:'):
        issues.append('r3 handoff must expose a typed sql_ref')
    if handoff.sql_record.get('kind') != 'specialist_output':
        issues.append('r3 SQL record must be specialist_output')
    if passage_profile.role != 'passage':
        issues.append('passage_profile.role must be passage')
    if query_profile.role != 'query':
        issues.append('query_profile.role must be query')
    if not _profiles_share_vector_space(passage_profile, query_profile):
        issues.append('query and passage profiles must share one vector space')
    if str(handoff.compatibility.get('profile_ref', '')) != (
        passage_profile.profile_ref
    ):
        issues.append('r3 compatibility profile must match passage profile')
    projection_request = _mapping(handoff.projection.get('request'))
    if projection_request.get('collection_name') != (
        passage_profile.collection_name
    ):
        issues.append('r3 projection collection must match passage profile')
    if projection_request.get('vector_dimension') != passage_profile.dimension:
        issues.append('r3 projection dimension must match passage profile')
    if handoff.github_preview.get('publication_gate_required') is not True:
        issues.append('r3 GitHub preview must require publication gate')
    if handoff.github_preview.get('github_mutation_performed') is not False:
        issues.append('r3 handoff must not have mutated GitHub')
    if command.execute and store is None:
        issues.append('execute requires existing SQLContextStore')
    if command.execute and recall_executor is None:
        issues.append('execute requires injected Qdrant recall executor')
    if command.publish_observations and event_bus is None:
        issues.append('publish_observations requires existing EventBus')
    return tuple(dict.fromkeys(issues))


def _profiles_share_vector_space(
    passage: EmbeddingSpaceProfile,
    query: EmbeddingSpaceProfile,
) -> bool:
    passage_mapping = passage.to_mapping()
    query_mapping = query.to_mapping()
    ignored = {'schema', 'profile_ref', 'role'}
    return {
        key: value
        for key, value in passage_mapping.items()
        if key not in ignored
    } == {
        key: value
        for key, value in query_mapping.items()
        if key not in ignored
    }


def _verify_rehydrated_specialist_output(
    handoff: FakeLaboratoryClosedHandoffResult,
    recall: Mapping[str, Any],
) -> bool:
    sql_ref = str(handoff.sql_record.get('context_ref', ''))
    sql_refs = recall.get('sql_refs', [])
    if not isinstance(sql_refs, list) or sql_ref not in sql_refs:
        return False
    if recall.get('missing_count') != 0:
        return False
    records = recall.get('hydrated_records', [])
    if not isinstance(records, list):
        return False
    expected = _canonical_mapping(handoff.sql_record)
    for record in records:
        if not isinstance(record, Mapping):
            continue
        if record.get('context_ref') != sql_ref:
            continue
        return (
            record.get('kind') == 'specialist_output'
            and _canonical_mapping(record) == expected
        )
    return False


def _build_visual_snapshot(
    handoff: FakeLaboratoryClosedHandoffResult,
    frame: LaboratoryClosedResultFrame,
    recall: Mapping[str, Any],
) -> dict[str, Any]:
    sql_ref = frame.base_frame.sql_ref
    collection = str(
        _mapping(recall.get('request')).get('collection_name', '')
    )
    qdrant_ref = (
        f'qdrant:{collection}:recall:{_digest(frame.recall_query_ref)}'
    )
    rehydrate_ref = f'ctx-result:laboratory-rehydrate:{_digest(sql_ref)}'
    cells = [
        {
            'cell_id': frame.laboratory_ref,
            'cell_kind': 'LABORATORY',
            'state': 'closed',
            'health': 'healthy',
            'last_event': 'laboratory.closed_result_frame.validated',
            'payload': {
                'laboratory_ref': frame.laboratory_ref,
                'sql_ref': sql_ref,
                'final_ref': frame.final_ref,
                'synthesis_ref': frame.synthesis_ref,
            },
        },
        {
            'cell_id': sql_ref,
            'cell_kind': 'SQL_STORE',
            'state': 'authoritative',
            'health': 'healthy',
            'last_event': 'laboratory.recall.sql_rehydrated',
            'payload': {'sql_ref': sql_ref},
        },
        {
            'cell_id': qdrant_ref,
            'cell_kind': 'QDRANT_PROJECTION',
            'state': 'recall_confirmed',
            'health': 'healthy',
            'last_event': 'laboratory.qdrant.recall.completed',
            'payload': {
                'qdrant_ref': qdrant_ref,
                'sql_ref': sql_ref,
            },
        },
        {
            'cell_id': rehydrate_ref,
            'cell_kind': 'REHYDRATION',
            'state': 'verified',
            'health': 'healthy',
            'last_event': 'laboratory.specialist_output.verified',
            'payload': {
                'sql_ref': sql_ref,
                'qdrant_ref': qdrant_ref,
            },
        },
        {
            'cell_id': frame.final_ref,
            'cell_kind': 'FINAL_ARTIFACT',
            'state': 'pending_review',
            'health': 'healthy',
            'last_event': 'laboratory.github_preview.pending',
            'payload': {
                'final_ref': frame.final_ref,
                'synthesis_ref': frame.synthesis_ref,
                'sql_ref': sql_ref,
                'artifact_ref': handoff.github_preview.get('final_ref', ''),
            },
        },
    ]
    return {
        'generated_at': '',
        'event_count': 3,
        'cell_count': len(cells),
        'blocked_count': 0,
        'failed_count': 0,
        'stale_count': 0,
        'cells': cells,
    }


def _result(
    *,
    issues: Sequence[str],
    command: LaboratoryRecallClosureCommand,
    sql_ref: str,
    passage_profile: EmbeddingSpaceProfile,
    query_profile: EmbeddingSpaceProfile,
    query_embedding: Mapping[str, Any] | None = None,
    query_compatibility: Mapping[str, Any] | None = None,
    recall_rehydrate: Mapping[str, Any] | None = None,
    closed_frame: Mapping[str, Any] | None = None,
    observation_report: Mapping[str, Any] | None = None,
    published_event_ids: tuple[str, ...] = (),
    passive_supervisor: Mapping[str, Any] | None = None,
    visual_read_model: Mapping[str, Any] | None = None,
    visual_layout: Mapping[str, Any] | None = None,
    github_preview: Mapping[str, Any] | None = None,
    query_openvino_call_performed: bool = False,
    qdrant_recall_performed: bool = False,
    sql_rehydrate_performed: bool = False,
    closed_result_frame_built: bool = False,
    eventbus_publish_performed: bool = False,
) -> LaboratoryRecallClosureResult:
    normalized = tuple(dict.fromkeys(str(item) for item in issues if str(item)))
    return LaboratoryRecallClosureResult(
        valid=not normalized,
        issues=normalized,
        command=command,
        sql_ref=sql_ref,
        passage_profile=passage_profile.to_mapping(),
        query_profile=query_profile.to_mapping(),
        query_embedding=dict(query_embedding or {}),
        query_compatibility=dict(query_compatibility or {}),
        recall_rehydrate=dict(recall_rehydrate or {}),
        closed_frame=dict(closed_frame or {}),
        observation_report=dict(observation_report or {}),
        published_event_ids=published_event_ids,
        passive_supervisor=dict(passive_supervisor or {}),
        visual_read_model=dict(visual_read_model or {}),
        visual_layout=dict(visual_layout or {}),
        github_preview=dict(github_preview or {}),
        query_openvino_call_performed=query_openvino_call_performed,
        qdrant_recall_performed=qdrant_recall_performed,
        sql_rehydrate_performed=sql_rehydrate_performed,
        closed_result_frame_built=closed_result_frame_built,
        eventbus_publish_performed=eventbus_publish_performed,
    )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _canonical_mapping(value: Mapping[str, Any]) -> str:
    return json.dumps(
        dict(value),
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=False,
    )


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()[:16]


__all__ = (
    'LABORATORY_CLOSED_RESULT_FRAME_SCHEMA',
    'LABORATORY_RECALL_CLOSURE_RESULT_SCHEMA',
    'LABORATORY_RECALL_CLOSURE_VERSION',
    'LABORATORY_RECALL_COMMAND_SCHEMA',
    'LaboratoryClosedResultFrame',
    'LaboratoryRecallClosureCommand',
    'LaboratoryRecallClosureError',
    'LaboratoryRecallClosureResult',
    'run_fake_laboratory_recall_closure',
)
