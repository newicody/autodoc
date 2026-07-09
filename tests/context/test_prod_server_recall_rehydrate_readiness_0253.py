from pathlib import Path

from context.prod_server_recall_rehydrate_readiness_0253 import (
    RECALL_REHYDRATE_READINESS_BOUNDARY,
    build_recall_rehydrate_readiness,
    write_recall_rehydrate_readiness_report,
)


ROOT = Path(__file__).resolve().parents[2]
SERVER_CONFIG = ROOT / "doc/examples/autodoc_prod_server_initial_0241.ini"
OPENVINO_CONFIG = ROOT / "doc/examples/autodoc_openvino_embedding_e5_small_0246.ini"


def test_recall_rehydrate_boundary_is_readiness_only() -> None:
    assert RECALL_REHYDRATE_READINESS_BOUNDARY == {
        "readiness_only": True,
        "uses_handler_projection_readiness": True,
        "uses_postgresql_schema_readiness": True,
        "calls_qdrant_api": False,
        "executes_sql_select": False,
        "writes_postgresql": False,
        "runs_openvino_inference": False,
        "publishes_events": False,
        "dispatches_handler": False,
        "calls_scheduler_run": False,
        "calls_github_api": False,
        "requires_non_stdlib": False,
    }


def test_recall_rehydrate_readiness_is_ready() -> None:
    report = build_recall_rehydrate_readiness(
        server_config_path=SERVER_CONFIG,
        openvino_config_path=OPENVINO_CONFIG,
    )

    assert report.ready is True
    assert report.issues == ()
    assert report.qdrant_recall_payload is not None
    assert report.qdrant_recall_payload.collection == "autodoc_context_e5_small"
    assert report.qdrant_recall_payload.sql_ref == "context_records.id"
    assert "sql_ref" in report.qdrant_recall_payload.required_payload
    assert report.sql_rehydrate_read is not None
    assert report.sql_rehydrate_read.table == "context_records"
    assert report.sql_rehydrate_read.lookup_field == "id"
    assert "SELECT id, kind, payload_json, content_hash, created_at FROM context_records" in report.sql_rehydrate_read.preview_sql


def test_write_recall_rehydrate_readiness_report(tmp_path: Path) -> None:
    output = tmp_path / "recall_rehydrate.json"

    payload = write_recall_rehydrate_readiness_report(
        server_config_path=SERVER_CONFIG,
        openvino_config_path=OPENVINO_CONFIG,
        output_path=output,
    )

    assert payload["production_server_recall_rehydrate_readiness_written"] is True
    assert payload["recall_rehydrate_readiness"]["ready"] is True
    assert output.exists()
