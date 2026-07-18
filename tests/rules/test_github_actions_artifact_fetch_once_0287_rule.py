from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/run_github_actions_artifact_fetch_once_0287.py"


def test_r16_r4_r3_r3_r1_fetch_is_canonical_and_non_mutating() -> None:
    text = TOOL.read_text(encoding="utf-8")
    for marker in (
        "run_github_actions_artifact_scan_once_live_0272.py",
        "projects_repository_owns_initial_copilot_comment",
        '"local_initial_copilot_comment_publication": False',
        '"remote_issue_mutation_allowed": False',
        "fcntl.LOCK_EX | fcntl.LOCK_NB",
        'status = "artifacts-fetched"',
    ):
        assert marker in text

    for forbidden in (
        "run_github_actions_ready_run_copilot_issue_publication_once_0287.py",
        "AUTODOC_REMOTE_MUTATION_ALLOWED",
        "AUTODOC_ISSUE_PUBLICATION_ALLOWED",
        "issues: write",
        "Scheduler.run(",
        "LaboratoryManager",
        "while True",
        "time.sleep(",
    ):
        assert forbidden not in text


def test_r16_r4_r3_r3_r1_execute_fetches_without_issue_mutation_gates(
    tmp_path: Path,
) -> None:
    project_config = tmp_path / "project.ini"
    fetch_config = tmp_path / "fetch.ini"
    project_config.write_text("[project]\nurl=x\n", encoding="utf-8")
    fetch_config.write_text("[server_dataset]\nroot=x\n", encoding="utf-8")

    scan = tmp_path / "scan.py"
    scan.write_text(
        """#!/usr/bin/env python3
import argparse, json
p=argparse.ArgumentParser()
p.add_argument('--project-config'); p.add_argument('--fetch-config')
p.add_argument('--policy-decision-id'); p.add_argument('--max-runs')
p.add_argument('--max-artifacts'); p.add_argument('--format')
p.add_argument('--execute', action='store_true')
a=p.parse_args()
print(json.dumps({
    'schema':'missipy.github_actions.artifact_scan_once_live.v1',
    'valid':True,
    'status':'completed',
    'counts':{'ready_run_count':1},
    'ready_runs':[{'run_id':'29622831972'}],
    'execute':a.execute,
}))
""",
        encoding="utf-8",
    )

    env = dict(os.environ)
    env.pop("AUTODOC_REMOTE_MUTATION_ALLOWED", None)
    env.pop("AUTODOC_ISSUE_PUBLICATION_ALLOWED", None)

    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--project-config",
            str(project_config),
            "--fetch-config",
            str(fetch_config),
            "--report-root",
            str(tmp_path / "reports"),
            "--lock-path",
            str(tmp_path / "cycle.lock"),
            "--scan-tool",
            str(scan),
            "--policy-decision-id",
            "policy:test:r16-r4-r3-r3-r1",
            "--execute",
            "--format",
            "json",
        ],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["schema"] == "missipy.github_actions.artifact_fetch_cycle_once.v1"
    assert report["valid"] is True
    assert report["status"] == "artifacts-fetched"
    assert report["counts"]["ready_run_count"] == 1
    assert report["ready_runs"][0]["run_id"] == "29622831972"
    assert report["boundaries"]["projects_repository_owns_initial_copilot_comment"] is True
    assert report["boundaries"]["local_initial_copilot_comment_publication"] is False
    assert report["boundaries"]["remote_issue_mutation_allowed"] is False
    assert Path(report["reports"]["cycle"]).is_file()
