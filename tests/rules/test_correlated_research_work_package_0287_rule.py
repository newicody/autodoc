from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/correlated_research_work_package_0287.py"
CURRENT = ROOT / "doc/README_CURRENT.md"
REPORT = ROOT / "PHASE0287_R7_R7_CORRELATED_RESEARCH_WORK_PACKAGE_REPORT.md"
MANIFEST = (
    ROOT
    / "doc/manifests/MANIFEST_0287_R7_R7_CORRELATED_RESEARCH_WORK_PACKAGE.md"
)


def test_work_package_reuses_existing_ingress_and_locks_boundaries() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    for marker in (
        'WORK_PACKAGE_SCHEMA = "missipy.research.correlated_work_package.v1"',
        'RUN_ASSEMBLY_SCHEMA = "missipy.github.dual_artifact_run_assembly.v1"',
        'INTAKE_SCHEMA = "missipy.github.dual_artifact_source_candidate_intake.v1"',
        'ATTACHMENT_MANIFEST_SCHEMA = "missipy.github_issue.attachment_manifest.v1"',
        "advisory_used_as_hint_only",
        "attachment_bytes_embedded",
        "local_path_exposed",
        "scheduler_route_created",
        "sql_write_performed",
        "qdrant_write_performed",
        "github_mutation_performed",
    ):
        assert marker in source

    assert "requests." not in source
    assert "urllib.request" not in source
    assert "subprocess" not in source
    assert "Scheduler(" not in source


def test_current_roadmap_records_r7_closure_and_r8_boundary() -> None:
    text = CURRENT.read_text(encoding="utf-8")
    assert "0287-r7-r7 — correlated research work package" in text
    assert "missipy.research.correlated_work_package.v1" in text
    assert "preserves the request and" in text
    assert "excludes raw bytes and local paths" in text
    assert "0287-r7-r8 — specialist/laboratory message v2" in text
    assert "There is no phase 0288" in text


def test_phase_evidence_declares_no_installation_or_runtime_mutation() -> None:
    report = REPORT.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")
    for marker in (
        "code_rule_review: done",
        "code_rule_update_required: false",
        "live_path_status: contract_ready",
        "installation_update_required: false",
    ):
        assert marker in report
    assert "GitHub Actions workflows" in manifest
    assert "Scheduler, laboratory registry and fake laboratory" in manifest
    assert "SQL, Qdrant, OpenVINO and EventBus" in manifest
