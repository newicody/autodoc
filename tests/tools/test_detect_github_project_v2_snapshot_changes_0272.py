from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from context.github_project_v2_query_only_snapshot_0272 import SNAPSHOT_SCHEMA

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/detect_github_project_v2_snapshot_changes_0272.py"


def _snapshot(path: Path, ref: str, *, status: str = "Todo") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema": SNAPSHOT_SCHEMA,
                "snapshot_ref": ref,
                "project": {
                    "owner": "newicody",
                    "number": 2,
                    "id": "PVT_kwHOA3ouXM4Ba3Ar",
                    "title": "idea",
                    "url": "https://github.com/users/newicody/projects/2",
                    "closed": False,
                },
                "fields": [],
                "items": [
                    {
                        "id": "item-1",
                        "type": "DRAFT_ISSUE",
                        "content": {"id": "draft-1", "title": "Idea"},
                        "fieldValues": {
                            "nodes": [
                                {
                                    "name": status,
                                    "field": {"id": "status", "name": "Status"},
                                }
                            ]
                        },
                    }
                ],
                "counts": {"field_count": 0, "item_count": 1},
                "boundaries": {
                    "graphql_mutation_allowed": False,
                    "remote_mutation_allowed": False,
                },
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def test_plan_only_selects_baseline_without_change_artifact(tmp_path: Path) -> None:
    snapshot_dir = tmp_path / "snapshots"
    current = snapshot_dir / "project-v2-current.json"
    _snapshot(current, "github-project-v2-snapshot:current")
    report = tmp_path / "report.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--snapshot-dir",
            str(snapshot_dir),
            "--output",
            str(report),
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["valid"] is True
    assert payload["execute"] is False
    assert payload["change_set_ref"] == ""


def test_execute_compares_explicit_snapshots_and_writes_immutable_artifact(tmp_path: Path) -> None:
    previous = tmp_path / "previous.json"
    current = tmp_path / "current.json"
    _snapshot(previous, "github-project-v2-snapshot:previous", status="Todo")
    _snapshot(current, "github-project-v2-snapshot:current", status="Done")
    report = tmp_path / "report.json"
    change_dir = tmp_path / "changes"
    command = [
        sys.executable,
        str(TOOL),
        "--previous-snapshot",
        str(previous),
        "--current-snapshot",
        str(current),
        "--change-dir",
        str(change_dir),
        "--execute",
        "--policy-decision-id",
        "policy:0272:changes",
        "--output",
        str(report),
        "--format",
        "summary",
    ]
    first = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    second = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    assert first.returncode == second.returncode == 0
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["counts"]["changed_count"] == 1
    assert payload["counts"]["status_transition_count"] == 1
    artifact = Path(payload["change_set_path"])
    assert artifact.exists()
    assert len(list(change_dir.glob("project-v2-change-set-*.json"))) == 1
