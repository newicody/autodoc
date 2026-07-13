from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MATRIX = (
    ROOT / "tests/context/"
    "test_github_real_closed_loop_closure_matrix_0281.py"
)
DOCS = (
    ROOT / "doc/architecture/"
    "GITHUB_REAL_CLOSED_LOOP_CLOSURE_MATRIX_0281.md",
    ROOT / "doc/manifests/"
    "MANIFEST_0281_R8_REAL_CLOSED_LOOP_CLOSURE_MATRIX.md",
    ROOT / "doc/"
    "CHANGELOG_0281_R8_REAL_CLOSED_LOOP_CLOSURE_MATRIX.md",
    ROOT / "PHASE0281_R8_REAL_CLOSED_LOOP_CLOSURE_MATRIX_REPORT.md",
)


def test_matrix_names_every_closure_case() -> None:
    source = MATRIX.read_text(encoding="utf-8")
    for required in (
        "allow_missing_advisory=True",
        "allow_missing_advisory=False",
        "duplicate {slot} artifact member",
        "duplicate imported member",
        "sha256 mismatch",
        'action == "create"',
        'action == "replay"',
        'action == "collision"',
        "github_mutation_performed is False",
    ):
        assert required in source


def test_r8_adds_no_parallel_runtime_or_remote_effect() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8") for path in DOCS
    )
    for required in (
        "runtime_source_modified: false",
        "new_runtime_module_added: false",
        "new_cli_added: false",
        "scheduler_modified: false",
        "projects_repository_change_required: false",
        "external_dependencies_added: false",
        "github_mutation_performed: false",
    ):
        assert required in combined


def test_phase_report_has_complete_code_rule_review() -> None:
    report = DOCS[-1].read_text(encoding="utf-8")
    for required in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: n/a",
        "live_path_uses_real_backend: n/a",
        "context_contract_version: n/a",
        "context_contract_changed: false",
        "search_commands_bounded: n/a",
        "network_added: false",
        "github_api_added: false",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
    ):
        assert required in report
