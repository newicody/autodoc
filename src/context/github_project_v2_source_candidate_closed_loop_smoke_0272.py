"""Close the approved ProjectV2 candidate SQL/vector/recall loop.

0272-r10 composes the existing r8 durable SQL consumer, the existing 0261
OpenVINO/E5 embedding surface, the r9 vector-space compatibility gate and
projection, then the existing 0263 Qdrant recall -> SQL rehydrate surface.

The module starts from one immutable r7 gate record. r6 handoff construction
and r7 operator decision remain upstream contracts and are not duplicated.
SQL remains the durable authority. Qdrant carries references only. No GitHub
mutation, laboratory selection, Scheduler.run modification or SHM change is
opened here.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import hashlib
import json
from typing import Any, Callable, Mapping

from context.github_project_v2_source_candidate_durable_consumer_0272 import (
    GitHubProjectV2DurableConsumerCommand,
    consume_approved_gate_record,
    validate_approved_gate_record,
)
from context.github_project_v2_source_candidate_vector_projection_0272 import (
    EmbeddingSpaceProfile,
    GitHubProjectV2VectorProjectionCommand,
    run_project_v2_source_candidate_vector_projection,
    validate_embedding_against_profile,
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

CLOSED_LOOP_REPORT_SCHEMA = (
    "missipy.github.project_v2_source_candidate_closed_loop_smoke_report.v1"
)


@dataclass(frozen=True, slots=True)
class GitHubProjectV2ClosedLoopSmokeCommand:
    """Controlled r10 smoke command."""

    execute: bool = False
    policy_decision_id: str = ""
    model_dir: str | None = None
    device: str = "CPU"
    recall_limit: int = 8


@dataclass(frozen=True, slots=True)
class GitHubProjectV2ClosedLoopSmokeResult:
    """Serializable closed-loop result with all authority boundaries visible."""

    valid: bool
    issues: tuple[str, ...]
    execute: bool
    policy_decision_id: str
    sql_ref: str
    embedding_space_family_ref: str
    passage_profile_ref: str
    query_profile_ref: str
    durable: Mapping[str, Any] = field(default_factory=dict)
    durable_replay: Mapping[str, Any] = field(default_factory=dict)
    query_embedding: Mapping[str, Any] = field(default_factory=dict)
    query_compatibility: Mapping[str, Any] = field(default_factory=dict)
    projection: Mapping[str, Any] = field(default_factory=dict)
    recall: Mapping[str, Any] = field(default_factory=dict)
    recalled_sql_ref: bool = False
    hydrated_count: int = 0
    missing_count: int = 0
    boundaries: Mapping[str, bool] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": CLOSED_LOOP_REPORT_SCHEMA,
            "valid": self.valid,
            "issues": list(self.issues),
            "execute": self.execute,
            "policy_decision_id": self.policy_decision_id,
            "sql_ref": self.sql_ref,
            "embedding_space_family_ref": self.embedding_space_family_ref,
            "passage_profile_ref": self.passage_profile_ref,
            "query_profile_ref": self.query_profile_ref,
            "durable": dict(self.durable),
            "durable_replay": dict(self.durable_replay),
            "query_embedding": dict(self.query_embedding),
            "query_compatibility": dict(self.query_compatibility),
            "projection": dict(self.projection),
            "recall": dict(self.recall),
            "recalled_sql_ref": self.recalled_sql_ref,
            "hydrated_count": self.hydrated_count,
            "missing_count": self.missing_count,
            "boundaries": dict(self.boundaries),
        }

    def to_summary(self) -> str:
        return " ".join(
            (
                f"projectv2_closed_loop_valid={self.valid}",
                f"issues={len(self.issues)}",
                f"execute={self.execute}",
                f"sql_ref={self.sql_ref or '-'}",
                f"family_ref={self.embedding_space_family_ref or '-'}",
                f"recalled_sql_ref={self.recalled_sql_ref}",
                f"hydrated_count={self.hydrated_count}",
                f"missing_count={self.missing_count}",
                "sql_remains_authority=True",
                "laboratory_selected=False",
            )
        )


def embedding_space_family_ref(profile: EmbeddingSpaceProfile) -> str:
    """Return one stable space identity shared by passage and query roles."""

    identity = dict(profile.to_mapping())
    for key in ("schema", "profile_ref", "role"):
        identity.pop(key, None)
    digest = hashlib.sha256(_canonical_json(identity).encode("utf-8")).hexdigest()
    return f"embedding-space-family:{digest[:24]}"


def query_profile_from_passage(
    profile: EmbeddingSpaceProfile,
) -> EmbeddingSpaceProfile:
    """Build the query-role profile without changing the underlying space."""

    if profile.role != "passage":
        raise ValueError("r10 passage profile must declare role=passage")
    query_profile = replace(profile, role="query")
    if embedding_space_family_ref(query_profile) != embedding_space_family_ref(profile):
        raise ValueError("query and passage profiles must share one vector-space family")
    return query_profile


def run_project_v2_source_candidate_closed_loop_smoke(
    gate_record: Mapping[str, Any],
    store: Any | None,
    command: GitHubProjectV2ClosedLoopSmokeCommand,
    *,
    profile: EmbeddingSpaceProfile | None = None,
    embedder: Callable[..., Mapping[str, Any]] | None = None,
    qdrant_executor: Any | None = None,
) -> GitHubProjectV2ClosedLoopSmokeResult:
    """Run r7 gate -> r8 SQL -> E5/Qdrant -> 0263 SQL rehydrate."""

    passage_profile = profile or EmbeddingSpaceProfile()
    issues = list(validate_approved_gate_record(gate_record))
    if passage_profile.role != "passage":
        issues.append("r10 requires a passage-role projection profile")
    if command.recall_limit <= 0:
        issues.append("recall_limit must be > 0")
    if command.execute and not command.policy_decision_id.startswith("policy:"):
        issues.append("execute policy_decision_id must start with policy:")
    if command.execute and store is None:
        issues.append("execute mode requires an existing SQLContextStore object")
    if command.execute and qdrant_executor is None:
        issues.append("execute mode requires an injected Qdrant executor")

    try:
        query_profile = query_profile_from_passage(passage_profile)
    except ValueError as exc:
        issues.append(str(exc))
        query_profile = replace(passage_profile, role="query")

    family_ref = embedding_space_family_ref(passage_profile)
    if issues or not command.execute:
        return _result(
            issues=issues,
            command=command,
            family_ref=family_ref,
            passage_profile=passage_profile,
            query_profile=query_profile,
        )

    assert store is not None
    durable_result = consume_approved_gate_record(
        gate_record,
        GitHubProjectV2DurableConsumerCommand(
            execute=True,
            policy_decision_id=command.policy_decision_id,
        ),
        store=store,
    )
    durable_report = durable_result.to_json_dict()
    if not durable_result.valid:
        return _result(
            issues=durable_result.issues,
            command=command,
            family_ref=family_ref,
            passage_profile=passage_profile,
            query_profile=query_profile,
            sql_ref=durable_result.sql_ref,
            durable=durable_report,
        )

    replay_result = consume_approved_gate_record(
        gate_record,
        GitHubProjectV2DurableConsumerCommand(
            execute=True,
            policy_decision_id=command.policy_decision_id,
        ),
        store=store,
    )
    replay_report = replay_result.to_json_dict()
    if not replay_result.valid:
        issues.extend(replay_result.issues)
    if replay_result.idempotent_replay is not True:
        issues.append("second durable consumption must be an idempotent replay")

    sql_ref = durable_result.sql_ref
    query_request = SchedulerManagedSqlRefOpenVinoEmbeddingRequest(
        sql_ref=sql_ref,
        role="query",
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
            family_ref=family_ref,
            passage_profile=passage_profile,
            query_profile=query_profile,
            sql_ref=sql_ref,
            durable=durable_report,
            durable_replay=replay_report,
            query_embedding=query_report,
        )

    query_embedding = _mapping(query_report.get("embedding"))
    query_compatibility = validate_embedding_against_profile(
        query_embedding,
        query_profile,
        expected_sql_ref=sql_ref,
    )
    if not query_compatibility.compatible:
        issues.extend(query_compatibility.issues)
        return _result(
            issues=issues,
            command=command,
            family_ref=family_ref,
            passage_profile=passage_profile,
            query_profile=query_profile,
            sql_ref=sql_ref,
            durable=durable_report,
            durable_replay=replay_report,
            query_embedding=query_report,
            query_compatibility=query_compatibility.to_mapping(),
        )

    projection_result = run_project_v2_source_candidate_vector_projection(
        durable_report,
        store,
        GitHubProjectV2VectorProjectionCommand(
            execute=True,
            policy_decision_id=command.policy_decision_id,
            model_dir=command.model_dir,
            device=command.device,
        ),
        profile=passage_profile,
        embedder=embedder,
        qdrant_executor=qdrant_executor,
    )
    projection_report = projection_result.to_json_dict()
    if not projection_result.valid:
        issues.extend(projection_result.issues)
        return _result(
            issues=issues,
            command=command,
            family_ref=family_ref,
            passage_profile=passage_profile,
            query_profile=query_profile,
            sql_ref=sql_ref,
            durable=durable_report,
            durable_replay=replay_report,
            query_embedding=query_report,
            query_compatibility=query_compatibility.to_mapping(),
            projection=projection_report,
        )

    recall_request = SchedulerManagedQdrantRecallSqlRehydrateRequest(
        query_ref=default_query_ref_from_embedding_report(query_report),
        policy_decision_id=command.policy_decision_id,
        collection_name=passage_profile.collection_name,
        vector_dimension=passage_profile.dimension,
        limit=command.recall_limit,
    )
    recall_result = run_scheduler_managed_qdrant_recall_sql_rehydrate_usage(
        query_report,
        store,
        recall_request,
        execute=True,
        executor=qdrant_executor,
    )
    recall_report = recall_result.to_mapping()
    if not recall_result.valid:
        issues.extend(recall_result.issues)

    recalled_sql_ref = sql_ref in recall_result.sql_refs
    if not recalled_sql_ref:
        issues.append("Qdrant recall did not return the durable sql_ref")
    if recall_result.missing_sql_refs:
        issues.append("Qdrant recall returned SQL refs missing from durable authority")
    hydrated_refs = {
        str(_mapping(record).get("context_ref", ""))
        for record in recall_result.hydrated_records
    }
    if sql_ref not in hydrated_refs:
        issues.append("SQL rehydration did not return the durable candidate record")

    return _result(
        issues=issues,
        command=command,
        family_ref=family_ref,
        passage_profile=passage_profile,
        query_profile=query_profile,
        sql_ref=sql_ref,
        durable=durable_report,
        durable_replay=replay_report,
        query_embedding=query_report,
        query_compatibility=query_compatibility.to_mapping(),
        projection=projection_report,
        recall=recall_report,
        recalled_sql_ref=recalled_sql_ref,
        hydrated_count=len(recall_result.hydrated_records),
        missing_count=len(recall_result.missing_sql_refs),
    )


def _result(
    *,
    issues: Any,
    command: GitHubProjectV2ClosedLoopSmokeCommand,
    family_ref: str,
    passage_profile: EmbeddingSpaceProfile,
    query_profile: EmbeddingSpaceProfile,
    sql_ref: str = "",
    durable: Mapping[str, Any] | None = None,
    durable_replay: Mapping[str, Any] | None = None,
    query_embedding: Mapping[str, Any] | None = None,
    query_compatibility: Mapping[str, Any] | None = None,
    projection: Mapping[str, Any] | None = None,
    recall: Mapping[str, Any] | None = None,
    recalled_sql_ref: bool = False,
    hydrated_count: int = 0,
    missing_count: int = 0,
) -> GitHubProjectV2ClosedLoopSmokeResult:
    normalized_issues = tuple(dict.fromkeys(str(item) for item in issues if str(item)))
    projection_map = dict(projection or {})
    recall_map = dict(recall or {})
    durable_map = dict(durable or {})
    replay_map = dict(durable_replay or {})
    query_map = dict(query_embedding or {})
    return GitHubProjectV2ClosedLoopSmokeResult(
        valid=not normalized_issues,
        issues=normalized_issues,
        execute=command.execute,
        policy_decision_id=command.policy_decision_id,
        sql_ref=sql_ref,
        embedding_space_family_ref=family_ref,
        passage_profile_ref=passage_profile.profile_ref,
        query_profile_ref=query_profile.profile_ref,
        durable=durable_map,
        durable_replay=replay_map,
        query_embedding=query_map,
        query_compatibility=dict(query_compatibility or {}),
        projection=projection_map,
        recall=recall_map,
        recalled_sql_ref=recalled_sql_ref,
        hydrated_count=hydrated_count,
        missing_count=missing_count,
        boundaries={
            "r7_gate_record_required": True,
            "r8_sql_consumer_reused": True,
            "r8_replay_checked": bool(replay_map),
            "query_embedding_checked_before_qdrant_write": bool(query_map),
            "r9_projection_reused": bool(projection_map),
            "recall_0263_reused": bool(recall_map),
            "sql_write_performed": bool(durable_map.get("sql_write_performed", False)),
            "idempotent_replay": bool(replay_map.get("idempotent_replay", False)),
            "openvino_call_performed": bool(query_map),
            "qdrant_write_performed": bool(
                projection_map.get("qdrant_write_performed", False)
            ),
            "qdrant_search_performed": bool(recall_map.get("execute", False)),
            "sql_rehydrate_performed": hydrated_count > 0,
            "sql_remains_authority": True,
            "external_embedding_accepted": False,
            "remote_mutation_allowed": False,
            "laboratory_selection_allowed": False,
            "scheduler_run_modified": False,
            "shm_touched": False,
        },
    )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(dict(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
