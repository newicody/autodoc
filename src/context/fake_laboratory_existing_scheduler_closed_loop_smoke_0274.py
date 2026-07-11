"""Existing-Scheduler fake laboratory closed-loop smoke for 0274-r5.

This module composes the already-existing phase surfaces:

    0274-r2 laboratory deliberation
    -> 0274-r3 SQL / passage projection / passive preview
    -> 0274-r4 query recall / SQL rehydration / closed ResultFrame

It is a smoke composition function, not a new orchestration authority.  The
caller injects the one already-running platform Scheduler, existing SQL store,
existing EventBus and controlled Qdrant executors.

The module does not instantiate or start a Scheduler, queue, EventBus,
registry, laboratory manager, laboratory orchestrator, SQL authority, Qdrant
authority, renderer or GitHub client.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import Any, Callable

from contracts.scheduler import SchedulerContract
from context.fake_laboratory_closed_local_handoff_0274 import (
    ExistingObservationBus,
    ExistingSqlContextStore,
    FakeLaboratoryClosedHandoffCommand,
    FakeLaboratoryClosedHandoffResult,
    run_fake_laboratory_closed_local_handoff,
)
from context.fake_laboratory_deliberation_composition_0274 import (
    FakeLaboratoryDeliberationCommand,
    FakeLaboratoryDeliberationResult,
    run_fake_laboratory_deliberation,
)
from context.fake_laboratory_recall_closed_result_frame_0274 import (
    LaboratoryRecallClosureCommand,
    LaboratoryRecallClosureResult,
    run_fake_laboratory_recall_closure,
)
from context.github_project_v2_source_candidate_vector_projection_0272 import (
    EmbeddingSpaceProfile,
)

FAKE_LABORATORY_CLOSED_LOOP_SMOKE_COMMAND_SCHEMA = (
    "missipy.laboratory.closed_loop_smoke_command.v1"
)
FAKE_LABORATORY_CLOSED_LOOP_SMOKE_RESULT_SCHEMA = (
    "missipy.laboratory.closed_loop_smoke_result.v1"
)
FAKE_LABORATORY_CLOSED_LOOP_SMOKE_VERSION = "0274.r5"

EmbeddingCallable = Callable[[str, str, str | None, str], Mapping[str, Any]]
RecallExecutorFactory = Callable[[str], Any]


class FakeLaboratoryClosedLoopSmokeError(RuntimeError):
    """Raised when the r5 smoke would violate the existing architecture."""


@dataclass(frozen=True, slots=True)
class FakeLaboratoryClosedLoopSmokeCommand:
    """One explicit command spanning r2, r3 and r4."""

    deliberation: FakeLaboratoryDeliberationCommand
    handoff: FakeLaboratoryClosedHandoffCommand
    recall: LaboratoryRecallClosureCommand
    verify_sql_replay: bool = True
    timeout_per_visit: float | None = None
    schema: str = FAKE_LABORATORY_CLOSED_LOOP_SMOKE_COMMAND_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != FAKE_LABORATORY_CLOSED_LOOP_SMOKE_COMMAND_SCHEMA:
            raise FakeLaboratoryClosedLoopSmokeError(
                "unsupported fake laboratory closed-loop smoke command schema"
            )
        if not isinstance(
            self.deliberation,
            FakeLaboratoryDeliberationCommand,
        ):
            raise FakeLaboratoryClosedLoopSmokeError(
                "deliberation must be FakeLaboratoryDeliberationCommand"
            )
        if not isinstance(self.handoff, FakeLaboratoryClosedHandoffCommand):
            raise FakeLaboratoryClosedLoopSmokeError(
                "handoff must be FakeLaboratoryClosedHandoffCommand"
            )
        if not isinstance(self.recall, LaboratoryRecallClosureCommand):
            raise FakeLaboratoryClosedLoopSmokeError(
                "recall must be LaboratoryRecallClosureCommand"
            )
        if not self.handoff.execute:
            raise FakeLaboratoryClosedLoopSmokeError(
                "r5 smoke requires handoff execute mode"
            )
        if not self.handoff.vector_execute:
            raise FakeLaboratoryClosedLoopSmokeError(
                "r5 smoke requires passage vector projection"
            )
        if not self.recall.execute:
            raise FakeLaboratoryClosedLoopSmokeError(
                "r5 smoke requires recall execute mode"
            )
        if self.timeout_per_visit is not None:
            if self.timeout_per_visit <= 0:
                raise FakeLaboratoryClosedLoopSmokeError(
                    "timeout_per_visit must be > 0"
                )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "deliberation": self.deliberation.to_mapping(),
            "handoff": self.handoff.to_mapping(),
            "recall": self.recall.to_mapping(),
            "verify_sql_replay": self.verify_sql_replay,
            "timeout_per_visit": self.timeout_per_visit,
            "scheduler_supplied_by_caller": True,
            "scheduler_created": False,
            "scheduler_run_owned": False,
            "parallel_orchestrator_created": False,
        }


@dataclass(frozen=True, slots=True)
class FakeLaboratoryClosedLoopSmokeResult:
    """Serializable semantic proof for the complete local fake laboratory loop."""

    valid: bool
    issues: tuple[str, ...]
    command: FakeLaboratoryClosedLoopSmokeCommand
    deliberation: Mapping[str, Any] = field(default_factory=dict)
    handoff: Mapping[str, Any] = field(default_factory=dict)
    recall: Mapping[str, Any] = field(default_factory=dict)
    sql_replay: Mapping[str, Any] = field(default_factory=dict)
    phase_trace: tuple[str, ...] = (
        "0274-r2-deliberation",
        "0274-r3-durable-passage-projection",
        "0274-r4-query-recall-result-frame",
    )
    sql_ref: str = ""
    final_ref: str = ""
    synthesis_ref: str = ""
    passage_profile_ref: str = ""
    query_profile_ref: str = ""
    closed_loop_complete: bool = False
    sql_replay_verified: bool = False
    specialist_output_verified: bool = False
    visual_path_complete: bool = False
    publication_preview_ready: bool = False
    existing_scheduler_used: bool = True
    scheduler_created: bool = False
    scheduler_modified: bool = False
    scheduler_run_owned: bool = False
    parallel_orchestrator_created: bool = False
    parallel_queue_created: bool = False
    parallel_eventbus_created: bool = False
    parallel_registry_created: bool = False
    github_mutation_performed: bool = False
    schema: str = FAKE_LABORATORY_CLOSED_LOOP_SMOKE_RESULT_SCHEMA

    def __post_init__(self) -> None:
        if self.schema != FAKE_LABORATORY_CLOSED_LOOP_SMOKE_RESULT_SCHEMA:
            raise FakeLaboratoryClosedLoopSmokeError(
                "unsupported fake laboratory closed-loop smoke result schema"
            )
        forbidden = (
            not self.existing_scheduler_used,
            self.scheduler_created,
            self.scheduler_modified,
            self.scheduler_run_owned,
            self.parallel_orchestrator_created,
            self.parallel_queue_created,
            self.parallel_eventbus_created,
            self.parallel_registry_created,
            self.github_mutation_performed,
        )
        if any(forbidden):
            raise FakeLaboratoryClosedLoopSmokeError(
                "r5 smoke must preserve the single-Scheduler architecture"
            )
        if self.valid:
            required = (
                self.closed_loop_complete,
                self.specialist_output_verified,
                self.visual_path_complete,
                self.publication_preview_ready,
            )
            if not all(required):
                raise FakeLaboratoryClosedLoopSmokeError(
                    "valid r5 smoke requires complete local closure"
                )
            if self.command.verify_sql_replay and not self.sql_replay_verified:
                raise FakeLaboratoryClosedLoopSmokeError(
                    "valid r5 smoke requires verified SQL replay"
                )

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "valid": self.valid,
            "issues": list(self.issues),
            "command": self.command.to_mapping(),
            "deliberation": dict(self.deliberation),
            "handoff": dict(self.handoff),
            "recall": dict(self.recall),
            "sql_replay": dict(self.sql_replay),
            "phase_trace": list(self.phase_trace),
            "sql_ref": self.sql_ref,
            "final_ref": self.final_ref,
            "synthesis_ref": self.synthesis_ref,
            "passage_profile_ref": self.passage_profile_ref,
            "query_profile_ref": self.query_profile_ref,
            "closed_loop_complete": self.closed_loop_complete,
            "sql_replay_verified": self.sql_replay_verified,
            "specialist_output_verified": self.specialist_output_verified,
            "visual_path_complete": self.visual_path_complete,
            "publication_preview_ready": self.publication_preview_ready,
            "existing_scheduler_used": self.existing_scheduler_used,
            "scheduler_created": self.scheduler_created,
            "scheduler_modified": self.scheduler_modified,
            "scheduler_run_owned": self.scheduler_run_owned,
            "parallel_orchestrator_created": (
                self.parallel_orchestrator_created
            ),
            "parallel_queue_created": self.parallel_queue_created,
            "parallel_eventbus_created": self.parallel_eventbus_created,
            "parallel_registry_created": self.parallel_registry_created,
            "github_mutation_performed": self.github_mutation_performed,
            "sql_remains_authority": True,
            "qdrant_projection_and_recall_only": True,
            "eventbus_observation_only": True,
            "passive_supervisor_observation_only": True,
            "vispy_passive": True,
            "publication_gate_required": True,
            "live_backend_claimed": False,
        }


async def run_fake_laboratory_existing_scheduler_closed_loop_smoke(
    scheduler: SchedulerContract,
    command: FakeLaboratoryClosedLoopSmokeCommand,
    *,
    store: ExistingSqlContextStore,
    passage_profile: EmbeddingSpaceProfile,
    embedder: EmbeddingCallable,
    projection_executor: Any,
    recall_executor_factory: RecallExecutorFactory,
    event_bus: ExistingObservationBus | None = None,
) -> FakeLaboratoryClosedLoopSmokeResult:
    """Run r2 -> r3 -> r4 using only injected existing runtime surfaces."""

    if not isinstance(scheduler, SchedulerContract):
        raise TypeError("scheduler must implement SchedulerContract")
    if not isinstance(command, FakeLaboratoryClosedLoopSmokeCommand):
        raise TypeError(
            "command must be FakeLaboratoryClosedLoopSmokeCommand"
        )
    if not isinstance(passage_profile, EmbeddingSpaceProfile):
        raise TypeError("passage_profile must be EmbeddingSpaceProfile")
    if not callable(recall_executor_factory):
        raise TypeError("recall_executor_factory must be callable")
    if (
        command.handoff.publish_observations
        or command.recall.publish_observations
    ) and event_bus is None:
        raise FakeLaboratoryClosedLoopSmokeError(
            "observation publication requires an existing EventBus"
        )

    issues: list[str] = []
    deliberation = await run_fake_laboratory_deliberation(
        scheduler,
        command.deliberation,
        timeout_per_visit=command.timeout_per_visit,
    )
    deliberation_mapping = deliberation.to_mapping()
    issues.extend(_deliberation_issues(deliberation))
    if issues:
        return _result(
            command=command,
            issues=issues,
            deliberation=deliberation_mapping,
        )

    handoff = await run_fake_laboratory_closed_local_handoff(
        deliberation,
        command.handoff,
        store=store,
        profile=passage_profile,
        embedder=embedder,
        qdrant_executor=projection_executor,
        event_bus=event_bus,
    )
    handoff_mapping = handoff.to_mapping()
    issues.extend(_handoff_issues(handoff))
    if issues:
        return _result(
            command=command,
            issues=issues,
            deliberation=deliberation_mapping,
            handoff=handoff_mapping,
        )

    sql_ref = str(handoff.sql_record.get("context_ref", ""))
    recall_executor = recall_executor_factory(sql_ref)
    recall = await run_fake_laboratory_recall_closure(
        handoff,
        command.recall,
        store=store,
        passage_profile=passage_profile,
        embedder=embedder,
        recall_executor=recall_executor,
        event_bus=event_bus,
    )
    recall_mapping = recall.to_mapping()
    issues.extend(_recall_issues(handoff, recall))

    replay_mapping: dict[str, Any] = {}
    replay_verified = not command.verify_sql_replay
    if not issues and command.verify_sql_replay:
        replay_command = replace(
            command.handoff,
            vector_execute=False,
            publish_observations=False,
        )
        replay = await run_fake_laboratory_closed_local_handoff(
            deliberation,
            replay_command,
            store=store,
        )
        replay_mapping = replay.to_mapping()
        replay_verified = _verify_sql_replay(
            expected_sql_ref=sql_ref,
            replay=replay,
        )
        if not replay_verified:
            issues.append(
                "r3 replay did not prove immutable idempotent SQL reuse"
            )

    final_ref = str(recall.closed_frame.get("final_ref", ""))
    synthesis_ref = str(recall.closed_frame.get("synthesis_ref", ""))
    specialist_output_verified = (
        recall.closed_frame.get("specialist_output_verified") is True
    )
    visual_path_complete = (
        bool(recall.passive_supervisor)
        and bool(recall.visual_read_model)
        and bool(recall.visual_layout)
        and recall.passive_supervisor.get("valid") is True
    )
    preview = handoff.github_preview
    publication_preview_ready = (
        bool(preview)
        and preview.get("status") == "pending"
        and preview.get("publication_gate_required") is True
        and preview.get("remote_mutation_allowed") is False
        and preview.get("github_mutation_performed") is False
    )
    closed_loop_complete = (
        not issues
        and recall.valid
        and recall.closed_result_frame_built
        and specialist_output_verified
        and str(recall.closed_frame.get("sql_ref", "")) == sql_ref
        and final_ref
        == str(deliberation.final_artifact.final_ref)
        and synthesis_ref
        == str(deliberation.final_artifact.synthesis_ref)
    )

    if not specialist_output_verified:
        issues.append("closed frame did not verify specialist_output")
    if not visual_path_complete:
        issues.append("passive supervisor and visual path are incomplete")
    if not publication_preview_ready:
        issues.append("GitHub preview is not locally gated")
    if not closed_loop_complete and not issues:
        issues.append("r2/r3/r4 semantic identities did not close")

    return _result(
        command=command,
        issues=issues,
        deliberation=deliberation_mapping,
        handoff=handoff_mapping,
        recall=recall_mapping,
        sql_replay=replay_mapping,
        sql_ref=sql_ref,
        final_ref=final_ref,
        synthesis_ref=synthesis_ref,
        passage_profile_ref=str(
            handoff.compatibility.get("profile_ref", "")
        ),
        query_profile_ref=str(
            recall.query_profile.get("profile_ref", "")
        ),
        closed_loop_complete=closed_loop_complete,
        sql_replay_verified=replay_verified,
        specialist_output_verified=specialist_output_verified,
        visual_path_complete=visual_path_complete,
        publication_preview_ready=publication_preview_ready,
    )


def _deliberation_issues(
    result: FakeLaboratoryDeliberationResult,
) -> tuple[str, ...]:
    issues: list[str] = []
    if not result.publication_ready:
        issues.append("r2 deliberation is not locally publication-ready")
    if result.final_artifact is None or result.final_packet is None:
        issues.append("r2 deliberation did not build final local artifacts")
    if result.scheduler_created or result.parallel_orchestrator_created:
        issues.append("r2 deliberation claimed a parallel authority")
    if result.github_mutation_performed:
        issues.append("r2 deliberation mutated GitHub")
    return tuple(issues)


def _handoff_issues(
    result: FakeLaboratoryClosedHandoffResult,
) -> tuple[str, ...]:
    issues = list(result.issues)
    if not result.valid:
        issues.append("r3 closed local handoff is invalid")
    if not result.sql_write_performed or not result.sql_readback_performed:
        issues.append("r3 did not close SQL write/readback")
    if not result.qdrant_write_performed:
        issues.append("r3 did not acknowledge passage projection")
    if result.github_mutation_performed:
        issues.append("r3 handoff mutated GitHub")
    return tuple(dict.fromkeys(issues))


def _recall_issues(
    handoff: FakeLaboratoryClosedHandoffResult,
    result: LaboratoryRecallClosureResult,
) -> tuple[str, ...]:
    issues = list(result.issues)
    sql_ref = str(handoff.sql_record.get("context_ref", ""))
    if not result.valid:
        issues.append("r4 recall closure is invalid")
    if not result.qdrant_recall_performed:
        issues.append("r4 did not execute Qdrant recall")
    if not result.sql_rehydrate_performed:
        issues.append("r4 did not rehydrate specialist_output from SQL")
    if not result.closed_result_frame_built:
        issues.append("r4 did not build closed ResultFrame")
    if result.sql_ref != sql_ref:
        issues.append("r4 sql_ref does not match r3 durable output")
    if result.github_mutation_performed:
        issues.append("r4 recall mutated GitHub")
    return tuple(dict.fromkeys(issues))


def _verify_sql_replay(
    *,
    expected_sql_ref: str,
    replay: FakeLaboratoryClosedHandoffResult,
) -> bool:
    return (
        replay.valid
        and replay.sql_record.get("context_ref") == expected_sql_ref
        and replay.sql_write.get("idempotent_replay") is True
        and replay.sql_write.get("inserted") is False
        and replay.sql_write.get("replaced") is False
        and replay.qdrant_write_performed is False
        and replay.github_mutation_performed is False
    )


def _result(
    *,
    command: FakeLaboratoryClosedLoopSmokeCommand,
    issues: Sequence[str],
    deliberation: Mapping[str, Any] | None = None,
    handoff: Mapping[str, Any] | None = None,
    recall: Mapping[str, Any] | None = None,
    sql_replay: Mapping[str, Any] | None = None,
    sql_ref: str = "",
    final_ref: str = "",
    synthesis_ref: str = "",
    passage_profile_ref: str = "",
    query_profile_ref: str = "",
    closed_loop_complete: bool = False,
    sql_replay_verified: bool = False,
    specialist_output_verified: bool = False,
    visual_path_complete: bool = False,
    publication_preview_ready: bool = False,
) -> FakeLaboratoryClosedLoopSmokeResult:
    normalized = tuple(
        dict.fromkeys(str(issue) for issue in issues if str(issue))
    )
    return FakeLaboratoryClosedLoopSmokeResult(
        valid=not normalized,
        issues=normalized,
        command=command,
        deliberation=dict(deliberation or {}),
        handoff=dict(handoff or {}),
        recall=dict(recall or {}),
        sql_replay=dict(sql_replay or {}),
        sql_ref=sql_ref,
        final_ref=final_ref,
        synthesis_ref=synthesis_ref,
        passage_profile_ref=passage_profile_ref,
        query_profile_ref=query_profile_ref,
        closed_loop_complete=closed_loop_complete,
        sql_replay_verified=sql_replay_verified,
        specialist_output_verified=specialist_output_verified,
        visual_path_complete=visual_path_complete,
        publication_preview_ready=publication_preview_ready,
    )


__all__ = (
    "FAKE_LABORATORY_CLOSED_LOOP_SMOKE_COMMAND_SCHEMA",
    "FAKE_LABORATORY_CLOSED_LOOP_SMOKE_RESULT_SCHEMA",
    "FAKE_LABORATORY_CLOSED_LOOP_SMOKE_VERSION",
    "FakeLaboratoryClosedLoopSmokeCommand",
    "FakeLaboratoryClosedLoopSmokeError",
    "FakeLaboratoryClosedLoopSmokeResult",
    "run_fake_laboratory_existing_scheduler_closed_loop_smoke",
)
