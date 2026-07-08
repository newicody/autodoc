from src.context.passive_supervisor_visual_read_model import build_visual_read_model


def test_visual_read_model_builds_nodes_edges_and_zones() -> None:
    snapshot = {
        "generated_at": "2026-07-08T00:00:00Z",
        "event_count": 3,
        "cell_count": 3,
        "cells": [
            {
                "cell_id": "scheduler:main",
                "cell_kind": "SCHEDULER",
                "state": "success",
                "health": "active",
                "route_ref": "route-1",
            },
            {
                "cell_id": "sql_store:sql-1",
                "cell_kind": "SQL_STORE",
                "state": "success",
                "health": "active",
                "sql_ref": "sql-1",
            },
            {
                "cell_id": "qdrant_projection:qdrant-1",
                "cell_kind": "QDRANT_PROJECTION",
                "state": "success",
                "health": "active",
                "qdrant_ref": "qdrant-1",
            },
        ],
    }

    model = build_visual_read_model(snapshot).to_dict()

    assert model["node_count"] == 3
    assert model["edge_count"] == 3
    assert {node["zone"] for node in model["nodes"]} == {
        "orchestration",
        "storage",
        "index",
    }
    assert model["authority_boundary"]["read_only_visual_model"] is True
    assert model["authority_boundary"]["uses_scheduler_run"] is False
    assert model["authority_boundary"]["writes_sql"] is False
    assert model["authority_boundary"]["writes_qdrant"] is False


def test_visual_read_model_rejects_non_mapping_cells() -> None:
    snapshot = {"cells": ["bad-cell"]}

    try:
        build_visual_read_model(snapshot)
    except TypeError as exc:
        assert "entries must be mappings" in str(exc)
    else:
        raise AssertionError("expected TypeError")
