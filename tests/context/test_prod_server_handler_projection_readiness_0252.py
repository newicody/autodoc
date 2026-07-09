from pathlib import Path

from context.prod_server_handler_projection_readiness_0252 import (
    HANDLER_PROJECTION_READINESS_BOUNDARY,
    build_handler_projection_readiness,
    write_handler_projection_readiness_report,
)


ROOT = Path(__file__).resolve().parents[2]
SERVER_CONFIG = ROOT / "doc/examples/autodoc_prod_server_initial_0241.ini"
OPENVINO_CONFIG = ROOT / "doc/examples/autodoc_openvino_embedding_e5_small_0246.ini"


def test_handler_projection_boundary_is_readiness_only() -> None:
    assert HANDLER_PROJECTION_READINESS_BOUNDARY == {
        "readiness_only": True,
        "uses_sql_controlled_write_handler_readiness": True,
        "uses_openvino_readiness": True,
        "uses_qdrant_readiness": True,
        "executes_sql": False,
        "runs_openvino_inference": False,
        "calls_qdrant_api": False,
        "writes_qdrant_points": False,
        "publishes_events": False,
        "dispatches_handler": False,
        "calls_scheduler_run": False,
        "calls_github_api": False,
        "requires_non_stdlib": False,
    }


def test_handler_projection_request_is_ready() -> None:
    report = build_handler_projection_readiness(
        server_config_path=SERVER_CONFIG,
        openvino_config_path=OPENVINO_CONFIG,
    )

    assert report.ready is True
    assert report.issues == ()
    assert report.projection_request is not None
    request = report.projection_request
    assert request.source_table == "context_records"
    assert request.text_source_field == "payload_json"
    assert request.vector_dimension == 384
    assert request.qdrant_collection == "autodoc_context_e5_small"
    assert request.payload_shape.sql_ref == request.sql_ref
    assert request.payload_shape.model_id == "openvino.embedding.e5-small"
    assert request.payload_shape.embedding_version == "0252.r1"


def test_handler_projection_uses_sql_handler_hash() -> None:
    report = build_handler_projection_readiness(
        server_config_path=SERVER_CONFIG,
        openvino_config_path=OPENVINO_CONFIG,
    )

    assert report.projection_request is not None
    assert report.projection_request.content_hash == "sha256:sample-content-hash"
    assert report.projection_request.payload_shape.content_hash == "sha256:sample-content-hash"


def test_write_handler_projection_readiness_report(tmp_path: Path) -> None:
    output = tmp_path / "handler_projection_readiness.json"
    payload = write_handler_projection_readiness_report(
        server_config_path=SERVER_CONFIG,
        openvino_config_path=OPENVINO_CONFIG,
        output_path=output,
    )

    assert payload["production_server_handler_projection_readiness_written"] is True
    assert payload["handler_projection_readiness"]["ready"] is True
    assert output.exists()
