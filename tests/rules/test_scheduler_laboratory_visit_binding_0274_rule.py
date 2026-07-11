from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
EVENTS = ROOT / "src/contracts/event.py"
SOURCE = ROOT / "src/context/scheduler_laboratory_visit_binding_0274.py"
ARCH = ROOT / "doc/architecture/EXISTING_SCHEDULER_LABORATORY_VISIT_BINDING_0274.md"
GRAPH = ROOT / "doc/docs/architecture/runtime/274_r1_existing_scheduler_laboratory_visit_binding.dot"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0274_R1_EXISTING_SCHEDULER_LABORATORY_VISIT_BINDING_CHANGED_FILES.md"
REPORT = ROOT / "PHASE0274_R1_EXISTING_SCHEDULER_LABORATORY_VISIT_BINDING_TEST_REPORT.md"


def test_event_contract_adds_laboratory_visit_pair() -> None:
    text = EVENTS.read_text(encoding="utf-8")
    assert "LABORATORY_VISIT_REQUEST = auto()" in text
    assert "LABORATORY_VISIT_RESULT = auto()" in text


def test_binding_uses_scheduler_contract_without_creating_scheduler() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for marker in (
        "SchedulerContract",
        "await scheduler.emit(event)",
        "EventType.LABORATORY_VISIT_REQUEST",
        "LaboratoryVisitRequestHandler",
        "LaboratoryProvider.execute()",
        "existing_scheduler_used: bool = True",
        "scheduler_created: bool = False",
        "scheduler_run_modified: bool = False",
    ):
        assert marker in text

    forbidden = (
        "class LaboratoryScheduler:",
        "class LaboratoryManager:",
        "Scheduler(",
        "PriorityQueue(",
        "EventBus(",
        "Registry(",
        "await scheduler.run(",
        "asyncio.create_task(scheduler.run",
    )
    for marker in forbidden:
        assert marker not in text


def test_binding_keeps_eventbus_observation_only() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert "dispatcher.register(EventType.LABORATORY_VISIT_REQUEST, handler)" in text
    assert "result_event_published: bool = False" in text
    assert '"eventbus_role": "Dispatcher observation copy only"' in text
    assert ".publish(" not in text


def test_documentation_declares_one_scheduler_only() -> None:
    architecture = ARCH.read_text(encoding="utf-8")
    graph = GRAPH.read_text(encoding="utf-8")

    for marker in (
        "one existing Scheduler",
        "No LaboratoryScheduler",
        "Scheduler.run() is unchanged",
        "0274-r2",
        "ServerOrientation",
        "DeliberationRound",
        "FinalArtifactEnvelope",
        "EventBus remains observation-only",
        "VisPy remains passive",
    ):
        assert marker in architecture

    for marker in (
        "ExistingScheduler -> Policy",
        "Policy -> ExistingQueue",
        "ExistingQueue -> UnchangedRun",
        "UnchangedRun -> Dispatcher",
        "Dispatcher -> LaboratoryHandler",
        "LaboratoryHandler -> FakeProvider",
    ):
        assert marker in graph


def test_manifest_and_report_exclude_parallel_runtime_artifacts() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")

    for marker in ("__pycache__", ".pyc", ".pyo", ".svg"):
        assert marker not in manifest

    for marker in (
        "scheduler_created: false",
        "scheduler_modified: false",
        "scheduler_run_modified: false",
        "parallel_queue_created: false",
        "parallel_eventbus_created: false",
        "parallel_registry_created: false",
        "external_dependencies_added: false",
        "provider_active: true",
    ):
        assert marker in report
