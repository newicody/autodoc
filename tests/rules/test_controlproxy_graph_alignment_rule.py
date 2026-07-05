from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "CONTROLPROXY_GRAPH_ALIGNMENT_0097.md"
DOT = ROOT / "doc" / "architecture" / "RUNTIME_CONTROLFS_SHM_CLUSTER_FABRIC_GRAPH_0097.dot"
PLAN = ROOT / "doc" / "architecture" / "CONTROLPROXY_OPERATIONAL_PLAN_0097.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0097_CHANGED_FILES.md"
REPORT = ROOT / "PHASE0097_TEST_REPORT.md"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_0097_graph_is_integrated_root_graph() -> None:
    text = "\n".join(_read(path) for path in (DOC, DOT, PLAN, REPORT))
    required = [
        "Root graph, not an isolated phase graph",
        "digraph runtime_controlfs_shm_cluster_fabric_graph_0097",
        "subgraph cluster_policy_zone",
        "subgraph cluster_controlproxy_controlfs",
        "subgraph cluster_runtime_surfaces",
        "subgraph cluster_future_extensions",
        "ControlProxy / ControlFS bounded subsystem",
        "existing event.bus",
        "existing context.bus",
    ]
    for phrase in required:
        assert phrase in text


def test_0097_policy_zone_boundary_stays_authoritative_upstream() -> None:
    text = "\n".join(_read(path) for path in (DOC, DOT, PLAN, REPORT))
    required = [
        "ControlProxy enforces authorized route decisions but does not decide policy",
        "Scheduler/policy/zone remain the authority",
        "authorized=True",
        "policy_decision_id",
        "zone",
        "Dispatcher selects and invokes the registered handler",
        "Scheduler.run() -> Dispatcher -> ControlProxy route handler -> ControlProxy/ControlFS",
    ]
    for phrase in required:
        assert phrase in text


def test_0097_scheduler_loop_remains_locked_until_explicit_design() -> None:
    text = "\n".join(_read(path) for path in (DOC, DOT, PLAN, REPORT))
    required = [
        "No Scheduler.run() modification",
        "explicit loop-extension design",
        "PolicyEngine and zone checks stay before execution",
        "the patch explains why the change is kernel-loop work and not ControlProxy shortcut work",
    ]
    for phrase in required:
        assert phrase in text


def test_0097_operational_invariants_are_present() -> None:
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
        "live_path_status: n/a",
    ]
    for phrase in required:
        assert phrase in text


def test_0097_manifest_does_not_claim_kernel_or_runtime_changes() -> None:
    manifest = _read(MANIFEST)
    expected = [
        "doc/architecture/CONTROLPROXY_GRAPH_ALIGNMENT_0097.md",
        "doc/architecture/RUNTIME_CONTROLFS_SHM_CLUSTER_FABRIC_GRAPH_0097.dot",
        "doc/architecture/CONTROLPROXY_OPERATIONAL_PLAN_0097.md",
        "doc/manifests/MANIFEST_0097_CHANGED_FILES.md",
        "tests/rules/test_controlproxy_graph_alignment_rule.py",
        "PHASE0097_TEST_REPORT.md",
    ]
    for path in expected:
        assert path in manifest
    forbidden = [
        "src/kernel/scheduler.py",
        "src/kernel/queue.py",
        "src/kernel/dispatcher.py",
        "src/runtime/controlproxy_scheduler_handler.py",
        "src/runtime/route_runtime_placement.py",
    ]
    for path in forbidden:
        assert path not in manifest
