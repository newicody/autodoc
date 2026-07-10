from context.closed_result_frame_eventbus_observation_0265 import (
    build_and_optionally_publish_closed_result_frame_eventbus_observation,
    build_closed_result_frame_eventbus_observation_report,
    observation_fact_to_event,
)


FRAME = {
    "schema": "missipy.scheduler_managed_closed_result_frame.v1",
    "valid": True,
    "sql_ref": "sql:inference_context:test",
    "embedding_ref": "embedding:passage:test",
    "projection_point_count": 1,
    "recall_hit_count": 1,
    "hydrated_count": 1,
    "missing_count": 0,
    "sql_remains_authority": True,
    "qdrant_projection_recall_refs_only": True,
    "openvino_already_executed_by_0261": True,
    "executes_runtime": False,
    "starts_postgresql": False,
    "starts_openvino": False,
    "starts_qdrant": False,
    "modifies_scheduler_run": False,
    "trace": {"0260": {}, "0261": {}, "0262": {}, "0263": {}},
}


def test_observation_report_builds_fact_only_events() -> None:
    report = build_closed_result_frame_eventbus_observation_report(FRAME, frame_ref="frame:0264")
    payload = report.to_mapping()

    assert payload["valid"] is True
    assert payload["fact_count"] == 3
    assert payload["eventbus_observation_only"] is True
    assert payload["events_are_facts_not_commands"] is True
    assert payload["executes_runtime"] is False

    event = observation_fact_to_event(report.facts[0])
    assert event.request is None
    assert event.dest == "observability"
    assert event.metadata["observation_only"] is True
    assert event.metadata["command"] is False


def test_observation_rejects_runtime_frame() -> None:
    frame = {**FRAME, "executes_runtime": True}
    report = build_closed_result_frame_eventbus_observation_report(frame, frame_ref="frame:bad")

    assert report.valid is False
    assert "closed ResultFrame observation must be non-runtime" in report.issues


def test_publish_demo_uses_eventbus_as_observation_channel() -> None:
    report = build_and_optionally_publish_closed_result_frame_eventbus_observation(
        FRAME,
        frame_ref="frame:0264",
        publish_demo=True,
    )
    payload = report.to_mapping()

    assert payload["valid"] is True
    assert payload["published_count"] == 3
    assert payload["observed_count"] == 3
    assert payload["event_types"] == ["INFERENCE_RESULT", "INFERENCE_RESULT", "INFERENCE_RESULT"]
