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


def test_passive_supervisor_sink_accepts_scheduler_bus_events_without_journal() -> None:
    from src.context.passive_bus_supervisor_cellular_snapshot import PassiveSupervisorSink

    sink = PassiveSupervisorSink(metadata={"surface": "eventbus"})
    normalized = sink.accept(
        {
            "event_id": "evt-scheduler-1",
            "event_kind": "scheduler_handler_completed",
            "cell_id": "scheduler:default",
            "cell_kind": "SCHEDULER",
            "state": "success",
            "observed_at": "2026-07-08T00:00:00Z",
            "source_ref": "scheduler:default",
            "payload": {"handler": "existing"},
        }
    )
    sink.accept(
        {
            "event_id": "evt-policy-1",
            "event_kind": "policy_decision_observed",
            "cell_id": "policy:gate",
            "cell_kind": "POLICY_GATE",
            "state": "blocked",
            "observed_at": "2026-07-08T00:00:01Z",
            "policy_decision_id": "policy-1",
            "artifact_ref": "artifact-1",
            "sql_ref": "sql-1",
            "qdrant_ref": "qdrant-1",
        }
    )

    assert normalized.event_kind == "scheduler_handler_completed"
    assert sink.event_count() == 2

    payload = sink.snapshot_payload(generated_at="2026-07-08T00:00:02Z")
    cells = {cell["cell_id"]: cell for cell in payload["cells"]}

    assert payload["event_count"] == 2
    assert payload["blocked_count"] == 1
    assert payload["audit_journal_enabled"] is False
    assert payload["cellular_snapshot_written"] is False
    assert payload["metadata"]["scheduler_role"] == "upstream_orchestration_authority"
    assert payload["metadata"]["eventbus_role"] == "canonical_runtime_event_transport"
    assert cells["scheduler:default"]["cell_kind"] == "SCHEDULER"
    assert cells["policy:gate"]["refs"]["policy_decision_id"] == "policy-1"
    assert cells["policy:gate"]["refs"]["artifact_ref"] == "artifact-1"
    assert cells["policy:gate"]["refs"]["sql_ref"] == "sql-1"
    assert cells["policy:gate"]["refs"]["qdrant_ref"] == "qdrant-1"


def test_passive_supervisor_sink_audit_is_optional(tmp_path) -> None:
    from src.context.passive_bus_supervisor_cellular_snapshot import PassiveSupervisorSink

    audit_jsonl = tmp_path / "audit" / "events.jsonl"
    snapshot_json = tmp_path / "snapshot.json"
    sink = PassiveSupervisorSink(audit_jsonl=audit_jsonl)

    sink.accept(
        {
            "event_id": "evt-route-1",
            "event_kind": "routeproxy_status_observed",
            "cell_id": "routeproxy:main",
            "cell_kind": "ROUTEPROXY",
            "state": "running",
            "observed_at": "2026-07-08T00:00:00Z",
            "route_ref": "route-1",
            "shm_ref": "shm-ring-1",
        }
    )
    payload = sink.write_snapshot(
        snapshot_json,
        generated_at="2026-07-08T00:00:01Z",
    )

    assert audit_jsonl.exists()
    assert snapshot_json.exists()
    assert payload["cellular_snapshot_written"] is True
    assert payload["audit_journal_enabled"] is True
    assert "routeproxy_status_observed" in audit_jsonl.read_text(encoding="utf-8")


def test_scheduler_supervision_event_is_canonical_and_sink_accepts_it() -> None:
    from src.context.passive_bus_supervisor_cellular_snapshot import (
        PassiveSupervisorSink,
        scheduler_supervision_event,
    )

    event = scheduler_supervision_event(
        event_id="evt-scheduler-0222",
        event_kind="scheduler_handler_completed",
        scheduler_ref="main",
        handler_ref="route-handler",
        state="success",
        observed_at="2026-07-08T00:00:00Z",
        route_ref="route-1",
        policy_decision_id="policy-1",
        payload={"cycle": "1"},
    )
    sink = PassiveSupervisorSink()
    sink.accept(event)
    payload = sink.snapshot_payload(generated_at="2026-07-08T00:00:01Z")
    cells = {cell["cell_id"]: cell for cell in payload["cells"]}

    assert event.cell_kind == "SCHEDULER"
    assert event.cell_id == "scheduler:main"
    assert event.source_ref == "scheduler:main"
    assert event.payload["handler_ref"] == "route-handler"
    assert cells["scheduler:main"]["refs"]["route_ref"] == "route-1"
    assert cells["scheduler:main"]["refs"]["policy_decision_id"] == "policy-1"
    assert payload["authority_boundary"]["allows_scheduler_run"] is False


def test_passive_supervisor_sink_accept_scheduler_event_keeps_scheduler_downstream() -> None:
    from src.context.passive_bus_supervisor_cellular_snapshot import PassiveSupervisorSink

    sink = PassiveSupervisorSink(metadata={"surface": "eventbus"})
    event = sink.accept_scheduler_event(
        event_id="evt-scheduler-accept-1",
        event_kind="scheduler_handler_started",
        scheduler_ref="main",
        handler_ref="route-handler",
        state="running",
        observed_at="2026-07-08T00:00:00Z",
    )
    snapshot = sink.snapshot_payload(generated_at="2026-07-08T00:00:01Z")

    assert event.cell_kind == "SCHEDULER"
    assert snapshot["event_count"] == 1
    assert snapshot["cells"][0]["health"] == "active"
    assert snapshot["supervision_authority_violation"] is False


def test_runtime_surface_events_keep_proxy_shm_policy_refs() -> None:
    from src.context.passive_bus_supervisor_cellular_snapshot import (
        PassiveSupervisorSink,
        policy_supervision_event,
        proxy_supervision_event,
        shm_supervision_event,
    )

    sink = PassiveSupervisorSink(metadata={"surface": "eventbus"})
    sink.accept(
        proxy_supervision_event(
            event_id="evt-routeproxy-1",
            event_kind="routeproxy_route_active",
            proxy_kind="routeproxy",
            proxy_ref="main",
            state="running",
            observed_at="2026-07-08T00:00:00Z",
            route_ref="route-1",
            shm_ref="route-ring-1",
        )
    )
    sink.accept(
        proxy_supervision_event(
            event_id="evt-controlproxy-1",
            event_kind="controlproxy_zone_visible",
            proxy_kind="controlproxy",
            proxy_ref="main",
            state="running",
            observed_at="2026-07-08T00:00:01Z",
            route_ref="route-1",
            shm_ref="route-ring-1",
        )
    )
    sink.accept(
        shm_supervision_event(
            event_id="evt-shm-1",
            event_kind="shm_ring_status_observed",
            shm_ref="route-ring-1",
            state="running",
            observed_at="2026-07-08T00:00:02Z",
            route_ref="route-1",
        )
    )
    sink.accept(
        policy_supervision_event(
            event_id="evt-policy-1",
            event_kind="policy_gate_decision_observed",
            policy_ref="gate",
            state="blocked",
            observed_at="2026-07-08T00:00:03Z",
            policy_decision_id="policy-1",
            route_ref="route-1",
            artifact_ref="artifact-1",
            sql_ref="sql-1",
            qdrant_ref="qdrant-1",
            shm_ref="route-ring-1",
            decision="blocked",
        )
    )

    payload = sink.snapshot_payload(generated_at="2026-07-08T00:00:04Z")
    cells = {cell["cell_id"]: cell for cell in payload["cells"]}

    assert payload["event_count"] == 4
    assert payload["blocked_count"] == 1
    assert cells["routeproxy:main"]["cell_kind"] == "ROUTEPROXY"
    assert cells["controlproxy:main"]["cell_kind"] == "CONTROLPROXY"
    assert cells["shm:route-ring-1"]["refs"]["shm_ref"] == "route-ring-1"
    assert cells["policy:gate"]["health"] == "blocked"
    assert cells["policy:gate"]["refs"]["policy_decision_id"] == "policy-1"
    assert cells["policy:gate"]["refs"]["artifact_ref"] == "artifact-1"
    assert cells["policy:gate"]["refs"]["sql_ref"] == "sql-1"
    assert cells["policy:gate"]["refs"]["qdrant_ref"] == "qdrant-1"
    assert payload["authority_boundary"]["allows_proxy_control"] is False
    assert payload["authority_boundary"]["allows_policy_decision"] is False


def test_passive_supervisor_sink_accepts_runtime_surface_helpers() -> None:
    from src.context.passive_bus_supervisor_cellular_snapshot import PassiveSupervisorSink

    sink = PassiveSupervisorSink()
    route_event = sink.accept_proxy_event(
        event_id="evt-routeproxy-accept-1",
        event_kind="routeproxy_eventbus_status_observed",
        proxy_kind="routeproxy",
        proxy_ref="main",
        state="running",
        observed_at="2026-07-08T00:00:00Z",
        route_ref="route-1",
    )
    control_event = sink.accept_runtime_surface_event(
        event_id="evt-controlproxy-accept-1",
        event_kind="controlproxy_eventbus_status_observed",
        cell_kind="CONTROLPROXY",
        surface_ref="main",
        state="running",
        observed_at="2026-07-08T00:00:01Z",
        route_ref="route-1",
    )
    shm_event = sink.accept_shm_event(
        event_id="evt-shm-accept-1",
        event_kind="shm_ring_eventbus_status_observed",
        shm_ref="route-ring-1",
        state="running",
        observed_at="2026-07-08T00:00:02Z",
    )
    policy_event = sink.accept_policy_event(
        event_id="evt-policy-accept-1",
        event_kind="policy_gate_eventbus_decision_observed",
        policy_ref="gate",
        state="success",
        observed_at="2026-07-08T00:00:03Z",
        policy_decision_id="policy-1",
        decision="allow",
    )

    snapshot = sink.snapshot_payload(generated_at="2026-07-08T00:00:04Z")
    cells = {cell["cell_id"]: cell for cell in snapshot["cells"]}

    assert route_event.cell_id == "routeproxy:main"
    assert control_event.cell_id == "controlproxy:main"
    assert shm_event.cell_id == "shm:route-ring-1"
    assert policy_event.cell_id == "policy:gate"
    assert policy_event.payload["decision"] == "allow"
    assert snapshot["cell_count"] == 4
    assert cells["routeproxy:main"]["health"] == "active"
    assert cells["policy:gate"]["refs"]["policy_decision_id"] == "policy-1"


def test_runtime_surface_event_rejects_unknown_surface_kind() -> None:
    import pytest

    from src.context.passive_bus_supervisor_cellular_snapshot import (
        runtime_surface_supervision_event,
    )

    with pytest.raises(ValueError):
        runtime_surface_supervision_event(
            event_id="evt-invalid",
            event_kind="invalid_surface",
            cell_kind="SQL_AUTHORITY",
            surface_ref="sql",
            state="running",
            observed_at="2026-07-08T00:00:00Z",
        )
