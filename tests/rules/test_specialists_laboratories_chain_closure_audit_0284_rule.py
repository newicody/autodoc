from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/context/specialists_laboratories_chain_closure_audit_0284.py"
REPORT = ROOT / "PHASE0284_R8_SPECIALISTS_LABORATORIES_CHAIN_CLOSURE_AUDIT_REPORT.md"
ARCHITECTURE = ROOT / "doc/architecture/SPECIALISTS_LABORATORIES_CHAIN_CLOSURE_AUDIT_0284.md"
DOT = ROOT / "doc/architecture/SPECIALISTS_LABORATORIES_CHAIN_CLOSURE_AUDIT_0284.dot"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0284_R8_SPECIALISTS_LABORATORIES_CHAIN_CLOSURE_AUDIT.md"
CHANGELOG = ROOT / "doc/CHANGELOG_0284_R8_SPECIALISTS_LABORATORIES_CHAIN_CLOSURE_AUDIT.md"


def test_closure_audit_is_source_only_and_does_not_create_runtime_authority() -> None:
    text = MODULE.read_text(encoding="utf-8")

    assert "from dataclasses import dataclass" in text
    assert "Scheduler(" not in text
    assert "QdrantClient" not in text
    assert "import openvino" not in text.lower()
    assert "requests" not in text
    assert "subprocess" not in text
    assert "new_scheduler_added: bool = False" in text
    assert "new_laboratory_manager_added: bool = False" in text


def test_closure_requires_real_evidence_and_preserves_projects_boundary() -> None:
    text = MODULE.read_text(encoding="utf-8")

    assert "operational_evidence_supplied" in text
    assert "operationally_green" in text
    assert "phase_0284_closed=operationally_green" in text
    assert 'projects_configuration_owned_by: str = "newicody/projects"' in text
    assert ".github/workflows/autodoc-controlled-research.yml" in text
    assert "0284-r9-specialists-laboratories-live-path-evidence" in text


def test_phase_documents_contain_required_review_and_honest_transition() -> None:
    report = REPORT.read_text(encoding="utf-8")
    architecture = ARCHITECTURE.read_text(encoding="utf-8")

    required = (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: n/a",
        "live_path_uses_real_backend: n/a",
        "external_dependencies_added: false",
        "scheduler_modified: false",
        "network_added: false",
        "github_api_added: false",
        "qdrant_added: false",
        "llm_or_openvino_added: false",
        "search_commands_bounded: n/a",
        "phase_0284_implementation_complete: true",
        "phase_0284_closed_by_patch_validation: false",
    )
    for marker in required:
        assert marker in report
    assert "implémentation" in architecture
    assert "preuve opérationnelle" in architecture


def test_manifest_changelog_and_dot_are_present_without_generated_svg() -> None:
    assert MANIFEST.is_file()
    assert CHANGELOG.is_file()
    assert DOT.is_file()
    assert "digraph" in DOT.read_text(encoding="utf-8")
    assert not (DOT.with_suffix(".svg")).exists()
