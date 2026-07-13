from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / "tools/run_qdrant_real_binding_0283.py"
TEST = (
    ROOT
    / "tests/tools/"
    "test_run_qdrant_real_binding_0283.py"
)
REPORT = (
    ROOT
    / "PHASE0283_R7_R1_LAZY_SQL_STORE_IMPORT_FIX_REPORT.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/"
    "MANIFEST_0283_R7_R1_LAZY_SQL_STORE_IMPORT_FIX.md"
)
CHANGELOG = (
    ROOT
    / "doc/"
    "CHANGELOG_0283_R7_R1_LAZY_SQL_STORE_IMPORT_FIX.md"
)


def test_sql_store_import_is_lazy() -> None:
    source = TOOL.read_text(encoding="utf-8")

    function_pos = source.index("def _open_read_only_sql_store(")
    import_pos = source.index(
        "from context.sql_context_store import ("
    )

    assert import_pos > function_pos
    assert source[:function_pos].count(
        "from context.sql_context_store import ("
    ) == 0


def test_regression_covers_preexisting_stub_module() -> None:
    source = TEST.read_text(encoding="utf-8")

    assert (
        "test_tool_import_ignores_preexisting_sql_store_stub"
        in source
    )
    assert 'ModuleType("context.sql_context_store")' in source


def test_fix_preserves_runtime_boundaries() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (REPORT, MANIFEST, CHANGELOG)
    )

    for required in (
        "sql_store_import_lazy: true",
        "readiness_imports_sql_store: false",
        "projection_imports_sql_store: false",
        "recall_preview_imports_sql_store: false",
        "recall_execute_imports_sql_store: true",
        "scheduler_modified: false",
        "new_runtime_module_added: false",
        "new_transport_added: false",
        "qdrant_effect_added: false",
        "sql_write_added: false",
        "projects_repository_change_required: false",
    ):
        assert required in combined
