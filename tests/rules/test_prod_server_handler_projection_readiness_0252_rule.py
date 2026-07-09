from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0252_handler_projection_does_not_run_embedding_or_qdrant() -> None:
    source = (ROOT / "src/context/prod_server_handler_projection_readiness_0252.py").read_text(
        encoding="utf-8"
    )
    lowered = source.lower()

    assert "readiness_only" in source
    assert "uses_sql_controlled_write_handler_readiness" in source
    assert "runs_openvino_inference" in source
    assert "calls_qdrant_api" in source
    assert "writes_qdrant_points" in source
    assert "dispatches_handler" in source
    assert "calls_scheduler_run" in source
    assert "import openvino" not in lowered
    assert "import qdrant" not in lowered
    assert "psycopg" not in lowered
    assert "subprocess.run" not in source
    assert ".execute(" not in lowered
    assert ".infer(" not in lowered
    assert ".upsert(" not in lowered


def test_0252_docs_lock_handler_projection_boundary() -> None:
    doc = (ROOT / "doc/architecture/PROD_SERVER_HANDLER_PROJECTION_READINESS_0252.md").read_text(
        encoding="utf-8"
    )

    assert "Handler projection readiness" in doc
    assert "SQL handler frame -> OpenVINO embedding -> Qdrant projection" in doc
    assert "No embedding is computed" in doc
    assert "No Qdrant point is written" in doc
    assert "0253" in doc
