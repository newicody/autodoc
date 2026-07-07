from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "RUNTIME_GRAPH_REBUILD_FROM_CODE_AUDIT_0173.md"
RULE = ROOT / "doc" / "code-rules" / "0173_runtime_graph_rebuild_from_code_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0173_CHANGED_FILES.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "173_runtime_graph_rebuild_from_code_audit.dot"
GLOBAL_DOT = ROOT / "doc" / "docs" / "architecture" / "00_global.dot"
VIS_ADAPTER = ROOT / "src" / "runtime" / "bus_visualization_adapter.py"
SCHEDULER_ADAPTER = ROOT / "src" / "runtime" / "scheduler_route_adapter.py"
SCHEDULER_HANDLER = ROOT / "src" / "runtime" / "scheduler_route_handler_minimal.py"
SHM_SCHEMA = ROOT / "src" / "runtime" / "shm_runtime_schema.py"


def test_0173_doc_prioritizes_code_over_stale_graphs_and_changelog_holes() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "architecture DOT graphs, graph documentation, and some changelogs are not fresh enough",
        "code surfaces that exist and pass tests",
        "rule tests and manifests",
        "planned 0162..0172 chain",
        "stale DOT files only as historical input",
        "Changelogs are useful but incomplete",
        "code plus passing tests wins",
        "stale changelog is then marked as a documentation gap",
    ]:
        assert token in doc


def test_0173_doc_locks_rebuilt_global_chain_and_subgraphs() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "External idea source",
        "GitHub Actions artifacts",
        "server dataset sync",
        "scheduler route/intake surfaces",
        "ControlProxy/RouteProxy runtime path",
        "OpenVINO/E5 embedding",
        "Qdrant projection/search",
        "SQL durable hydration",
        "event.bus/context.bus",
        "bus_visualization_adapter",
        "DOT activity graph support",
        "VisPy/browser view",
        "runtime-bus",
        "scheduler-route",
        "github-artifact-dataset",
        "vector-sql-qdrant",
        "controlproxy-routeproxy",
        "activity-graph-vispy",
        "docs-provenance",
    ]:
        assert token in doc


def test_0173_rule_blocks_stale_global_graph_refreshes() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Do not use stale DOT or stale changelog entries as the only source of truth",
        "Changelog gaps must be marked as documentation gaps",
        "Rebuild the global graph from current code and the validated 0162..0172 chain",
        "Mark stale graph/doc areas explicitly with `stale-doc`",
        "Do not patch `doc/docs/architecture/00_global.dot` from assumptions",
        "DOT remains representation; Scheduler/policy/zone remain authority",
        "Do not create a parallel bus or direct VisPy writer",
    ]:
        assert token in rule


def test_0173_existing_code_surfaces_anchor_the_rebuild() -> None:
    vis_adapter = VIS_ADAPTER.read_text(encoding="utf-8")
    scheduler_adapter = SCHEDULER_ADAPTER.read_text(encoding="utf-8")
    scheduler_handler = SCHEDULER_HANDLER.read_text(encoding="utf-8")
    shm_schema = SHM_SCHEMA.read_text(encoding="utf-8")

    for token in [
        "event_bus.subscribe()",
        "read_existing_bus_visualization_snapshot",
        "The adapter reads existing event.bus/context.bus objects",
        "The adapter does not create a parallel bus",
    ]:
        assert token in vis_adapter

    for token in [
        "SchedulerRouteRequest",
        "prepare_route_for_scheduler(...)",
        "SchedulerRouteReply",
        "publish adapter facts to event.bus/context.bus",
        "not the Scheduler loop itself",
    ]:
        assert token in scheduler_adapter

    for token in [
        "SchedulerRouteHandlerCommand",
        "event_bus_observation_only",
        "extends_existing_scheduler_route_handler",
    ]:
        assert token in scheduler_handler

    for token in [
        "EVENT_BUS_MESSAGE_SCHEMA",
        "CONTEXT_BUS_MESSAGE_SCHEMA",
    ]:
        assert token in shm_schema


def test_0173_global_dot_is_present_but_not_modified_by_this_patch_contract() -> None:
    global_dot = GLOBAL_DOT.read_text(encoding="utf-8")
    assert "digraph Global" in global_dot
    assert "ROADMAP_ID: global" in global_dot
    assert "phase0155" in global_dot


def test_0173_dot_contains_rebuild_source_priority_and_forbidden_edges() -> None:
    dot = DOT.read_text(encoding="utf-8")
    for token in [
        "Rebuild source priority",
        "working code surfaces",
        "passing tests / rules",
        "validated 0162..0172 chain",
        "stale DOT graphs",
        "Canonical activity chain",
        "Observation and visualization",
        "forbidden command path",
        "forbidden direct writer",
    ]:
        assert token in dot


def test_0173_manifest_lists_only_audit_contract_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "PHASE0173_TEST_REPORT.md",
        "RUNTIME_GRAPH_REBUILD_FROM_CODE_AUDIT_0173.md",
        "0173_runtime_graph_rebuild_from_code_rule.md",
        "173_runtime_graph_rebuild_from_code_audit.dot",
        "test_runtime_graph_rebuild_from_code_audit_0173_rule.py",
    ]:
        assert token in manifest

    assert "doc/docs/architecture/00_global.dot" not in manifest
    assert "src/" not in manifest
    assert "tools/" not in manifest
