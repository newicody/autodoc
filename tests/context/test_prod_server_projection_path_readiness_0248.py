from pathlib import Path

from context.prod_server_projection_path_readiness_0248 import (
    PROJECTION_PATH_READINESS_BOUNDARY,
    build_projection_path_readiness,
    write_projection_path_readiness_report,
)


ROOT = Path(__file__).resolve().parents[2]
SERVER_CONFIG = ROOT / "doc/examples/autodoc_prod_server_initial_0241.ini"
OPENVINO_CONFIG = ROOT / "doc/examples/autodoc_openvino_embedding_e5_small_0246.ini"


def test_projection_path_boundary_is_readiness_only() -> None:
    assert PROJECTION_PATH_READINESS_BOUNDARY == {
        "readiness_only": True,
        "uses_postgresql_readiness": True,
        "uses_openvino_readiness": True,
        "uses_qdrant_readiness": True,
        "connects_postgresql": False,
        "runs_openvino_inference": False,
        "calls_qdrant_api": False,
        "creates_qdrant_collection": False,
        "writes_qdrant_points": False,
        "publishes_events": False,
        "calls_github_api": False,
        "requires_non_stdlib": False,
    }


def test_projection_path_is_ready() -> None:
    report = build_projection_path_readiness(
        server_config_path=SERVER_CONFIG,
        openvino_config_path=OPENVINO_CONFIG,
    )

    assert report.ready is True
    assert report.issues == ()
    assert report.point_shape is not None
    assert report.point_shape.source_table == "context_records"
    assert report.point_shape.collection == "autodoc_context_e5_small"
    assert report.point_shape.vector_dimension == 384
    assert report.point_shape.payload_sql_ref == "context_records.id"
    assert "sql_ref" in report.point_shape.required_payload


def test_projection_path_detects_openvino_qdrant_dimension_mismatch(tmp_path: Path) -> None:
    openvino_config = tmp_path / "bad_openvino.ini"
    openvino_config.write_text(
        OPENVINO_CONFIG.read_text(encoding="utf-8").replace("dimension = 384", "dimension = 768"),
        encoding="utf-8",
    )

    report = build_projection_path_readiness(
        server_config_path=SERVER_CONFIG,
        openvino_config_path=openvino_config,
    )

    assert report.ready is False
    assert any(issue.surface == "openvino" and issue.field == "dimension" for issue in report.issues)
    assert any(issue.surface == "qdrant" and issue.field == "vector_dimension" for issue in report.issues)


def test_write_projection_path_readiness_report(tmp_path: Path) -> None:
    output = tmp_path / "projection_path_readiness.json"
    payload = write_projection_path_readiness_report(
        server_config_path=SERVER_CONFIG,
        openvino_config_path=OPENVINO_CONFIG,
        output_path=output,
    )

    assert payload["production_server_projection_path_readiness_written"] is True
    assert payload["projection_path_readiness"]["ready"] is True
    assert output.exists()
