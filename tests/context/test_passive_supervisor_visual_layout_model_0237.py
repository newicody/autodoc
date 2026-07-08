from context.passive_supervisor_visual_layout_model import (
    VISUAL_LAYOUT_AUTHORITY_BOUNDARY,
    build_passive_supervisor_visual_layout_model,
)


def test_visual_layout_model_places_nodes_by_zone() -> None:
    layout = build_passive_supervisor_visual_layout_model(
        {
            "generated_at": "2026-07-08T00:00:00Z",
            "nodes": [
                {"id": "scheduler:main", "kind": "SCHEDULER", "zone": "scheduler", "state": "success"},
                {"id": "sql_store:sql-1", "kind": "SQL_STORE", "zone": "sql_store", "state": "success"},
                {"id": "policy:gate", "kind": "POLICY_GATE", "zone": "policy", "state": "blocked"},
            ],
            "edges": [
                {"source": "scheduler:main", "target": "policy:gate", "kind": "observes"},
            ],
        },
        generated_at="2026-07-08T00:00:01Z",
    )

    assert layout["passive_supervisor_visual_layout_model_written"] is True
    assert layout["zone_count"] == 3
    assert layout["node_count"] == 3
    assert layout["edge_count"] == 1
    assert {node["id"] for node in layout["nodes"]} == {
        "scheduler:main",
        "sql_store:sql-1",
        "policy:gate",
    }
    assert all("position" in node for node in layout["nodes"])


def test_visual_layout_model_is_read_only() -> None:
    assert VISUAL_LAYOUT_AUTHORITY_BOUNDARY == {
        "read_only_visual_layout": True,
        "uses_scheduler_run": False,
        "creates_eventbus": False,
        "controls_proxy": False,
        "mutates_shm": False,
        "decides_policy": False,
        "writes_sql": False,
        "writes_qdrant": False,
        "mutates_github": False,
        "requires_non_stdlib": False,
    }
