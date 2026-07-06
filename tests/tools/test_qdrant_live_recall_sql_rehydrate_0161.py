from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_qdrant_live_recall_sql_rehydrate_smoke.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("run_qdrant_live_recall_sql_rehydrate_smoke", TOOL)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_0161_reads_values_vector_and_builds_qdrant_search_payload(tmp_path: Path) -> None:
    module = _load_module()
    vector_json = tmp_path / "query.json"
    vector_json.write_text(json.dumps({"dimension": 3, "values": [0.1, 0.2, 0.3]}), encoding="utf-8")

    vector = module.read_query_vector(vector_json)
    assert vector == [0.1, 0.2, 0.3]

    payload = module.qdrant_search_payload(vector, limit=7, score_threshold=0.4)
    assert payload["vector"] == [0.1, 0.2, 0.3]
    assert payload["limit"] == 7
    assert payload["with_payload"] is True
    assert payload["with_vector"] is False
    assert payload["score_threshold"] == 0.4


def test_0161_normalizes_qdrant_response_for_0159() -> None:
    module = _load_module()
    normalized = module.normalize_qdrant_recall_payload(
        {
            "status": "ok",
            "time": 0.1,
            "result": [
                {"id": "abc", "score": 0.99, "payload": {"sql_ref": "sql:artifact/vector-indexing/0158"}},
                {"id": "ignored", "score": 0.2, "payload": None},
            ],
        }
    )

    assert normalized["status"] == "ok"
    assert normalized["result"][0]["payload"]["sql_ref"] == "sql:artifact/vector-indexing/0158"
    assert normalized["result"][1]["payload"] == {}


def test_0161_plan_reuses_existing_surfaces_without_new_backend(tmp_path: Path) -> None:
    module = _load_module()
    vector_json = tmp_path / "query.json"
    vector_json.write_text(json.dumps({"dimension": 3, "values": [0.1, 0.2, 0.3]}), encoding="utf-8")

    plan = module.build_qdrant_live_recall_sql_rehydrate_plan(
        ROOT,
        output_dir=tmp_path / "out",
        query_vector_json=vector_json,
        db_path=tmp_path / "sql.sqlite3",
        qdrant_url="http://127.0.0.1:6333",
        collection="autodoc_smoke_e5_384",
        limit=5,
        score_threshold=None,
        query_text="P1 closed loop",
        execute=False,
    )

    assert plan.ready
    payload = plan.to_mapping()
    assert payload["ready_for_qdrant_live_recall_sql_rehydrate"] is True
    assert payload["query_text"] == "query: P1 closed loop"
    assert "/points/search" in " ".join(payload["commands"]["qdrant_rest_search"])
    assert "does not create VectorQdrantProjectionAdapter" in payload["boundary"]
    assert "does not create QdrantRecallOrchestrator" in payload["boundary"]


def test_0161_cli_json_dry_run_is_machine_readable(tmp_path: Path) -> None:
    vector_json = tmp_path / "query.json"
    vector_json.write_text(json.dumps({"dimension": 3, "values": [0.1, 0.2, 0.3]}), encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            str(ROOT),
            "--query-vector-json",
            str(vector_json),
            "--output-dir",
            str(tmp_path / "out"),
            "--db-path",
            str(tmp_path / "sql.sqlite3"),
            "--query-text",
            "P1 closed loop",
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["ready_for_qdrant_live_recall_sql_rehydrate"] is True
    assert payload["query_text"] == "query: P1 closed loop"
