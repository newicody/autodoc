from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0249_eventbus_attributes_do_not_publish_or_trigger_runtime() -> None:
    source = (ROOT / "src/context/prod_server_eventbus_attributes_readiness_0249.py").read_text(
        encoding="utf-8"
    )
    lowered = source.lower()

    assert "readiness_only" in source
    assert "creates_eventbus" in source
    assert "publishes_events" in source
    assert "triggers_scheduler" in source
    assert "runs_openvino_inference" in source
    assert "writes_qdrant" in source
    assert "EventBus(" not in source
    assert ".publish(" not in lowered
    assert "scheduler.run(" not in lowered
    assert "subprocess.run" not in source
    assert "requests." not in lowered
    assert ".upsert(" not in lowered


def test_0249_docs_lock_eventbus_attribute_boundary() -> None:
    doc = (ROOT / "doc/architecture/PROD_SERVER_EVENTBUS_ATTRIBUTES_READINESS_0249.md").read_text(
        encoding="utf-8"
    )

    assert "EventBus advanced attribute readiness" in doc
    assert "EventBus remains observation only" in doc
    assert "refs only, no large payloads" in doc
    assert "schema_version" in doc
    assert "0250" in doc
