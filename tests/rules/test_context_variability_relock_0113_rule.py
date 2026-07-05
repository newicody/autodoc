from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "CONTEXT_VARIABILITY_RELOCK_0113.md"
PLAN = ROOT / "doc" / "architecture" / "CONTEXT_VARIABILITY_OPERATIONAL_PLAN_0113.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "103_context_variability_relock.dot"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0113_CHANGED_FILES.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_0113_recenters_on_context_variability() -> None:
    text = _read(DOC) + "\n" + _read(PLAN)
    required = [
        "ContextRequest -> ContextCollector -> ContextVariant[] -> ContextReducer -> GlobalContextSnapshot -> InferenceContext",
        "produce solutions quickly",
        "context variability",
        "Policy/security/zone are guardrails, not the objective",
        "No CapabilityRequest security-first direction",
        "No route-journal-first AI pipeline",
    ]
    for phrase in required:
        assert phrase in text


def test_0113_locks_context_authority_and_projection_roles() -> None:
    text = _read(DOC) + "\n" + _read(PLAN) + "\n" + _read(DOT)
    required = [
        "SQLContextStore = durable context authority",
        "ContextGate / TaskContext = authority for context selection",
        "Qdrant = vector projection and retrieval, not context authority",
        "OpenVINO = local embedding/inference worker",
        "LLM = specialist/enricher that consumes InferenceContext",
        "ControlProxy / RouteRuntimeManager = secondary data plane",
        "Route mmap/eventfd = data plane, not EventBus",
        "EventBus = observation only",
    ]
    for phrase in required:
        assert phrase in text


def test_0113_graph_is_root_attached_and_not_a_parallel_architecture() -> None:
    dot = _read(DOT)
    required = [
        "ROOT_GRAPH: doc/docs/architecture/00_global.dot",
        "root-attached context/runtime overlay",
        "ContextRequest",
        "ContextVariant[]",
        "ContextReducer",
        "InferenceContext",
        "Scheduler",
        "Dispatcher",
        "Handler",
        "No second bus",
    ]
    for phrase in required:
        assert phrase in dot


def test_0113_manifest_is_docs_graph_rules_only() -> None:
    manifest = _read(MANIFEST)
    assert "tests/rules/test_context_variability_relock_0113_rule.py" in manifest
    assert "doc/docs/architecture/runtime/103_context_variability_relock.dot" in manifest
    forbidden = [
        "src/kernel/scheduler.py",
        "src/kernel/dispatcher.py",
        "src/kernel/queue.py",
        "src/policy/engine.py",
        "src/kernel/event_bus.py",
        "src/runtime/route_runtime_manager.py",
        "src/contracts/capability.py",
    ]
    for path in forbidden:
        assert path not in manifest


def test_0113_phase_report_declares_no_runtime_capability() -> None:
    report = _read(ROOT / "PHASE0113_TEST_REPORT.md")
    required = [
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: n/a",
        "context_contract_changed: false",
        "no runtime code",
        "no Qdrant/OpenVINO/LLM import",
        "no SQL runtime code yet",
    ]
    for phrase in required:
        assert phrase in report
