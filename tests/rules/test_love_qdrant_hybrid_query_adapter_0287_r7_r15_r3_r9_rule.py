from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
ADAPTER = ROOT / "src/context/love_qdrant_hybrid_query_adapter_0287.py"
EXECUTOR = ROOT / "src/inference/qdrant_client_projection_executor.py"


def test_context_adapter_reuses_existing_executor_without_sdk_import() -> None:
    text = ADAPTER.read_text(encoding="utf-8")
    for required in (
        "query_named_dense",
        "query_named_sparse",
        "HybridRetrievalCandidate",
        "QdrantCollectionProfile",
        "reference_only_payloads",
        "sql_remains_authority",
    ):
        assert required in text
    for forbidden in (
        "qdrant_client",
        "QdrantClient(",
        "Scheduler(",
        "upsert",
        "asyncio.run",
    ):
        assert forbidden not in text


def test_existing_io_membrane_exposes_named_dense_and_sparse_queries() -> None:
    text = EXECUTOR.read_text(encoding="utf-8")
    for required in (
        "class QdrantClientReferenceHit",
        "def query_named_dense",
        "def query_named_sparse",
        "using=vector_name",
        "SparseVector",
        "with_vectors=False",
        "_FORBIDDEN_REFERENCE_PAYLOAD_FIELDS",
    ):
        assert required in text
