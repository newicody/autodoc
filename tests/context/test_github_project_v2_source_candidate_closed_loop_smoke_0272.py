from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from context.github_project_v2_source_candidate_closed_loop_smoke_0272 import (
    GitHubProjectV2ClosedLoopSmokeCommand,
    embedding_space_family_ref,
    query_profile_from_passage,
    run_project_v2_source_candidate_closed_loop_smoke,
)
from context.github_project_v2_source_candidate_vector_projection_0272 import (
    EmbeddingSpaceProfile,
)
from context.github_project_v2_change_handoff_0272 import (
    GitHubProjectV2ChangeHandoffPolicy,
    build_change_handoff_batch,
)
from context.github_project_v2_snapshot_change_detection_0272 import CHANGE_SET_SCHEMA
from context.github_project_v2_source_candidate_gate_0272 import (
    GitHubProjectV2SourceCandidateGateCommand,
    build_gate_record,
)
from inference.qdrant_projection_adapter import (
    QdrantProjectionWriteResult,
    QdrantRecallHit,
    QdrantRecallResult,
)


@dataclass
class Record:
    context_ref: str
    kind: str
    title: str
    body: str
    parent_ref: str | None
    metadata: tuple[tuple[str, str], ...]

    def to_mapping(self) -> dict[str, Any]:
        return {
            "context_ref": self.context_ref,
            "kind": self.kind,
            "title": self.title,
            "body": self.body,
            "parent_ref": self.parent_ref,
            "metadata": dict(self.metadata),
        }


class Store:
    def __init__(self) -> None:
        self.records: dict[str, Any] = {}
        self.initialize_calls = 0
        self.upsert_calls = 0

    def initialize_schema(self) -> None:
        self.initialize_calls += 1

    def upsert_record(self, record: Any) -> None:
        self.upsert_calls += 1
        self.records[record.context_ref] = record

    def get_record(self, context_ref: str) -> Any | None:
        return self.records.get(context_ref)


class Executor:
    def __init__(self) -> None:
        self.points: tuple[Any, ...] = ()
        self.write_calls = 0
        self.search_calls = 0

    def upsert_points(self, points: Sequence[Any], *, target, policy):
        self.write_calls += 1
        self.points = tuple(points)
        return QdrantProjectionWriteResult(
            target=target,
            point_ids=tuple(point.point_id for point in points),
            acknowledged=True,
        )

    def search_vector(self, vector, *, target, policy, query):
        self.search_calls += 1
        point = self.points[0]
        payload = dict(point.payload)
        sql_ref = str(payload.get("sql_ref") or payload.get("sql_context_ref"))
        hit = QdrantRecallHit(
            point_id=point.point_id,
            sql_context_ref=sql_ref,
            score=1.0,
            source_ref=point.source_ref,
            payload=point.payload,
        )
        return QdrantRecallResult(
            target=target,
            query=query,
            hits=(hit,),
            capped=False,
        )


def _change_set() -> dict[str, object]:
    return {
        "schema": CHANGE_SET_SCHEMA,
        "kind": "github_project_v2_snapshot_change_set",
        "baseline": False,
        "change_set_ref": "github-project-v2-change-set:r10",
        "previous_snapshot_ref": "github-project-v2-snapshot:r10-previous",
        "current_snapshot_ref": "github-project-v2-snapshot:r10-current",
        "project": {
            "id": "PVT_r10",
            "owner": "newicody",
            "number": 2,
            "title": "idea",
            "url": "https://github.com/users/newicody/projects/2",
        },
        "items": {
            "added": [
                {
                    "item_id": "PVTI_r10",
                    "item_type": "DRAFT_ISSUE",
                    "content_id": "DI_r10",
                    "title": "R10 closed-loop candidate",
                    "body": "Validate SQL, E5, Qdrant recall and SQL rehydrate.",
                    "status": "Todo",
                    "repository": "",
                    "number": 0,
                    "url": "",
                }
            ],
            "changed": [],
            "removed": [],
            "unchanged_ids": [],
        },
        "counts": {
            "added_count": 1,
            "changed_count": 0,
            "removed_count": 0,
            "unchanged_count": 0,
        },
        "boundaries": {
            "external_call_performed": False,
            "remote_mutation_allowed": False,
            "sql_write_allowed": False,
            "qdrant_write_allowed": False,
        },
    }


def gate_record() -> dict[str, Any]:
    batch = build_change_handoff_batch(
        change_set=_change_set(),
        policy=GitHubProjectV2ChangeHandoffPolicy(),
    )
    handoff = batch["handoffs"][0]
    return build_gate_record(
        handoff_batch=batch,
        command=GitHubProjectV2SourceCandidateGateCommand(
            candidate_id=str(handoff["candidate"]["candidate_id"]),
            action="promote",
            reason="r10 closed-loop smoke",
            execute=True,
            policy_decision_id="policy:0272:r7:r10",
        ),
    )


def profile() -> EmbeddingSpaceProfile:
    return EmbeddingSpaceProfile(
        model_ref="test.e5",
        tokenizer_ref="test.tokenizer",
        model_revision="test-r10",
        collection_name="test_collection",
    )


def embedder(
    text: str,
    sql_ref: str,
    model_dir: str | None,
    device: str,
) -> Mapping[str, Any]:
    role = "query" if text.startswith("query:") else "passage"
    vector = [0.0] * 384
    vector[0] = 1.0
    return {
        "schema": "missipy.scheduler_managed_sql_ref_openvino_embedding.v1",
        "embedding_ref": f"embedding:{role}:r10",
        "source_ref": f"ctx-fragment:{sql_ref}",
        "sql_ref": sql_ref,
        "backend_ref": "openvino:model:multilingual-e5-small",
        "role": role,
        "dimension": 384,
        "normalized": True,
        "l2_norm": 1.0,
        "metadata": {
            "context_ref": sql_ref,
            "model": "test.e5",
            "tokenizer": "test.tokenizer",
            "device": device,
        },
        "vector": vector,
    }


def test_query_and_passage_profiles_share_one_family() -> None:
    passage = profile()
    query = query_profile_from_passage(passage)
    assert passage.profile_ref != query.profile_ref
    assert embedding_space_family_ref(passage) == embedding_space_family_ref(query)


def test_execute_closes_sql_vector_recall_and_rehydrate_loop() -> None:
    store = Store()
    executor = Executor()
    result = run_project_v2_source_candidate_closed_loop_smoke(
        gate_record(),
        store,
        GitHubProjectV2ClosedLoopSmokeCommand(
            execute=True,
            policy_decision_id="policy:0272:r10:test",
            recall_limit=4,
        ),
        profile=profile(),
        embedder=embedder,
        qdrant_executor=executor,
    )
    assert result.valid is True
    assert result.sql_ref.startswith("sql:github_artifact:")
    assert result.durable["rehydrated"] is True
    assert result.durable_replay["idempotent_replay"] is True
    assert result.query_compatibility["compatible"] is True
    assert result.projection["qdrant_write_performed"] is True
    assert result.recalled_sql_ref is True
    assert result.hydrated_count == 1
    assert result.missing_count == 0
    assert executor.write_calls == 1
    assert executor.search_calls == 1
    assert store.upsert_calls == 1
    assert result.boundaries["sql_remains_authority"] is True
    assert result.boundaries["laboratory_selection_allowed"] is False


def test_dry_run_is_pure_and_does_not_require_runtime_dependencies() -> None:
    result = run_project_v2_source_candidate_closed_loop_smoke(
        gate_record(),
        None,
        GitHubProjectV2ClosedLoopSmokeCommand(execute=False),
        profile=profile(),
    )
    assert result.valid is True
    assert result.execute is False
    assert result.sql_ref == ""
    assert result.boundaries["qdrant_write_performed"] is False
    assert result.boundaries["qdrant_search_performed"] is False
    assert result.boundaries["remote_mutation_allowed"] is False


def test_incompatible_query_embedding_blocks_qdrant_before_write() -> None:
    store = Store()
    executor = Executor()

    def incompatible(
        text: str,
        sql_ref: str,
        model_dir: str | None,
        device: str,
    ) -> Mapping[str, Any]:
        payload = dict(embedder(text, sql_ref, model_dir, device))
        if text.startswith("query:"):
            payload["metadata"] = dict(payload["metadata"])
            payload["metadata"]["tokenizer"] = "other.tokenizer"
        return payload

    result = run_project_v2_source_candidate_closed_loop_smoke(
        gate_record(),
        store,
        GitHubProjectV2ClosedLoopSmokeCommand(
            execute=True,
            policy_decision_id="policy:0272:r10:blocked",
        ),
        profile=profile(),
        embedder=incompatible,
        qdrant_executor=executor,
    )
    assert result.valid is False
    assert "embedding tokenizer is incompatible with profile" in result.issues
    assert executor.write_calls == 0
    assert executor.search_calls == 0


def test_execute_requires_typed_policy_and_injected_effect_surfaces() -> None:
    result = run_project_v2_source_candidate_closed_loop_smoke(
        gate_record(),
        None,
        GitHubProjectV2ClosedLoopSmokeCommand(execute=True),
        profile=profile(),
    )
    assert result.valid is False
    assert "execute policy_decision_id must start with policy:" in result.issues
    assert "execute mode requires an existing SQLContextStore object" in result.issues
    assert "execute mode requires an injected Qdrant executor" in result.issues
