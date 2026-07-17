from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "src/context/love_live_runtime_composer_reuse_audit_0287.py"
REPORT = ROOT / "PHASE0287_R7_R15_R3_R5_LIVE_RUNTIME_COMPOSER_REUSE_AUDIT_REPORT.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0287_R7_R15_R3_R5_LIVE_RUNTIME_COMPOSER_REUSE_AUDIT.md"
DOT = ROOT / "doc/architecture/LIVE_RUNTIME_COMPOSER_REUSE_AUDIT_0287_R7_R15_R3_R5.dot"


def test_audit_is_passive_stdlib_only_and_constructs_no_runtime() -> None:
    text = CORE.read_text(encoding="utf-8")
    for forbidden in (
        "import psycopg",
        "from psycopg",
        "import qdrant_client",
        "from qdrant_client",
        "import openvino",
        "from openvino",
        "Scheduler(",
        "Dispatcher(",
        "QdrantClient(",
        "asyncio.run(",
        "subprocess",
        "urllib.request",
        "requests.",
    ):
        assert forbidden not in text


def test_audit_locks_existing_surfaces_and_explicit_missing_adapters() -> None:
    text = CORE.read_text(encoding="utf-8")
    for required in (
        "DbApiContextRevisionAuthorityStore",
        "PostgresSqlContextStoreTarget",
        "build_multilingual_e5_small_pipeline",
        "async def embed_text",
        "QdrantClientProjectionExecutor",
        "QdrantNamedVectorProfile",
        "DenseQueryEmbedder",
        "QdrantHybridQueryExecutor",
        "LoveAnalysisProjectionPort",
        "postgresql_live_binding_needed",
        "dense_query_adapter_needed",
        "hybrid_qdrant_adapters_needed",
        "projection_adapter_needed",
        "base_revision_seed_needed",
        "new_scheduler_allowed: bool = False",
        "runtime_manager_allowed: bool = False",
    ):
        assert required in text


def test_phase_documents_transition_without_modifying_existing_runtime() -> None:
    report = REPORT.read_text(encoding="utf-8")
    assert "live_path_status: n/a" in report
    assert "external_dependencies_added: false" in report
    assert "scheduler_modified: false" in report
    assert "network_added: false" in report

    manifest = MANIFEST.read_text(encoding="utf-8")
    for forbidden in (
        "src/kernel/scheduler.py`",
        "src/kernel/dispatcher.py`",
        "src/context/context_revision_sql_authority_0287.py`",
        "src/inference/e5_pipeline.py`",
        "src/inference/qdrant_client_projection_executor.py`",
        "tools/run_love_actions_closed_loop_0287.py`",
    ):
        assert forbidden not in manifest

    assert DOT.exists()
    assert not (DOT.with_suffix(".svg")).exists()
