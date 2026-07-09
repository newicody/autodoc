from pathlib import Path

from context.prod_server_openvino_embedding_readiness_0246 import (
    OPENVINO_EMBEDDING_READINESS_BOUNDARY,
    build_openvino_embedding_readiness,
    write_openvino_embedding_readiness_report,
)


ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "doc/examples/autodoc_openvino_embedding_e5_small_0246.ini"


def test_openvino_embedding_boundary_is_readiness_only() -> None:
    assert OPENVINO_EMBEDDING_READINESS_BOUNDARY == {
        "readiness_only": True,
        "imports_openvino": False,
        "imports_transformers": False,
        "loads_model": False,
        "runs_inference": False,
        "reads_model_files": False,
        "writes_postgresql": False,
        "writes_qdrant": False,
        "publishes_events": False,
        "calls_github_api": False,
        "requires_non_stdlib_for_readiness": False,
    }


def test_example_openvino_embedding_is_ready() -> None:
    report = build_openvino_embedding_readiness(CONFIG)

    assert report.ready is True
    assert report.issues == ()
    assert report.embedding is not None
    assert report.embedding.dimension == 384
    assert report.embedding.normalized is True
    assert report.embedding.qdrant_distance == "cosine"
    assert report.embedding.query_prefix == "query:"
    assert report.embedding.passage_prefix == "passage:"


def test_wrong_dimension_is_reported(tmp_path: Path) -> None:
    config = tmp_path / "bad_openvino.ini"
    config.write_text(CONFIG.read_text(encoding="utf-8").replace("dimension = 384", "dimension = 768"), encoding="utf-8")

    report = build_openvino_embedding_readiness(config)

    assert report.ready is False
    assert any(issue.field == "dimension" and "384" in issue.message for issue in report.issues)


def test_device_must_be_candidate(tmp_path: Path) -> None:
    config = tmp_path / "bad_device.ini"
    config.write_text(CONFIG.read_text(encoding="utf-8").replace("device = CPU", "device = NPU"), encoding="utf-8")

    report = build_openvino_embedding_readiness(config)

    assert report.ready is False
    assert any(issue.field == "device" for issue in report.issues)


def test_write_openvino_embedding_readiness_report(tmp_path: Path) -> None:
    output = tmp_path / "openvino_embedding_readiness.json"
    payload = write_openvino_embedding_readiness_report(config_path=CONFIG, output_path=output)

    assert payload["production_server_openvino_embedding_readiness_written"] is True
    assert payload["openvino_embedding_readiness"]["ready"] is True
    assert output.exists()
