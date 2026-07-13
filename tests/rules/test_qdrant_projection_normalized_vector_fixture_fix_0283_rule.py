from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TEST = (
    ROOT
    / "tests/context/"
    "test_scheduler_managed_qdrant_projection_binding_0283.py"
)
REPORT = (
    ROOT
    / "PHASE0283_R4_R1_NORMALIZED_VECTOR_FIXTURE_FIX_REPORT.md"
)
MANIFEST = (
    ROOT
    / "doc/manifests/"
    "MANIFEST_0283_R4_R1_NORMALIZED_VECTOR_FIXTURE_FIX.md"
)
CHANGELOG = (
    ROOT
    / "doc/"
    "CHANGELOG_0283_R4_R1_NORMALIZED_VECTOR_FIXTURE_FIX.md"
)


def test_projection_fixture_is_a_real_unit_vector() -> None:
    source = TEST.read_text(encoding="utf-8")

    assert '"vector": [1.0] + [0.0] * 383,' in source
    assert '"vector": [0.0] * 384,' not in source
    assert '"normalized": True,' in source


def test_fix_is_test_only_and_documents_runtime_unchanged() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (REPORT, MANIFEST, CHANGELOG)
    )

    for required in (
        "runtime_source_modified: false",
        "fixture_only_fix: true",
        "projection_binding_logic_modified: false",
        "qdrant_write_performed: false",
        "qdrant_search_performed: false",
        "scheduler_modified: false",
        "projects_repository_change_required: false",
        "external_dependencies_added: false",
    ):
        assert required in combined
