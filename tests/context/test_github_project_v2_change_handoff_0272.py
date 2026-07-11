from __future__ import annotations

from context.github_project_v2_change_handoff_0272 import (
    HANDOFF_BATCH_SCHEMA,
    GitHubProjectV2ChangeHandoffCommand,
    GitHubProjectV2ChangeHandoffPolicy,
    build_change_handoff_batch,
    build_change_handoff_plan,
    close_change_handoff_result,
    validate_change_set,
)
from context.github_project_v2_snapshot_change_detection_0272 import CHANGE_SET_SCHEMA


def _change_set(*, baseline: bool = False) -> dict[str, object]:
    return {
        "schema": CHANGE_SET_SCHEMA,
        "kind": "github_project_v2_snapshot_change_set",
        "baseline": baseline,
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
            "changed": [
                {
                    "item_id": "PVTI_changed",
                    "item_type": {"before": "DRAFT_ISSUE", "after": "DRAFT_ISSUE"},
                    "title": {"before": "Hydrologie", "after": "Hydrologie mondiale"},
                    "status": {"before": "Todo", "after": "In progress"},
                    "changed_paths": ["content.title", "field_values.Status"],
                    "before": {"id": "PVTI_changed"},
                    "after": {
                        "id": "PVTI_changed",
                        "type": "DRAFT_ISSUE",
                        "content": {
                            "id": "DI_changed",
                            "title": "Hydrologie mondiale",
                            "body": "Comparer les techniques historiques.",
                        },
                    },
                }
            ],
            "removed": [
                {
                    "item_id": "PVTI_removed",
                    "item_type": "DRAFT_ISSUE",
                    "content_id": "DI_removed",
                    "title": "Ancienne idée",
                    "body": "Ne pas supprimer automatiquement le contexte local.",
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
            "changed_count": 1,
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


def test_change_set_is_valid_and_builds_source_candidate_handoffs() -> None:
    change_set = _change_set()
    assert validate_change_set(change_set) == ()
    batch = build_change_handoff_batch(
        change_set=change_set,
        policy=GitHubProjectV2ChangeHandoffPolicy(),
    )
    assert batch["schema"] == HANDOFF_BATCH_SCHEMA
    assert batch["counts"] == {
        "candidate_count": 3,
        "added_candidate_count": 1,
        "changed_candidate_count": 1,
        "removed_candidate_count": 1,
        "truncated_count": 0,
    }
    candidates = [handoff["candidate"] for handoff in batch["handoffs"]]
    assert all(candidate["schema"] == "missipy.source_candidate.v1" for candidate in candidates)
    assert all(candidate["candidate_id"].startswith("ghpv2-") for candidate in candidates)
    assert all(handoff["requires_operator_gate"] is True for handoff in batch["handoffs"])
    assert all(handoff["durable_ingestion_allowed"] is False for handoff in batch["handoffs"])
    added = next(h for h in batch["handoffs"] if h["change_kind"] == "added")
    assert added["candidate"]["body"] == "Étudier un levier et un contrepoids."
    removed = next(h for h in batch["handoffs"] if h["change_kind"] == "removed")
    assert removed["candidate"]["metadata"]["removal_is_advisory"] is True


def test_baseline_does_not_flood_handoffs_by_default() -> None:
    batch = build_change_handoff_batch(
        change_set=_change_set(baseline=True),
        policy=GitHubProjectV2ChangeHandoffPolicy(include_baseline=False),
    )
    assert batch["baseline"] is True
    assert batch["counts"]["candidate_count"] == 0
    assert batch["handoffs"] == []


def test_handoff_budget_is_bounded_and_deterministic() -> None:
    policy = GitHubProjectV2ChangeHandoffPolicy(max_handoffs=2)
    first = build_change_handoff_batch(change_set=_change_set(), policy=policy)
    second = build_change_handoff_batch(change_set=_change_set(), policy=policy)
    assert first == second
    assert first["counts"]["candidate_count"] == 2
    assert first["counts"]["truncated_count"] == 1


def test_plan_requires_decision_id_only_for_execute() -> None:
    plan = build_change_handoff_plan(
        GitHubProjectV2ChangeHandoffCommand(execute=False),
        change_set_path="change.json",
        policy=GitHubProjectV2ChangeHandoffPolicy(),
    )
    assert plan.valid is True
    live = build_change_handoff_plan(
        GitHubProjectV2ChangeHandoffCommand(execute=True),
        change_set_path="change.json",
        policy=GitHubProjectV2ChangeHandoffPolicy(),
    )
    assert live.valid is False
    assert "policy_decision_id is required for execute mode" in live.issues


def test_result_closure_keeps_all_write_boundaries_closed() -> None:
    plan = build_change_handoff_plan(
        GitHubProjectV2ChangeHandoffCommand(
            execute=True,
            policy_decision_id="policy:0272:change-handoff",
        ),
        change_set_path="change.json",
        policy=GitHubProjectV2ChangeHandoffPolicy(),
    )
    batch = build_change_handoff_batch(
        change_set=_change_set(),
        policy=plan.policy,
    )
    result = close_change_handoff_result(
        plan,
        handoff_batch=batch,
        handoff_batch_path="handoff.json",
    )
    assert result.valid is True
    assert result.candidate_count == 3
    assert result.boundaries["sql_write_allowed"] is False
    assert result.boundaries["qdrant_write_allowed"] is False
    assert result.boundaries["remote_mutation_allowed"] is False
