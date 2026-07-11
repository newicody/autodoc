from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/github_project_v2_source_candidate_closed_loop_smoke_0272.py"
TOOL = ROOT / "tools/run_github_project_v2_source_candidate_closed_loop_smoke_0272.py"
ARCH = ROOT / "doc/architecture/GITHUB_PROJECT_V2_SOURCE_CANDIDATE_CLOSED_LOOP_SMOKE_0272.md"
GRAPH = ROOT / "doc/docs/architecture/runtime/272_r10_github_project_v2_closed_loop_smoke.dot"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0272_R10_GITHUB_PROJECT_V2_CLOSED_LOOP_SMOKE_CHANGED_FILES.md"
EMBEDDING_0261 = ROOT / "src/context/scheduler_managed_sql_ref_openvino_embedding_usage_0261.py"


def test_r10_composes_existing_surfaces_without_parallel_runtime() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert "github_project_v2_source_candidate_durable_consumer_0272" in source
    assert "github_project_v2_source_candidate_vector_projection_0272" in source
    assert "scheduler_managed_sql_ref_openvino_embedding_usage_0261" in source
    assert "scheduler_managed_qdrant_recall_sql_rehydrate_usage_0263" in source
    assert "LaboratoryManager" not in source
    assert "RuntimeManager" not in source
    assert "Scheduler.run" in source


def test_r10_keeps_real_clients_at_cli_boundary() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    tool = TOOL.read_text(encoding="utf-8")
    assert "qdrant_client" not in source
    assert "QdrantClientConnectionConfig" in tool
    assert '"remote_mutation_allowed": False' in source
    assert '"laboratory_selection_allowed": False' in source
    assert '"sql_remains_authority": True' in source


def test_r10_documents_upstream_and_laboratory_sequence() -> None:
    architecture = ARCH.read_text(encoding="utf-8")
    graph = GRAPH.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")
    assert "r6" in architecture
    assert "r7" in architecture
    assert "0273-r1" in architecture
    assert "laboratoire fictif" in architecture
    assert "HandoffR6 -> GateR7" in graph
    assert "GateR7 -> DurableR8" in graph
    assert "QdrantRecall0263 -> SqlRehydrate" in graph
    assert "ClosedR10 -> LaboratoryAudit0273" in graph
    assert "non_stdlib_dependency_added: false" in manifest


def test_patch_contains_no_generated_python_artifacts() -> None:
    for path in (SOURCE, TOOL, ARCH, GRAPH, MANIFEST):
        assert "__pycache__" not in path.read_text(encoding="utf-8")
        assert ".pyc" not in path.read_text(encoding="utf-8")


def test_r10_repairs_0261_query_role_propagation_without_parallel_embedder() -> None:
    source = EMBEDDING_0261.read_text(encoding="utf-8")
    assert "def build_openvino_text_from_sql_record" in source
    assert "role=request.role" in source
    assert "role=effective_role" in source
    assert "QueryEmbeddingManager" not in source
