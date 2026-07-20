from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/runtime/controlproxy_scheduler_adapter.py"
ARCHITECTURE = (
    ROOT
    / "doc/architecture/CONTROLPROXY_SCHEDULER_ADAPTER_0287_R16_R43.md"
)
RULE = (
    ROOT
    / "doc/code-rules/0287_r16_r43_controlproxy_scheduler_adapter_rule.md"
)


def test_r16_r43_adapter_keeps_locked_runtime_boundaries() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    assert "AUTODOC_CONTROLFS_ROOT" in text
    assert "prepare_dev_shm_route_runtime_root" in text
    assert "handle_scheduler_route_request as _handle_scheduler_route_request" in text
    assert "publish_bus=False" in text
    assert "ensure_desired_scheduler_route_manifest" in text

    for forbidden in (
        "Scheduler(",
        "Dispatcher(",
        "PriorityQueue(",
        "EventBus(",
        "Thread(",
        "Process(",
        ".jsonl",
        "psycopg",
        "qdrant",
    ):
        assert forbidden not in text


def test_r16_r43_documents_json_boundary_and_single_scheduler() -> None:
    architecture = ARCHITECTURE.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")
    combined = architecture + "\n" + rule

    assert "Scheduler canonique unique" in combined
    assert "PostgreSQL" in combined
    assert "ControlFS" in combined
    assert "/dev/shm" in combined
    assert "JSON" in combined
    assert "file JSONL" in combined
    assert "OpenRC" in combined
