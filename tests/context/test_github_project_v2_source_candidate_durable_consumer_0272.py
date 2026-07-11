from __future__ import annotations

from context.github_project_v2_change_handoff_0272 import (
    GitHubProjectV2ChangeHandoffPolicy,
    build_change_handoff_batch,
)
from context.github_project_v2_snapshot_change_detection_0272 import CHANGE_SET_SCHEMA
from context.github_project_v2_source_candidate_durable_consumer_0272 import (
    GitHubProjectV2DurableConsumerCommand,
    build_durable_consumer_plan,
    build_durable_sql_record,
    consume_approved_gate_record,
    validate_approved_gate_record,
)
from context.github_project_v2_source_candidate_gate_0272 import (
    GitHubProjectV2SourceCandidateGateCommand,
    build_gate_record,
)
from context.sql_context_store import SQLiteSqlContextStore


def _change_set() -> dict[str, object]:
    return {
        "schema": CHANGE_SET_SCHEMA,
        "kind": "github_project_v2_snapshot_change_set",
        "baseline": False,
        "change_set_ref": "github-project-v2-change-set:0123456789abcdef",
        "previous_snapshot_ref": "github-project-v2-snapshot:previous",
        "current_snapshot_ref": "github-project-v2-snapshot:current",
        "project": {
            "id": "PVT_test",
            "owner": "newicody",
            "number": 2,
            "title": "idea",
            "url": "https://github.com/users/newicody/projects/2",
        },
        "items": {
            "added": [
                {
                    "item_id": "PVTI_chalouf",
                    "item_type": "DRAFT_ISSUE",
                    "content_id": "DI_chalouf",
                    "title": "Construire un chalouf",
                    "body": "Préparer une demande durable avant laboratoire.",
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


def _approved_gate(*, action: str = "promote") -> dict[str, object]:
    batch = build_change_handoff_batch(
        change_set=_change_set(),
        policy=GitHubProjectV2ChangeHandoffPolicy(),
    )
    handoff = batch["handoffs"][0]
    candidate_id = handoff["candidate"]["candidate_id"]
    command = GitHubProjectV2SourceCandidateGateCommand(
        candidate_id=str(candidate_id),
        action=action,
        target_context_id="sql:inference_context:existing" if action == "merge" else None,
        reason="validation opérateur",
        execute=True,
        policy_decision_id=f"policy:0272:r8:{action}",
    )
    return build_gate_record(handoff_batch=batch, command=command)


def test_approved_promote_gate_builds_laboratory_neutral_sql_record() -> None:
    gate = _approved_gate()
    assert validate_approved_gate_record(gate) == ()
    record = build_durable_sql_record(gate)
    payload = record.to_mapping()
    assert payload["kind"] == "github_artifact"
    assert payload["title"] == "Construire un chalouf"
    assert payload["metadata"]["embedding_projection_state"] == "pending"
    assert payload["metadata"]["laboratory_assignment_state"] == "unassigned"
    assert payload["context_ref"].startswith("sql:github_artifact:")


def test_execute_writes_and_rehydrates_existing_sql_store() -> None:
    gate = _approved_gate()
    store = SQLiteSqlContextStore(":memory:")
    result = consume_approved_gate_record(
        gate,
        GitHubProjectV2DurableConsumerCommand(
            execute=True,
            policy_decision_id="policy:0272:r8:execute",
        ),
        store=store,
    )
    assert result.valid is True
    assert result.sql_write_performed is True
    assert result.idempotent_replay is False
    assert result.rehydrated is True
    assert result.boundaries["qdrant_write_performed"] is False
    assert result.boundaries["openvino_call_performed"] is False
    assert store.get_record(result.sql_ref) is not None


def test_replay_is_idempotent_and_does_not_rewrite() -> None:
    gate = _approved_gate()
    store = SQLiteSqlContextStore(":memory:")
    command = GitHubProjectV2DurableConsumerCommand(
        execute=True,
        policy_decision_id="policy:0272:r8:replay",
    )
    first = consume_approved_gate_record(gate, command, store=store)
    second = consume_approved_gate_record(gate, command, store=store)
    assert first.valid is True
    assert first.sql_write_performed is True
    assert second.valid is True
    assert second.sql_write_performed is False
    assert second.idempotent_replay is True
    assert second.sql_ref == first.sql_ref


def test_merge_preserves_target_context_without_collapsing_it() -> None:
    gate = _approved_gate(action="merge")
    record = build_durable_sql_record(gate).to_mapping()
    assert record["metadata"]["decision_action"] == "merge"
    assert record["metadata"]["target_context_id"] == (
        "sql:inference_context:existing"
    )
    assert record["parent_ref"] is None


def test_non_approving_gate_is_rejected() -> None:
    batch = build_change_handoff_batch(
        change_set=_change_set(),
        policy=GitHubProjectV2ChangeHandoffPolicy(),
    )
    candidate_id = batch["handoffs"][0]["candidate"]["candidate_id"]
    gate = build_gate_record(
        handoff_batch=batch,
        command=GitHubProjectV2SourceCandidateGateCommand(
            candidate_id=str(candidate_id),
            action="inspect",
            execute=True,
            policy_decision_id="policy:0272:r8:inspect",
        ),
    )
    issues = validate_approved_gate_record(gate)
    assert "gate action must be promote or merge" in issues
    result = consume_approved_gate_record(
        gate,
        GitHubProjectV2DurableConsumerCommand(execute=False),
    )
    assert result.valid is False
    assert result.sql_write_performed is False


def test_plan_requires_policy_decision_only_for_execute() -> None:
    dry = build_durable_consumer_plan(
        GitHubProjectV2DurableConsumerCommand(execute=False),
        gate_record_path="gate.json",
    )
    assert dry.valid is True
    live = build_durable_consumer_plan(
        GitHubProjectV2DurableConsumerCommand(execute=True),
        gate_record_path="gate.json",
    )
    assert live.valid is False
    assert "policy_decision_id is required for execute mode" in live.issues
