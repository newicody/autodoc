from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools" / "run_query_recall_rehydrate_contract_smoke.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("run_query_recall_rehydrate_contract_smoke", TOOL)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_0160_normalizes_query_text_and_rejects_passage_role() -> None:
    module = _load_module()
    assert module._normalize_query_text("hello") == "query: hello"
    assert module._normalize_query_text("query: hello") == "query: hello"
    try:
        module._normalize_query_text("passage: hello")
    except ValueError as exc:
        assert "query role" in str(exc)
    else:
        raise AssertionError("passage role should be rejected")


def test_0160_plan_reuses_existing_surfaces_without_new_backend(tmp_path: Path) -> None:
    module = _load_module()
    recall_json = tmp_path / "recall.json"
    recall_json.write_text(json.dumps({"sql_ref": "sql:artifact/vector-indexing/0158"}), encoding="utf-8")
    plan = module.build_query_recall_rehydrate_contract_plan(
        ROOT,
        output_dir=tmp_path / "out",
        recall_json=recall_json,
        query_embedding_json=None,
        db_path=tmp_path / "sql.sqlite3",
        query_text="P1 closed loop",
        execute=False,
    )
    assert plan.ready
    payload = plan.to_mapping()
    assert payload["ready_for_query_recall_rehydrate_contract"] is True
    assert payload["query_text"] == "query: P1 closed loop"
    assert "tools/embed_e5.py" in " ".join(payload["commands"]["optional_query_embedding"])
    assert "tools/run_qdrant_recall_sql_rehydrate_smoke.py" in " ".join(payload["commands"]["0159_rehydrate"])
    assert "does not create VectorQdrantProjectionAdapter" in payload["boundary"]
    assert "does not create QueryRecallOrchestrator" in payload["boundary"]


def test_0160_cli_json_dry_run_is_machine_readable(tmp_path: Path) -> None:
    recall_json = tmp_path / "recall.json"
    recall_json.write_text(json.dumps({"sql_ref": "sql:artifact/vector-indexing/0158"}), encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            str(TOOL),
            str(ROOT),
            "--recall-json",
            str(recall_json),
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
    assert payload["ready_for_query_recall_rehydrate_contract"] is True
    assert payload["query_text"] == "query: P1 closed loop"
    assert payload["commands"]["0159_rehydrate"]
