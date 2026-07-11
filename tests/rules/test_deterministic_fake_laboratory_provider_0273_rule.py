from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/deterministic_fake_laboratory_provider_0273.py"
ARCH = ROOT / "doc/architecture/DETERMINISTIC_FAKE_LABORATORY_PROVIDER_0273.md"
GRAPH = ROOT / "doc/docs/architecture/runtime/273_r3_deterministic_fake_laboratory_provider.dot"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0273_R3_DETERMINISTIC_FAKE_LABORATORY_PROVIDER_CHANGED_FILES.md"
REPORT = ROOT / "PHASE0273_R3_DETERMINISTIC_FAKE_LABORATORY_PROVIDER_TEST_REPORT.md"


def test_fake_provider_reuses_existing_registry_type() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for marker in (
        "SchedulerOwnedRuntimeComponentRegistration",
        "SchedulerOwnedRuntimeRegistry",
        "validate_scheduler_owned_runtime_registry",
        "selected_from_existing_surfaces=False",
        "bind_deterministic_fake_laboratory_registration",
    ):
        assert marker in text


def test_fake_provider_is_bounded_deterministic_and_not_real_backend() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    for marker in (
        "DeterministicFakeLaboratoryProvider",
        "validate_laboratory_visit_result",
        '"deterministic": True',
        '"real_backend_used": False',
        "request.resource_budget.allow_network",
        "max_external_calls",
    ):
        assert marker in text


def test_fake_provider_does_not_create_parallel_authorities_or_backends() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    forbidden_imports = (
        "import openvino",
        "import qdrant",
        "import vispy",
        "import genai",
        "import requests",
        "import httpx",
        "from kernel.scheduler",
        "from kernel.event_bus",
        "RouteRuntimeManager",
    )
    for marker in forbidden_imports:
        assert marker not in text
    for marker in (
        "provider_owns_orchestration: bool = False",
        "provider_owns_persistence: bool = False",
        "provider_owns_vector_index: bool = False",
        "provider_publishes_commands: bool = False",
        "provider_uses_network: bool = False",
        "real_backend_used: bool = False",
    ):
        assert marker in text


def test_fake_provider_keeps_handler_and_scheduler_path_explicit() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    architecture = ARCH.read_text(encoding="utf-8")
    assert "Dispatcher -> Handler -> LaboratoryProvider.execute" in text
    assert "Scheduler.emit()" in architecture
    assert "Scheduler.run()" in architecture
    assert "EventBus" in architecture
    assert "VisPy" in architecture


def test_graph_binds_existing_registry_to_fake_provider() -> None:
    graph = GRAPH.read_text(encoding="utf-8")
    for marker in (
        "ExistingRegistry -> Registration",
        "Registration -> Handler",
        "Handler -> FakeProvider",
        "FakeProvider -> VisitResult",
        "VisitResult -> EventBus",
        "EventBus -> PassiveSupervisor",
        "PassiveSupervisor -> VisPy",
    ):
        assert marker in graph


def test_report_marks_tracer_bullet_not_real_backend() -> None:
    report = REPORT.read_text(encoding="utf-8")
    for marker in (
        "live_path_status: transition",
        "live_path_uses_real_backend: false",
        "provider_active: true",
        "network_added: false",
        "external_dependencies_added: false",
        "scheduler_modified: false",
    ):
        assert marker in report


def test_manifest_contains_no_generated_or_binary_artifact() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for marker in ("__pycache__", ".pyc", ".pyo", ".svg"):
        assert marker not in manifest
