import json
import subprocess
import sys
from pathlib import Path

from context.sql_context_store import SQLiteSqlContextStore, build_sql_context_record


ROOT = Path(__file__).resolve().parents[2]


def test_0261_tool_dry_run_and_demo_execute(tmp_path: Path) -> None:
    db_path = tmp_path / "context.sqlite3"
    store = SQLiteSqlContextStore(db_path)
    store.initialize_schema()
    record = build_sql_context_record(
        kind="inference_context",
        identity="tool-0261",
        title="Tool title",
        body="Tool body",
    )
    store.upsert_record(record)
    store.close()

    report = tmp_path / "binding.json"
    report.write_text(json.dumps({"usage": {"sql_ref": record.context_ref}}), encoding="utf-8")

    dry = subprocess.run(
        [
            sys.executable,
            "tools/run_scheduler_managed_sql_ref_openvino_embedding_0261.py",
            "--db-path",
            str(db_path),
            "--binding-report",
            str(report),
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "scheduler_managed_sql_ref_openvino_embedding_valid=True" in dry.stdout
    assert "execute=False" in dry.stdout

    execute = subprocess.run(
        [
            sys.executable,
            "tools/run_scheduler_managed_sql_ref_openvino_embedding_0261.py",
            "--db-path",
            str(db_path),
            "--binding-report",
            str(report),
            "--execute",
            "--policy-decision-id",
            "policy:0261:test",
            "--demo-embedding",
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "execute=True" in execute.stdout
    assert "dimension=384" in execute.stdout
