from __future__ import annotations

from pathlib import Path

import pytest

from context.github_project_push_frame import (
    CopilotPreliminaryOpinionArtifact,
    ProjectPushContextOptions,
    build_project_push_frame_from_ticket_payload,
    validate_copilot_preliminary_opinion,
)
from context.github_project_push_frame_config import (
    build_fcron_entry,
    build_fcron_marker,
    load_github_artifact_scan_config,
    upsert_fcron_table,
)


def _config_text() -> str:
    return """[github]
token_env = GITHUB_TOKEN
api_url = https://api.github.com

[project]
url = https://github.com/users/newicody/projects/2
owner = newicody
number = 2

[artifact_source]
repositories = newicody/autodoc-ideas
workflow_name = autodoc-ticket-artifact.yml
artifact_name_prefix = autodoc-ticket-artifact-
trigger_source = github_action_on_ticket_event

[scan]
mode = fcron
interval_minutes = 10
working_directory = /home/eric/projet/git/autodoc
python_executable = /home/eric/python/bin/python
scan_command = tools/run_github_artifact_scan_once.py
state_path = .var/github/artifacts/state/index.json
inbox_dir = .var/github/artifacts/inbox
fcron_table_path = .var/fcron/autodoc-github-artifact-scan.fcrontab

[safety]
development_repository = newicody/autodoc
allowed_repositories = newicody/autodoc-ideas

[pipeline]
context_option_names = include_current_ticket, include_total_project, include_repository_context
copilot_preliminary_opinion = true
history_mode = append_only
"""


def test_0165_loads_configobj_style_config_without_secret_literal(tmp_path: Path) -> None:
    path = tmp_path / "github_project_push_frame.ini"
    path.write_text(_config_text(), encoding="utf-8")
    config = load_github_artifact_scan_config(path)
    assert config.token_env == "GITHUB_TOKEN"
    assert config.external_repository == "newicody/autodoc-ideas"
    assert config.development_repository == "newicody/autodoc"
    assert config.scan_mode == "fcron"
    assert config.interval_minutes == 10
    assert config.copilot_preliminary_opinion is True
    assert "include_repository_context" in config.context_option_names


def test_0165_rejects_development_repository_as_external_source(tmp_path: Path) -> None:
    path = tmp_path / "bad.ini"
    path.write_text(_config_text().replace("repositories = newicody/autodoc-ideas", "repositories = newicody/autodoc"), encoding="utf-8")
    with pytest.raises(ValueError, match="development_repo_ingestion"):
        load_github_artifact_scan_config(path)


def test_0165_rejects_secret_keys_in_config(tmp_path: Path) -> None:
    path = tmp_path / "bad_secret.ini"
    path.write_text(_config_text() + "\n[bad]\nsecret = ghp_not_allowed\n", encoding="utf-8")
    with pytest.raises(ValueError, match="secret_literal_forbidden"):
        load_github_artifact_scan_config(path)


def test_0165_fcron_entry_upsert_is_idempotent_and_has_no_duplicate(tmp_path: Path) -> None:
    path = tmp_path / "github_project_push_frame.ini"
    path.write_text(_config_text(), encoding="utf-8")
    config = load_github_artifact_scan_config(path)
    entry = build_fcron_entry(config)
    marker = build_fcron_marker(config)
    first = upsert_fcron_table("MAILTO=eric\n", entry, marker)
    second = upsert_fcron_table(first, entry, marker)
    assert first == second
    assert second.count(f"# BEGIN {marker}") == 1
    assert second.count(f"# END {marker}") == 1
    assert "*/10 * * * * cd /home/eric/projet/git/autodoc" in second
    assert "tools/run_github_artifact_scan_once.py --config" in second


def test_0165_project_push_frame_from_ticket_payload_is_minimal() -> None:
    frame = build_project_push_frame_from_ticket_payload(
        {
            "repository": "newicody/autodoc-ideas",
            "project": {"url": "https://github.com/users/newicody/projects/2"},
            "ticket": {"kind": "issue", "number": 42, "title": "Investigate idea", "url": "https://github.com/newicody/autodoc-ideas/issues/42"},
            "workflow": {"column_name": "Backlog"},
            "context_options": {"include_current_ticket": True, "include_total_project": True, "include_repository_context": True},
        }
    )
    payload = frame.to_json_dict()
    assert payload["origin_frame_id"] == "github-frame:newicody/autodoc-ideas/issues/42"
    assert payload["workflow"]["column_name"] == "Backlog"
    assert payload["context_options"]["include_total_project"] is True
    assert payload["context_options"]["include_repository_context"] is True


def test_0165_copilot_preliminary_opinion_is_advisory_only() -> None:
    opinion = CopilotPreliminaryOpinionArtifact(
        origin_frame_id="github-frame:newicody/autodoc-ideas/issues/42",
        ticket_revision_id="github-ticket-revision:abc",
        artifact_ref="github-artifact:copilot:abc",
        summary="first orientation",
        suggested_route="architecture_review",
        confidence=0.25,
        risks=("needs local validation",),
    )
    validation = validate_copilot_preliminary_opinion(opinion)
    payload = opinion.to_json_dict()
    assert validation["allowed"] is True
    assert payload["server_use_policy"]["usable_as_hint"] is True
    assert payload["server_use_policy"]["usable_as_authority"] is False


def test_0165_context_options_default_to_current_ticket_only() -> None:
    options = ProjectPushContextOptions()
    assert options.to_json_dict()["include_current_ticket"] is True
    assert options.to_json_dict()["include_total_project"] is False
