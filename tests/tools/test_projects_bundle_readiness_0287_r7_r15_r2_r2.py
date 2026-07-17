from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT / "templates/github/projects-repository/scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from projects_bundle_readiness_contract import (  # noqa: E402
    ActionsPolicy,
    CurrentField,
    CurrentView,
    build_readiness_report,
    compare_fields,
    compare_views,
    declared_fields,
    declared_views,
    evaluate_workflow,
)


def _load_cli() -> Any:
    path = SCRIPT_DIR / "check_projects_bundle_readiness.py"
    spec = importlib.util.spec_from_file_location("check_projects_bundle_readiness", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _configuration() -> dict[str, Any]:
    return {
        "schema": "autodoc.github.projects_repository_configuration.v1",
        "project": {"owner_kind": "user", "owner": "newicody", "number": 3},
        "fields": [
            {
                "name": "Thème",
                "data_type": "single_select",
                "options": [
                    {"name": "Général"},
                    {"name": "Architecture"},
                ],
            },
            {"name": "Résumé", "data_type": "text"},
        ],
        "views": [
            {
                "name": "Recherches",
                "layout": "board",
                "filter": "Affichage:Action",
                "visible_fields": ["Title", "Status", "Thème"],
                "manual_layout": {"column_field": "Status", "group_by": "Thème"},
            },
            {
                "name": "Tous",
                "layout": "table",
                "filter": "is:issue",
                "visible_fields": ["Title", "Status"],
            },
        ],
    }


def test_exact_fields_and_views_are_readiness_true() -> None:
    configuration = _configuration()
    fields = compare_fields(
        declared_fields(configuration),
        (
            CurrentField("Thème", "single_select", ("Général", "Architecture")),
            CurrentField("Résumé", "text"),
        ),
    )
    views = compare_views(
        declared_views(configuration),
        (
            CurrentView(
                "Recherches",
                "BOARD_LAYOUT",
                "Affichage:Action",
                ("Title", "Status", "Thème"),
                ("Status",),
                ("Thème",),
            ),
            CurrentView("Tous", "TABLE_LAYOUT", "is:issue", ("Title", "Status")),
        ),
    )
    assert all(item.exact for item in fields)
    assert all(item.exact for item in views)


def test_existing_name_with_wrong_layout_filter_or_fields_is_drift() -> None:
    checks = compare_views(
        declared_views(_configuration()),
        (
            CurrentView(
                "Recherches",
                "TABLE_LAYOUT",
                "",
                ("Title",),
                (),
                (),
            ),
            CurrentView("Tous", "TABLE_LAYOUT", "is:issue", ("Title", "Status")),
        ),
    )
    research = checks[0]
    assert research.exists is True
    assert research.exact is False
    assert "filter differs" in research.drift
    assert "visible fields or their order differ" in research.drift
    assert "board column field differs" in research.drift
    assert "vertical group field differs" in research.drift


def test_field_option_drift_reports_missing_and_unexpected_options() -> None:
    checks = compare_fields(
        declared_fields(_configuration()),
        (
            CurrentField("Thème", "single_select", ("Général", "Obsolète")),
            CurrentField("Résumé", "text"),
        ),
    )
    theme = checks[0]
    assert theme.missing_options == ("Architecture",)
    assert theme.unexpected_options == ("Obsolète",)
    assert theme.exact is False


def test_selected_policy_allows_github_owned_actions_but_copilot_false_is_visible() -> None:
    workflow = evaluate_workflow(
        repository="newicody/projects",
        workflow_name="Autodoc controlled research request",
        workflow_path=".github/workflows/autodoc-controlled-research.yml",
        workflow_state="active",
        workflow_dispatch_present=True,
        automatic_triggers=(),
        required_actions=(
            "actions/checkout@v6",
            "actions/setup-python@v6",
            "actions/cache@v4",
            "actions/upload-artifact@v7",
        ),
        actions_policy=ActionsPolicy(
            enabled=True,
            allowed_actions="selected",
            github_owned_allowed=True,
        ),
        copilot_variable_present=True,
        copilot_enabled=False,
        copilot_permission_declared=True,
        obsolete_copilot_secret_reference=False,
    )
    assert workflow.authoritative_ready is True
    assert workflow.copilot_ready is False
    assert workflow.blocked_actions == ()
    assert "Copilot advisory is explicitly disabled" in workflow.warnings
    assert "manual-dispatch only" in workflow.warnings[0]



def test_copilot_permission_failure_does_not_block_authoritative_path() -> None:
    workflow = evaluate_workflow(
        repository="newicody/projects",
        workflow_name="workflow",
        workflow_path="workflow.yml",
        workflow_state="active",
        workflow_dispatch_present=True,
        automatic_triggers=(),
        required_actions=(),
        actions_policy=ActionsPolicy(enabled=True, allowed_actions="all"),
        copilot_variable_present=True,
        copilot_enabled=True,
        copilot_permission_declared=False,
        obsolete_copilot_secret_reference=False,
    )
    assert workflow.authoritative_ready is True
    assert workflow.copilot_ready is False
    assert "Copilot is enabled but copilot-requests: write is missing" in workflow.warnings


def test_single_select_without_options_is_read_as_empty() -> None:
    cli = _load_cli()
    field = cli._current_field(
        {
            "__typename": "ProjectV2SingleSelectField",
            "name": "Status",
            "options": None,
        }
    )
    assert field == CurrentField("Status", "single_select", ())

def test_sha_pinning_policy_blocks_major_action_references() -> None:
    workflow = evaluate_workflow(
        repository="newicody/projects",
        workflow_name="workflow",
        workflow_path="workflow.yml",
        workflow_state="active",
        workflow_dispatch_present=True,
        automatic_triggers=(),
        required_actions=("actions/checkout@v6",),
        actions_policy=ActionsPolicy(
            enabled=True,
            allowed_actions="selected",
            github_owned_allowed=True,
            sha_pinning_required=True,
        ),
        copilot_variable_present=True,
        copilot_enabled=True,
        copilot_permission_declared=True,
        obsolete_copilot_secret_reference=False,
    )
    assert workflow.authoritative_ready is False
    assert workflow.unpinned_actions == ("actions/checkout@v6",)


class FakeTransport:
    def __init__(self) -> None:
        self.rest_calls: list[str] = []

    def graphql(self, query: str, variables: dict[str, Any]) -> Any:
        assert "groupByFields" in query
        assert variables == {"login": "newicody", "number": 3}
        fields = [
            {
                "__typename": "ProjectV2SingleSelectField",
                "id": "PVTSSF_theme",
                "name": "Thème",
                "options": [
                    {"id": "one", "name": "Général"},
                    {"id": "two", "name": "Architecture"},
                ],
            },
            {
                "__typename": "ProjectV2Field",
                "id": "PVTF_summary",
                "name": "Résumé",
                "dataType": "TEXT",
            },
        ]
        title = {"__typename": "ProjectV2Field", "name": "Title", "dataType": "TITLE"}
        status = {
            "__typename": "ProjectV2SingleSelectField",
            "name": "Status",
            "options": [],
        }
        theme = fields[0]
        return {
            "data": {
                "user": {
                    "projectV2": {
                        "id": "PVT_project",
                        "title": "Autodoc",
                        "number": 3,
                        "fields": {"nodes": fields},
                        "views": {
                            "nodes": [
                                {
                                    "id": "PVTV_research",
                                    "name": "Recherches",
                                    "number": 1,
                                    "layout": "BOARD_LAYOUT",
                                    "filter": "Affichage:Action",
                                    "fields": {"nodes": [title, status, theme]},
                                    "groupByFields": {"nodes": [status]},
                                    "verticalGroupByFields": {"nodes": [theme]},
                                },
                                {
                                    "id": "PVTV_all",
                                    "name": "Tous",
                                    "number": 2,
                                    "layout": "TABLE_LAYOUT",
                                    "filter": "is:issue",
                                    "fields": {"nodes": [title, status]},
                                    "groupByFields": {"nodes": []},
                                    "verticalGroupByFields": {"nodes": []},
                                },
                            ]
                        },
                    }
                }
            }
        }

    def rest(self, endpoint: str) -> Any:
        self.rest_calls.append(endpoint)
        if endpoint.endswith("/actions/permissions"):
            return {
                "enabled": True,
                "allowed_actions": "selected",
                "sha_pinning_required": False,
            }
        if endpoint.endswith("/actions/permissions/selected-actions"):
            return {
                "github_owned_allowed": True,
                "verified_allowed": False,
                "patterns_allowed": [],
            }
        raise AssertionError(endpoint)

    def rest_optional(self, endpoint: str) -> Any | None:
        self.rest_calls.append(endpoint)
        if "/actions/workflows/" in endpoint:
            return {
                "name": "Autodoc controlled research request",
                "path": ".github/workflows/autodoc-controlled-research.yml",
                "state": "active",
            }
        if endpoint.endswith("/actions/variables/AUTODOC_COPILOT_ADVISORY_ENABLED"):
            return {"name": "AUTODOC_COPILOT_ADVISORY_ENABLED", "value": "true"}
        raise AssertionError(endpoint)


def test_cli_build_report_is_read_only_and_exact(tmp_path: Path) -> None:
    cli = _load_cli()
    config = tmp_path / "projectv2_views.json"
    config.write_text(json.dumps(_configuration()), encoding="utf-8")
    workflow = tmp_path / "autodoc-controlled-research.yml"
    workflow.write_text(
        """name: test
on:
  workflow_dispatch:
permissions:
  copilot-requests: write
jobs:
  build:
    steps:
      - uses: actions/checkout@v6
      - uses: actions/setup-python@v6
      - uses: actions/cache@v4
      - uses: actions/upload-artifact@v7
""",
        encoding="utf-8",
    )
    transport = FakeTransport()
    report = cli.build_report(
        configuration_path=config,
        workflow_path=workflow,
        repository="newicody/projects",
        transport=transport,
    )
    assert report.projectv2_exact is True
    assert report.authoritative_ready is True
    assert report.copilot_ready is True
    assert report.full_ready is True
    assert all(call.startswith("repos/") for call in transport.rest_calls)


def test_report_mapping_never_claims_remote_mutation() -> None:
    workflow = evaluate_workflow(
        repository="newicody/projects",
        workflow_name="workflow",
        workflow_path="workflow.yml",
        workflow_state="active",
        workflow_dispatch_present=True,
        automatic_triggers=(),
        required_actions=(),
        actions_policy=ActionsPolicy(enabled=True, allowed_actions="all"),
        copilot_variable_present=True,
        copilot_enabled=True,
        copilot_permission_declared=True,
        obsolete_copilot_secret_reference=False,
    )
    report = build_readiness_report(
        project_owner="newicody",
        project_number=3,
        project_id="PVT_project",
        project_title="Autodoc",
        expected_fields=(),
        current_fields=(),
        expected_views=(),
        current_views=(),
        workflow=workflow,
    )
    mapping = report.to_mapping()
    assert mapping["remote_mutation_allowed"] is False
    assert mapping["mutation_performed"] is False
