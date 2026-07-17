from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/love_qdrant_live_analysis_projection_0287.py"
EXECUTOR = ROOT / "src/inference/qdrant_client_projection_executor.py"


def test_r11_reuses_existing_ports_and_keeps_authority_boundaries() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    executor = EXECUTOR.read_text(encoding="utf-8")

    for required in (
        "AsyncEmbeddingPipeline",
        "build_sparse_lexical_query",
        "await self._pipeline.embed_text",
        'passage_prefix: str = "passage:"',
        'dense_vector_name: str = "dense_e5_v1"',
        'sparse_vector_name: str = "sparse_lexical_v1"',
        'collection_name: str = "autodoc_context_e5_384_hybrid_v1"',
        "VectorProjectionMetadata",
        "reference_only_payload",
        "authoritative_body_in_qdrant",
    ):
        assert required in source

    for required in (
        "def upsert_named_hybrid_point",
        "self._models.PointStruct",
        "self._models.SparseVector",
        "self._gate.allow_write",
        "_canonical_named_projection_payload",
        "with_vectors=False",
    ):
        assert required in executor

    combined = source + executor
    for forbidden in (
        "Scheduler(",
        "LaboratoryManager",
        "asyncio.run(",
        "psycopg.connect",
        "create_collection(",
        "delete_collection(",
        "update_collection_aliases(",
    ):
        assert forbidden not in combined
