from pathlib import Path


SOURCE = (
    Path(__file__).parents[2]
    / "src/context/love_full_deterministic_local_smoke_0287.py"
)


def test_live_local_smoke_reuses_r12_and_r13_without_parallel_orchestration() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    for required in (
        "run_love_full_live_local_smoke",
        "live_async=True",
        "await bind_love_specialist_analyses_live",
        "await run_love_async_hybrid_recall_liaison_synthesis",
        "continuation.analysis_reprojected",
        '"r12_live_binding_used": self.live_path_used',
        '"r13_async_recall_used": self.live_path_used',
    ):
        assert required in text

    for forbidden in (
        "asyncio.run(",
        "create_task(",
        "gather(",
        "LaboratoryManager",
        "LaboratoryScheduler",
        "QdrantClient(",
        "RealOpenVINORuntime(",
        "psycopg.connect(",
    ):
        assert forbidden not in text
