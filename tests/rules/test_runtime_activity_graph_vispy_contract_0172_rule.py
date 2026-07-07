from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "RUNTIME_ACTIVITY_GRAPH_VISPY_CONTRACT_0172.md"
RULE = ROOT / "doc" / "code-rules" / "0172_runtime_activity_graph_vispy_contract_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0172_CHANGED_FILES.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "172_runtime_activity_graph_vispy_contract.dot"
VIS_ADAPTER = ROOT / "src" / "runtime" / "bus_visualization_adapter.py"
SHM_SCHEMA = ROOT / "src" / "runtime" / "shm_runtime_schema.py"


def test_0172_doc_locks_dot_as_representation_not_authority() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "DOT is a representation contract, not a command path",
        "DOT can describe the shape of activity, states, scores, successes, failures, and navigation modes",
        "event.bus/context.bus",
        "bus_visualization_adapter",
        "VisPy/browser",
        "Scheduler/policy/zone",
        "not patch `doc/docs/architecture/00_global.dot` from stale assumptions",
    ]:
        assert token in doc


def test_0172_doc_locks_modes_states_scores_and_navigation() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "architecture",
        "runtime",
        "artifact",
        "scheduler",
        "bus",
        "score",
        "population",
        "debug",
        "planned",
        "born",
        "fetched",
        "synced",
        "queued",
        "succeeded",
        "failed",
        "dead",
        "superseded",
        "zoom and pan",
        "selectable nodes",
        "collapse/expand of subgraphs",
    ]:
        assert token in doc


def test_0172_rule_blocks_parallel_bus_and_direct_vispy_writer() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "DOT must not command runtime components",
        "DOT must not replace Scheduler/policy/zone authority",
        "DOT must not replace event.bus/context.bus facts",
        "Do not create a parallel bus",
        "Do not write directly to VisPy",
        "Reuse `runtime.shm_runtime_schema`",
        "`doc/docs/architecture/00_global.dot` must be patched only from exact local state",
    ]:
        assert token in rule


def test_0172_existing_surfaces_are_reused() -> None:
    adapter = VIS_ADAPTER.read_text(encoding="utf-8")
    schema = SHM_SCHEMA.read_text(encoding="utf-8")

    for token in [
        "event_bus.subscribe()",
        "read_existing_bus_visualization_snapshot",
        "The adapter reads existing event.bus/context.bus objects",
        "The adapter does not create a parallel bus",
    ]:
        assert token in adapter

    for token in [
        "EVENT_BUS_MESSAGE_SCHEMA",
        "CONTEXT_BUS_MESSAGE_SCHEMA",
        "Lightweight fact message for event.bus",
        "Compact active context message for context.bus",
    ]:
        assert token in schema


def test_0172_dot_shows_supported_view_modes_and_forbidden_edges() -> None:
    dot = DOT.read_text(encoding="utf-8")
    for token in [
        "0172 runtime activity graph / VisPy contract",
        "View modes",
        "architecture",
        "runtime",
        "artifact",
        "scheduler",
        "bus",
        "score",
        "population",
        "debug",
        "forbidden direct write",
        "forbidden command path",
    ]:
        assert token in dot


def test_0172_manifest_lists_only_audit_contract_files() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "PHASE0172_TEST_REPORT.md",
        "RUNTIME_ACTIVITY_GRAPH_VISPY_CONTRACT_0172.md",
        "0172_runtime_activity_graph_vispy_contract_rule.md",
        "172_runtime_activity_graph_vispy_contract.dot",
        "test_runtime_activity_graph_vispy_contract_0172_rule.py",
    ]:
        assert token in manifest

    assert "src/context/runtime_activity_graph" not in manifest
    assert "tools/" not in manifest
