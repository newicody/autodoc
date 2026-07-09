from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0246_openvino_readiness_does_not_import_or_run_inference() -> None:
    source = (ROOT / "src/context/prod_server_openvino_embedding_readiness_0246.py").read_text(
        encoding="utf-8"
    )
    lowered = source.lower()

    assert "readiness_only" in source
    assert "imports_openvino" in source
    assert "imports_transformers" in source
    assert "loads_model" in source
    assert "runs_inference" in source
    assert "reads_model_files" in source
    assert "writes_qdrant" in source
    assert "import openvino" not in lowered
    assert "import transformers" not in lowered
    assert "core.compile_model" not in lowered
    assert ".infer(" not in lowered
    assert "subprocess.run" not in source
    assert "requests." not in lowered


def test_0246_example_locks_e5_small_shape() -> None:
    example = (ROOT / "doc/examples/autodoc_openvino_embedding_e5_small_0246.ini").read_text(
        encoding="utf-8"
    )

    assert "model_id = openvino.embedding.e5-small" in example
    assert "model_xml = openvino_model.xml" in example
    assert "dimension = 384" in example
    assert "normalized = true" in example
    assert "qdrant_distance = cosine" in example
    assert "query_prefix = query:" in example
    assert "passage_prefix = passage:" in example


def test_0246_docs_lock_openvino_boundary() -> None:
    doc = (ROOT / "doc/architecture/PROD_SERVER_OPENVINO_EMBEDDING_READINESS_0246.md").read_text(
        encoding="utf-8"
    )

    assert "OpenVINO embedding readiness" in doc
    assert "No model is loaded" in doc
    assert "multilingual-e5-small" in doc
    assert "Qdrant comes after OpenVINO" in doc
