from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from context.github_project_v2_change_handoff_0272 import (
    GitHubProjectV2ChangeHandoffPolicy,
    build_change_handoff_batch,
)
from context.github_project_v2_snapshot_change_detection_0272 import CHANGE_SET_SCHEMA

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/gate_github_project_v2_source_candidate_0272.py"


def _batch() -> dict[str, object]:
    change_set = {
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
            "added": [{
                "item_id": "PVTI_1",
                "item_type": "DRAFT_ISSUE",
                "content_id": "DI_1",
                "title": "Test gate",
                "body": "Local only",
                "status": "Todo",
                "repository": "",
                "number": 0,
                "url": "",
            }],
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
    }
    return build_change_handoff_batch(
        change_set=change_set,
        policy=GitHubProjectV2ChangeHandoffPolicy(),
    )


def test_cli_execute_writes_immutable_local_gate_record(tmp_path: Path) -> None:
    handoff_dir = tmp_path / "handoffs"
    decision_dir = tmp_path / "decisions"
    handoff_dir.mkdir()
    batch = _batch()
    batch_path = handoff_dir / "project-v2-handoff-batch-test.json"
    batch_path.write_text(json.dumps(batch, indent=2) + "\n", encoding="utf-8")
    candidate_id = batch["handoffs"][0]["candidate"]["candidate_id"]
    config = tmp_path / "config.ini"
    config.write_text(
        "\n".join((
            "[candidate_gate]",
            f"handoff_dir = {handoff_dir}",
            f"decision_dir = {decision_dir}",
            "",
        )),
        encoding="utf-8",
    )
    report = tmp_path / "report.json"
    command = [
        sys.executable,
        str(TOOL),
        "--config", str(config),
        "--candidate-id", str(candidate_id),
        "--action", "promote",
        "--reason", "operator approved",
        "--execute",
        "--policy-decision-id", "policy:0272:test:gate",
        "--output", str(report),
        "--format", "summary",
    ]
    first = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    assert first.returncode == 0, first.stderr + first.stdout
    payload = json.loads(report.read_text(encoding="utf-8"))
    assert payload["valid"] is True
    assert payload["durable_ingestion_allowed"] is True
    assert payload["external_call_performed"] is False
    gate_path = Path(payload["gate_path"])
    assert gate_path.is_file()
    before = gate_path.read_text(encoding="utf-8")

    second = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    assert second.returncode == 0, second.stderr + second.stdout
    assert gate_path.read_text(encoding="utf-8") == before
