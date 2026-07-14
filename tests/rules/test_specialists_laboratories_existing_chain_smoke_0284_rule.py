from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/specialists_laboratories_existing_chain_smoke_0284.py"
REPORT = ROOT / "PHASE0284_R5_SPECIALISTS_LABORATORIES_EXISTING_CHAIN_SMOKE_REPORT.md"
ARCHITECTURE = ROOT / "doc/architecture/SPECIALISTS_LABORATORIES_EXISTING_CHAIN_SMOKE_0284.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0284_R5_SPECIALISTS_LABORATORIES_EXISTING_CHAIN_SMOKE.md"
TRANSFER_CONTRACT = ROOT / "src/context/specialist_laboratory_transfer_contract_0284.py"


def test_r5_reuses_existing_scheduler_smoke_and_portable_contracts() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert "run_fake_laboratory_existing_scheduler_closed_loop_smoke" in text
    assert "PortableSpecialistDescriptor" in text
    assert "SpecialistDemandFrame" in text
    assert "SpecialistOpinionFrame" in text
    assert "SpecialistLaboratoryConversation" in text
    assert "scheduler.run(" not in text
    assert "Scheduler(" not in text
    assert "LaboratoryManager" not in text


def test_r5_requires_the_preceding_transfer_contract_without_executing_it() -> None:
    assert TRANSFER_CONTRACT.is_file()
    source = SOURCE.read_text(encoding="utf-8")
    assert "transfer_execution_performed: bool = False" in source


def test_r5_reports_fake_transition_without_real_backend_claim() -> None:
    report = REPORT.read_text(encoding="utf-8")
    architecture = ARCHITECTURE.read_text(encoding="utf-8")
    joined = report + architecture
    assert "live_path_status: transition" in joined
    assert "live_path_uses_real_backend: false" in joined
    assert "fake_specialist_functional: true" in joined
    assert "transfer_execution_performed: false" in joined
    assert "scheduler_modified: false" in joined
    assert "new_scheduler_added: false" in joined
    assert "new_laboratory_manager_added: false" in joined


def test_r5_manifest_lists_only_the_declared_patch_surface() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    assert "src/context/specialists_laboratories_existing_chain_smoke_0284.py" in text
    assert "tests/context/test_specialists_laboratories_existing_chain_smoke_0284.py" in text
    assert "tests/rules/test_specialists_laboratories_existing_chain_smoke_0284_rule.py" in text
    assert "tools/" not in text
