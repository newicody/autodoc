from __future__ import annotations
import importlib.util, json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_qdrant_recall_sql_rehydrate_smoke.py"
def _load_module():
    spec = importlib.util.spec_from_file_location("run_qdrant_recall_sql_rehydrate_smoke", TOOL)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

def test_0159_extracts_unique_sql_refs_from_qdrant_style_payload() -> None:
    module = _load_module()
    payload = {"result": [{"payload": {"sql_ref": "sql:artifact/vector-indexing/0158"}}, {"payload": {"context_ref": "sql:artifact/vector-indexing/0158"}}, {"payload": {"sql_ref": "sql:artifact/vector-indexing/0159"}}]}
    assert module.extract_sql_refs_from_recall_payload(payload) == ["sql:artifact/vector-indexing/0158", "sql:artifact/vector-indexing/0159"]

def test_0159_plan_reuses_existing_surfaces_without_new_backend(tmp_path: Path) -> None:
    module = _load_module(); recall_json = tmp_path / "recall.json"
    recall_json.write_text(json.dumps({"sql_ref": "sql:artifact/vector-indexing/0158"}), encoding="utf-8")
    plan = module.build_qdrant_recall_sql_rehydrate_plan(ROOT, recall_json=recall_json, output_dir=tmp_path / "out", db_path=tmp_path / "sql.sqlite3", environ={}, query_text="P1 closed loop", execute=False)
    assert plan.ready
    assert plan.db_path == tmp_path / "sql.sqlite3"
    payload = plan.to_mapping()
    assert payload["ready_for_qdrant_recall_sql_rehydrate"] is True
    assert "does not create VectorQdrantProjectionAdapter" in payload["boundary"]
    assert "SQL remains durable authority" in payload["boundary"]

def test_0159_cli_json_dry_run_is_machine_readable(tmp_path: Path) -> None:
    recall_json = tmp_path / "recall.json"
    recall_json.write_text(json.dumps({"sql_ref": "sql:artifact/vector-indexing/0158"}), encoding="utf-8")
    completed = subprocess.run([sys.executable, str(TOOL), str(ROOT), "--recall-json", str(recall_json), "--output-dir", str(tmp_path / "out"), "--db-path", str(tmp_path / "sql.sqlite3"), "--format", "json"], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    payload = json.loads(completed.stdout)
    assert payload["ready_for_qdrant_recall_sql_rehydrate"] is True
    assert payload["db_path_source"] == "cli:--db-path"
    assert payload["query_text"].startswith("query: ")
