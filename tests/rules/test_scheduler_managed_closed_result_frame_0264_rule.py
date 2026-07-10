from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0264_source_locks_result_frame_boundary() -> None:
    source = (ROOT / "src/context/scheduler_managed_closed_result_frame_0264.py").read_text(
        encoding="utf-8"
    )

    assert "0264 does not execute SQL, OpenVINO, or Qdrant" in source
    assert "SQL remains the durable authority" in source
    assert "Qdrant remains projection/recall only" in source
    assert "Scheduler does not start PostgreSQL, OpenVINO, or Qdrant" in source
    assert "compose_scheduler_managed_closed_result_frame" in source
    assert "subprocess.run" not in source
    assert "RuntimeManager(" not in source
    assert "Scheduler.run(" not in source


def test_0264_docs_lock_axis() -> None:
    doc = (ROOT / "doc/architecture/SCHEDULER_MANAGED_CLOSED_RESULT_FRAME_0264.md").read_text(
        encoding="utf-8"
    )

    assert "Scheduler-managed closed ResultFrame" in doc
    assert "0260 -> 0261 -> 0262 -> 0263" in doc
    assert "does not execute SQL, OpenVINO, or Qdrant" in doc
    assert "SQL remains the durable authority" in doc
    assert "0265 can attach EventBus observation-only facts" in doc
