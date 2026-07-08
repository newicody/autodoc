"""Read-only visual read-model for passive bus supervisor snapshots.

This module deliberately does not depend on the VisPy package.  It turns the existing passive
supervisor snapshot shape into a stable JSON-compatible view model that a future
renderer may read.

Authority boundary:
- no scheduler execution
- no EventBus creation
- no proxy/SHM/policy control
- no SQL/Qdrant/GitHub mutation
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any


REF_KEYS: tuple[str, ...] = (
    "route_ref",
    "shm_ref",
    "policy_decision_id",
    "artifact_ref",
    "source_candidate_ref",
    "sql_ref",
    "qdrant_ref",
    "handoff_ref",
    "pushback_ref",
)


ZONE_BY_CELL_KIND: Mapping[str, str] = {
    "SCHEDULER": "orchestration",
    "ROUTEPROXY": "runtime",
    "CONTROLPROXY": "runtime",
    "SHM_RING": "runtime",
    "POLICY_GATE": "policy",
    "GITHUB_ARTIFACT": "data",
    "SOURCE_CANDIDATE": "data",
    "SQL_STORE": "storage",
    "QDRANT_PROJECTION": "index",
    "REHYDRATION": "context",
    "PUSHBACK": "feedback",
    "UNKNOWN": "unknown",
}


AUTHORITY_BOUNDARY: Mapping[str, bool] = {
    "read_only_visual_model": True,
    "creates_eventbus": False,
    "uses_scheduler_run": False,
    "controls_proxy": False,
    "mutates_shm": False,
    "decides_policy": False,
    "writes_sql": False,
    "writes_qdrant": False,
    "mutates_github": False,
    "requires_non_stdlib": False,
}


@dataclass(frozen=True)
class VisualReadModel:
    """JSON-compatible visual model derived from a passive supervisor snapshot."""

    generated_at: str
    layout_kind: str
    nodes: tuple[Mapping[str, Any], ...]
    edges: tuple[Mapping[str, Any], ...]
    zones: tuple[Mapping[str, Any], ...]
    source_snapshot: Mapping[str, Any]
    authority_boundary: Mapping[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "layout_kind": self.layout_kind,
            "node_count": len(self.nodes),
            "edge_count": len(self.edges),
            "zone_count": len(self.zones),
            "authority_boundary": dict(self.authority_boundary),
            "nodes": [dict(node) for node in self.nodes],
            "edges": [dict(edge) for edge in self.edges],
            "zones": [dict(zone) for zone in self.zones],
            "source_snapshot": dict(self.source_snapshot),
        }


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if hasattr(value, "to_dict"):
        mapped = value.to_dict()
        if isinstance(mapped, Mapping):
            return mapped
    if isinstance(value, Mapping):
        return value
    raise TypeError("snapshot must be a mapping or expose to_dict()")


def _as_string(value: Any) -> str:
    return "" if value is None else str(value)


def _cell_zone(cell_kind: str) -> str:
    return ZONE_BY_CELL_KIND.get(_as_string(cell_kind).upper(), "unknown")


def _cell_refs(cell: Mapping[str, Any]) -> dict[str, str]:
    refs: dict[str, str] = {}
    for key in REF_KEYS:
        value = _as_string(cell.get(key, "")).strip()
        if value:
            refs[key] = value
    payload = cell.get("payload")
    if isinstance(payload, Mapping):
        for key in REF_KEYS:
            value = _as_string(payload.get(key, "")).strip()
            if value and key not in refs:
                refs[key] = value
    return refs


def _node_from_cell(cell: Mapping[str, Any]) -> dict[str, Any]:
    cell_id = _as_string(cell.get("cell_id", "")).strip() or "unknown"
    cell_kind = _as_string(cell.get("cell_kind", "UNKNOWN")).strip() or "UNKNOWN"
    refs = _cell_refs(cell)
    return {
        "node_id": cell_id,
        "label": cell_id,
        "cell_id": cell_id,
        "cell_kind": cell_kind,
        "zone": _cell_zone(cell_kind),
        "state": _as_string(cell.get("state", "unknown")),
        "health": _as_string(cell.get("health", "unknown")),
        "last_event": _as_string(cell.get("last_event", "")),
        "last_seen_at": _as_string(cell.get("last_seen_at", "")),
        "refs": refs,
        "error": _as_string(cell.get("error", "")),
    }


def _edges_from_node(node: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    source = _as_string(node.get("node_id", "unknown"))
    refs = node.get("refs", {})
    if not isinstance(refs, Mapping):
        return ()
    edges: list[Mapping[str, Any]] = []
    for ref_key, ref_value in sorted(refs.items()):
        target_ref = _as_string(ref_value)
        edge_id = f"{source}->{ref_key}:{target_ref}"
        edges.append(
            {
                "edge_id": edge_id,
                "edge_kind": ref_key,
                "source": source,
                "target_ref": target_ref,
                "read_only": True,
            }
        )
    return tuple(edges)


def _zones_from_nodes(nodes: Sequence[Mapping[str, Any]]) -> tuple[Mapping[str, Any], ...]:
    counts: dict[str, int] = {}
    for node in nodes:
        zone = _as_string(node.get("zone", "unknown")) or "unknown"
        counts[zone] = counts.get(zone, 0) + 1
    return tuple(
        {"zone_id": zone, "label": zone, "node_count": count}
        for zone, count in sorted(counts.items())
    )


def build_visual_read_model(
    snapshot: Mapping[str, Any] | Any,
    *,
    generated_at: str = "",
    layout_kind: str = "cellular",
) -> VisualReadModel:
    """Build a read-only visual model from an existing supervisor snapshot."""

    mapped = _as_mapping(snapshot)
    cells = mapped.get("cells", ())
    if not isinstance(cells, Sequence) or isinstance(cells, (str, bytes)):
        raise TypeError("snapshot['cells'] must be a sequence of mappings")

    nodes: list[Mapping[str, Any]] = []
    edges: list[Mapping[str, Any]] = []
    for cell in cells:
        if not isinstance(cell, Mapping):
            raise TypeError("snapshot['cells'] entries must be mappings")
        node = _node_from_cell(cell)
        nodes.append(node)
        edges.extend(_edges_from_node(node))

    return VisualReadModel(
        generated_at=generated_at or _as_string(mapped.get("generated_at", "")),
        layout_kind=layout_kind,
        nodes=tuple(nodes),
        edges=tuple(edges),
        zones=_zones_from_nodes(nodes),
        source_snapshot={
            "generated_at": _as_string(mapped.get("generated_at", "")),
            "event_count": mapped.get("event_count", 0),
            "cell_count": mapped.get("cell_count", len(nodes)),
            "blocked_count": mapped.get("blocked_count", 0),
            "failed_count": mapped.get("failed_count", 0),
            "stale_count": mapped.get("stale_count", 0),
        },
        authority_boundary=dict(AUTHORITY_BOUNDARY),
    )
