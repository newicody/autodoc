from __future__ import annotations

import json
from pathlib import Path

import pytest

from context.source_candidate_projection_preview import (
    SourceCandidateProjectionPreviewPolicy,
    build_source_candidate_projection_preview,
    read_operator_report,
    write_source_candidate_projection_preview,
)


def _report() -> dict[str, object]:
    return {
        "schema": "missipy.source_candidate.operator_report.v1",
        "items": [
            {
                "candidate_id": "candidate-a",
                "title": "Inspect this",
                "status": "new",
                "decision_summary": {"action": "inspect", "reason": "needs review"},
                "audit_present": False,
            },
            {
                "candidate_id": "candidate-b",
                "title": "Already archived",
                "status": "archived",
                "decision_summary": {"action": "archive", "reason": "done"},
                "audit_present": True,
            },
        ],
    }


def test_projection_preview_filters_terminal_items_by_default() -> None:
    preview = build_source_candidate_projection_preview(_report())

    assert preview.item_count == 1
    assert preview.source_report_schema == "missipy.source_candidate.operator_report.v1"
    assert preview.items[0].candidate_id == "candidate-a"
    assert preview.items[0].recommended_action == "inspect"
    assert preview.items[0].labels == ("status:new", "decision:inspect", "audit:missing")


def test_projection_preview_can_include_terminal_items() -> None:
    preview = build_source_candidate_projection_preview(
        _report(),
        SourceCandidateProjectionPreviewPolicy(include_terminal=True),
    )

    assert preview.item_count == 2
    assert preview.items[1].recommended_action == "none"


def test_projection_preview_limit_is_stable() -> None:
    preview = build_source_candidate_projection_preview(
        _report(),
        SourceCandidateProjectionPreviewPolicy(max_items=1, include_terminal=True),
    )

    assert preview.item_count == 1
    assert [item.candidate_id for item in preview.items] == ["candidate-a"]


def test_projection_preview_rejects_invalid_policy() -> None:
    with pytest.raises(ValueError, match="max_items"):
        build_source_candidate_projection_preview(
            _report(),
            SourceCandidateProjectionPreviewPolicy(max_items=0),
        )


def test_projection_preview_writes_atomically(tmp_path: Path) -> None:
    path = tmp_path / "projection" / "preview.json"
    preview = build_source_candidate_projection_preview(_report())

    returned = write_source_candidate_projection_preview(path, preview)
    reloaded = json.loads(path.read_text(encoding="utf-8"))

    assert returned == path
    assert reloaded["schema"] == "missipy.source_candidate.projection_preview.v1"
    assert reloaded["item_count"] == 1


def test_read_operator_report_requires_object(tmp_path: Path) -> None:
    path = tmp_path / "report.json"
    path.write_text("[]\n", encoding="utf-8")

    with pytest.raises(ValueError, match="JSON object"):
        read_operator_report(path)
