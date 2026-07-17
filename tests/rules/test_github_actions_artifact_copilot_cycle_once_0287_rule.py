from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/run_github_actions_artifact_copilot_cycle_once_0287.py"


def test_r16_r4_r3_reuses_two_existing_one_shot_tools_without_new_loop() -> None:
    text = TOOL.read_text(encoding="utf-8")
    for marker in (
        "run_github_actions_artifact_scan_once_live_0272.py",
        "run_github_actions_ready_run_copilot_issue_publication_once_0287.py",
        "fcntl.LOCK_EX | fcntl.LOCK_NB",
        "AUTODOC_REMOTE_MUTATION_ALLOWED",
        "AUTODOC_ISSUE_PUBLICATION_ALLOWED",
        "fcron_remains_external_process_authority",
        "polling_loop_added",
        "scheduler_modified",
    ):
        assert marker in text
    for forbidden in (
        "while True",
        "time.sleep(",
        "Scheduler.run(",
        "LaboratoryManager",
        "gh run download",
        "issues: write",
    ):
        assert forbidden not in text


def test_r16_r4_r3_execute_chains_scan_then_publication(tmp_path: Path) -> None:
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
  'kind':'result',
  'counts':{'ready_run_count':1},
  'ready_runs':[{'run_id':'9001'}],
  'execute':a.execute
}))
""",
        encoding="utf-8",
    )
    publisher = tmp_path / "publisher.py"
    publisher.write_text(
        """#!/usr/bin/env python3
import argparse, json
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--scan-report'); p.add_argument('--dataset-root')
p.add_argument('--state-path'); p.add_argument('--policy-decision-id')
p.add_argument('--operator-decision'); p.add_argument('--max-runs')
p.add_argument('--run-id', action='append', default=[])
p.add_argument('--format'); p.add_argument('--execute', action='store_true')
a=p.parse_args()
scan=json.loads(Path(a.scan_report).read_text())
assert scan['ready_runs'][0]['run_id']=='9001'
print(json.dumps({
  'schema':'missipy.github_actions.ready_run_copilot_issue_publication_once.v1',
  'valid':True,
  'counts':{
    'candidate_count':1, 'created_count':1,
    'replayed_count':0, 'failed_count':0
  },
  'execute':a.execute
}))
""",
        encoding="utf-8",
    )

    env = dict(os.environ)
    env.update(
        {
            "AUTODOC_REMOTE_MUTATION_ALLOWED": "true",
            "AUTODOC_ISSUE_PUBLICATION_ALLOWED": "true",
        }
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--project-config",
            str(project_config),
            "--fetch-config",
            str(fetch_config),
            "--dataset-root",
            str(tmp_path / "dataset"),
            "--publication-state-path",
            str(tmp_path / "publication-state.json"),
            "--report-root",
            str(tmp_path / "reports"),
            "--lock-path",
            str(tmp_path / "cycle.lock"),
            "--scan-tool",
            str(scan),
            "--publication-tool",
            str(publisher),
            "--policy-decision-id",
            "policy:test:r16-r4-r3",
            "--operator-decision",
            "approve",
            "--run-id",
            "9001",
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
    assert report["schema"] == (
        "missipy.github_actions.artifact_copilot_publication_cycle_once.v1"
    )
    assert report["valid"] is True
    assert report["status"] == "completed"
    assert report["children"]["artifact_scan"]["called"] is True
    assert report["children"]["copilot_issue_publication"]["called"] is True
    assert report["counts"]["artifact_scan"]["ready_run_count"] == 1
    assert (
        report["counts"]["copilot_issue_publication"]["created_count"] == 1
    )
    assert report["boundaries"]["polling_loop_added"] is False
    assert report["boundaries"]["scheduler_modified"] is False
    cycle_report = Path(report["reports"]["cycle"])
    assert cycle_report.is_file()


def test_r16_r4_r3_execute_requires_local_publication_gates(tmp_path: Path) -> None:
    project_config = tmp_path / "project.ini"
    fetch_config = tmp_path / "fetch.ini"
    dummy = tmp_path / "dummy.py"
    project_config.write_text("[x]\ny=z\n", encoding="utf-8")
    fetch_config.write_text("[x]\ny=z\n", encoding="utf-8")
    dummy.write_text("print('{}')\n", encoding="utf-8")

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
            "--scan-tool",
            str(dummy),
            "--publication-tool",
            str(dummy),
            "--report-root",
            str(tmp_path / "reports"),
            "--lock-path",
            str(tmp_path / "cycle.lock"),
            "--policy-decision-id",
            "policy:test:r16-r4-r3",
            "--operator-decision",
            "approve",
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
    assert completed.returncode == 2
    report = json.loads(completed.stdout)
    assert report["status"] == "rejected"
    assert "AUTODOC_REMOTE_MUTATION_ALLOWED is not enabled" in report["issues"]
    assert "AUTODOC_ISSUE_PUBLICATION_ALLOWED is not enabled" in report["issues"]
