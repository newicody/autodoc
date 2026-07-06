from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "doc" / "architecture" / "CURRENT_ARCHITECTURE_STATE_0154.md"
ROADMAP = ROOT / "doc" / "architecture" / "P1_TO_P5_ROADMAP_0154.md"
POLICY = ROOT / "doc" / "architecture" / "DOC_REFRESH_POLICY_0154.md"
DOT_PIPELINE = ROOT / "doc" / "docs" / "architecture" / "runtime" / "154_current_p1_pipeline.dot"
DOT_ROADMAP = ROOT / "doc" / "docs" / "architecture" / "runtime" / "154_p1_to_p5_roadmap.dot"
RULE = ROOT / "doc" / "code-rules" / "0154_architecture_current_state_refresh_rule.md"


def test_0154_current_state_docs_exist_and_keep_hierarchy() -> None:
    for path in [CURRENT, ROADMAP, POLICY, DOT_PIPELINE, DOT_ROADMAP, RULE]:
        assert path.exists(), path


def test_0154_current_state_declares_authority_boundaries() -> None:
    text = CURRENT.read_text(encoding="utf-8")
    required = [
        "SQL owns durable context",
        "Qdrant owns recall projections",
        "OpenVINO/E5 owns vector generation",
        "RouteProxy owns fast frames",
        "DbApiSqlContextStore.upsert_record",
        "AUTODOC_SQL_CONTEXT_DB",
    ]
    for phrase in required:
        assert phrase in text


def test_0154_roadmap_covers_p1_to_p5_and_after_p5() -> None:
    text = ROADMAP.read_text(encoding="utf-8")
    for phrase in ["P1", "P2", "P3", "P4", "P5", "After P5", "P6", "P12"]:
        assert phrase in text


def test_0154_docs_do_not_introduce_parallel_runtime_signatures() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [CURRENT, ROADMAP, POLICY, RULE, DOT_PIPELINE, DOT_ROADMAP]
    )
    forbidden = [
        "SQLPersistenceWorker" + "(",
        "SQLOrchestrator" + "(",
        "LocalArtifactOrchestrator" + "(",
        "LocalVectorIndexingOrchestrator" + "(",
        "SchedulerOpenVINORunner" + "(",
        "VectorOpenVINOEmbeddingAdapter" + "(",
        "VectorQdrantProjectionAdapter" + "(",
        "Scheduler" + ".run(",
        "qdrant_client",
        "openvino.runtime",
    ]
    for phrase in forbidden:
        assert phrase not in combined


def test_0154_dot_graphs_parse_as_graphviz_sources() -> None:
    for path in [DOT_PIPELINE, DOT_ROADMAP]:
        text = path.read_text(encoding="utf-8")
        assert text.startswith("digraph ")
        assert "->" in text
        assert text.rstrip().endswith("}")
