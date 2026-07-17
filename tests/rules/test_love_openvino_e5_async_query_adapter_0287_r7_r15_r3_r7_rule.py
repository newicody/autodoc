from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/love_openvino_e5_async_query_adapter_0287.py"
REPORT = (
    ROOT
    / "PHASE0287_R7_R15_R3_R7_OPENVINO_E5_ASYNC_QUERY_ADAPTER_REPORT.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/"
    "MANIFEST_0287_R7_R15_R3_R7_OPENVINO_E5_ASYNC_QUERY_ADAPTER.md"
)


def test_adapter_reuses_existing_contract_and_remains_async() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for required in (
        "DenseQueryEmbedding",
        "DENSE_QUERY_EMBEDDING_SCHEMA",
        "async def embed_query",
        "await self._pipeline.embed_text",
        "dimension: int = 384",
        'query_prefix: str = "query:"',
        "raw_vector_serialized",
    ):
        assert required in text

    for forbidden in (
        "asyncio.run",
        "Scheduler(",
        "QdrantClient",
        "psycopg",
        "openvino.runtime",
        "RealOpenVINORuntime",
        "build_multilingual_e5_small_pipeline",
    ):
        assert forbidden not in text


def test_phase_artifacts_lock_next_boundary() -> None:
    report = REPORT.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")
    assert "async hybrid retrieval execution" in report
    assert "no nested event loop" in report
    assert "love_openvino_e5_async_query_adapter_0287.py" in manifest
# r7-r1 aligns the module documentation with this source-level rule.
