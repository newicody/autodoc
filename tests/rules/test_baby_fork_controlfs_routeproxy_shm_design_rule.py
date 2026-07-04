from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MANIFEST_DOC = ROOT / "doc" / "architecture" / "BABY_FORK_CONTROLFS_ROUTE_MANIFESTS.md"
PLAN_DOC = ROOT / "doc" / "architecture" / "BABY_FORK_ROUTEPROXY_DRY_RUN_PLAN.md"
SHM_DOC = ROOT / "doc" / "architecture" / "SHM_RING_BUFFER_BOUNDARY_DESIGN.md"
MODULE = ROOT / "src" / "context" / "baby_fork_controlfs.py"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_baby_fork_controlfs_doc_locks_desired_routes() -> None:
    text = _read(MANIFEST_DOC)

    required_phrases = [
        "baby_fork.retrieval",
        "baby_fork.variant_stub",
        "baby_fork.context_gate",
        "desired/",
        "routes/",
        "active route creation",
        "real shared memory",
        "RouteProxy daemon",
        "Scheduler wiring",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_baby_fork_routeproxy_plan_doc_locks_create_plan() -> None:
    text = _read(PLAN_DOC)

    required_phrases = [
        "create baby_fork.context_gate",
        "create baby_fork.retrieval",
        "create baby_fork.variant_stub",
        "does not materialize routes",
        "real shared memory",
        "semaphores",
        "RouteProxy daemon",
        "Scheduler wiring",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_shm_ring_design_is_design_only() -> None:
    text = _read(SHM_DOC)

    required_phrases = [
        "Status: 0073 design only.",
        "/dev/shm/autodoc/",
        "event.bus",
        "context.bus",
        "data.index",
        "routes/<route_id>/",
        "Notification is separate from payload.",
        "real shared memory implementation",
        "mmap implementation",
        "ring buffer code",
        "eventfd code",
        "futex code",
        "semaphore code",
        "RouteProxy daemon",
        "Scheduler wiring",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_baby_fork_controlfs_module_is_manifest_and_plan_only() -> None:
    text = _read(MODULE)

    required_phrases = [
        "It only writes desired route manifests",
        "create shared memory",
        "create semaphores",
        "start RouteProxy",
        "start Scheduler",
        "write active/routes",
        "mutate revoked/routes",
        "implement NetworkBridge or HardwareBridge",
    ]

    for phrase in required_phrases:
        assert phrase in text
