from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "runtime" / "route_dispatch_filter_envelope.py"
DOC = ROOT / "doc" / "architecture" / "CONTROLPROXY_DISPATCH_FILTERING_0098.md"
DOT = ROOT / "doc" / "architecture" / "RUNTIME_CONTROLFS_SHM_CLUSTER_FABRIC_GRAPH_0098.dot"
PLAN = ROOT / "doc" / "architecture" / "CONTROLPROXY_OPERATIONAL_PLAN_0098.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0098_CHANGED_FILES.md"
REPORT = ROOT / "PHASE0098_TEST_REPORT.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_0098_names_dispatch_filtering_instead_of_security_goal() -> None:
    text = "\n".join(_read(path) for path in (MODULE, DOC, DOT, PLAN, REPORT))
    required = [
        "policy/zone dispatch filtering",
        "not a security objective",
        "ControlProxy does not decide security policy",
        "Scheduler/policy/zone remain the authority",
        "security-shaped envelope",
        "boundary filter, not a new security decision",
    ]
    for phrase in required:
        assert phrase in text


def test_0098_graph_remains_integrated_root_graph() -> None:
    text = "\n".join(_read(path) for path in (DOC, DOT, PLAN, REPORT))
    required = [
        "Root graph, not an isolated phase graph",
        "digraph runtime_controlfs_shm_cluster_fabric_graph_0098",
        "subgraph cluster_policy_zone",
        "subgraph cluster_controlproxy_controlfs",
        "subgraph cluster_runtime_surfaces",
        "subgraph cluster_future_extensions",
        "RouteDispatchFilterEnvelope",
        "existing event.bus",
        "existing context.bus",
    ]
    for phrase in required:
        assert phrase in text


def test_0098_scheduler_loop_and_dispatcher_boundary_stay_locked() -> None:
    text = "\n".join(_read(path) for path in (DOC, DOT, PLAN, REPORT))
    required = [
        "No Scheduler.run() modification",
        "Dispatcher remains required",
        "Dispatcher -> Handler path is still sufficient",
        "Scheduler.run() and ControlProxy",
        "Dispatcher is the kernel dispatch boundary",
    ]
    for phrase in required:
        assert phrase in text


def test_0098_module_is_importable_envelope_not_io_or_bus() -> None:
    source = _read(MODULE)
    required = [
        "class RouteDispatchFilterEnvelope",
        "class RouteDispatchFilterDecision",
        "def evaluate_route_dispatch_filter",
        "def require_route_dispatch_filter_envelope",
        "authorized=True is required",
    ]
    for phrase in required:
        assert phrase in source
    forbidden = [
        "argparse",
        "subprocess",
        "Thread",
        "EventBus(",
        "ContextBus(",
        "Scheduler.run",
        "import qdrant",
        "openvino",
    ]
    for phrase in forbidden:
        assert phrase not in source


def test_0098_operational_invariants_are_present() -> None:
    text = "\n".join(_read(path) for path in (DOC, DOT, PLAN, REPORT))
    required = [
        "No CLI",
        "No OpenRC service and no resident daemon",
        "No watcher",
        "No live mmap resize",
        "g2/g3",
        "Not /dev/shm-only",
        "No NetworkBridge or HardwareBridge implementation",
        "No Qdrant, LLM, or OpenVINO path",
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: transition",
    ]
    for phrase in required:
        assert phrase in text


def test_0098_manifest_keeps_kernel_files_out() -> None:
    manifest = _read(MANIFEST)
    expected = [
        "src/runtime/route_dispatch_filter_envelope.py",
        "tests/runtime/test_route_dispatch_filter_envelope.py",
        "tests/rules/test_route_dispatch_filter_envelope_rule.py",
        "doc/architecture/CONTROLPROXY_DISPATCH_FILTERING_0098.md",
        "doc/architecture/RUNTIME_CONTROLFS_SHM_CLUSTER_FABRIC_GRAPH_0098.dot",
        "doc/architecture/CONTROLPROXY_OPERATIONAL_PLAN_0098.md",
        "doc/manifests/MANIFEST_0098_CHANGED_FILES.md",
        "PHASE0098_TEST_REPORT.md",
    ]
    for path in expected:
        assert path in manifest
    forbidden = [
        "src/kernel/scheduler.py",
        "src/kernel/queue.py",
        "src/kernel/dispatcher.py",
    ]
    for path in forbidden:
        assert path not in manifest
