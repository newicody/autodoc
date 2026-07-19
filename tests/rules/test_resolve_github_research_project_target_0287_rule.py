from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tools import resolve_github_research_project_target_0287 as tool


class FakeAdapter:
    requests = []

    def __init__(self, *, gh_command: str, token_env: str) -> None:
        self.gh_command = gh_command
        self.token_env = token_env

    def resolve_project_target(self, request):
        self.requests.append(request)
        return SimpleNamespace(
            to_mapping=lambda: {
                "project_id": "PVT_project",
                "project_owner": request.project_owner,
                "project_number": request.project_number,
                "project_item_id": "PVTI_issue_15",
                "field_ref": "PVTF_resume",
                "field_name": request.field_name,
                "resolution_source": (
                    "authoritative-request-and-project-config"
                ),
            }
        )


def test_resolution_reuses_existing_adapter_and_returns_exact_target() -> None:
    FakeAdapter.requests.clear()

    result = tool.resolve_project_target_report(
        repository="newicody/projects",
        issue_number=15,
        project_owner="newicody",
        project_number=3,
        field_name="Résumé",
        gh_command="gh",
        token_env="AUTODOC_PROJECT_TOKEN",
        adapter_factory=FakeAdapter,
    )

    assert result["valid"] is True
    assert result["status"] == "resolved"
    assert result["project_item_id"] == "PVTI_issue_15"
    assert result["project_field_ref"] == "PVTF_resume"
    assert result["project_field_name"] == "Résumé"
    assert result["boundaries"]["remote_mutation_performed"] is False
    assert len(FakeAdapter.requests) == 1
    assert FakeAdapter.requests[0].issue_number == 15


def test_cli_shell_output_is_sourceable(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_resolver = tool.resolve_project_target_report
    monkeypatch.setattr(
        tool,
        "resolve_project_target_report",
        lambda **kwargs: original_resolver(
            **kwargs,
            adapter_factory=FakeAdapter,
        ),
    )

    exit_code = tool.main(
        (
            "--repository",
            "newicody/projects",
            "--issue-number",
            "15",
            "--project-owner",
            "newicody",
            "--project-number",
            "3",
            "--field-name",
            "Résumé",
            "--format",
            "shell",
        )
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "PROJECT_ITEM_ID='PVTI_issue_15'" in output
    assert "RESUME_FIELD_ID='PVTF_resume'" in output
    assert "PROJECT_FIELD_NAME='Résumé'" in output


def test_cli_writes_json_report_atomically(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "target.json"
    monkeypatch.setattr(
        tool,
        "resolve_project_target_report",
        lambda **kwargs: {
            "schema": tool.SCHEMA,
            "valid": True,
            "status": "resolved",
            "issues": [],
            "project_item_id": "PVTI_issue_15",
            "project_field_ref": "PVTF_resume",
            "project_field_name": "Résumé",
            "target": {},
            "boundaries": tool._boundaries(),
        },
    )

    exit_code = tool.main(
        (
            "--repository",
            "newicody/projects",
            "--issue-number",
            "15",
            "--project-owner",
            "newicody",
            "--project-number",
            "3",
            "--output",
            str(output),
            "--format",
            "summary",
        )
    )
    payload = json.loads(output.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert payload["project_item_id"] == "PVTI_issue_15"
    assert output.with_suffix(".json.tmp").exists() is False


def test_partial_overrides_are_rejected_before_remote_read() -> None:
    with pytest.raises(
        ValueError,
        match="overrides must be supplied together",
    ):
        tool.resolve_project_target_report(
            repository="newicody/projects",
            issue_number=15,
            project_owner="newicody",
            project_number=3,
            field_name="Résumé",
            project_item_id_override="PVTI_issue_15",
            field_ref_override="",
            adapter_factory=FakeAdapter,
        )


def test_tool_creates_no_second_transport_or_mutation_surface() -> None:
    source = Path(tool.__file__).read_text(encoding="utf-8")

    assert "GitHubCliFinalDeliverablePublicationAdapter" in source
    assert "] = GitHubCliFinalDeliverablePublicationAdapter" in source
    assert "adapter = adapter_factory(" in source
    assert "LoveProjectV2TargetRequest(" in source
    assert "resolve_project_target(request)" in source

    for forbidden in (
        "subprocess.run(",
        "requests.",
        "updateProjectV2ItemFieldValue",
        "create_comment(",
        "update_field(",
        "Scheduler(",
        "psycopg.connect(",
        "QdrantClient(",
    ):
        assert forbidden not in source
