from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys

from context.github_operator_laboratory_advisory_projection_0281 import (
    PUBLICATION_PREVIEW_SCHEMA,
)


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/publish_github_advisory_issue_comment_0281.py"


def _load_tool():
    spec = spec_from_file_location("publish_0281", TOOL)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _preview(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": PUBLICATION_PREVIEW_SCHEMA,
                "source_candidate_ref": "github-request-0123456789abcdef",
                "advisory_context_ref": (
                    "ctx:github-advisory:0123456789abcdef01234567"
                ),
                "advisory_artifact_ref": "github-advisory:abc",
                "summary": "Résumé",
                "suggested_route": "Route",
                "questions": [],
                "risks": [],
                "confidence": 0.5,
                "advisory_is_authority": False,
                "operator_decision_required": True,
                "publication_gate_required": True,
                "github_mutation_performed": False,
            }
        ),
        encoding="utf-8",
    )


def test_preview_mode_lists_comments_but_never_posts(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    tool = _load_tool()
    preview = tmp_path / "preview.json"
    _preview(preview)
    calls = []

    def fake_gh(command, arguments):
        calls.append(tuple(arguments))
        return []

    monkeypatch.setattr(tool, "_gh_json", fake_gh)
    result = tool.main(
        (
            "--repository",
            "newicody/projects",
            "--issue-number",
            "15",
            "--preview",
            str(preview),
            "--policy-decision-id",
            "policy:0281:r6:test",
            "--operator-decision",
            "approve",
            "--format",
            "json",
        )
    )

    assert result == 0
    assert len(calls) == 1
    assert "--method" not in calls[0]
    report = json.loads(capsys.readouterr().out)
    assert report["mode"] == "preview"
    assert report["plan"]["action"] == "create"
    assert report["github_mutation_performed"] is False


def test_execute_requires_exact_plan_digest(
    tmp_path: Path,
    monkeypatch,
) -> None:
    tool = _load_tool()
    preview = tmp_path / "preview.json"
    _preview(preview)
    calls = []

    def fake_gh(command, arguments):
        calls.append(tuple(arguments))
        return []

    monkeypatch.setattr(tool, "_gh_json", fake_gh)
    result = tool.main(
        (
            "--repository",
            "newicody/projects",
            "--issue-number",
            "15",
            "--preview",
            str(preview),
            "--policy-decision-id",
            "policy:0281:r6:test",
            "--operator-decision",
            "approve",
            "--execute",
            "--confirm-plan-digest",
            "wrong",
        )
    )

    assert result == 3
    assert len(calls) == 1


def test_execute_posts_once_after_exact_confirmation(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    tool = _load_tool()
    preview = tmp_path / "preview.json"
    _preview(preview)
    responses = [
        [],
        {
            "id": 99,
            "html_url": (
                "https://github.com/newicody/projects/issues/15"
                "#issuecomment-99"
            ),
        },
    ]
    calls = []

    def fake_gh(command, arguments):
        calls.append(tuple(arguments))
        return responses.pop(0)

    monkeypatch.setattr(tool, "_gh_json", fake_gh)

    # First obtain the deterministic digest in preview mode.
    assert tool.main(
        (
            "--repository",
            "newicody/projects",
            "--issue-number",
            "15",
            "--preview",
            str(preview),
            "--policy-decision-id",
            "policy:0281:r6:test",
            "--operator-decision",
            "approve",
            "--format",
            "json",
        )
    ) == 0
    preview_report = json.loads(capsys.readouterr().out)
    digest = preview_report["plan"]["plan_digest"]

    # Reset responses because the preview consumed the first comment listing.
    responses[:] = [
        [],
        {
            "id": 99,
            "html_url": (
                "https://github.com/newicody/projects/issues/15"
                "#issuecomment-99"
            ),
        },
    ]
    calls.clear()

    result = tool.main(
        (
            "--repository",
            "newicody/projects",
            "--issue-number",
            "15",
            "--preview",
            str(preview),
            "--policy-decision-id",
            "policy:0281:r6:test",
            "--operator-decision",
            "approve",
            "--execute",
            "--confirm-plan-digest",
            digest,
            "--format",
            "json",
        )
    )

    assert result == 0
    assert len(calls) == 2
    assert "--method" in calls[1]
    assert "POST" in calls[1]
    report = json.loads(capsys.readouterr().out)
    assert report["mutation_action"] == "created"
    assert report["github_mutation_performed"] is True
