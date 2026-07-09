from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0247_qdrant_readiness_does_not_call_qdrant_or_run_openvino() -> None:
    source = (ROOT / "src/context/prod_server_qdrant_collection_readiness_0247.py").read_text(
        encoding="utf-8"
    )
    lowered = source.lower()

    assert "readiness_only" in source
    assert "calls_qdrant_api" in source
    assert "creates_qdrant_collection" in source
    assert "upserts_qdrant_points" in source
    assert "runs_openvino_inference" in source
    assert "writes_postgresql" in source
    assert "import qdrant" not in lowered
    assert "qdrantclient" not in lowered
    assert "openvino.runtime" not in lowered
    assert "subprocess.run" not in source
    assert "requests." not in lowered
    assert ".upsert(" not in lowered


def test_0247_docs_lock_openvino_to_qdrant_alignment() -> None:
    doc = (ROOT / "doc/architecture/PROD_SERVER_QDRANT_COLLECTION_READINESS_0247.md").read_text(
        encoding="utf-8"
    )

    assert "Qdrant collection readiness" in doc
    assert "aligned with OpenVINO" in doc
    assert "No Qdrant API call is made" in doc
    assert "sql_ref" in doc
    assert "0248" in doc
