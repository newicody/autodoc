from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/projects_copilot_specialist_integrated_smoke_0284.py"
REPORT = ROOT / "PHASE0284_R7_PROJECTS_COPILOT_SPECIALIST_INTEGRATED_SMOKE_REPORT.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0284_R7_PROJECTS_COPILOT_SPECIALIST_INTEGRATED_SMOKE.md"
ARCHITECTURE = ROOT / "doc/architecture/PROJECTS_COPILOT_SPECIALIST_INTEGRATED_SMOKE_0284.md"


def test_r7_reuses_existing_assembly_memory_and_publication_surfaces() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    assert "run_github_dual_artifact_run_assembly" in text
    assert "build_copilot_advisory_laboratory_projection" in text
    assert "run_portable_specialist_real_memory_closure" in text
    assert "plan_github_controlled_advisory_issue_publication" in text
    assert "project_copilot_advisory_fields.py" in text


def test_r7_does_not_add_remote_or_orchestration_authority() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    assert '"scheduler_created": False' in text
    assert '"scheduler_modified": False' in text
    assert '"github_mutation_performed": False' in text
    assert '"projectv2_mutation_performed": False' in text
    assert '"projects_configuration_owned_by": "newicody/projects"' in text
    assert "class LaboratoryManager" not in text
    assert "Scheduler(" not in text


def test_r7_keeps_copilot_hint_only_and_sql_authoritative() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    assert '"advisory_is_authority": False' in text
    assert '"request_authoritative": True' in text
    assert '"sql_remains_authority": True' in text
    assert '"qdrant_projection_recall_only": True' in text
    assert '["Résumé", "Serveur"]' in text


def test_r7_report_manifest_and_architecture_lock_the_live_path() -> None:
    report = REPORT.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")
    architecture = ARCHITECTURE.read_text(encoding="utf-8")

    for text in (report, manifest, architecture):
        assert "newicody/projects" in text
        assert "0284-r6" in text
        assert "github_mutation_performed: false" in text
        assert "projectv2_mutation_performed: false" in text
    assert "live_path_status: green" in report
    assert "live_path_uses_real_backend: true" in report
