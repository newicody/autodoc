from pathlib import Path


SOURCE = (
    Path(__file__).parents[2]
    / "src/context/love_specialist_live_projection_binding_0287.py"
)


def test_r12_live_binding_reuses_existing_surfaces() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    for required in (
        "LoveMemoryEvidenceSynthesisCommand",
        "_analysis_object",
        "_artifact_descriptor",
        "_merge_memberships",
        "_put_relations",
        "_validate_chain",
        "async def bind_love_specialist_analyses_live",
        "await projection_port.project",
        "authority_store.put_projection",
        "security_scope=command.security_scope",
        "synthesis_performed: bool = False",
    ):
        assert required in text

    for forbidden in (
        "Scheduler(",
        "asyncio.run(",
        "QdrantClient(",
        "RealOpenVINORuntime(",
        "psycopg.connect(",
        "LaboratoryManager",
        "LaboratoryScheduler",
        "create_task(",
        "gather(",
    ):
        assert forbidden not in text
