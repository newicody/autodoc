from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / "doc" / "architecture" / "REBUILT_RUNTIME_GLOBAL_GRAPH_DRAFT_0174.md"
RULE = ROOT / "doc" / "code-rules" / "0174_rebuilt_runtime_global_graph_draft_rule.md"
MANIFEST = ROOT / "doc" / "manifests" / "MANIFEST_0174_CHANGED_FILES.md"
GLOBAL = ROOT / "doc" / "docs" / "architecture" / "runtime" / "174_rebuilt_runtime_global_current_state.dot"
SUBGRAPH_DIR = ROOT / "doc" / "docs" / "architecture" / "runtime" / "0174_subgraphs"


REQUIRED_SUBGRAPHS = (
    "runtime_bus.dot",
    "scheduler_route.dot",
    "github_artifact_dataset.dot",
    "vector_sql_qdrant.dot",
    "controlproxy_routeproxy.dot",
    "activity_graph_vispy.dot",
    "docs_provenance.dot",
)


def test_0174_doc_locks_parallel_draft_not_global_rewrite() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "0174 adds a rebuilt current-state graph draft",
        "does not replace `doc/docs/architecture/00_global.dot`",
        "current-state draft, not runtime authority",
        "code surfaces that currently exist",
        "validated 0162..0173 chain",
        "stale docs and changelogs only as historical context",
        "A later patch may merge this into `00_global.dot` after review",
    ]:
        assert token in doc


def test_0174_doc_contains_canonical_chain_and_observation_chain() -> None:
    doc = DOC.read_text(encoding="utf-8")
    for token in [
        "GitHub Project / issue / idea repo",
        "GitHub Actions ticket artifact",
        "Copilot preliminary opinion artifact",
        "read-only artifact fetch",
        "configured server dataset",
        "Scheduler / policy / zone",
        "scheduler route handshake / adapter / handler",
        "ControlProxy / RouteProxy runtime data plane",
        "OpenVINO / E5 / specialist work",
        "Qdrant projection/search",
        "SQL durable store / rehydrate",
        "runtime facts",
        "event.bus/context.bus",
        "bus_visualization_adapter",
        "DOT activity graph support",
        "VisPy/browser view",
    ]:
        assert token in doc


def test_0174_rule_locks_no_parallel_bus_or_vispy_writer() -> None:
    rule = RULE.read_text(encoding="utf-8")
    for token in [
        "Treat 0174 graphs as representation drafts, not runtime authority",
        "Do not replace `00_global.dot` in this patch",
        "Keep GitHub as workflow/exchange/validation surface",
        "Keep Qdrant as projection/search, not durable authority",
        "Keep EventBus as observation-only",
        "Keep VisPy/browser as a read/projection surface",
        "Do not create a parallel bus, direct VisPy writer, or Scheduler bypass",
    ]:
        assert token in rule


def test_0174_global_draft_contains_required_clusters_and_forbidden_edges() -> None:
    graph = GLOBAL.read_text(encoding="utf-8")
    for token in [
        "0174 rebuilt runtime global current-state draft",
        "External workflow / exchange",
        "Configured server dataset",
        "Scheduler authority",
        "Local compute / context",
        "Observation / visualization",
        "forbidden command path",
        "forbidden direct writer",
        "forbidden internal bus source",
    ]:
        assert token in graph


def test_0174_subgraph_files_exist_and_have_labels() -> None:
    for name in REQUIRED_SUBGRAPHS:
        path = SUBGRAPH_DIR / name
        assert path.exists(), name
        text = path.read_text(encoding="utf-8")
        assert "0174 subgraph:" in text
        assert "digraph" in text


def test_0174_manifest_lists_graph_files_but_not_00_global_dot() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    for name in REQUIRED_SUBGRAPHS:
        assert name in manifest
    assert "174_rebuilt_runtime_global_current_state.dot" in manifest
    assert "doc/docs/architecture/00_global.dot" not in manifest


def test_0174_docs_provenance_marks_old_graphs_as_historical_input() -> None:
    provenance = (SUBGRAPH_DIR / "docs_provenance.dot").read_text(encoding="utf-8")
    for token in [
        "working code surfaces",
        "tests / rules",
        "patch queue traces",
        "changelogs",
        "old DOT graphs",
        "stale-doc possible",
        "forbidden sole truth",
        "forbidden absence proof",
    ]:
        assert token in provenance
