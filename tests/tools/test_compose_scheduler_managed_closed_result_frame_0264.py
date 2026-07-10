import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SQL_REF = "sql:inference_context:tool"
EMBEDDING_REF = "embedding:passage:tool"


def test_0264_tool_composes_closed_result_frame(tmp_path: Path) -> None:
    sql_write = tmp_path / "0260.json"
    embedding = tmp_path / "0261.json"
    projection = tmp_path / "0262.json"
    recall = tmp_path / "0263.json"
    output = tmp_path / "result_frame.json"

    sql_write.write_text(json.dumps({"usage": {"sql_ref": SQL_REF}}), encoding="utf-8")
    embedding.write_text(
        json.dumps({"embedding": {"sql_ref": SQL_REF, "embedding_ref": EMBEDDING_REF}}),
        encoding="utf-8",
    )
    projection.write_text(
        json.dumps(
            {
                "batch": {
                    "points": [
                        {
                            "sql_context_ref": SQL_REF,
                            "embedding_ref": EMBEDDING_REF,
                            "payload": {"sql_ref": SQL_REF},
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    recall.write_text(
        json.dumps(
            {
                "recall": {"hit_count": 1, "hits": [{"sql_context_ref": SQL_REF}]},
                "sql_refs": [SQL_REF],
                "hydrated_records": [{"context_ref": SQL_REF, "title": "T", "body": "B"}],
                "missing_count": 0,
            }
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            "tools/compose_scheduler_managed_closed_result_frame_0264.py",
            "--sql-write-report",
            str(sql_write),
            "--embedding-report",
            str(embedding),
            "--projection-report",
            str(projection),
            "--recall-rehydrate-report",
            str(recall),
            "--output",
            str(output),
            "--format",
            "summary",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert "scheduler_managed_closed_result_frame_valid=True" in result.stdout
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["schema"] == "missipy.scheduler_managed_closed_result_frame.v1"
    assert payload["trace"]["0263"]["hydrated_count"] == 1
