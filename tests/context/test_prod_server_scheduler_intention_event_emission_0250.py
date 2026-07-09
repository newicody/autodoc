from pathlib import Path

from context.prod_server_scheduler_intention_event_emission_0250 import (
    SCHEDULER_INTENTION_EVENT_EMISSION_BOUNDARY,
    TypedSchedulerIntention,
    event_envelope_from_intention,
    sample_scheduler_intention,
    write_scheduler_intention_event_emission_report,
)


ROOT = Path(__file__).resolve().parents[2]
SERVER_CONFIG = ROOT / "doc/examples/autodoc_prod_server_initial_0241.ini"
OPENVINO_CONFIG = ROOT / "doc/examples/autodoc_openvino_embedding_e5_small_0246.ini"


def test_scheduler_intention_event_boundary_is_emission_surface_only() -> None:
    assert SCHEDULER_INTENTION_EVENT_EMISSION_BOUNDARY == {
        "emission_surface_only": True,
        "uses_eventbus_attribute_readiness": True,
        "creates_eventbus": False,
        "publishes_events": False,
        "calls_scheduler_run": False,
        "dispatches_handler": False,
        "starts_threads": False,
        "writes_postgresql": False,
        "runs_openvino_inference": False,
        "writes_qdrant": False,
        "calls_github_api": False,
        "requires_non_stdlib": False,
    }


def test_sample_intention_builds_valid_event_envelope() -> None:
    report = event_envelope_from_intention(
        sample_scheduler_intention(),
        server_config_path=SERVER_CONFIG,
        openvino_config_path=OPENVINO_CONFIG,
    )

    assert report.valid is True
    assert report.issues == ()
    assert report.envelope is not None
    assert report.envelope.schema_version == "0250.r1"
    assert report.envelope.event_type == "scheduler.intention.observed"
    assert report.envelope.attributes["intent_id"] == report.intention.intent_id
    assert report.envelope.attributes["sql_ref"] == "context_records.id"
    assert "payload_json" not in report.envelope.attributes


def test_secret_is_redacted() -> None:
    intention = TypedSchedulerIntention(
        intent_id="intent:secret",
        intent_type="scheduler.intent.secret-test",
        component="scheduler",
        phase="D07_functional_handler_chain",
        trace_id="trace:secret",
        priority=10,
        secret="top-secret",
    )

    report = event_envelope_from_intention(
        intention,
        server_config_path=SERVER_CONFIG,
        openvino_config_path=OPENVINO_CONFIG,
    )

    assert report.valid is True
    assert report.envelope is not None
    assert report.envelope.attributes["secret"] == "<redacted>"
    assert report.intention.secret == "<redacted>"


def test_write_scheduler_intention_event_emission_report(tmp_path: Path) -> None:
    output = tmp_path / "scheduler_intention_event_emission.json"
    payload = write_scheduler_intention_event_emission_report(
        server_config_path=SERVER_CONFIG,
        openvino_config_path=OPENVINO_CONFIG,
        output_path=output,
    )

    assert payload["production_server_scheduler_intention_event_emission_written"] is True
    assert payload["scheduler_intention_event_emission"]["valid"] is True
    assert output.exists()
