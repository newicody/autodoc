from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from context.sql_persistence_handoff_contract import (
    build_sql_persistence_handoff_contract,
    default_handoff_ref,
)

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_sql_persistence_handoff_smoke.py"


def _write_sample_artifact_outputs(tmp_path: Path) -> tuple[Path, Path, Path]:
    contract = {
        "artifact_ref": "artifact:local/0148/demo",
        "artifact_kind": "local_markdown",
        "artifact_path": str(tmp_path / "artifact_input.md"),
        "text_kind": "passage",
        "sql_ref": "sql:artifact/vector-indexing/0148",
        "collection": "autodoc_smoke_e5_384",
        "dimension": 384,
        "route_root": str(tmp_path / "routes"),
        "vector_indexing_job_ref": "vector-indexing-job:artifact/0148-demo",
        "text": "passage: demo",
    }
    result_frame = {
        "payload": {
            "status": "ok",
            "sql_ref": "sql:artifact/vector-indexing/0148",
            "point_id": "qdrant-point:0148demo",
            "qdrant_rest_id": "7cc3d6a4-9c02-545f-9b83-014800000000",
            "vector_json": str(tmp_path / "e5_vector_0148.json"),
            "machine_vector_handoff": True,
            "strict_vector_handoff": True,
        }
    }
    artifact_result = {
        "artifact_input": str(tmp_path / "artifact_input.md"),
        "artifact_contract_path": str(tmp_path / "artifact_intake_contract.json"),
        "artifact_report": str(tmp_path / "artifact_vector_indexing_report.md"),
        "artifact_json": str(tmp_path / "artifact_vector_indexing_report.json"),
        "sql_ref": "sql:artifact/vector-indexing/0148",
        "scheduler_route_frame": "ok",
        "local_vector_indexing_smoke": "ok",
        "vector_indexing_result_frame": "ok",
        "strict_vector_handoff": True,
        "machine_vector_handoff": True,
        "result_frame_path": str(tmp_path / "vector_indexing_result.json"),
        "point_id": "qdrant-point:0148demo",
        "qdrant_rest_id": "7cc3d6a4-9c02-545f-9b83-014800000000",
        "vector_json": str(tmp_path / "e5_vector_0148.json"),
    }
    contract_path = tmp_path / "artifact_intake_contract.json"
    frame_path = tmp_path / "vector_indexing_result.json"
    result_path = tmp_path / "artifact_vector_indexing_report.json"
    contract_path.write_text(json.dumps(contract), encoding="utf-8")
    frame_path.write_text(json.dumps(result_frame), encoding="utf-8")
    result_path.write_text(json.dumps(artifact_result), encoding="utf-8")
    return result_path, contract_path, frame_path


def test_default_handoff_ref_is_sql_handoff_ref() -> None:
    ref = default_handoff_ref(
        artifact_ref="artifact:local/0148/demo",
        sql_ref="sql:artifact/vector-indexing/0148",
    )
    assert ref.startswith("sql-handoff:")
    assert "artifact-local-0148-demo" in ref


def test_contract_builds_handoff_only_payload(tmp_path: Path) -> None:
    result_path, contract_path, frame_path = _write_sample_artifact_outputs(tmp_path)
    artifact_result = json.loads(result_path.read_text(encoding="utf-8"))
    artifact_contract = json.loads(contract_path.read_text(encoding="utf-8"))
    frame_payload = json.loads(frame_path.read_text(encoding="utf-8"))["payload"]
    contract = build_sql_persistence_handoff_contract(
        handoff_ref="sql-handoff:artifact-local-0148-demo",
        artifact_result=artifact_result,
        artifact_contract=artifact_contract,
        result_frame_payload=frame_payload,
    )
    mapping = contract.to_mapping()
    assert mapping["durable_authority"] == "sql"
    assert mapping["qdrant_role"] == "projection_recall_index"
    assert mapping["persistence_mode"] == "handoff_only"
    assert mapping["point_id"] == "qdrant-point:0148demo"
    assert mapping["machine_vector_handoff"] is True


def test_tool_dry_run_and_execute_write_handoff_files(tmp_path: Path) -> None:
    result_path, contract_path, frame_path = _write_sample_artifact_outputs(tmp_path)
    output_dir = tmp_path / "handoff"
    dry = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            str(ROOT),
            "--artifact-json",
            str(result_path),
            "--artifact-contract",
            str(contract_path),
            "--result-frame",
            str(frame_path),
            "--output-dir",
            str(output_dir),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert dry.returncode == 0, dry.stdout
    assert "ready_for_sql_persistence_handoff: `true`" in dry.stdout
    assert "handoff-only envelope" in dry.stdout

    live = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            str(ROOT),
            "--artifact-json",
            str(result_path),
            "--artifact-contract",
            str(contract_path),
            "--result-frame",
            str(frame_path),
            "--output-dir",
            str(output_dir),
            "--execute",
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert live.returncode == 0, live.stdout
    payload = json.loads((output_dir / "sql_persistence_handoff.json").read_text(encoding="utf-8"))
    assert payload["sql_ref"] == "sql:artifact/vector-indexing/0148"
    assert payload["durable_authority"] == "sql"
    assert payload["qdrant_role"] == "projection_recall_index"
    assert (output_dir / "sql_persistence_handoff_report.md").exists()
