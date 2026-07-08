"""Read-only layout model for passive supervisor visualization.

This module is deliberately renderer-agnostic. It consumes an existing passive
supervisor snapshot or visual read-model and returns deterministic zones, nodes,
edges, and positions for a future human display.

Boundary:
- no scheduler execution
- no EventBus creation
- no proxy, SHM, or policy control
- no SQL, Qdrant, GitHub, or pushback mutation
- no graphical package dependency
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence


VISUAL_LAYOUT_AUTHORITY_BOUNDARY: dict[str, bool] = {
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


def _as_string(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def _as_mapping(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _as_sequence(value: object) -> Sequence[object]:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return value
    return ()


def _zone_from_mapping(mapping: Mapping[str, Any]) -> str:
    for key in ("zone", "location", "group", "surface", "cell_kind", "kind"):
        value = _as_string(mapping.get(key, "")).strip()
        if value:
            return value.lower()
    cell_id = _as_string(mapping.get("id", mapping.get("cell_id", ""))).strip()
    if ":" in cell_id:
        return cell_id.split(":", 1)[0].lower()
    return "default"


def _node_from_mapping(mapping: Mapping[str, Any], *, fallback_id: str) -> dict[str, Any]:
    node_id = _as_string(mapping.get("id", mapping.get("cell_id", fallback_id))).strip()
    if not node_id:
        node_id = fallback_id
    node_kind = _as_string(mapping.get("kind", mapping.get("cell_kind", "UNKNOWN"))).strip()
    return {
        "id": node_id,
        "label": _as_string(mapping.get("label", node_id)).strip() or node_id,
        "kind": node_kind or "UNKNOWN",
        "zone": _zone_from_mapping(mapping),
        "state": _as_string(mapping.get("state", "unknown")).strip() or "unknown",
        "health": _as_string(mapping.get("health", "")).strip(),
        "refs": dict(_as_mapping(mapping.get("refs", {}))),
    }


def _nodes_from_model(model: Mapping[str, Any]) -> list[dict[str, Any]]:
    raw_nodes = _as_sequence(model.get("nodes"))
    if raw_nodes:
        return [
            _node_from_mapping(_as_mapping(item), fallback_id=f"node:{index}")
            for index, item in enumerate(raw_nodes)
        ]

    raw_cells = _as_sequence(model.get("cells"))
    return [
        _node_from_mapping(_as_mapping(item), fallback_id=f"cell:{index}")
        for index, item in enumerate(raw_cells)
    ]


def _edges_from_model(model: Mapping[str, Any]) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = []
    for index, item in enumerate(_as_sequence(model.get("edges"))):
        mapping = _as_mapping(item)
        source = _as_string(mapping.get("source", "")).strip()
        target = _as_string(mapping.get("target", "")).strip()
        if not source or not target:
            continue
        edge_id = _as_string(mapping.get("id", f"edge:{index}")).strip() or f"edge:{index}"
        edges.append(
            {
                "id": edge_id,
                "source": source,
                "target": target,
                "kind": _as_string(mapping.get("kind", "observes")).strip() or "observes",
            }
        )
    return edges


def build_passive_supervisor_visual_layout_model(
    model: Mapping[str, Any],
    *,
    generated_at: str = "",
    zone_spacing: int = 320,
    cell_spacing: int = 96,
) -> dict[str, Any]:
    """Build a deterministic read-only layout from a snapshot/read-model mapping."""

    nodes = _nodes_from_model(model)
    nodes.sort(key=lambda item: (item["zone"], item["kind"], item["id"]))

    zones = sorted({node["zone"] for node in nodes} or {"default"})
    zone_index = {zone: index for index, zone in enumerate(zones)}
    zone_local_counts: dict[str, int] = {zone: 0 for zone in zones}

    positioned_nodes: list[dict[str, Any]] = []
    for node in nodes:
        zone = node["zone"]
        local_index = zone_local_counts[zone]
        zone_local_counts[zone] += 1
        column = local_index % 4
        row = local_index // 4
        positioned = dict(node)
        positioned["position"] = {
            "x": zone_index[zone] * zone_spacing + column * cell_spacing,
            "y": row * cell_spacing,
            "z": 0,
        }
        positioned_nodes.append(positioned)

    zone_models = [
        {
            "id": zone,
            "label": zone,
            "index": zone_index[zone],
            "node_count": zone_local_counts[zone],
            "origin": {"x": zone_index[zone] * zone_spacing, "y": 0, "z": 0},
        }
        for zone in zones
    ]

    edges = _edges_from_model(model)

    return {
        "passive_supervisor_visual_layout_model_written": True,
        "generated_at": generated_at or _as_string(model.get("generated_at", "")),
        "authority_boundary": dict(VISUAL_LAYOUT_AUTHORITY_BOUNDARY),
        "zone_count": len(zone_models),
        "node_count": len(positioned_nodes),
        "edge_count": len(edges),
        "zones": zone_models,
        "nodes": positioned_nodes,
        "edges": edges,
        "metadata": {
            "source_kind": _as_string(model.get("source_kind", "passive_supervisor_visual_model")),
            "layout_kind": "deterministic_grid",
        },
    }


def write_passive_supervisor_visual_layout_model(
    path: Path,
    model: Mapping[str, Any],
    *,
    generated_at: str = "",
) -> dict[str, Any]:
    """Write the read-only layout model as JSON and return it."""

    layout = build_passive_supervisor_visual_layout_model(
        model,
        generated_at=generated_at,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(layout, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return layout
