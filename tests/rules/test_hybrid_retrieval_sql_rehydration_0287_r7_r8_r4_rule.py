from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/hybrid_retrieval_sql_rehydration_0287.py"
CURRENT = ROOT / "doc/README_CURRENT.md"
REPORT = ROOT / "PHASE0287_R7_R8_R4_HYBRID_RETRIEVAL_SQL_REHYDRATION_REPORT.md"
ARCH = ROOT / "doc/architecture/HYBRID_RETRIEVAL_SQL_REHYDRATION_0287_R7_R8_R4.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0287_R7_R8_R4_HYBRID_RETRIEVAL_SQL_REHYDRATION.md"


def test_hybrid_retrieval_reuses_sql_qdrant_and_openvino_boundaries() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    for marker in (
        "missipy.retrieval.hybrid_filter.v1",
        "missipy.retrieval.hybrid_query.v1",
        "missipy.retrieval.hybrid_result.v1",
        "DenseQueryEmbedder",
        "QdrantHybridQueryExecutor",
        "SqlAuthorityReader",
        "reciprocal_rank_k",
        "context_revision_ref",
        "security_scope",
        "source_content_digest",
        "raw_vector_serialized",
    ):
        assert marker in source
    assert "import qdrant_client" not in source
    assert "from qdrant_client" not in source
    assert "import openvino" not in source
    assert "ControlProxy" in source
    assert "Scheduler" in source


def test_sql_is_authority_and_qdrant_content_is_rejected() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    for marker in (
        "Qdrant hit is not a member of the requested revision",
        "Qdrant hit is not active in the requested revision",
        "Qdrant source digest differs from SQL authority",
        "candidate payload contains forbidden fields",
        "qdrant_write_performed",
        "sql_is_authority",
    ):
        assert marker in source


def test_documentation_locks_r8_r4_and_next_scheduler_impact_unit() -> None:
    current = CURRENT.read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")
    architecture = ARCH.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")
    assert "0287-r7-r8-r4 — hybrid retrieval and SQL rehydration" in current
    assert "0287-r7-r8-r5" in current
    assert "SQL remains durable authority" in report
    assert "reciprocal-rank fusion" in architecture
    assert "no `qdrant-client` dependency" in manifest


def test_installation_is_not_part_of_the_patch() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    assert "no `INSTALLATION.md` change" in manifest
