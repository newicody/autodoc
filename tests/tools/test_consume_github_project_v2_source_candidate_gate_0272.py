from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from context.github_project_v2_change_handoff_0272 import (
    GitHubProjectV2ChangeHandoffPolicy,
    build_change_handoff_batch,
)
from context.github_project_v2_snapshot_change_detection_0272 import CHANGE_SET_SCHEMA
from context.github_project_v2_source_candidate_gate_0272 import (
    GitHubProjectV2SourceCandidateGateCommand,
    build_gate_record,
)

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/consume_github_project_v2_source_candidate_gate_0272.py"


def _load_tool():
    spec = importlib.util.spec_from_file_location("durable_consumer_tool_0272", TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _gate_record() -> dict[str, object]:
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
            "added": [
                {
                    "item_id": "PVTI_added",
                    "item_type": "DRAFT_ISSUE",
                    "content_id": "DI_added",
                    "title": "Demande laboratoire",
                    "body": "Fermer la chaîne durable avant laboratoire.",
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
        "counts": {
            "added_count": 1,
            "changed_count": 0,
            "removed_count": 0,
            "unchanged_count": 0,
        },
        "boundaries": {
            "external_call_performed": False,
            "remote_mutation_allowed": False,
            "sql_write_allowed": False,
            "qdrant_write_allowed": False,
        },
    }
    batch = build_change_handoff_batch(
        change_set=change_set,
        policy=GitHubProjectV2ChangeHandoffPolicy(),
    )
    candidate_id = batch["handoffs"][0]["candidate"]["candidate_id"]
    return build_gate_record(
        handoff_batch=batch,
        command=GitHubProjectV2SourceCandidateGateCommand(
            candidate_id=str(candidate_id),
            action="promote",
            execute=True,
            policy_decision_id="policy:0272:r8:tool-gate",
        ),
    )


def test_tool_executes_existing_store_binding_and_writes_report(
    tmp_path: Path,
    capsys,
) -> None:
    module = _load_tool()
    gate_path = tmp_path / "gate.json"
    output = tmp_path / "report.json"
    db_path = tmp_path / "context.sqlite3"
    gate_path.write_text(json.dumps(_gate_record()), encoding="utf-8")

    rc = module.main(
        (
            "--gate-record",
            str(gate_path),
            "--db-path",
            str(db_path),
            "--execute",
            "--policy-decision-id",
            "policy:0272:r8:tool",
            "--output",
            str(output),
            "--format",
            "summary",
        )
    )
    captured = capsys.readouterr()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert rc == 0
    assert "durable_consumer_valid=True" in captured.out
    assert payload["valid"] is True
    assert payload["sql_write_performed"] is True
    assert payload["rehydrated"] is True
    assert payload["binding"]["uses_existing_store_object"] is True
