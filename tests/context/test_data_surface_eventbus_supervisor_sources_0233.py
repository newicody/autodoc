from src.context.passive_bus_supervisor_cellular_snapshot import (
    DATA_SURFACE_CELL_KINDS,
    build_cellular_snapshot,
    data_surface_supervision_event,
    github_artifact_supervision_event,
    qdrant_supervision_event,
    rehydration_supervision_event,
    source_candidate_supervision_event,
    sql_supervision_event,
    pushback_supervision_event,
)


def test_data_surface_event_keeps_references_visible() -> None:
    event = data_surface_supervision_event(
        event_id="evt-data-1",
        event_kind="github_artifact_seen",
        cell_kind="GITHUB_ARTIFACT",
        surface_ref="artifact-1",
        state="queued",
        observed_at="2026-07-08T00:00:00Z",
        artifact_ref="artifact-1",
        source_candidate_ref="candidate-1",
        sql_ref="sql-1",
        qdrant_ref="qdrant-1",
        payload={"stage": "fetch"},
    )

    assert event.cell_kind == "GITHUB_ARTIFACT"
    assert event.cell_id == "github_artifact:artifact-1"
    assert event.artifact_ref == "artifact-1"
    assert event.sql_ref == "sql-1"
    assert event.qdrant_ref == "qdrant-1"
    assert event.payload["source_candidate_ref"] == "candidate-1"

    snapshot = build_cellular_snapshot(
        [event], generated_at="2026-07-08T00:00:01Z"
    )
    snapshot_dict = snapshot.to_dict()
    assert snapshot_dict["cell_count"] == 1
    assert snapshot_dict["cells"][0]["cell_kind"] == "GITHUB_ARTIFACT"
    assert snapshot_dict["authority_boundary"]["allows_github_mutation"] is False
    assert snapshot_dict["authority_boundary"]["allows_sql_write"] is False
    assert snapshot_dict["authority_boundary"]["allows_qdrant_write"] is False


def test_data_surface_helpers_cover_planned_sources() -> None:
    events = [
        github_artifact_supervision_event(
            event_id="evt-github",
            event_kind="artifact_seen",
            artifact_ref="artifact-1",
            state="queued",
            observed_at="2026-07-08T00:00:00Z",
        ),
        source_candidate_supervision_event(
            event_id="evt-candidate",
            event_kind="source_candidate_imported",
            source_candidate_ref="candidate-1",
            state="success",
            observed_at="2026-07-08T00:00:01Z",
        ),
        sql_supervision_event(
            event_id="evt-sql",
            event_kind="sql_persisted",
            sql_ref="sql-1",
            state="success",
            observed_at="2026-07-08T00:00:02Z",
        ),
        qdrant_supervision_event(
            event_id="evt-qdrant",
            event_kind="qdrant_projected",
            qdrant_ref="qdrant-1",
            state="success",
            observed_at="2026-07-08T00:00:03Z",
        ),
        rehydration_supervision_event(
            event_id="evt-rehydrate",
            event_kind="rehydrated",
            rehydrate_ref="rehydrate-1",
            state="success",
            observed_at="2026-07-08T00:00:04Z",
        ),
        pushback_supervision_event(
            event_id="evt-pushback",
            event_kind="pushback_prepared",
            pushback_ref="pushback-1",
            state="success",
            observed_at="2026-07-08T00:00:05Z",
        ),
    ]

    assert {event.cell_kind for event in events} == DATA_SURFACE_CELL_KINDS
    assert {event.state for event in events} == {"queued", "success"}
    assert all(event.source_ref for event in events)


def test_data_surface_event_rejects_unknown_kind() -> None:
    try:
        data_surface_supervision_event(
            event_id="evt-bad",
            event_kind="bad",
            cell_kind="SQL_WRITER",
            surface_ref="sql",
            state="unknown",
            observed_at="2026-07-08T00:00:00Z",
        )
    except ValueError as exc:
        assert "cell_kind must be one of" in str(exc)
    else:
        raise AssertionError("unknown data-surface kind must be rejected")
