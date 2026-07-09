from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0250_intention_event_does_not_publish_or_run_scheduler() -> None:
    source = (ROOT / "src/context/prod_server_scheduler_intention_event_emission_0250.py").read_text(
        encoding="utf-8"
    )
    lowered = source.lower()

    assert "emission_surface_only" in source
    assert "creates_eventbus" in source
    assert "publishes_events" in source
    assert "calls_scheduler_run" in source
    assert "dispatches_handler" in source
    assert "runs_openvino_inference" in source
    assert "EventBus(" not in source
    assert ".publish(" not in lowered
    assert "scheduler.run(" not in lowered
    assert "subprocess.run" not in source
    assert "requests." not in lowered
    assert ".execute(" not in lowered
    assert ".upsert(" not in lowered


def test_0250_docs_lock_intention_event_boundary() -> None:
    doc = (ROOT / "doc/architecture/PROD_SERVER_SCHEDULER_INTENTION_EVENT_EMISSION_0250.md").read_text(
        encoding="utf-8"
    )

    assert "Scheduler intention event emission" in doc
    assert "No EventBus is created" in doc
    assert "No Scheduler.run call is made" in doc
    assert "EventBus remains observation only" in doc
    assert "0251" in doc
