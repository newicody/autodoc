from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/fake_laboratory_deliberation_composition_0274.py"
ARCH = ROOT / "doc/architecture/FAKE_LABORATORY_DELIBERATION_COMPOSITION_0274.md"
GRAPH = ROOT / "doc/docs/architecture/runtime/274_r2_fake_laboratory_deliberation_composition.dot"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0274_R2_FAKE_LABORATORY_DELIBERATION_COMPOSITION_CHANGED_FILES.md"
REPORT = ROOT / "PHASE0274_R2_FAKE_LABORATORY_DELIBERATION_COMPOSITION_TEST_REPORT.md"


def test_composition_reuses_existing_deliberation_and_liaison_contracts() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for marker in (
        "ServerOrientation",
        "build_specialist_preliminary_opinion",
        "build_refined_demands_from_opinions",
        "build_deliberation_round",
        "build_bus_statistics_from_rounds",
        "SpecialistOutputFragment",
        "build_specialist_liaison_synthesis",
        "build_final_synthesis_packet",
        "FinalArtifactEnvelope",
        "submit_laboratory_visit",
    ):
        assert marker in text


def test_composition_does_not_create_or_run_scheduler() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    forbidden = (
        "Scheduler(",
        "PriorityQueue(",
        "EventBus(",
        "Registry(",
        "create_task(scheduler.run",
        "await scheduler.run(",
        "LaboratoryManager",
        "LaboratoryOrchestrator",
        "class LaboratoryScheduler:",
    )
    for marker in forbidden:
        assert marker not in text
    for marker in (
        "scheduler_created: bool = False",
        "scheduler_run_owned: bool = False",
        "parallel_orchestrator_created: bool = False",
        "parallel_queue_created: bool = False",
        "parallel_eventbus_created: bool = False",
        "parallel_registry_created: bool = False",
    ):
        assert marker in text


def test_composition_keeps_external_effects_closed() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for marker in (
        "sql_write_performed: bool = False",
        "qdrant_projection_performed: bool = False",
        "github_mutation_performed: bool = False",
        '"publication_gate_required": True',
    ):
        assert marker in text
    for forbidden in (
        "import openvino",
        "import qdrant",
        "import requests",
        "import httpx",
        "import vispy",
        ".publish(",
    ):
        assert forbidden not in text


def test_documentation_preserves_single_scheduler_and_next_steps() -> None:
    architecture = ARCH.read_text(encoding="utf-8")
    graph = GRAPH.read_text(encoding="utf-8")
    for marker in (
        "one existing Scheduler",
        "No new Scheduler",
        "FinalArtifactEnvelope",
        "publication gate",
        "0274-r3",
        "EventBus",
        "PassiveSupervisor",
        "VisPy",
        "GitHub",
    ):
        assert marker in architecture
    for marker in (
        "Orientation -> ExistingScheduler",
        "ExistingScheduler -> FakeProvider",
        "FakeProvider -> Opinions",
        "Opinions -> Round",
        "Round -> Synthesis",
        "Synthesis -> FinalPacket",
        "FinalPacket -> FinalArtifact",
    ):
        assert marker in graph


def test_manifest_and_report_keep_patch_clean() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")
    for marker in ("__pycache__", ".pyc", ".pyo", ".svg"):
        assert marker not in manifest
    for marker in (
        "scheduler_created: false",
        "scheduler_modified: false",
        "scheduler_run_owned: false",
        "parallel_orchestrator_created: false",
        "external_dependencies_added: false",
        "provider_active: true",
        "github_mutation_performed: false",
    ):
        assert marker in report
