from dataclasses import replace

from context.github_project_system_deployment_readiness_0272 import (
    GitHubProjectSystemReadinessCommand,
    GitHubProjectSystemReadinessConfig,
    analyze_workflow,
    build_plan,
    close_result,
)

WORKFLOW = """name: autodoc-ticket-artifact
on:
  issues:
    types: [opened]
permissions:
  contents: read
  issues: read
  actions: read
jobs:
  build:
    steps:
      - run: python scripts/build_autodoc_ticket_artifact.py
      - uses: actions/upload-artifact@v4
"""


def config() -> GitHubProjectSystemReadinessConfig:
    return GitHubProjectSystemReadinessConfig(
        config_path="config/example.ini", token_env="GITHUB_TOKEN",
        api_url="https://api.github.com", graphql_url="https://api.github.com/graphql",
        project_owner="newicody", project_number=2,
        project_id="PVT_kwHOA3ouXM4Ba3Ar",
        project_url="https://github.com/users/newicody/projects/2",
        workflow_repository="newicody/autodoc-ideas",
        workflow_name="autodoc-ticket-artifact.yml",
        workflow_path=".github/workflows/autodoc-ticket-artifact.yml",
        workflow_template_path="templates/github/autodoc-ticket-artifact.yml",
        builder_path="scripts/build_autodoc_ticket_artifact.py",
        builder_template_path="templates/github/scripts/build_autodoc_ticket_artifact.py",
        snapshot_tool_path="tools/run_github_project_v2_query_only_snapshot_0272.py",
        change_detection_tool_path="tools/detect_github_project_v2_snapshot_changes_0272.py",
        snapshot_dir=".var/github/project_v2/snapshots", report_dir=".var/reports",
        require_actions_deployment=True, query_only=True,
        graphql_mutation_allowed=False, remote_mutation_allowed=False,
    )


def test_workflow_policy_accepts_read_only_template() -> None:
    analysis = analyze_workflow(WORKFLOW, expected_builder_path="scripts/build_autodoc_ticket_artifact.py")
    assert analysis.valid
    assert not analysis.has_workflow_dispatch
    assert not analysis.has_write_permission


def test_workflow_policy_rejects_dispatch_and_write() -> None:
    text = WORKFLOW + "\nworkflow_dispatch:\npermissions:\n  contents: write\n"
    analysis = analyze_workflow(text, expected_builder_path="scripts/build_autodoc_ticket_artifact.py")
    assert not analysis.valid
    assert analysis.has_workflow_dispatch
    assert analysis.has_write_permission


def test_fixture_closes_green_readiness() -> None:
    analysis = analyze_workflow(WORKFLOW, expected_builder_path="scripts/build_autodoc_ticket_artifact.py")
    plan = build_plan(config(), GitHubProjectSystemReadinessCommand(True, "policy:test", True),
                      local_checks={
                          "config": True,
                          "snapshot_tool": True,
                          "change_detection_tool": True,
                          "snapshot_dir_parent": True,
                          "report_dir_parent": True,
                          "workflow_template": True,
                          "builder_template": True,
                      },
                      local_workflow_analysis=analysis, token_present=False)
    result = close_result(
        plan,
        project_payload={"id": config().project_id, "number": 2, "url": config().project_url},
        workflow_payload={"state": "active", "path": config().workflow_path},
        remote_workflow_analysis=analysis,
        local_builder_sha256="abc", remote_builder_sha256="abc",
    )
    assert result.valid
    assert result.system_ready
    assert not result.installation_performed
    assert not result.deployment_performed


def test_project_native_mode_is_ready_without_actions_bridge() -> None:
    native = replace(config(), require_actions_deployment=False)
    analysis = analyze_workflow(
        WORKFLOW,
        expected_builder_path="scripts/build_autodoc_ticket_artifact.py",
    )
    local_checks = {
        "config": True,
        "snapshot_tool": True,
        "change_detection_tool": True,
        "snapshot_dir_parent": True,
        "report_dir_parent": True,
        "workflow_template": False,
        "builder_template": False,
    }
    plan = build_plan(
        native,
        GitHubProjectSystemReadinessCommand(True, "policy:project-native", True),
        local_checks=local_checks,
        local_workflow_analysis=analysis,
        token_present=False,
    )
    result = close_result(
        plan,
        project_payload={"id": native.project_id, "number": 2, "url": native.project_url},
    )
    assert result.valid is True
    assert result.project_read_ready is True
    assert result.actions_deployment_ready is False
    assert result.system_ready is True
    assert result.details["actions_bridge_optional"] is True
