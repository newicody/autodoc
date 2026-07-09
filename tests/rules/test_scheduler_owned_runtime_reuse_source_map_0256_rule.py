from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_0256_source_map_is_filtered_and_read_only() -> None:
    source = (ROOT / "src/context/scheduler_owned_runtime_reuse_source_map_0256.py").read_text(
        encoding="utf-8"
    )

    assert "audit_first_adapt_second" in source
    assert "scheduler_owns_runtime_components" in source
    assert "no_cli_per_component" in source
    assert "PHASE" in source
    assert ".aider.chat.history.md" in source
    assert "docs_excluded_from_source_selection" in source
    assert "importlib" not in source
    assert "Scheduler.run(" not in source
    assert ".upsert(" not in source
    assert "requests." not in source


def test_0256_docs_lock_development_axis() -> None:
    doc = (ROOT / "doc/architecture/SCHEDULER_OWNED_RUNTIME_REUSE_SOURCE_MAP_0256.md").read_text(
        encoding="utf-8"
    )

    assert "in line with 0254 and 0255" in doc
    assert "Scheduler owns runtime components" in doc
    assert "reuse existing implementation surfaces" in doc
    assert "no CLI per component" in doc
    assert "last audit before adaptation" in doc
