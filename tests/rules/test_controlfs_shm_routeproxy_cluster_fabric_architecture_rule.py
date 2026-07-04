from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
GRAPH_DOC = ROOT / "doc" / "architecture" / "RUNTIME_CONTROLFS_SHM_CLUSTER_FABRIC_GRAPH.md"
PLAN_DOC = ROOT / "doc" / "architecture" / "RUNTIME_CONTROLFS_SHM_PRIORITY_PLAN.md"
ADR_DOC = ROOT / "doc" / "architecture" / "ADR-0062-controlfs-shm-routeproxy-cluster-fabric.md"


def _read(path: Path) -> str:
    assert path.exists(), f"missing architecture document: {path}"
    return path.read_text(encoding="utf-8")


def test_controlfs_shm_routeproxy_graph_locks_the_runtime_surfaces() -> None:
    text = _read(GRAPH_DOC)

    required_phrases = [
        "SecurityFS decides the rules.",
        "Scheduler compiles and writes desired state.",
        "ControlFS carries declarative state.",
        "RouteProxy materializes routes.",
        "SHM Runtime carries fast local runtime traffic.",
        "DataHandle references heavy payloads.",
        "Recorder persists facts.",
        "ZFS Store keeps durable memory.",
        "NetworkBridge and Hardware Cluster Fabric are future extensions.",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_routeproxy_is_passive_and_does_not_call_scheduler() -> None:
    text = _read(GRAPH_DOC) + "\n" + _read(ADR_DOC)

    required_phrases = [
        "RouteProxy passively watches ControlFS.",
        "RouteProxy creates/deletes shm routes and semaphores.",
        "RouteProxy does not call Scheduler.",
        "RouteProxy does not decide security.",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_scheduler_is_not_a_payload_pipe() -> None:
    text = _read(GRAPH_DOC)

    required_phrases = [
        "The Scheduler should not become a throughput pipe.",
        "large PDFs",
        "large embeddings",
        "large blobs",
        "network streams",
        "full datasets",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_priorities_keep_network_and_hardware_as_future_only() -> None:
    text = _read(PLAN_DOC)

    required_phrases = [
        "P0 docs vocabulary and graph",
        "P1 ControlFS schema",
        "P2 RouteProxy dry-run reconciler",
        "P3 SHM message/handle schemas",
        "P4 baby-fork route vocabulary integration",
        "P5 local shm/semaphore prototype",
        "P7 NetworkBridge design only",
        "P8 Hardware Cluster Fabric design only",
        "Do not implement FPGA/ASIC bridge.",
        "Do not implement network routing.",
    ]

    for phrase in required_phrases:
        assert phrase in text


def test_hardware_cluster_fabric_is_kept_as_distant_future() -> None:
    text = _read(GRAPH_DOC) + "\n" + _read(PLAN_DOC)

    required_phrases = [
        "Hardware Cluster Fabric is future lointain",
        "FPGA/ASIC does not share /dev/shm directly.",
        "DMA-backed route buffers",
        "LVDS or a dedicated direct link",
        "cluster task dispatch future",
    ]

    for phrase in required_phrases:
        assert phrase in text
