from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/run_production_prototype_smoke_composition_0269.py"
DOC = ROOT / "doc/architecture/QDRANT_SQL_AUTHORITY_FINAL_AGGREGATION_FIX_0271.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0271_QDRANT_SQL_AUTHORITY_FINAL_AGGREGATION_FIX_CHANGED_FILES.md"


def test_0271_r6_extracts_and_summarises_sql_authority_ref() -> None:
    text = TOOL.read_text(encoding="utf-8")
    assert '"sql_authority_ref",' in text
    assert "sql_authority_ref={references.get('sql_authority_ref', '-')}" in text


def test_0271_r6_is_aggregation_only() -> None:
    manifest = MANIFEST.read_text(encoding="utf-8")
    forbidden = (
        "src/scheduler.py",
        "RuntimeManager",
        "QdrantClientProjectionExecutor",
        "run_scheduler_managed_embedding_qdrant_projection_0262.py",
        "run_scheduler_managed_qdrant_recall_sql_rehydrate_0263.py",
    )
    for value in forbidden:
        assert value not in manifest


def test_0271_r6_documents_no_runtime_or_network_change() -> None:
    text = DOC.read_text(encoding="utf-8")
    for phrase in (
        "aggregation-only",
        "no Qdrant call",
        "no SQL write",
        "no SHM change",
        "no Scheduler loop change",
    ):
        assert phrase in text
