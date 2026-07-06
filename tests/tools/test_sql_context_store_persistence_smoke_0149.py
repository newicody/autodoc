from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from context.sql_context_store_persistence_contract import (
    build_sql_context_store_persistence_record,
    default_persistence_ref,
    inspect_sql_context_store_surface,
)

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_sql_context_store_persistence_smoke.py"


def _sample_handoff(tmp_path: Path) -> Path:
    payload = {
        "handoff_ref": "sql-handoff:artifact-local-0149-demo-to-sql-artifact-vector-indexing-0149",
        "sql_ref": "sql:artifact/vector-indexing/0149",
        "artifact_ref": "artifact:local/0149/demo",
        "artifact_kind": "local_markdown",
        "artifact_path": str(tmp_path / "artifact_input.md"),
        "artifact_contract_path": str(tmp_path / "artifact_intake_contract.json"),
        "artifact_report": str(tmp_path / "artifact_vector_indexing_report.md"),
        "artifact_json": str(tmp_path / "artifact_vector_indexing_report.json"),
        "result_frame_path": str(tmp_path / "vector_indexing_result.json"),
        "point_id": "qdrant-point:0149demo",
        "qdrant_rest_id": "7cc3d6a4-9c02-545f-9b83-014900000000",
        "vector_json": str(tmp_path / "e5_vector_0149.json"),
        "collection": "autodoc_smoke_e5_384",
        "dimension": 384,
        "status": "ok",
        "machine_vector_handoff": True,
        "strict_vector_handoff": True,
        "persistence_mode": "handoff_only",
        "durable_authority": "sql",
        "qdrant_role": "projection_recall_index",
        "payload": {},
    }
    path = tmp_path / "sql_persistence_handoff.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_default_persistence_ref_is_sql_context_persist_ref() -> None:
    ref = default_persistence_ref(
        handoff_ref="sql-handoff:artifact-local-0149-demo",
        sql_ref="sql:artifact/vector-indexing/0149",
    )
    assert ref.startswith("sql-context-persist:")
    assert "artifact-local-0149-demo" in ref


def test_surface_inspection_detects_fake_sql_context_store(tmp_path: Path) -> None:
    store = tmp_path / "src" / "context"
    store.mkdir(parents=True)
    (store / "sql_context_store.py").write_text(
        "class SQLContextStore:\n    def upsert_context(self, record):\n        return record\n",
        encoding="utf-8",
    )
    surface = inspect_sql_context_store_surface(tmp_path)
    mapping = surface.to_mapping()
    assert mapping["exists"] is True
    assert mapping["has_sql_context_store"] is True
    assert mapping["selected_write_method"] == "upsert_context"


def test_record_builds_from_handoff(tmp_path: Path) -> None:
    handoff_path = _sample_handoff(tmp_path)
    handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
    surface = inspect_sql_context_store_surface(ROOT)
    record = build_sql_context_store_persistence_record(
        handoff=handoff,
        sql_context_store_surface=surface,
    )
    mapping = record.to_mapping()
    assert mapping["durable_authority"] == "sql"
    assert mapping["qdrant_role"] == "projection_recall_index"
    assert mapping["persistence_mode"] == "sql_context_store_record"
    assert mapping["payload"]["write_status"] == "record_only"


def test_tool_dry_run_and_execute_write_record_files(tmp_path: Path) -> None:
    handoff_path = _sample_handoff(tmp_path)
    output_dir = tmp_path / "persistence"
    dry = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            str(ROOT),
            "--handoff-json",
            str(handoff_path),
            "--output-dir",
            str(output_dir),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert dry.returncode == 0, dry.stdout
    assert "ready_for_sql_context_store_persistence_smoke: `true`" in dry.stdout
    assert "sql_context_store_persistence_record.json" in dry.stdout

    live = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            str(ROOT),
            "--handoff-json",
            str(handoff_path),
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
    payload = json.loads((output_dir / "sql_context_store_persistence_record.json").read_text(encoding="utf-8"))
    assert payload["sql_ref"] == "sql:artifact/vector-indexing/0149"
    assert payload["durable_authority"] == "sql"
    assert payload["qdrant_role"] == "projection_recall_index"
    assert (output_dir / "sql_context_store_persistence_report.md").exists()
