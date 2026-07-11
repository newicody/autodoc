from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/fake_laboratory_closed_local_handoff_0274.py"
READ_MODEL = ROOT / "src/context/passive_supervisor_visual_read_model.py"
LAYOUT = ROOT / "src/context/passive_supervisor_visual_layout_model.py"
ARCH = ROOT / "doc/architecture/FAKE_LABORATORY_CLOSED_LOCAL_HANDOFF_0274.md"
GRAPH = ROOT / "doc/docs/architecture/runtime/274_r3_fake_laboratory_closed_local_handoff.dot"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0274_R3_FAKE_LABORATORY_CLOSED_LOCAL_HANDOFF_CHANGED_FILES.md"
REPORT = ROOT / "PHASE0274_R3_FAKE_LABORATORY_CLOSED_LOCAL_HANDOFF_TEST_REPORT.md"


def test_handoff_reuses_existing_sql_vector_and_observation_surfaces() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for marker in (
        "build_sql_context_record",
        "run_scheduler_managed_sql_ref_openvino_embedding_usage",
        "EmbeddingSpaceProfile",
        "validate_embedding_against_profile",
        "attach_profile_to_embedding",
        "run_scheduler_managed_embedding_qdrant_projection_usage",
        "ClosedResultFrameObservationFact",
        "build_passive_supervisor_closed_frame_observation_report",
        "build_visual_read_model",
        "build_passive_supervisor_visual_layout_model",
        "context.github_publication_review",
    ):
        assert marker in text


def test_handoff_creates_no_scheduler_or_parallel_authority() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for forbidden in (
        "Scheduler(",
        "PriorityQueue(",
        "EventBus(",
        "Registry(",
        "LaboratoryManager",
        "LaboratoryOrchestrator",
        "create_task(scheduler.run",
        "await scheduler.run(",
        "import vispy",
        "import requests",
        "import httpx",
    ):
        assert forbidden not in text
    for marker in (
        "scheduler_created: bool = False",
        "scheduler_modified: bool = False",
        "parallel_orchestrator_created: bool = False",
        "parallel_eventbus_created: bool = False",
        "parallel_registry_created: bool = False",
        "github_mutation_performed: bool = False",
    ):
        assert marker in text


def test_eventbus_facts_are_observation_only() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert "EventType.LABORATORY_VISIT_RESULT" in text
    assert "request=None" in text
    assert '"observation_only": True' in text
    assert '"command": False' in text
    assert "event_bus.publish(event)" in text


def test_visual_models_gain_laboratory_refs_and_zone() -> None:
    read_model = READ_MODEL.read_text(encoding="utf-8")
    layout = LAYOUT.read_text(encoding="utf-8")
    for marker in (
        '"laboratory_ref"',
        '"specialist_ref"',
        '"visit_ref"',
        '"synthesis_ref"',
        '"final_ref"',
        '"LABORATORY": "laboratory"',
        '"SPECIALIST": "laboratory"',
        '"DELIBERATION": "laboratory"',
        '"SYNTHESIS": "laboratory"',
    ):
        assert marker in read_model
    assert 'mapping.get("target_ref"' in layout
    assert 'mapping.get("edge_kind"' in layout
    assert 'mapping.get("edge_id"' in layout


def test_documentation_keeps_github_and_visual_paths_gated() -> None:
    architecture = ARCH.read_text(encoding="utf-8")
    graph = GRAPH.read_text(encoding="utf-8")
    for marker in (
        "one existing Scheduler",
        "SQL remains durable authority",
        "Qdrant remains projection-only",
        "EventBus remains observation-only",
        "PassiveSupervisor",
        "VisPy",
        "publication gate",
        "0274-r4",
        "recall",
    ):
        assert marker in architecture
    for marker in (
        "Deliberation -> SQL",
        "SQL -> E5",
        "E5 -> Profile",
        "Profile -> Qdrant",
        "Deliberation -> Facts",
        "Facts -> PassiveSupervisor",
        "PassiveSupervisor -> Visual",
        "Preview -> PublicationGate",
    ):
        assert marker in graph


def test_manifest_and_report_are_clean() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")
    for marker in ("__pycache__", ".pyc", ".pyo", ".svg"):
        assert marker not in manifest
    for marker in (
        "scheduler_created: false",
        "scheduler_modified: false",
        "parallel_orchestrator_created: false",
        "external_dependencies_added: false",
        "sql_remains_authority: true",
        "qdrant_projection_only: true",
        "github_mutation_performed: false",
    ):
        assert marker in report
