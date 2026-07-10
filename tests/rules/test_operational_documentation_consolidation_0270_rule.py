from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
LAYERS = ROOT / "doc/ARCHITECTURE_LAYERS.md"
CURRENT = ROOT / "doc/architecture/CURRENT_ARCHITECTURE_STATE_0154.md"
DECISION = ROOT / "doc/architecture/OPERATIONAL_DOCUMENTATION_CONSOLIDATION_0270.md"
GLOBAL = ROOT / "doc/docs/architecture/00_global.dot"
PHASE_GRAPH = ROOT / "doc/docs/architecture/runtime/270_operational_documentation_consolidation.dot"
RULE = ROOT / "doc/code-rules/0270_operational_documentation_consolidation_rule.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0270_OPERATIONAL_DOCUMENTATION_CONSOLIDATION_CHANGED_FILES.md"

CHAIN = "0260 -> 0261 -> 0262 -> 0263 -> 0264 -> 0265 -> 0266 -> 0267 -> 0268 -> 0269"


def test_current_entrypoints_expose_the_0260_0269_baseline() -> None:
    readme = README.read_text(encoding="utf-8")
    layers = LAYERS.read_text(encoding="utf-8")
    current = CURRENT.read_text(encoding="utf-8")
    decision = DECISION.read_text(encoding="utf-8")

    assert "0260 SQL write" in readme
    assert "Current operational baseline — 0270" in layers
    assert "canonical index refreshed by 0270" in current
    assert CHAIN in decision


def test_authority_boundaries_are_locked_in_current_docs() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (README, CURRENT, DECISION, RULE)
    )

    assert "SQL = durable authority" in combined
    assert "payload.sql_ref" in combined
    assert "EventBus = observation only" in combined
    assert "PassiveSupervisor = observation only" in combined
    assert "OpenRC / OS / admin = external process authority" in combined
    assert "remote mutation remains forbidden" in combined
    assert "Scheduler.run is not modified" in combined


def test_master_graph_contains_a_root_attached_0270_baseline() -> None:
    text = GLOBAL.read_text(encoding="utf-8")

    assert "cluster_0270_PROTOTYPE_OPERATIONAL_BASELINE" in text
    assert "PrototypeSql0260 -> PrototypeEmbedding0261" in text
    assert "PrototypeReadiness0268 -> PrototypeSmoke0269" in text
    assert "P1DocsRefresh -> PrototypeSql0260" in text
    assert "no remote mutation" in text
    assert "no service start" in text


def test_phase_graph_and_manifest_are_documentation_only() -> None:
    graph = PHASE_GRAPH.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")
    rule = RULE.read_text(encoding="utf-8")

    assert "0260..0269" in graph
    assert "No source, tool, Scheduler, handler, adapter or runtime file is changed" in manifest
    assert "new runtime module" in rule
    assert "new RuntimeManager or Orchestrator" in rule
    assert "no non-stdlib dependency" in rule


def test_0270_preserves_stable_readme_and_0154_compatibility_contracts() -> None:
    readme = README.read_text(encoding="utf-8")
    current = CURRENT.read_text(encoding="utf-8")

    for section in (
        "## Current architecture",
        "## Source of truth",
        "## Documentation map",
        "## AI-assisted development",
        "## Current boundary",
        "## Roadmap orientation",
    ):
        assert section in readme

    for phrase in (
        "SQL owns durable context",
        "Qdrant owns recall projections",
        "OpenVINO/E5 owns vector generation",
        "RouteProxy owns fast frames",
        "DbApiSqlContextStore.upsert_record",
        "AUTODOC_SQL_CONTEXT_DB",
    ):
        assert phrase in current

    assert "Scheduler.run(" not in current
