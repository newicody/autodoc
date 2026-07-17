from context.love_live_runtime_composer_reuse_audit_0287 import (
    IMPLEMENTATION_SEQUENCE,
    REQUIRED_SURFACES,
    audit_love_live_runtime_composer_reuse,
)


def _baseline_sources() -> dict[str, str]:
    sources = {path: "surface" for path in REQUIRED_SURFACES}
    sources[REQUIRED_SURFACES[0]] = (
        "class DbApiContextRevisionAuthorityStore:\n    pass\n"
    )
    sources[REQUIRED_SURFACES[1]] = (
        "class PostgresSqlContextStoreTarget:\n    pass\n"
    )
    sources[REQUIRED_SURFACES[2]] = """
class MultilingualE5SmallPipelineBundle:
    pass

def build_multilingual_e5_small_pipeline():
    pass
"""
    sources[REQUIRED_SURFACES[3]] = """
class OpenVINOEmbeddingPipeline:
    async def embed_text(self, text):
        pass
"""
    sources[REQUIRED_SURFACES[4]] = """
class QdrantClientProjectionExecutor:
    def close(self):
        pass
"""
    sources[REQUIRED_SURFACES[5]] = """
class QdrantNamedVectorProfile:
    pass
class QdrantCollectionProfile:
    named_vectors = ()
"""
    sources[REQUIRED_SURFACES[6]] = """
from typing import Protocol
class DenseQueryEmbedder(Protocol):
    def embed_query(self): ...
class QdrantHybridQueryExecutor(Protocol):
    def search_dense(self): ...
    def search_sparse(self): ...
"""
    sources[REQUIRED_SURFACES[7]] = """
from typing import Protocol
class LoveAnalysisProjectionPort(Protocol):
    def project(self): ...
"""
    sources[REQUIRED_SURFACES[9]] = (
        "def register_native_love_laboratory_visit_handler(): pass"
    )
    sources[REQUIRED_SURFACES[10]] = (
        "def register_native_love_collaboration_visit_handler(): pass"
    )
    return sources


def test_audit_locks_reuse_and_reports_only_missing_live_adapters() -> None:
    result = audit_love_live_runtime_composer_reuse(_baseline_sources())

    assert result.valid is True
    assert result.sql_authority_store_found is True
    assert result.postgresql_target_descriptor_found is True
    assert result.postgresql_connection_factory_found is False
    assert result.e5_pipeline_factory_found is True
    assert result.e5_embedding_is_async is True
    assert result.dense_query_adapter_found is False
    assert result.qdrant_client_executor_found is True
    assert result.qdrant_client_close_found is True
    assert result.hybrid_query_adapter_found is False
    assert result.projection_adapter_found is False
    assert result.base_revision_seed_found is False
    assert result.live_composer_ready is False
    assert result.next_recommended_patch == IMPLEMENTATION_SEQUENCE[0]
    assert result.network_used is False
    assert result.backend_loaded is False
    assert result.write_performed is False


def test_audit_accepts_existing_leaf_adapters_and_seed_for_composer() -> None:
    sources = _baseline_sources()
    sources["src/context/existing_live_leaf_adapters.py"] = """
def connect():
    return psycopg.connect()

def embed_query():
    pass

def search_dense():
    pass

def search_sparse():
    pass

def project():
    pass

def seed_revision():
    put_revision("context-revision:love-base")
"""

    result = audit_love_live_runtime_composer_reuse(sources)

    assert result.valid is True
    assert result.postgresql_connection_factory_found is True
    assert result.dense_query_adapter_found is True
    assert result.hybrid_query_adapter_found is True
    assert result.projection_adapter_found is True
    assert result.base_revision_seed_found is True
    assert result.live_composer_ready is True
    assert result.next_recommended_patch == IMPLEMENTATION_SEQUENCE[3]


def test_audit_fails_closed_when_a_required_surface_is_missing() -> None:
    sources = _baseline_sources()
    del sources[REQUIRED_SURFACES[4]]

    result = audit_love_live_runtime_composer_reuse(sources)

    assert result.valid is False
    assert REQUIRED_SURFACES[4] in result.missing_required_surfaces
