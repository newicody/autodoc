from context.passive_supervisor_closed_result_frame_observation_0266 import (
    build_passive_supervisor_closed_frame_observation_report,
)


OBSERVATION_REPORT = {
    "valid": True,
    "eventbus_observation_only": True,
    "events_are_facts_not_commands": True,
    "executes_runtime": False,
    "starts_postgresql": False,
    "starts_openvino": False,
    "starts_qdrant": False,
    "modifies_scheduler_run": False,
    "facts": [
        {
            "fact_ref": "event-fact:0265:sql:x:closed",
            "fact_kind": "closed_result_frame.validated",
            "observation_only": True,
            "command": False,
            "payload": {"sql_ref": "sql:x", "frame_ref": "frame:0264"},
        },
        {
            "fact_ref": "event-fact:0265:sql:x:authority",
            "fact_kind": "closed_result_frame.authority_boundary",
            "observation_only": True,
            "command": False,
            "payload": {"sql_ref": "sql:x", "frame_ref": "frame:0264"},
        },
    ],
}


def test_passive_supervisor_accepts_observation_only_facts() -> None:
    report = build_passive_supervisor_closed_frame_observation_report(
        OBSERVATION_REPORT,
        source_observation_ref="obs:0265",
    )
    payload = report.to_mapping()

    assert payload["valid"] is True
    assert payload["fact_count"] == 2
    assert payload["accepted_fact_count"] == 2
    assert payload["rejected_fact_count"] == 0
    assert payload["passive_supervisor_observation_only"] is True
    assert payload["executes_runtime"] is False
    assert payload["publishes_events"] is False
    assert all(finding["command"] is False for finding in payload["findings"])


def test_passive_supervisor_rejects_command_like_fact() -> None:
    bad = {
        **OBSERVATION_REPORT,
        "facts": [{**OBSERVATION_REPORT["facts"][0], "command": True}],
    }
    report = build_passive_supervisor_closed_frame_observation_report(
        bad,
        source_observation_ref="obs:0265",
    )
    payload = report.to_mapping()

    assert payload["valid"] is False
    assert payload["command_like_fact_count"] == 1
    assert payload["rejected_fact_count"] == 1


def test_passive_supervisor_rejects_runtime_input() -> None:
    bad = {**OBSERVATION_REPORT, "starts_qdrant": True}
    report = build_passive_supervisor_closed_frame_observation_report(
        bad,
        source_observation_ref="obs:0265",
    )

    assert report.valid is False
    assert "PassiveSupervisor input must not start Qdrant" in report.issues
