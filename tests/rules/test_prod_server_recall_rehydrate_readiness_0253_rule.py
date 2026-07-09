from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0253_source_is_readiness_only() -> None:
    source = (ROOT / "src/context/prod_server_recall_rehydrate_readiness_0253.py").read_text(
        encoding="utf-8"
    )
    lowered = source.lower()

    assert "RECALL_REHYDRATE_READINESS_BOUNDARY" in source
    assert "calls_qdrant_api" in source
    assert "executes_sql_select" in source
    assert "writes_postgresql" in source
    assert "runs_openvino_inference" in source
    assert "subprocess.run" not in source
    assert "requests." not in lowered
    assert ".search(" not in lowered
    assert ".upsert(" not in lowered
    assert "scheduler.run(" not in lowered
    assert "psycopg" not in lowered


def test_0253_docs_lock_recall_rehydrate_boundary() -> None:
    doc = (ROOT / "doc/architecture/PROD_SERVER_RECALL_REHYDRATE_READINESS_0253.md").read_text(
        encoding="utf-8"
    )

    assert "Recall rehydrate readiness" in doc
    assert "Qdrant recall payload -> sql_ref -> PostgreSQL rehydrate read" in doc
    assert "No Qdrant search is executed" in doc
    assert "No SQL SELECT is executed" in doc
    assert "PostgreSQL remains the durable authority" in doc
    assert "0254" in doc
