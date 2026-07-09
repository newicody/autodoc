from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0248_projection_path_does_not_execute_projection() -> None:
    source = (ROOT / "src/context/prod_server_projection_path_readiness_0248.py").read_text(
        encoding="utf-8"
    )
    lowered = source.lower()

    assert "readiness_only" in source
    assert "uses_postgresql_readiness" in source
    assert "uses_openvino_readiness" in source
    assert "uses_qdrant_readiness" in source
    assert "connects_postgresql" in source
    assert "runs_openvino_inference" in source
    assert "calls_qdrant_api" in source
    assert "writes_qdrant_points" in source
    assert "import openvino" not in lowered
    assert "import qdrant" not in lowered
    assert "psycopg" not in lowered
    assert "subprocess.run" not in source
    assert "requests." not in lowered
    assert ".execute(" not in lowered
    assert ".upsert(" not in lowered


def test_0248_docs_lock_sql_openvino_qdrant_path() -> None:
    doc = (ROOT / "doc/architecture/PROD_SERVER_PROJECTION_PATH_READINESS_0248.md").read_text(
        encoding="utf-8"
    )

    assert "Projection path readiness" in doc
    assert "SQL record -> OpenVINO embedding -> Qdrant point" in doc
    assert "No projection is executed" in doc
    assert "sql_ref" in doc
    assert "0249" in doc
