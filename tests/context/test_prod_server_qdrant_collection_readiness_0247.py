from pathlib import Path

from context.prod_server_qdrant_collection_readiness_0247 import (
    QDRANT_COLLECTION_READINESS_BOUNDARY,
    build_qdrant_collection_readiness,
    write_qdrant_collection_readiness_report,
)


ROOT = Path(__file__).resolve().parents[2]
SERVER_CONFIG = ROOT / "doc/examples/autodoc_prod_server_initial_0241.ini"
OPENVINO_CONFIG = ROOT / "doc/examples/autodoc_openvino_embedding_e5_small_0246.ini"


def test_qdrant_collection_boundary_is_readiness_only() -> None:
    assert QDRANT_COLLECTION_READINESS_BOUNDARY == {
        "readiness_only": True,
        "uses_validated_ini": True,
        "uses_openvino_readiness": True,
        "calls_qdrant_api": False,
        "creates_qdrant_collection": False,
        "upserts_qdrant_points": False,
        "runs_openvino_inference": False,
        "writes_postgresql": False,
        "publishes_events": False,
        "calls_github_api": False,
        "requires_non_stdlib": False,
    }


def test_qdrant_collection_is_ready_and_aligned_with_openvino() -> None:
    report = build_qdrant_collection_readiness(
        server_config_path=SERVER_CONFIG,
        openvino_config_path=OPENVINO_CONFIG,
    )

    assert report.ready is True
    assert report.issues == ()
    assert report.collection is not None
    assert report.collection.collection == "autodoc_context_e5_small"
    assert report.collection.vector_dimension == 384
    assert report.collection.distance == "cosine"
    assert report.collection.normalized_vectors is True
    assert "sql_ref" in report.collection.required_payload
    assert report.collection.aligned_openvino_model_id == "openvino.embedding.e5-small"


def test_missing_sql_ref_payload_is_reported(tmp_path: Path) -> None:
    config = tmp_path / "bad_qdrant.ini"
    config.write_text(
        SERVER_CONFIG.read_text(encoding="utf-8").replace(
            "required_payload = sql_ref, model_id, embedding_version, content_hash",
            "required_payload = model_id, embedding_version, content_hash",
        ),
        encoding="utf-8",
    )

    report = build_qdrant_collection_readiness(
        server_config_path=config,
        openvino_config_path=OPENVINO_CONFIG,
    )

    assert report.ready is False
    assert any(issue.field == "required_payload" and "sql_ref" in issue.message for issue in report.issues)


def test_dimension_must_match_openvino(tmp_path: Path) -> None:
    config = tmp_path / "bad_dimension.ini"
    config.write_text(
        SERVER_CONFIG.read_text(encoding="utf-8").replace("vector_dimension = 384", "vector_dimension = 768"),
        encoding="utf-8",
    )

    report = build_qdrant_collection_readiness(
        server_config_path=config,
        openvino_config_path=OPENVINO_CONFIG,
    )

    assert report.ready is False
    assert any(issue.field == "vector_dimension" for issue in report.issues)


def test_write_qdrant_collection_readiness_report(tmp_path: Path) -> None:
    output = tmp_path / "qdrant_collection_readiness.json"
    payload = write_qdrant_collection_readiness_report(
        server_config_path=SERVER_CONFIG,
        openvino_config_path=OPENVINO_CONFIG,
        output_path=output,
    )

    assert payload["production_server_qdrant_collection_readiness_written"] is True
    assert payload["qdrant_collection_readiness"]["ready"] is True
    assert output.exists()
