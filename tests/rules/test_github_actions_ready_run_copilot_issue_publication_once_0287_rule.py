from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from context.github_actions_ready_run_copilot_issue_publication_once_0287 import (
    STATE_SCHEMA,
    durable_raw_member_paths,
    select_ready_run_publication_candidates,
)

TOOL = ROOT / "tools/run_github_actions_ready_run_copilot_issue_publication_once_0287.py"
WORKFLOW = (
    ROOT
    / "templates/github/projects-repository/.github/workflows/"
    "autodoc-controlled-research.yml"
)


def _scan_report() -> dict[str, object]:
    artifacts = {
        "authoritative_request": {
            "artifact_id": "101",
            "artifact_name": "autodoc-i15-title--authoritative-request-v1",
            "availability": "downloaded",
            "run_id": "9001",
        },
        "copilot_advisory": {
            "artifact_id": "102",
            "artifact_name": "autodoc-i15-title--copilot-advisory-v2",
            "availability": "downloaded",
            "run_id": "9001",
        },
        "run_manifest": {
            "artifact_id": "103",
            "artifact_name": "autodoc-i15-title--run-manifest-v1",
            "availability": "downloaded",
            "run_id": "9001",
        },
    }
    return {
        "schema": "missipy.github_actions.artifact_scan_once_live.v1",
        "kind": "result",
        "valid": True,
        "ready_runs": [
            {
                "repository": "newicody/projects",
                "run_id": "9001",
                "handoff_ref": "github-actions-ready-run:newicody-projects:9001",
                "status": "ready",
                "artifact_count": 3,
                "artifacts": artifacts,
                "local_execution_started": False,
                "remote_mutation_performed": False,
            }
        ],
    }


def test_r16_r4_r2_selects_strict_ready_run_and_durable_raw_members(tmp_path: Path) -> None:
    candidates = select_ready_run_publication_candidates(_scan_report())
    assert len(candidates) == 1
    candidate = candidates[0]
    assert candidate.repository == "newicody/projects"
    assert candidate.run_id == "9001"
    assert candidate.publication_key.startswith("ready-run-copilot-issue-publication:")
    assert durable_raw_member_paths(tmp_path, candidate) == {
        "authoritative_request": tmp_path
        / "raw/newicody__projects/9001/101/authoritative_request.json",
        "copilot_advisory": tmp_path
        / "raw/newicody__projects/9001/102/copilot_advisory.json",
        "run_manifest": tmp_path
        / "raw/newicody__projects/9001/103/dual_artifact_manifest.json",
    }
    assert (
        select_ready_run_publication_candidates(
            _scan_report(), completed_keys=(candidate.publication_key,)
        )
        == ()
    )


def test_r16_r4_r2_keeps_workflow_read_only_and_reuses_local_adapters() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    tool = TOOL.read_text(encoding="utf-8")
    assert "issues: read" in workflow
    assert "issues: write" not in workflow
    for marker in (
        "build_copilot_advisory_v2_publication_preview.py",
        "publish_github_copilot_advisory_v2_issue_comment_0287.py",
        "AUTODOC_REMOTE_MUTATION_ALLOWED",
        "AUTODOC_ISSUE_PUBLICATION_ALLOWED",
        "--confirm-plan-digest",
        "readback_verified",
        "state_written_after_readback_only",
    ):
        assert marker in tool
    for forbidden in (
        "gh run download",
        "actions/download-artifact",
        "Scheduler.run(",
        "LaboratoryManager",
    ):
        assert forbidden not in tool


def test_r16_r4_r2_execute_writes_receipt_only_after_verified_readback(
    tmp_path: Path,
) -> None:
    scan_path = tmp_path / "scan.json"
    scan_path.write_text(json.dumps(_scan_report()), encoding="utf-8")
    dataset = tmp_path / "dataset"
    members = {
        "101/authoritative_request.json": {
            "schema": "missipy.github.authoritative_request.v1",
            "repository": "newicody/projects",
            "issue_number": 15,
        },
        "102/copilot_advisory.json": {},
        "103/dual_artifact_manifest.json": {},
    }
    for relative, payload in members.items():
        path = dataset / "raw/newicody__projects/9001" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    builder = tmp_path / "builder.py"
    builder.write_text(
        """#!/usr/bin/env python3
import argparse, json
from pathlib import Path
p=argparse.ArgumentParser()
for name in ('advisory','request','manifest','run-id','repository','issue-number','output'):
    p.add_argument('--'+name, required=True)
a=p.parse_args()
Path(a.output).parent.mkdir(parents=True, exist_ok=True)
Path(a.output).write_text(json.dumps({
  'schema':'missipy.github.copilot_advisory_publication_preview.v2',
  'response_digest':'a'*64
}), encoding='utf-8')
print(a.output)
""",
        encoding="utf-8",
    )
    publisher = tmp_path / "publisher.py"
    publisher.write_text(
        """#!/usr/bin/env python3
import argparse, json
p=argparse.ArgumentParser()
p.add_argument('--repository'); p.add_argument('--issue-number')
p.add_argument('--preview'); p.add_argument('--policy-decision-id')
p.add_argument('--operator-decision'); p.add_argument('--gh-command')
p.add_argument('--format'); p.add_argument('--execute', action='store_true')
p.add_argument('--confirm-plan-digest', default='')
a=p.parse_args()
if a.execute:
  print(json.dumps({
    'mutation_action':'created', 'readback_verified':True,
    'published_comment':{'comment_id':77}
  }))
else:
  print(json.dumps({'plan':{
    'valid':True, 'plan_digest':'b'*64, 'marker':'autodoc:test'
  }}))
""",
        encoding="utf-8",
    )
    state_path = tmp_path / "state.json"
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
            "--scan-report",
            str(scan_path),
            "--dataset-root",
            str(dataset),
            "--state-path",
            str(state_path),
            "--work-root",
            str(tmp_path / "work"),
            "--preview-builder",
            str(builder),
            "--publisher-tool",
            str(publisher),
            "--policy-decision-id",
            "policy:test:r16-r4-r2",
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
    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["valid"] is True
    assert report["counts"]["created_count"] == 1
    assert report["results"][0]["readback_verified"] is True
    state = json.loads(state_path.read_text(encoding="utf-8"))
    assert state["schema"] == STATE_SCHEMA
    receipt = next(iter(state["completed"].values()))
    assert receipt["readback_verified"] is True
    assert receipt["run_id"] == "9001"
