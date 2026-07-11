from __future__ import annotations

import pytest

from context.github_project_v2_change_handoff_0272 import (
    GitHubProjectV2ChangeHandoffPolicy,
    build_change_handoff_batch,
)
from context.github_project_v2_snapshot_change_detection_0272 import CHANGE_SET_SCHEMA
from context.github_project_v2_source_candidate_gate_0272 import (
    GATE_RECORD_SCHEMA,
    GitHubProjectV2SourceCandidateGateCommand,
    build_gate_plan,
    build_gate_record,
    close_gate_result,
)


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
                    "item_id": "PVTI_added",
                    "item_type": "DRAFT_ISSUE",
                    "content_id": "DI_added",
                    "title": "Construire un chalouf",
                    "body": "Étudier un levier et un contrepoids.",
                    "status": "Todo",
                    "repository": "",
                    "number": 0,
                    "url": "",
                }
            ],
            "changed": [],
            "removed": [
                {
                    "item_id": "PVTI_removed",
                    "item_type": "DRAFT_ISSUE",
                    "content_id": "DI_removed",
                    "title": "Ancienne idée",
                    "body": "Le retrait distant reste advisory.",
                    "status": "Done",
                    "repository": "",
                    "number": 0,
                    "url": "",
                }
            ],
            "unchanged_ids": [],
        },
        "counts": {
            "added_count": 1,
            "changed_count": 0,
            "removed_count": 1,
            "unchanged_count": 0,
        },
        "boundaries": {
            "external_call_performed": False,
            "remote_mutation_allowed": False,
            "sql_write_allowed": False,
            "qdrant_write_allowed": False,
        },
    }


def _batch() -> dict[str, object]:
    return build_change_handoff_batch(
        change_set=_change_set(),
        policy=GitHubProjectV2ChangeHandoffPolicy(),
    )


def _candidate_id(batch: dict[str, object], change_kind: str) -> str:
    handoffs = batch["handoffs"]
    assert isinstance(handoffs, list)
    handoff = next(item for item in handoffs if item["change_kind"] == change_kind)
    return str(handoff["candidate"]["candidate_id"])


def test_promote_reuses_existing_decision_and_opens_only_future_ingestion() -> None:
    batch = _batch()
    command = GitHubProjectV2SourceCandidateGateCommand(
        candidate_id=_candidate_id(batch, "added"),
        action="promote",
        reason="preuve opérateur",
        execute=True,
        policy_decision_id="policy:0272:gate:promote",
    )
    record = build_gate_record(handoff_batch=batch, command=command)
    assert record["schema"] == GATE_RECORD_SCHEMA
    assert record["candidate_before"]["status"] == "new"
    assert record["candidate_after"]["status"] == "promoted"
    assert record["approval"] == {
        "durable_ingestion_allowed": True,
        "ingestion_mode": "promote",
        "target_context_id": None,
        "durable_ingestion_performed": False,
    }
    assert record["boundaries"]["sql_write_allowed"] is False
    assert record["boundaries"]["qdrant_write_allowed"] is False
    assert record["boundaries"]["remote_mutation_allowed"] is False


def test_reject_closes_durable_ingestion() -> None:
    batch = _batch()
    command = GitHubProjectV2SourceCandidateGateCommand(
        candidate_id=_candidate_id(batch, "added"),
        action="reject",
        reason="hors périmètre",
        execute=True,
        policy_decision_id="policy:0272:gate:reject",
    )
    record = build_gate_record(handoff_batch=batch, command=command)
    assert record["candidate_after"]["status"] == "rejected"
    assert record["approval"]["durable_ingestion_allowed"] is False
    assert record["approval"]["ingestion_mode"] == "none"


def test_merge_requires_target_context() -> None:
    with pytest.raises(ValueError, match="target_context_id is required for merge"):
        GitHubProjectV2SourceCandidateGateCommand(
            candidate_id="ghpv2-test",
            action="merge",
            execute=True,
            policy_decision_id="policy:test",
        )


def test_removed_item_cannot_be_promoted_or_merged() -> None:
    batch = _batch()
    removed_id = _candidate_id(batch, "removed")
    for action, target in (("promote", None), ("merge", "ctx-existing")):
        command = GitHubProjectV2SourceCandidateGateCommand(
            candidate_id=removed_id,
            action=action,
            target_context_id=target,
            execute=True,
            policy_decision_id=f"policy:0272:gate:{action}",
        )
        with pytest.raises(ValueError, match="removed ProjectV2 items are advisory"):
            build_gate_record(handoff_batch=batch, command=command)


def test_execute_plan_requires_policy_decision_id() -> None:
    command = GitHubProjectV2SourceCandidateGateCommand(
        candidate_id="ghpv2-test",
        action="inspect",
        execute=True,
    )
    plan = build_gate_plan(command, handoff_batch_path="handoff.json")
    assert plan.valid is False
    assert "policy_decision_id is required for execute mode" in plan.issues


def test_result_closure_reports_immutable_gate_without_side_effects() -> None:
    batch = _batch()
    command = GitHubProjectV2SourceCandidateGateCommand(
        candidate_id=_candidate_id(batch, "added"),
        action="inspect",
        execute=True,
        policy_decision_id="policy:0272:gate:inspect",
    )
    plan = build_gate_plan(command, handoff_batch_path="handoff.json")
    record = build_gate_record(handoff_batch=batch, command=command)
    result = close_gate_result(plan, gate_record=record, gate_path="decision.json")
    assert result.valid is True
    assert result.after_status == "analyzed"
    assert result.durable_ingestion_allowed is False
    assert result.external_call_performed is False
    assert result.boundaries["sql_write_performed"] is False
    assert result.boundaries["qdrant_write_performed"] is False
