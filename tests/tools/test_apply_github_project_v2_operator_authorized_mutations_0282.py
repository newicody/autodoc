from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/apply_github_project_v2_operator_authorized_mutations_0282.py"
SPEC = importlib.util.spec_from_file_location("operator_adapter_0282", TOOL)
assert SPEC is not None and SPEC.loader is not None
subject = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(subject)


def _parent_plan(action="create_and_link"):
    operations = []
    if action == "create_and_link":
        operations = [
            {
                "kind": "create_issue",
                "operation_ref": "github-project-v2-operation:create",
                "repository": "newicody/projects",
                "target_ref": "github-planned-issue:abc",
                "title": "Cycle 2",
                "body": "body",
            },
            {
                "kind": "add_sub_issue",
                "operation_ref": "github-project-v2-operation:link",
                "repository": "newicody/projects",
                "parent_issue_ref": "github-frame:newicody/projects/issues/15",
                "child_issue_ref": "github-planned-issue:abc",
            },
        ]
    elif action == "link_existing":
        operations = [
            {
                "kind": "add_sub_issue",
                "operation_ref": "github-project-v2-operation:link",
                "repository": "newicody/projects",
                "parent_issue_ref": "github-frame:newicody/projects/issues/15",
                "child_issue_ref": "github-frame:newicody/projects/issues/16",
            }
        ]
    return {
        "schema": subject.PARENT_PLAN_SCHEMA,
        "valid": True,
        "action": action,
        "plan_digest": "a" * 64,
        "operations": operations,
        "boundaries": {
            "github_mutation_performed": False,
            "scheduler_modified": False,
        },
    }


def _theme_plan(action="create_field"):
    return {
        "schema": subject.THEME_PLAN_SCHEMA,
        "valid": True,
        "action": action,
        "plan_digest": "b" * 64,
        "field_id": "",
        "operations": [
            {
                "operation_kind": "field_create",
                "endpoint_or_mutation": "POST /users/newicody/projectsV2/3/fields",
                "payload": {
                    "name": "Thème",
                    "data_type": "single_select",
                    "single_select_options": [
                        {"name": "Général", "color": "BLUE", "description": ""}
                    ],
                    "api_version": "2026-03-10",
                },
                "requires_operator_authorization": True,
                "execution_allowed": False,
            },
            {
                "operation_kind": "item_theme_assignment",
                "endpoint_or_mutation": "mutation updateProjectV2ItemFieldValue",
                "payload": {
                    "projectId": "PVT_project",
                    "itemRef": "github-project-v2-item:PVTI_15",
                    "fieldId": "",
                    "themeName": "Général",
                    "singleSelectOptionId": "",
                },
                "requires_operator_authorization": True,
                "execution_allowed": False,
            },
        ],
        "operator_steps": ["Group view manually"],
        "boundaries": {
            "github_mutation_performed": False,
            "scheduler_modified": False,
        },
    }


def test_preview_mode_does_not_call_gh(tmp_path, monkeypatch, capsys):
    path = tmp_path / "parent.json"
    path.write_text(json.dumps(_parent_plan("replay")), encoding="utf-8")
    monkeypatch.setattr(subject, "_gh_json", lambda *a, **k: pytest.fail("gh called"))
    assert subject.main([
        "--parent-plan", str(path),
        "--operator-decision", "approve",
        "--format", "json",
    ]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["mode"] == "preview"
    assert report["github_mutation_performed"] is False


def test_execute_requires_exact_digest(tmp_path, capsys):
    path = tmp_path / "parent.json"
    path.write_text(json.dumps(_parent_plan("replay")), encoding="utf-8")
    assert subject.main([
        "--parent-plan", str(path),
        "--operator-decision", "approve",
        "--execute",
        "--confirm-parent-plan-digest", "wrong",
        "--format", "json",
    ]) == 3
    report = json.loads(capsys.readouterr().out)
    assert "mismatch" in report["execution_error"]


def test_create_and_link_resolves_created_issue(monkeypatch):
    calls = []
    def fake_gh(command, arguments, input_payload=None):
        calls.append((arguments, input_payload))
        if "repos/newicody/projects/issues" in arguments:
            return {"node_id": "I_child", "number": 16, "html_url": "url"}
        if "repos/newicody/projects/issues/15" in arguments:
            return {"node_id": "I_parent", "number": 15}
        if "graphql" in arguments:
            return {"data": {"addSubIssue": {"issue": {"id": "I_parent"}, "subIssue": {"id": "I_child"}}}}
        raise AssertionError(arguments)
    monkeypatch.setattr(subject, "_gh_json", fake_gh)
    results = subject._execute_parent_plan("gh", _parent_plan())
    assert [r["operation_kind"] for r in results] == ["create_issue", "add_sub_issue"]
    graphql_payload = calls[-1][1]
    assert graphql_payload["variables"]["input"] == {"issueId": "I_parent", "subIssueId": "I_child"}


def test_link_existing_resolves_both_node_ids(monkeypatch):
    def fake_gh(command, arguments, input_payload=None):
        joined = " ".join(arguments)
        if "issues/15" in joined:
            return {"node_id": "I_parent"}
        if "issues/16" in joined:
            return {"node_id": "I_child"}
        return {"data": {"addSubIssue": {}}}
    monkeypatch.setattr(subject, "_gh_json", fake_gh)
    results = subject._execute_parent_plan("gh", _parent_plan("link_existing"))
    assert results[0]["parent_node_id"] == "I_parent"
    assert results[0]["child_node_id"] == "I_child"


def test_theme_create_resolves_field_and_option_for_assignment(monkeypatch):
    calls = []
    def fake_gh(command, arguments, input_payload=None):
        calls.append((arguments, input_payload))
        if "users/newicody/projectsV2/3/fields" in arguments:
            return {
                "node_id": "PVTF_theme",
                "options": [{"id": "opt_general", "name": {"raw": "Général"}}],
            }
        return {"data": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "PVTI_15"}}}}
    monkeypatch.setattr(subject, "_gh_json", fake_gh)
    results = subject._execute_theme_plan("gh", _theme_plan())
    assert results[0]["field_id"] == "PVTF_theme"
    assert results[1]["single_select_option_id"] == "opt_general"
    mutation_input = calls[-1][1]["variables"]["input"]
    assert mutation_input["itemId"] == "PVTI_15"
    assert mutation_input["value"] == {"singleSelectOptionId": "opt_general"}


def test_graphql_errors_are_blocking(monkeypatch):
    monkeypatch.setattr(subject, "_gh_json", lambda *a, **k: {"errors": [{"message": "denied"}]})
    with pytest.raises(RuntimeError, match="GraphQL errors"):
        subject._gh_graphql("gh", "query", {"input": {}})


def test_invalid_or_collision_plans_are_refused():
    plan = _parent_plan()
    plan["valid"] = False
    plan["action"] = "collision"
    assert subject._validate_parent_plan(plan)


def test_subprocess_boundary_never_uses_shell(monkeypatch):
    observed = {}
    class Completed:
        returncode = 0
        stdout = "{}"
        stderr = ""
    def fake_run(args, **kwargs):
        observed.update(kwargs)
        assert isinstance(args, list)
        return Completed()
    monkeypatch.setattr(subject.subprocess, "run", fake_run)
    subject._gh_json("gh", ["api", "rate_limit"])
    assert "shell" not in observed
