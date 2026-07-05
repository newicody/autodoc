"""Passive context graph export boundary.

0122 adds a passive graph exporter for the local context pipeline.  It turns
reference-only contracts into deterministic graph nodes and DOT text without
watchers, services, Graphviz imports, runtime sockets, live bus subscriptions,
or scheduler integration.

Passive context graph export reads contracts only; it does not observe live events.
SQLContextStore is durable context authority.
Qdrant is vector projection and retrieval, not context authority.
Scheduler orchestrates context exploration jobs; it does not build graphs itself.
MVTC remains future, not runtime in 0122.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import re
from typing import Iterable, Sequence

from context.github_project_scenario import GitHubProjectScenarioPacket

_GRAPH_SCHEMA = "missipy.context_graph.snapshot.v1"
_NODE_SCHEMA = "missipy.context_graph.node.v1"
_EDGE_SCHEMA = "missipy.context_graph.edge.v1"
_TYPED_REF_RE = re.compile(r"^[a-z][a-z0-9-]*:[^\s].*$")
_NODE_ID_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
_ALLOWED_NODE_KINDS = frozenset(
    {
        "github_artifact",
        "source_candidate",
        "sql_authority",
        "context_objective",
        "context_plan",
        "context_variant",
        "embedding_projection",
        "specialist_result",
        "github_publication",
        "future_adapter",
    }
)
_ALLOWED_EDGE_KINDS = frozenset(
    {
        "originates",
        "persists",
        "plans",
        "varies",
        "projects",
        "produces",
        "publishes",
        "future_adapter",
    }
)


@dataclass(frozen=True, slots=True)
class ContextGraphPolicy:
    """Limits for deterministic graph rendering."""

    max_nodes: int = 128
    max_edges: int = 256
    max_label_chars: int = 80
    include_future_adapter: bool = True

    def __post_init__(self) -> None:
        if self.max_nodes <= 0:
            raise ValueError("max_nodes must be > 0")
        if self.max_edges <= 0:
            raise ValueError("max_edges must be > 0")
        if self.max_label_chars <= 0:
            raise ValueError("max_label_chars must be > 0")


@dataclass(frozen=True, slots=True)
class ContextGraphNode:
    """Reference-only node for a passive context graph."""

    node_id: str
    label: str
    kind: str
    ref: str
    authority: str = "contract"
    metadata: tuple[tuple[str, str], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_node_id("node_id", self.node_id)
        _require_non_empty("label", self.label)
        if self.kind not in _ALLOWED_NODE_KINDS:
            raise ValueError("kind must be a known context graph node kind")
        _require_typed_ref("ref", self.ref)
        _require_non_empty("authority", self.authority)
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _NODE_SCHEMA,
            "node_id": self.node_id,
            "label": self.label,
            "kind": self.kind,
            "ref": self.ref,
            "authority": self.authority,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class ContextGraphEdge:
    """Directed relation between passive graph nodes."""

    edge_id: str
    source_id: str
    target_id: str
    label: str
    kind: str

    def __post_init__(self) -> None:
        _require_node_id("edge_id", self.edge_id)
        _require_node_id("source_id", self.source_id)
        _require_node_id("target_id", self.target_id)
        _require_non_empty("label", self.label)
        if self.kind not in _ALLOWED_EDGE_KINDS:
            raise ValueError("kind must be a known context graph edge kind")

    def to_mapping(self) -> dict[str, str]:
        return {
            "schema": _EDGE_SCHEMA,
            "edge_id": self.edge_id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "label": self.label,
            "kind": self.kind,
        }


@dataclass(frozen=True, slots=True)
class ContextGraphSnapshot:
    """Deterministic passive graph snapshot for documentation or UI export."""

    snapshot_ref: str
    title: str
    nodes: tuple[ContextGraphNode, ...]
    edges: tuple[ContextGraphEdge, ...]
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_typed_ref("snapshot_ref", self.snapshot_ref)
        _require_non_empty("title", self.title)
        if not self.nodes:
            raise ValueError("nodes must not be empty")
        node_ids = [node.node_id for node in self.nodes]
        if len(set(node_ids)) != len(node_ids):
            raise ValueError("nodes must have unique node_id values")
        known = set(node_ids)
        for edge in self.edges:
            if edge.source_id not in known or edge.target_id not in known:
                raise ValueError("edges must reference known node ids")
        object.__setattr__(self, "notes", _normalize_strings("notes", self.notes, allow_empty=True))

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _GRAPH_SCHEMA,
            "snapshot_ref": self.snapshot_ref,
            "title": self.title,
            "nodes": [node.to_mapping() for node in self.nodes],
            "edges": [edge.to_mapping() for edge in self.edges],
            "notes": list(self.notes),
            "runtime_import": "none; passive export only",
        }


@dataclass(frozen=True, slots=True)
class DotGraphExport:
    """Plain DOT export of a passive context graph snapshot."""

    snapshot_ref: str
    dot: str
    node_count: int
    edge_count: int

    def __post_init__(self) -> None:
        _require_typed_ref("snapshot_ref", self.snapshot_ref)
        _require_non_empty("dot", self.dot)
        if self.node_count <= 0:
            raise ValueError("node_count must be > 0")
        if self.edge_count < 0:
            raise ValueError("edge_count must be >= 0")

    def to_mapping(self) -> dict[str, object]:
        return {
            "snapshot_ref": self.snapshot_ref,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "format": "dot",
            "dot": self.dot,
        }


def build_github_project_context_graph(
    packet: GitHubProjectScenarioPacket,
    *,
    policy: ContextGraphPolicy | None = None,
) -> ContextGraphSnapshot:
    """Build a passive graph from the GitHub baby-fork scenario packet."""

    effective = policy or ContextGraphPolicy()
    publication = packet.publication
    nodes = [
        ContextGraphNode(
            node_id="github_artifact",
            label="GitHub artifact",
            kind="github_artifact",
            ref=packet.artifact.artifact_ref,
            authority="external workflow surface",
        ),
        ContextGraphNode(
            node_id="source_candidate",
            label="SourceCandidate SQL",
            kind="source_candidate",
            ref=packet.source_candidate.source_ref,
            authority="local importer contract",
        ),
        ContextGraphNode(
            node_id="sql_authority",
            label="SQLContextStore authority",
            kind="sql_authority",
            ref=packet.source_candidate.sql_record.context_ref,
            authority="durable SQL context authority",
        ),
        ContextGraphNode(
            node_id="context_objective",
            label="ContextVariationObjective",
            kind="context_objective",
            ref=f"ctx:objective:{packet.objective.objective_id}",
            authority="context contract",
        ),
        ContextGraphNode(
            node_id="context_plan",
            label="ContextExplorationPlan",
            kind="context_plan",
            ref=f"ctx:plan:{packet.plan.plan_id}",
            authority="bounded planner contract",
        ),
        ContextGraphNode(
            node_id="qdrant_projection",
            label="Qdrant projection/retrieval",
            kind="embedding_projection",
            ref=f"qdrant:projection:{_digest(packet.plan.plan_id)}",
            authority="rebuildable vector projection",
        ),
        ContextGraphNode(
            node_id="specialist_result",
            label="LLMSpecialistResult",
            kind="specialist_result",
            ref=packet.specialist_result.result_ref,
            authority="specialist candidate producer",
        ),
        ContextGraphNode(
            node_id="github_publication",
            label="GitHubProjectPublication",
            kind="github_publication",
            ref=publication.publication_ref,
            authority="publication contract",
        ),
    ]
    if effective.include_future_adapter:
        nodes.append(
            ContextGraphNode(
                node_id="future_github_adapter",
                label="Future GitHub adapter posts result",
                kind="future_adapter",
                ref=publication.target_ref,
                authority="future external adapter",
            )
        )
    variant_edges = [
        ContextGraphEdge(
            edge_id=f"varies_{index}",
            source_id="context_plan",
            target_id="qdrant_projection",
            label=f"variant {candidate.variant_id}",
            kind="varies",
        )
        for index, candidate in enumerate(packet.plan.candidates, start=1)
    ]
    edges = [
        ContextGraphEdge("e_originates", "github_artifact", "source_candidate", "artifact becomes candidate", "originates"),
        ContextGraphEdge("e_persists", "source_candidate", "sql_authority", "persist via SQLContextStore", "persists"),
        ContextGraphEdge("e_objective", "sql_authority", "context_objective", "objective source_ref", "plans"),
        ContextGraphEdge("e_plan", "context_objective", "context_plan", "bounded exploration", "plans"),
        *variant_edges,
        ContextGraphEdge("e_projection", "qdrant_projection", "specialist_result", "recall refs then SQL re-hydrate", "projects"),
        ContextGraphEdge("e_solution", "context_plan", "specialist_result", "specialist produces candidates", "produces"),
        ContextGraphEdge("e_publication", "specialist_result", "github_publication", "publishable result packet", "publishes"),
    ]
    if effective.include_future_adapter:
        edges.append(
            ContextGraphEdge(
                "e_future_adapter",
                "github_publication",
                "future_github_adapter",
                "future adapter posts result",
                "future_adapter",
            )
        )
    _enforce_policy(effective, nodes, edges)
    identity = f"{packet.artifact.artifact_ref}\0{packet.plan.plan_id}\0{packet.specialist_result.result_ref}"
    return ContextGraphSnapshot(
        snapshot_ref=f"ctx-graph:github-project:{_digest(identity)}",
        title="GitHub project passive context graph",
        nodes=tuple(nodes),
        edges=tuple(edges),
        notes=(
            "Passive context graph export reads contracts only; it does not observe live events.",
            "SQLContextStore is durable context authority.",
            "Qdrant is vector projection and retrieval, not context authority.",
        ),
    )


def export_context_graph_dot(
    snapshot: ContextGraphSnapshot,
    *,
    graph_name: str = "context_graph_snapshot_0122",
    policy: ContextGraphPolicy | None = None,
) -> DotGraphExport:
    """Render a snapshot to deterministic DOT without Graphviz runtime imports."""

    effective = policy or ContextGraphPolicy()
    _require_node_id("graph_name", graph_name)
    _enforce_policy(effective, snapshot.nodes, snapshot.edges)
    lines = [
        f"digraph {graph_name} {{",
        "    rankdir=LR;",
        "    node [shape=box];",
        "",
    ]
    for node in snapshot.nodes:
        label = _truncate_label(node.label, effective.max_label_chars)
        lines.append(f"    {node.node_id} [label=\"{_dot_escape(label)}\", tooltip=\"{_dot_escape(node.ref)}\"];")
    if snapshot.edges:
        lines.append("")
    for edge in snapshot.edges:
        label = _truncate_label(edge.label, effective.max_label_chars)
        lines.append(f"    {edge.source_id} -> {edge.target_id} [label=\"{_dot_escape(label)}\"];")
    lines.append("}")
    return DotGraphExport(
        snapshot_ref=snapshot.snapshot_ref,
        dot="\n".join(lines),
        node_count=len(snapshot.nodes),
        edge_count=len(snapshot.edges),
    )


def _enforce_policy(
    policy: ContextGraphPolicy,
    nodes: Sequence[ContextGraphNode],
    edges: Sequence[ContextGraphEdge],
) -> None:
    if len(nodes) > policy.max_nodes:
        raise ValueError("nodes exceed policy.max_nodes")
    if len(edges) > policy.max_edges:
        raise ValueError("edges exceed policy.max_edges")


def _truncate_label(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    if max_chars <= 1:
        return value[:max_chars]
    return value[: max_chars - 1] + "…"


def _dot_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _normalize_metadata(values: tuple[tuple[str, str], ...]) -> tuple[tuple[str, str], ...]:
    normalized: dict[str, str] = {}
    for key, value in values:
        _require_non_empty("metadata key", key)
        _require_non_empty("metadata value", value)
        normalized[key] = value
    return tuple(sorted(normalized.items()))


def _normalize_strings(name: str, values: Iterable[str], *, allow_empty: bool = False) -> tuple[str, ...]:
    normalized = tuple(values)
    if not normalized and not allow_empty:
        raise ValueError(f"{name} must not be empty")
    for value in normalized:
        _require_non_empty(name, value)
    return normalized


def _require_typed_ref(name: str, value: str) -> None:
    _require_non_empty(name, value)
    if not _TYPED_REF_RE.match(value):
        raise ValueError(f"{name} must be a typed reference")


def _require_node_id(name: str, value: str) -> None:
    _require_non_empty(name, value)
    if not _NODE_ID_RE.match(value):
        raise ValueError(f"{name} must be a DOT-safe identifier")


def _require_non_empty(name: str, value: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{name} must not be empty")


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
