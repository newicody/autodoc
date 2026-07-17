from __future__ import annotations

import pytest

from context.love_actions_closed_loop_resolution_0287 import (
    LoveActionsClosedLoopResolutionError,
    LoveProjectV2TargetRequest,
    resolve_love_projectv2_target,
)


def _payload(*, duplicate_item: bool = False, field_name: str = "Statut révision"):
    items = [
        {
            "id": "PVTI_item",
            "project": {"id": "PVT_project", "number": 3},
        }
    ]
    if duplicate_item:
        items.append(
            {
                "id": "PVTI_other",
                "project": {"id": "PVT_project", "number": 3},
            }
        )
    return {
        "data": {
            "repository": {
                "issue": {"id": "I_issue", "projectItems": {"nodes": items}}
            },
            "user": {
                "projectV2": {
                    "id": "PVT_project",
                    "number": 3,
                    "fields": {
                        "nodes": [
                            {"id": "PVTSSF_field", "name": field_name}
                        ]
                    },
                }
            },
            "organization": None,
        }
    }


def _request(**overrides):
    values = {
        "repository": "newicody/projects",
        "issue_number": 42,
        "project_owner": "newicody",
        "project_number": 3,
        "field_name": "Statut révision",
    }
    values.update(overrides)
    return LoveProjectV2TargetRequest(**values)


def test_resolves_item_and_field_from_authoritative_issue_and_project() -> None:
    target = resolve_love_projectv2_target(_request(), _payload())
    assert target.project_id == "PVT_project"
    assert target.project_item_id == "PVTI_item"
    assert target.field_ref == "PVTSSF_field"
    assert target.field_name == "Statut révision"
    assert (
        target.resolution_source
        == "authoritative-request-and-project-config"
    )


def test_exact_overrides_remain_available_for_diagnostics() -> None:
    target = resolve_love_projectv2_target(
        _request(
            project_item_id_override="PVTI_item",
            field_ref_override="PVTSSF_field",
        ),
        _payload(),
    )
    assert target.resolution_source == "explicit-overrides"


def test_rejects_issue_missing_from_configured_project() -> None:
    payload = _payload()
    payload["data"]["repository"]["issue"]["projectItems"]["nodes"] = []
    with pytest.raises(
        LoveActionsClosedLoopResolutionError,
        match="not present exactly once",
    ):
        resolve_love_projectv2_target(_request(), payload)


def test_rejects_ambiguous_item_and_wrong_field() -> None:
    with pytest.raises(
        LoveActionsClosedLoopResolutionError,
        match="multiple matching",
    ):
        resolve_love_projectv2_target(
            _request(), _payload(duplicate_item=True)
        )
    with pytest.raises(
        LoveActionsClosedLoopResolutionError,
        match="field cannot be resolved",
    ):
        resolve_love_projectv2_target(
            _request(), _payload(field_name="Résumé")
        )


def test_override_pair_is_atomic() -> None:
    with pytest.raises(
        LoveActionsClosedLoopResolutionError,
        match="supplied together",
    ):
        _request(project_item_id_override="PVTI_item")
