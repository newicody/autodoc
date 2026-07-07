from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_github_project_push_frame_config_check.py"


def _config_text(tmp_path: Path) -> str:
    return f"""[github]
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
working_directory = {tmp_path}
python_executable = {sys.executable}
scan_command = tools/run_github_artifact_scan_once.py
state_path = .var/github/artifacts/state/index.json
inbox_dir = .var/github/artifacts/inbox
fcron_table_path = {tmp_path / 'autodoc.fcrontab'}

[safety]
development_repository = newicody/autodoc
allowed_repositories = newicody/autodoc-ideas

[pipeline]
context_option_names = include_current_ticket, include_total_project, include_repository_context
copilot_preliminary_opinion = true
history_mode = append_only
"""


def test_0165_config_check_writes_candidate_without_touching_system_scheduler(tmp_path: Path) -> None:
    config_path = tmp_path / "github_project_push_frame.ini"
    config_path.write_text(_config_text(tmp_path), encoding="utf-8")
    fcrontab_path = tmp_path / "user.fcrontab"
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--config",
            str(config_path),
            "--output-dir",
            str(tmp_path / "out"),
            "--fcrontab-path",
            str(fcrontab_path),
            "--write-fcrontab",
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    report = json.loads(completed.stdout)
    table = fcrontab_path.read_text(encoding="utf-8")
    assert report["status"] == "ok"
    assert report["fcron"]["started_fcron"] is False
    assert report["fcron"]["openrc_touched"] is False
    assert report["fcron"]["idempotent"] is True
    assert table.count("AUTODOC-GITHUB-ARTIFACT-SCAN") == 2
    assert "*/10 * * * *" in table
    assert "tools/run_github_artifact_scan_once.py --config" in table
    completed_again = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--config",
            str(config_path),
            "--output-dir",
            str(tmp_path / "out2"),
            "--fcrontab-path",
            str(fcrontab_path),
            "--write-fcrontab",
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    report_again = json.loads(completed_again.stdout)
    assert report_again["fcron"]["idempotent"] is True
    assert fcrontab_path.read_text(encoding="utf-8").count("AUTODOC-GITHUB-ARTIFACT-SCAN") == 2
