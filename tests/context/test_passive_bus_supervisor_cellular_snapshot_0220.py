from src.context.passive_bus_supervisor_cellular_snapshot import (
    AUTHORITY_BOUNDARY,
    BusSupervisorEvent,
    build_cellular_snapshot,
    event_from_mapping,
)


def test_passive_bus_supervisor_snapshot_keeps_latest_cell_state() -> None:
    events = [
        BusSupervisorEvent(
            event_id="evt-1",
            event_kind="scheduler_tick",
            cell_id="scheduler",
            cell_kind="SCHEDULER",
            state="running",
            observed_at="2026-07-08T00:00:00Z",
        ),
        BusSupervisorEvent(
            event_id="evt-2",
            event_kind="scheduler_idle",
            cell_id="scheduler",
            cell_kind="SCHEDULER",
            state="success",
            observed_at="2026-07-08T00:00:01Z",
        ),
        BusSupervisorEvent(
            event_id="evt-3",
            event_kind="policy_blocked",
            cell_id="policy",
            cell_kind="POLICY_GATE",
            state="blocked",
            observed_at="2026-07-08T00:00:02Z",
            policy_decision_id="policy-1",
            error="write denied",
        ),
    ]

    snapshot = build_cellular_snapshot(
        events,
        generated_at="2026-07-08T00:00:03Z",
        metadata={"source": "test"},
    )
    payload = snapshot.to_dict()

    assert payload["event_count"] == 3
    assert payload["cell_count"] == 2
    assert payload["blocked_count"] == 1
    assert payload["failed_count"] == 0
    assert payload["stale_count"] == 0
    assert payload["authority_boundary"]["observation_only"] is True
    assert payload["authority_boundary"]["allows_scheduler_run"] is False
    assert payload["authority_boundary"]["allows_sql_write"] is False
    assert payload["authority_boundary"]["allows_qdrant_write"] is False

    cells = {cell["cell_id"]: cell for cell in payload["cells"]}
    assert cells["scheduler"]["state"] == "success"
    assert cells["scheduler"]["event_count"] == 2
    assert cells["policy"]["health"] == "blocked"
    assert cells["policy"]["refs"]["policy_decision_id"] == "policy-1"


def test_event_from_mapping_normalizes_unknown_values() -> None:
    event = event_from_mapping(
        {
            "event_id": "evt-unknown",
            "event_kind": "custom_event",
            "cell_id": "custom",
            "cell_kind": "new-kind",
            "state": "custom-state",
            "observed_at": "2026-07-08T00:00:00Z",
            "payload": {"attempt": 1},
        }
    )

    assert event.cell_kind == "UNKNOWN"
    assert event.state == "unknown"
    assert event.payload == {"attempt": "1"}


def test_authority_boundary_is_passive_and_stdlib_only() -> None:
    assert AUTHORITY_BOUNDARY["observation_only"] is True
    assert AUTHORITY_BOUNDARY["allows_github_mutation"] is False
    assert AUTHORITY_BOUNDARY["allows_proxy_control"] is False
    assert AUTHORITY_BOUNDARY["requires_non_stdlib"] is False
