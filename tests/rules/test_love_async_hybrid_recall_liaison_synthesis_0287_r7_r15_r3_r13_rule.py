from pathlib import Path


ROOT = Path(__file__).parents[2]
ASYNC_SOURCE = ROOT / "src/context/love_async_hybrid_recall_liaison_synthesis_0287.py"
SYNC_SOURCE = ROOT / "src/context/love_memory_evidence_liaison_synthesis_0287.py"


def test_r13_reuses_async_retrieval_and_shared_finalizer() -> None:
    async_text = ASYNC_SOURCE.read_text(encoding="utf-8")
    sync_text = SYNC_SOURCE.read_text(encoding="utf-8")

    for required in (
        "await execute_love_async_hybrid_retrieval",
        "finalize_love_memory_evidence_liaison_synthesis",
        'artifact_kinds=("specialist_analysis",)',
        'contribution_kinds=("domain_analysis",)',
        'group_by="source_ref"',
        "analysis_reprojected: bool = False",
    ):
        assert required in async_text

    assert "def finalize_love_memory_evidence_liaison_synthesis" in sync_text
    assert "return finalize_love_memory_evidence_liaison_synthesis(" in sync_text

    for forbidden in (
        "projection_port.project(",
        "await projection_port.project(",
        "Scheduler(",
        "asyncio.run(",
        "create_task(",
        "gather(",
        "QdrantClient(",
        "RealOpenVINORuntime(",
        "psycopg.connect(",
        "LaboratoryManager",
    ):
        assert forbidden not in async_text
