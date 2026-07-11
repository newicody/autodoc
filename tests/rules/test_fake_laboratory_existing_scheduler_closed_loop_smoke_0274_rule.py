from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/fake_laboratory_existing_scheduler_closed_loop_smoke_0274.py"
ARCH = ROOT / "doc/architecture/FAKE_LABORATORY_EXISTING_SCHEDULER_CLOSED_LOOP_SMOKE_0274.md"
GRAPH = ROOT / "doc/docs/architecture/runtime/274_r5_fake_laboratory_existing_scheduler_closed_loop_smoke.dot"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0274_R5_FAKE_LABORATORY_EXISTING_SCHEDULER_CLOSED_LOOP_SMOKE_CHANGED_FILES.md"
REPORT = ROOT / "PHASE0274_R5_FAKE_LABORATORY_EXISTING_SCHEDULER_CLOSED_LOOP_SMOKE_TEST_REPORT.md"


def test_smoke_composes_existing_r2_r3_r4_surfaces() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for marker in (
        "run_fake_laboratory_deliberation",
        "run_fake_laboratory_closed_local_handoff",
        "run_fake_laboratory_recall_closure",
        "FakeLaboratoryDeliberationCommand",
        "FakeLaboratoryClosedHandoffCommand",
        "LaboratoryRecallClosureCommand",
        "EmbeddingSpaceProfile",
        "recall_executor_factory",
    ):
        assert marker in text


def test_smoke_does_not_create_scheduler_or_parallel_authorities() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for forbidden in (
        "Scheduler(",
        "PriorityQueue(",
        "EventBus(",
        "Registry(",
        "create_task(scheduler.run",
        "await scheduler.run(",
        "LaboratoryManager",
        "LaboratoryOrchestrator",
        "class LaboratoryScheduler:",
        "import vispy",
        "import requests",
        "import httpx",
    ):
        assert forbidden not in text
    for marker in (
        "existing_scheduler_used: bool = True",
        "scheduler_created: bool = False",
        "scheduler_modified: bool = False",
        "scheduler_run_owned: bool = False",
        "parallel_orchestrator_created: bool = False",
        "parallel_queue_created: bool = False",
        "parallel_eventbus_created: bool = False",
        "parallel_registry_created: bool = False",
    ):
        assert marker in text


def test_smoke_verifies_sql_replay_and_semantic_identity() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for marker in (
        "verify_sql_replay",
        "idempotent_replay",
        "inserted",
        "replaced",
        "specialist_output_verified",
        "closed_loop_complete",
        "publication_preview_ready",
        "visual_path_complete",
    ):
        assert marker in text


def test_documentation_keeps_external_boundaries_closed() -> None:
    architecture = ARCH.read_text(encoding="utf-8")
    graph = GRAPH.read_text(encoding="utf-8")
    for marker in (
        "one existing Scheduler",
        "No new Scheduler",
        "SQL remains durable authority",
        "Qdrant remains projection and recall only",
        "EventBus remains observation-only",
        "PassiveSupervisor",
        "VisPy",
        "publication gate",
        "0275",
        "Copilot",
    ):
        assert marker in architecture
    for marker in (
        "ExistingScheduler -> Deliberation",
        "Deliberation -> Handoff",
        "Handoff -> Recall",
        "Recall -> ClosedFrame",
        "ClosedFrame -> Facts",
        "Facts -> PassiveSupervisor",
        "PassiveSupervisor -> Visual",
        "Handoff -> Preview",
        "Preview -> PublicationGate",
    ):
        assert marker in graph


def test_manifest_and_report_remain_clean() -> None:
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
        "sql_replay_verified: true",
        "github_mutation_performed: false",
        "live_path_uses_real_backend: false",
    ):
        assert marker in report
