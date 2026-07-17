from pathlib import Path


COMPOSER = (
    Path(__file__).parents[2]
    / "src/context/love_tool_bounded_installed_runtime_composer_0287.py"
)
FACTORY = (
    Path(__file__).parents[2]
    / "src/context/love_installed_runtime_factory_0287.py"
)


def test_composer_uses_canonical_runtime_and_owned_leaf_resources() -> None:
    text = COMPOSER.read_text(encoding="utf-8")
    for required in (
        "Scheduler(",
        "PriorityQueue()",
        "Dispatcher(event_bus)",
        "Registry()",
        "open_love_postgresql_authority",
        "build_multilingual_e5_small_pipeline",
        "build_qdrant_client_projection_executor",
        "LoveQdrantLiveAnalysisProjection",
        "build_love_openvino_e5_async_query_embedder",
        "build_love_qdrant_hybrid_query_adapter",
        "ImportedActionsRuntimeLease(",
        "runtime-close:postgresql-authority",
        "runtime-close:qdrant-client",
        "AUTODOC_QDRANT_POINT_WRITE_ALLOWED",
        "AUTODOC_QDRANT_SEARCH_ALLOWED",
    ):
        assert required in text

    for forbidden in (
        "LaboratoryManager",
        "LaboratoryScheduler",
        "asyncio.run(",
        "create_task(",
        "Thread(",
        "Process(",
        "remote publication",
    ):
        assert forbidden not in text


def test_factory_preserves_runtime_lease_and_attests_physical_collection() -> None:
    text = FACTORY.read_text(encoding="utf-8")
    assert "ImportedActionsRuntimeLease" in text
    assert "isinstance(provided, ImportedActionsRuntimeLease)" in text
    assert '"physical_collection"' in text
