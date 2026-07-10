import json
import subprocess
import sys
from pathlib import Path

from context.sql_context_store import SQLiteSqlContextStore, build_sql_context_record


ROOT = Path(__file__).resolve().parents[2]


def test_0263_tool_dry_run_and_demo_execute(tmp_path: Path) -> None:
    db_path = tmp_path / "context.sqlite3"
    store = SQLiteSqlContextStore(db_path)
    store.initialize_schema()
    record = build_sql_context_record(
        kind="inference_context",
        identity="tool-0263",
        title="Tool recall title",
        body="Tool recall body",
    )
    store.upsert_record(record)
    store.close()

    embedding_report = tmp_path / "embedding.json"
    embedding_report.write_text(
        json.dumps(
            {
                "embedding": {
                    "embedding_ref": "embedding:passage:tool",
                    "dimension": 3,
                    "vector": [1.0, 0.0, 0.0],
                }
            }
        ),
        encoding="utf-8",
    )
    projection_report = tmp_path / "projection.json"
    projection_report.write_text(
        json.dumps({"batch": {"sql_context_refs": [record.context_ref]}}),
        encoding="utf-8",
    )

    dry = subprocess.run(
        [
            sys.executable,
            "tools/run_scheduler_managed_qdrant_recall_sql_rehydrate_0263.py",
            "--db-path",
            str(db_path),
            "--embedding-report",
            str(embedding_report),
            "--projection-report",
            str(projection_report),
            "--dimension",
            "3",
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "scheduler_managed_qdrant_recall_sql_rehydrate_valid=True" in dry.stdout
    assert "execute=False" in dry.stdout

    execute = subprocess.run(
        [
            sys.executable,
            "tools/run_scheduler_managed_qdrant_recall_sql_rehydrate_0263.py",
            "--db-path",
            str(db_path),
            "--embedding-report",
            str(embedding_report),
            "--projection-report",
            str(projection_report),
            "--execute",
            "--policy-decision-id",
            "policy:0263:test",
            "--demo-qdrant",
            "--dimension",
            "3",
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    assert "execute=True" in execute.stdout
    assert "hydrated=1" in execute.stdout
    assert "missing=0" in execute.stdout
