from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/love_async_hybrid_retrieval_execution_0287.py"
REPORT = (
    ROOT
    / "PHASE0287_R7_R15_R3_R8_ASYNC_HYBRID_RETRIEVAL_EXECUTION_REPORT.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/"
    "MANIFEST_0287_R7_R15_R3_R8_ASYNC_HYBRID_RETRIEVAL_EXECUTION.md"
)


def test_async_execution_reuses_r8_r4_without_logic_duplication() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for required in (
        "async def execute_love_async_hybrid_retrieval",
        "await embedder.embed_query",
        "execute_hybrid_retrieval(",
        "_PrecomputedDenseQueryEmbedder",
        "existing_hybrid_composition_reused",
        "embedding_dimension=embedding.dimension",
    ):
        assert required in text

    for forbidden in (
        "asyncio.run",
        "Scheduler(",
        "QdrantClient",
        "psycopg",
        "openvino.runtime",
        "fuse_hybrid_candidates(",
        "build_sparse_lexical_query(",
        "_rehydrate_hit(",
    ):
        assert forbidden not in text


def test_phase_artifacts_lock_qdrant_adapter_as_next_unit() -> None:
    report = REPORT.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")
    assert "Qdrant hybrid adapter" in report
    assert "love_async_hybrid_retrieval_execution_0287.py" in manifest
