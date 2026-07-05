from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / "doc" / "architecture" / "GRAPH_ARCHITECTURE_AUDIT_0099.md"
PLAN = ROOT / "doc" / "architecture" / "CONTROLPROXY_OPERATIONAL_PLAN_0099.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "90_controlproxy_runtime_overlay.dot"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0099_CHANGED_FILES.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_0099_graph_audit_files_exist() -> None:
    assert AUDIT.exists()
    assert PLAN.exists()
    assert DOT.exists()
    assert MANIFEST.exists()


def test_0099_audit_names_root_and_individual_graph_families() -> None:
    text = _read(AUDIT)
    required = [
        "doc/docs/architecture/00_global.dot",
        "scheduler/10_scheduler.dot",
        "scheduler/dispatcher/",
        "scheduler/event_bus/",
        "scheduler/priority_queue/",
        "scheduler/component_proxy/",
        "context/20_context.dot",
        "context/36_local_context_loop_design.dot",
        "services/30_services.dot",
        "experts/40_experts.dot",
        "validation/50_validation.dot",
        "learning/60_learning.dot",
        "observability/70_observability.dot",
        "runtime/90_controlproxy_runtime_overlay.dot",
    ]
    for phrase in required:
        assert phrase in text


def test_0099_overlay_is_attached_not_isolated() -> None:
    text = _read(AUDIT) + "\n" + _read(DOT)
    required = [
        "root-attached runtime overlay",
        "not an isolated island",
        "ROOT_GRAPH: doc/docs/architecture/00_global.dot",
        "RootGlobal -> ControlProxy",
        "SchedulerGraph -> ComponentProxy",
        "DispatcherGraph -> Dispatcher",
        "EventBusGraph -> ExistingEventBus",
        "ContextGraph -> TaskContext",
        "ObservabilityGraph -> Recorder",
    ]
    for phrase in required:
        assert phrase in text


def test_0099_overlay_covers_controlproxy_phases() -> None:
    text = _read(DOT)
    required = [
        "ControlProxySchedulerRouteRequestHandler",
        "handle_scheduler_route_request()",
        "prepare_route_for_scheduler()",
        "tick_controlproxy()",
        "active route materializer",
        "route lease state",
        "RouteGenerationTable",
        "route_id -> current_generation",
        "RouteGenerationLock",
        "locked materializer",
        "RouteRuntimePlacementPolicy",
        "RouteGenerationLifecycle",
        "RouteNotifier",
        "RouteWriteNotifyDrain",
        "RouteMessageJournal",
        "existing-bus visualization adapter",
        "RouteDispatchFilterEnvelope",
        "g2/g3",
    ]
    for phrase in required:
        assert phrase in text


def test_0099_dispatch_filtering_language_is_not_security_authority() -> None:
    text = _read(AUDIT) + "\n" + _read(PLAN) + "\n" + _read(DOT)
    required = [
        "dispatch filtering",
        "not policy invention",
        "not a separate ControlProxy security authority",
        "Scheduler/policy/zone remain the dispatch authority",
        "facts, not commands",
        "Qdrant\\nprojection/search only",
    ]
    for phrase in required:
        assert phrase in text


def test_0099_scheduler_run_constraint_remains_documented() -> None:
    text = _read(AUDIT) + "\n" + _read(PLAN)
    required = [
        "Do not release the `Scheduler.run()` constraint yet.",
        "Do not modify `Scheduler.run()` yet.",
        "Scheduler.emit()",
        "PolicyEngine.decide()",
        "PriorityQueue",
        "Scheduler.run()",
        "Dispatcher",
        "Handler",
    ]
    for phrase in required:
        assert phrase in text


def test_0099_manifest_stays_doc_and_rule_only() -> None:
    text = _read(MANIFEST)
    assert "src/kernel/scheduler.py" not in text
    assert "src/kernel/queue.py" not in text
    assert "src/kernel/dispatcher.py" not in text
    assert "src/contracts/component.py" not in text
    assert "doc/docs/architecture/runtime/90_controlproxy_runtime_overlay.dot" in text
    assert "tests/rules/test_architecture_graph_inventory_0099_rule.py" in text
