from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TOOL = (
    ROOT
    / "tools/run_qdrant_real_closed_loop_smoke_0283.py"
)
TEST = (
    ROOT
    / "tests/tools/"
    "test_run_qdrant_real_closed_loop_smoke_0283.py"
)
REPORT = (
    ROOT
    / "PHASE0283_R8_R1_LAZY_0261_EMBEDDING_IMPORT_FIX_REPORT.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/"
    "MANIFEST_0283_R8_R1_LAZY_0261_EMBEDDING_IMPORT_FIX.md"
)
CHANGELOG = (
    ROOT
    / "doc/"
    "CHANGELOG_0283_R8_R1_LAZY_0261_EMBEDDING_IMPORT_FIX.md"
)


def test_0261_import_is_lazy_and_grouped() -> None:
    source = TOOL.read_text(encoding="utf-8")

    resolver_pos = source.index("def _resolve_embedding_runtime(")
    import_pos = source.index(
        "from context."
        "scheduler_managed_sql_ref_openvino_embedding_usage_0261 import"
    )

    assert import_pos > resolver_pos
    assert source[:resolver_pos].count(
        "scheduler_managed_sql_ref_openvino_embedding_usage_0261"
    ) == 0
    assert (
        '"embedding injection requires runner, request builder "'
        in source
    )
    assert '"and demo builder together"' in source


def test_regression_covers_preexisting_0261_stub() -> None:
    source = TEST.read_text(encoding="utf-8")

    assert (
        "test_tool_import_ignores_preexisting_0261_stub"
        in source
    )
    assert (
        'ModuleType(\n'
        '        "context.'
        'scheduler_managed_sql_ref_openvino_embedding_usage_0261"'
    ) in source


def test_fix_preserves_runtime_and_effect_boundaries() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (REPORT, MANIFEST, CHANGELOG)
    )

    for required in (
        "embedding_0261_import_lazy: true",
        "canonical_0261_runtime_reused: true",
        "injected_tests_import_0261: false",
        "embedding_runtime_duplicated: false",
        "preview_effects_changed: false",
        "execute_effects_changed: false",
        "scheduler_modified: false",
        "new_runtime_module_added: false",
        "new_transport_added: false",
        "qdrant_effect_added: false",
        "sql_write_added: false",
        "projects_repository_change_required: false",
    ):
        assert required in combined
