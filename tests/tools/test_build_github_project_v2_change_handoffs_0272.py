from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from context.github_project_v2_snapshot_change_detection_0272 import CHANGE_SET_SCHEMA

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/build_github_project_v2_change_handoffs_0272.py"


def _write_fixture(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": CHANGE_SET_SCHEMA,
                "kind": "github_project_v2_snapshot_change_set",
                "baseline": False,
                "change_set_ref": "github-project-v2-change-set:0123456789abcdef",
                "previous_snapshot_ref": "github-project-v2-snapshot:previous",
                "current_snapshot_ref": "github-project-v2-snapshot:current",
                "project": {
                    "id": "PVT_test",
                    "owner": "newicody",
                    "number": 2,
                    "title": "idea",
                    "url": "https://github.com/users/newicody/projects/2",
                },
                "items": {
                    "added": [
                        {
                            "item_id": "PVTI_1",
                            "item_type": "DRAFT_ISSUE",
                            "content_id": "DI_1",
                            "title": "Test",
                            "body": "Local only",
                            "status": "Todo",
                            "repository": "",
                            "number": 0,
                            "url": "",
                        }
                    ],
                    "changed": [],
                    "removed": [],
                    "unchanged_ids": [],
                },
                "counts": {"added_count": 1, "changed_count": 0, "removed_count": 0},
                "boundaries": {
                    "external_call_performed": False,
                    "remote_mutation_allowed": False,
                    "sql_write_allowed": False,
                    "qdrant_write_allowed": False,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def _write_config(path: Path, change_dir: Path, handoff_dir: Path) -> None:
    path.write_text(
        "\n".join(
            (
                "[change_handoff]",
                f"change_set_dir = {change_dir}",
                f"handoff_dir = {handoff_dir}",
                "max_handoffs = 10",
                "include_removed = true",
                "include_baseline = false",
                "",
            )
        ),
        encoding="utf-8",
    )


def test_cli_execute_writes_immutable_local_batch(tmp_path: Path) -> None:
    change_dir = tmp_path / "changes"
    handoff_dir = tmp_path / "handoffs"
    change_dir.mkdir()
    fixture = change_dir / "project-v2-change-set-test.json"
    config = tmp_path / "config.ini"
    report = tmp_path / "report.json"
    _write_fixture(fixture)
    _write_config(config, change_dir, handoff_dir)
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--config",
            str(config),
            "--execute",
            "--policy-decision-id",
            "policy:0272:test-change-handoff",
            "--output",
            str(report),
            "--format",
            "summary",
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert "candidates=1" in completed.stdout
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["valid"] is True
    assert payload["external_call_performed"] is False
    batches = list(handoff_dir.glob("project-v2-handoff-batch-*.json"))
    assert len(batches) == 1
    first_content = batches[0].read_text(encoding="utf-8")
    repeated = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            "--config",
            str(config),
            "--execute",
            "--policy-decision-id",
            "policy:0272:test-change-handoff",
            "--output",
            str(report),
        ],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert repeated.returncode == 0, repeated.stderr
    assert batches[0].read_text(encoding="utf-8") == first_content


def test_cli_plan_only_does_not_write_handoff(tmp_path: Path) -> None:
    change_dir = tmp_path / "changes"
    handoff_dir = tmp_path / "handoffs"
    change_dir.mkdir()
    _write_fixture(change_dir / "project-v2-change-set-test.json")
    config = tmp_path / "config.ini"
    report = tmp_path / "report.json"
    _write_config(config, change_dir, handoff_dir)
    completed = subprocess.run(
        [sys.executable, str(TOOL), "--config", str(config), "--output", str(report)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr
    assert not handoff_dir.exists()
