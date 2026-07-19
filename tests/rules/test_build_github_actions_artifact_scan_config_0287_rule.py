from __future__ import annotations

from pathlib import Path

from context.github_actions_artifact_scan_once_live_0272 import (
    GitHubActionsArtifactScanCommand,
    GitHubActionsArtifactScanSnapshot,
    build_github_actions_artifact_scan_plan,
)
from context.github_artifact_server_fetch_config import (
    load_github_artifact_server_fetch_config,
)
from context.github_project_push_frame_config import (
    load_github_artifact_scan_config,
)
from tools import build_github_actions_artifact_scan_config_0287 as tool


def _project_config(path: Path) -> None:
    path.write_text(
        """
[github]
token_env = GITHUB_TOKEN
api_url = https://api.github.com

[project]
url = https://github.com/users/newicody/projects/3
owner = newicody
number = 3

[artifact_source]
repositories = newicody/projects
workflow_name = autodoc-controlled-research.yml
artifact_name_prefix = autodoc-
trigger_source = github_action_on_ticket_event

[scan]
mode = fcron
interval_minutes = 10
working_directory = /home/eric/projet/git/autodoc
python_executable = /home/eric/python/bin/python
scan_command = tools/run_github_project_v2_query_only_snapshot_0272.py --execute --policy-decision-id policy:test
state_path = .var/github/project_v2/state/index.json
inbox_dir = .var/github/project_v2/snapshots
fcron_table_path = .var/fcron/project-v2.fcrontab

[safety]
development_repository = newicody/autodoc
allowed_repositories = newicody/projects
read_only_scan = true
allow_workflow_dispatch = false
allow_remote_mutation = false
allow_sql_write = false
allow_qdrant_write = false

[pipeline]
context_option_names = include_current_ticket, include_total_project
copilot_preliminary_opinion = true
history_mode = append_only
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _fetch_config(path: Path, *, workflow: str = "autodoc-controlled-research.yml") -> None:
    path.write_text(
        f"""
[github]
token_env = GITHUB_TOKEN
api_url = https://api.github.com

[project]
url = https://github.com/users/newicody/projects/3
owner = newicody
number = 3

[artifact_source]
repositories = newicody/projects
workflow_name = {workflow}
artifact_name_prefix = autod-
trigger_source = github_action_on_ticket_event

[server_dataset]
root = .var/server_datasets/github_artifacts
raw_dir = raw
index_dir = index
history_dir = history
conversion_queue_dir = conversion_queue
converted_dir = converted
vispy_events_dir = vispy_events
state_file = index/fetch_state.json

[attachments]
allowed_kinds = image, audio, video, pdf, archive, text, binary
max_attachment_bytes = 524288000

[conversion]
queue_after_complete_sync = true
skip_already_processed = true

[safety]
development_repository = newicody/autodoc
allowed_repositories = newicody/projects
read_only_fetch = true
allow_workflow_dispatch = false
allow_remote_mutation = false
allow_sql_write = false
allow_qdrant_write = false
""".replace("artifact_name_prefix = autod-", "artifact_name_prefix = autodoc-").strip()
        + "\n",
        encoding="utf-8",
    )


def _snapshot(project, fetch):
    return GitHubActionsArtifactScanSnapshot(
        project_config_path=str(project.config_path),
        fetch_config_path=str(fetch.config_path),
        repository=project.external_repository,
        fetch_repository=fetch.external_repository,
        development_repository=project.development_repository,
        fetch_development_repository=fetch.development_repository,
        project_url=project.project_url,
        fetch_project_url=fetch.project_url,
        workflow_name=project.workflow_name,
        fetch_workflow_name=fetch.workflow_name,
        artifact_name_prefix=project.artifact_name_prefix,
        fetch_artifact_name_prefix=fetch.artifact_name_prefix,
        token_env=project.token_env,
        fetch_token_env=fetch.token_env,
        api_url=project.api_url,
        fetch_api_url=fetch.api_url,
        allowed_repositories=project.allowed_repositories,
        fetch_allowed_repositories=fetch.allowed_repositories,
        scan_command=project.scan_command,
        history_mode=project.history_mode,
        dataset_root=str(fetch.dataset.root),
        dataset_state_path=str(fetch.dataset.state_path),
        read_only_scan=True,
        read_only_fetch=True,
        allow_workflow_dispatch=False,
        allow_remote_mutation=False,
        allow_sql_write=False,
        allow_qdrant_write=False,
    )


def test_builder_preserves_source_and_writes_accepted_dedicated_config(
    tmp_path: Path,
) -> None:
    project_path = tmp_path / "project.ini"
    fetch_path = tmp_path / "fetch.ini"
    output = tmp_path / "artifact-scan.ini"
    _project_config(project_path)
    _fetch_config(fetch_path)
    original = project_path.read_text(encoding="utf-8")

    result = tool.build_artifact_scan_config_report(
        project_config=project_path,
        fetch_config=fetch_path,
        output=output,
        working_directory=tmp_path,
        python_executable="/home/eric/python/bin/python",
        execute=True,
    )

    assert result["valid"] is True
    assert result["status"] == "written"
    assert output.is_file()
    assert project_path.read_text(encoding="utf-8") == original

    project = load_github_artifact_scan_config(output)
    fetch = load_github_artifact_server_fetch_config(fetch_path)
    plan = build_github_actions_artifact_scan_plan(
        _snapshot(project, fetch),
        GitHubActionsArtifactScanCommand(
            execute=True,
            policy_decision_id="policy:test:artifact-scan",
        ),
    )

    assert plan.valid is True
    assert project.scan_command == (
        "tools/run_github_actions_artifact_scan_once_live_0272.py"
    )
    assert project.history_mode == "append_only"
    assert result["boundaries"]["source_configs_modified"] is False
    assert result["boundaries"]["token_value_read"] is False


def test_plan_mode_does_not_write(tmp_path: Path) -> None:
    project_path = tmp_path / "project.ini"
    fetch_path = tmp_path / "fetch.ini"
    output = tmp_path / "artifact-scan.ini"
    _project_config(project_path)
    _fetch_config(fetch_path)

    result = tool.build_artifact_scan_config_report(
        project_config=project_path,
        fetch_config=fetch_path,
        output=output,
        working_directory=tmp_path,
        python_executable="python",
        execute=False,
    )

    assert result["valid"] is True
    assert result["status"] == "plan-complete"
    assert output.exists() is False
    assert result["boundaries"]["local_config_write_performed"] is False


def test_alignment_mismatch_is_blocked(tmp_path: Path) -> None:
    project_path = tmp_path / "project.ini"
    fetch_path = tmp_path / "fetch.ini"
    output = tmp_path / "artifact-scan.ini"
    _project_config(project_path)
    _fetch_config(fetch_path, workflow="another-workflow.yml")

    result = tool.build_artifact_scan_config_report(
        project_config=project_path,
        fetch_config=fetch_path,
        output=output,
        working_directory=tmp_path,
        python_executable="python",
        execute=True,
    )

    assert result["valid"] is False
    assert result["status"] == "blocked"
    assert output.exists() is False
    assert (
        "workflow_name mismatch between project and fetch configs"
        in result["issues"]
    )


def test_example_and_tool_keep_scan_boundaries() -> None:
    root = Path(__file__).resolve().parents[2]
    source = Path(tool.__file__).read_text(encoding="utf-8")
    example = (
        root / "config/github_actions_artifact_scan.example.ini"
    ).read_text(encoding="utf-8")

    assert (
        "scan_command = "
        "tools/run_github_actions_artifact_scan_once_live_0272.py"
        in example
    )
    assert "history_mode = append_only" in example
    assert "allow_remote_mutation = false" in example
    assert "allow_sql_write = false" in example
    assert "allow_qdrant_write = false" in example

    for forbidden in (
        "subprocess.run(",
        "requests.",
        "psycopg.connect(",
        "QdrantClient(",
        "Scheduler(",
        "gh auth token",
    ):
        assert forbidden not in source
