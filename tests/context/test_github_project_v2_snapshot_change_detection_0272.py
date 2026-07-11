from __future__ import annotations

from copy import deepcopy

import pytest

from context.github_project_v2_query_only_snapshot_0272 import SNAPSHOT_SCHEMA
from context.github_project_v2_snapshot_change_detection_0272 import (
    CHANGE_SET_SCHEMA,
    GitHubProjectV2SnapshotChangeCommand,
    build_snapshot_change_plan,
    build_snapshot_change_set,
    close_snapshot_change_result,
)


def _snapshot(ref: str, *, status: str = "Todo") -> dict:
    return {
        "schema": SNAPSHOT_SCHEMA,
        "snapshot_ref": ref,
        "project": {
            "owner": "newicody",
            "number": 2,
            "id": "PVT_kwHOA3ouXM4Ba3Ar",
            "title": "idea",
            "url": "https://github.com/users/newicody/projects/2",
            "closed": False,
            "view_number_hint": 2,
        },
        "fields": [
            {"id": "status-field", "name": "Status", "dataType": "SINGLE_SELECT"}
        ],
        "items": [
            {
                "id": "item-1",
                "type": "DRAFT_ISSUE",
                "content": {"id": "draft-1", "title": "Idea", "body": "Body"},
                "fieldValues": {
                    "nodes": [
                        {
                            "__typename": "ProjectV2ItemFieldSingleSelectValue",
                            "name": status,
                            "optionId": f"option-{status}",
                            "field": {
                                "id": "status-field",
                                "name": "Status",
                                "dataType": "SINGLE_SELECT",
                            },
                        }
                    ]
                },
            }
        ],
        "counts": {"field_count": 1, "item_count": 1},
        "boundaries": {
            "graphql_mutation_allowed": False,
            "remote_mutation_allowed": False,
        },
    }


def test_baseline_is_valid_and_marks_current_items_unchanged() -> None:
    current = _snapshot("github-project-v2-snapshot:current")
    change_set = build_snapshot_change_set(previous_snapshot=None, current_snapshot=current)
    assert change_set["schema"] == CHANGE_SET_SCHEMA
    assert change_set["baseline"] is True
    assert change_set["counts"]["unchanged_count"] == 1
    assert change_set["counts"]["added_count"] == 0
    assert change_set["boundaries"]["external_call_performed"] is False


def test_detects_added_removed_changed_and_status_transition() -> None:
    previous = _snapshot("github-project-v2-snapshot:previous")
    previous["items"].append(
        {"id": "item-removed", "type": "DRAFT_ISSUE", "content": {"id": "draft-r", "title": "Old"}}
    )
    current = _snapshot("github-project-v2-snapshot:current", status="In progress")
    current["items"].append(
        {"id": "item-added", "type": "DRAFT_ISSUE", "content": {"id": "draft-a", "title": "New"}}
    )
    change_set = build_snapshot_change_set(
        previous_snapshot=previous,
        current_snapshot=current,
    )
    assert change_set["counts"]["added_count"] == 1
    assert change_set["counts"]["removed_count"] == 1
    assert change_set["counts"]["changed_count"] == 1
    assert change_set["counts"]["status_transition_count"] == 1
    changed = change_set["items"]["changed"][0]
    assert changed["status"] == {"before": "Todo", "after": "In progress"}


def test_field_value_order_does_not_create_false_change() -> None:
    previous = _snapshot("github-project-v2-snapshot:previous")
    current = deepcopy(previous)
    current["snapshot_ref"] = "github-project-v2-snapshot:current"
    nodes = current["items"][0]["fieldValues"]["nodes"]
    nodes.append(
        {
            "__typename": "ProjectV2ItemFieldTextValue",
            "text": "A",
            "field": {"id": "text-field", "name": "Note", "dataType": "TEXT"},
        }
    )
    previous["items"][0]["fieldValues"]["nodes"].insert(0, deepcopy(nodes[-1]))
    change_set = build_snapshot_change_set(previous_snapshot=previous, current_snapshot=current)
    assert change_set["counts"]["changed_count"] == 0
    assert change_set["counts"]["unchanged_count"] == 1


def test_different_projects_are_rejected() -> None:
    previous = _snapshot("github-project-v2-snapshot:previous")
    current = _snapshot("github-project-v2-snapshot:current")
    current["project"]["id"] = "PVT_other"
    with pytest.raises(ValueError, match="different projects"):
        build_snapshot_change_set(previous_snapshot=previous, current_snapshot=current)


def test_plan_requires_decision_only_for_execute() -> None:
    plan = build_snapshot_change_plan(
        GitHubProjectV2SnapshotChangeCommand(execute=False),
        previous_snapshot_path="",
        current_snapshot_path="current.json",
    )
    assert plan.valid is True
    execute_plan = build_snapshot_change_plan(
        GitHubProjectV2SnapshotChangeCommand(execute=True),
        previous_snapshot_path="",
        current_snapshot_path="current.json",
    )
    assert execute_plan.valid is False


def test_result_closure_keeps_local_only_boundaries() -> None:
    current = _snapshot("github-project-v2-snapshot:current")
    change_set = build_snapshot_change_set(previous_snapshot=None, current_snapshot=current)
    plan = build_snapshot_change_plan(
        GitHubProjectV2SnapshotChangeCommand(
            execute=True,
            policy_decision_id="policy:0272:changes",
        ),
        previous_snapshot_path="",
        current_snapshot_path="current.json",
    )
    result = close_snapshot_change_result(
        plan,
        change_set=change_set,
        change_set_path="change.json",
    )
    assert result.valid is True
    assert result.external_call_performed is False
    assert result.boundaries["remote_mutation_allowed"] is False
