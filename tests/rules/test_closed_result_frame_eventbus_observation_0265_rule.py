from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0265_source_locks_eventbus_observation_boundary() -> None:
    source = (ROOT / "src/context/closed_result_frame_eventbus_observation_0265.py").read_text(
        encoding="utf-8"
    )

    assert "EventBus is observation only" in source
    assert "Events are facts, not commands" in source
    assert "0265 does not execute SQL, OpenVINO, or Qdrant" in source
    assert "EventBus()" in source
    assert "event_bus.publish" in source
    assert "request=None" in source
    assert "subprocess.run" not in source
    assert "RuntimeManager(" not in source
    assert "Scheduler.run(" not in source


def test_0265_docs_lock_axis() -> None:
    doc = (ROOT / "doc/architecture/CLOSED_RESULT_FRAME_EVENTBUS_OBSERVATION_0265.md").read_text(
        encoding="utf-8"
    )

    assert "Closed ResultFrame EventBus observation" in doc
    assert "EventBus observation only" in doc
    assert "Events are facts, not commands" in doc
    assert "does not execute SQL, OpenVINO, or Qdrant" in doc
    assert "0266 can attach PassiveSupervisor observation" in doc
