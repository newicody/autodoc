from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "GRAPH_HERITAGE_OPERATIONAL_BASELINE_0175.md"
RULE = ROOT / "doc" / "code-rules" / "0175_graph_heritage_operational_baseline_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0175_CHANGED_FILES.md"
DOT = ROOT / "doc" / "docs" / "architecture" / "runtime" / "175_graph_heritage_operational_baseline.dot"


def test_0175_doc_preserves_old_graphs_as_heritage() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0175 explicitly avoids merging or replacing the old global graph",
        "old DOT graphs remain valuable as heritage",
        "ideas, orientation, roadmap memory, historical design attempts, and inspiration",
        "The immediate operational baseline is the rebuilt 0174 graph draft",
        "two-layer model",
        "Heritage layer",
        "Operational baseline layer",
    ]:
        assert token in doc


def test_0175_doc_locks_immediate_direction_without_merge() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "Old graphs should not be deleted just because they are stale",
        "heritage",
        "orientation",
        "inspiration",
        "stale-doc",
        "future-idea",
        "must not silently override the operational baseline",
        "The next implementation work should not be a graph merge",
        "GitHub artifacts / dataset",
        "existing event.bus/context.bus",
        "bus_visualization_adapter",
        "DOT/VisPy/browser projection",
    ]:
        assert token in doc


def test_0175_rule_blocks_premature_global_graph_merge() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Do not merge or replace `doc/docs/architecture/00_global.dot` in this phase",
        "Keep old DOT graphs as heritage, orientation, historical memory, and inspiration",
        "Mark stale graph areas as `stale-doc`",
        "0174 rebuilt graph draft and subgraphs as the immediate operational baseline",
        "Old graphs can inspire future work",
        "must not override the operational baseline",
        "Do not create a parallel bus, direct VisPy writer, or Scheduler bypass",
    ]:
        assert token in rule


def test_0175_dot_contains_two_layers_and_forbidden_edges() -> None:
    dot = DOT.read_text(encoding="utf-8")
    for token in [
        "0175 graph heritage and operational baseline",
        "Heritage layer",
        "Operational baseline layer",
        "Immediate work chain",
        "old 00_global.dot",
        "heritage / stale-doc",
        "0174 rebuilt graph draft",
        "immediate baseline",
        "event.bus/context.bus facts",
        "bus_visualization_adapter",
        "must not override",
        "forbidden command path",
        "forbidden direct writer",
    ]:
        assert token in dot


def test_0175_manifest_does_not_include_00_global_dot() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for token in [
        "PHASE0175_TEST_REPORT.md",
        "GRAPH_HERITAGE_OPERATIONAL_BASELINE_0175.md",
        "0175_graph_heritage_operational_baseline_rule.md",
        "175_graph_heritage_operational_baseline.dot",
        "test_graph_heritage_operational_baseline_0175_rule.py",
    ]:
        assert token in manifest

    assert "doc/docs/architecture/00_global.dot" not in manifest
    assert "00_global_0175_refresh_candidate.dot" not in manifest
