from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0266_source_locks_passive_supervisor_boundary() -> None:
    source = (ROOT / "src/context/passive_supervisor_closed_result_frame_observation_0266.py").read_text(
        encoding="utf-8"
    )

    assert "PassiveSupervisor observes only" in source
    assert "EventBus facts remain facts, not commands" in source
    assert "0266 does not execute SQL, OpenVINO, or Qdrant" in source
    assert "does not subscribe to a live bus" in source
    assert "build_passive_supervisor_closed_frame_observation_report" in source
    assert "EventBus(" not in source
    assert "publish(" not in source
    assert "subprocess.run" not in source
    assert "RuntimeManager(" not in source
    assert "Scheduler.run(" not in source


def test_0266_docs_lock_axis() -> None:
    doc = (ROOT / "doc/architecture/PASSIVE_SUPERVISOR_CLOSED_RESULT_FRAME_OBSERVATION_0266.md").read_text(
        encoding="utf-8"
    )

    assert "PassiveSupervisor closed ResultFrame observation" in doc
    assert "PassiveSupervisor observes only" in doc
    assert "EventBus facts remain facts, not commands" in doc
    assert "does not execute SQL, OpenVINO, or Qdrant" in doc
    assert "0267 can prepare the GitHub scan-once handoff" in doc
