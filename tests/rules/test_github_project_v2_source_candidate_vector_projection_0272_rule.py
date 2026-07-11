from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/github_project_v2_source_candidate_vector_projection_0272.py"
TOOL = ROOT / "tools/project_github_project_v2_source_candidate_vector_0272.py"
ARCH = ROOT / "doc/architecture/GITHUB_PROJECT_V2_SOURCE_CANDIDATE_VECTOR_PROJECTION_0272.md"
GRAPH = ROOT / "doc/docs/architecture/runtime/272_r9_github_project_v2_vector_projection.dot"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0272_R9_GITHUB_PROJECT_V2_VECTOR_PROJECTION_CHANGED_FILES.md"


def test_r9_reuses_existing_embedding_and_projection_surfaces() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "scheduler_managed_sql_ref_openvino_embedding_usage_0261" in source
    assert "scheduler_managed_embedding_qdrant_projection_usage_0262" in source
    assert "EmbeddingSpaceProfile" in source
    assert "embedding_profile_ref" in source
    assert "LaboratoryManager" not in source
    assert "Scheduler.run" in source


def test_r9_keeps_external_effects_at_cli_boundary() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    tool = TOOL.read_text(encoding="utf-8")
    assert "qdrant_client" not in source
    assert "QdrantClientConnectionConfig" in tool
    assert "build_qdrant_client_projection_executor" in tool
    assert "remote_mutation_allowed\": False" in source
    assert "laboratory_selection_allowed\": False" in source


def test_r9_documentation_keeps_sql_authority_and_next_sequence() -> None:
    architecture = ARCH.read_text(encoding="utf-8")
    graph = GRAPH.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")
    assert "SQL reste l'autorité durable" in architecture
    assert "0272-r10" in architecture
    assert "0273-r1" in architecture
    assert "laboratoire" in architecture
    assert "DurableR8 -> ProfileR9" in graph
    assert "ProfileR9 -> Qdrant" in graph
    assert "non_stdlib_dependency_added: false" in manifest
