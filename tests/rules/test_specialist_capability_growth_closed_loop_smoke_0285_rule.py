from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/specialist_capability_growth_closed_loop_smoke_0285.py"
TEST = ROOT / "tests/context/test_specialist_capability_growth_closed_loop_smoke_0285.py"
REPORT = ROOT / "PHASE0285_R8_SPECIALIST_CAPABILITY_GROWTH_CLOSED_LOOP_SMOKE_REPORT.md"
DOC = ROOT / "doc/architecture/SPECIALIST_CAPABILITY_GROWTH_CLOSED_LOOP_SMOKE_0285.md"
DOT = ROOT / "doc/architecture/SPECIALIST_CAPABILITY_GROWTH_CLOSED_LOOP_SMOKE_0285.dot"
CHANGELOG = ROOT / "doc/CHANGELOG_0285_R8_SPECIALIST_CAPABILITY_GROWTH_CLOSED_LOOP_SMOKE.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0285_R8_SPECIALIST_CAPABILITY_GROWTH_CLOSED_LOOP_SMOKE.md"
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"


def test_systematic_r8_deliverables_exist() -> None:
    for path in (SOURCE, TEST, REPORT, DOC, DOT, CHANGELOG, MANIFEST):
        assert path.is_file(), path


def test_r8_reuses_existing_contracts_and_laboratory_smoke() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    required = (
        "SpecialistCapabilityGrowthProposal",
        "PortableSpecialistRevision",
        "SpecialistCapabilityGrowthOperatorGate",
        "SpecialistCapabilityGrowthHistoryPort",
        "SchedulerApprovedSpecialistRevisionSelectionHandler",
        "build_specialist_capability_growth_observation_projection",
        "run_portable_specialist_existing_chain_smoke",
        "PortableSpecialistExistingChainSmokeCommand",
        "phase_0285_closed",
    )
    for token in required:
        assert token in source


def test_r8_does_not_import_or_create_parallel_runtime_authorities() -> None:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden_imports = {
        "kernel.scheduler",
        "kernel.dispatcher",
        "kernel.queue",
        "kernel.registry",
        "kernel.event_bus",
    }
    assert imported.isdisjoint(forbidden_imports)
    source = SOURCE.read_text(encoding="utf-8")
    assert "class LaboratoryManager" not in source
    assert "class Scheduler(" not in source
    assert "new_scheduler_created\": False" in source
    assert "parallel_orchestrator_created\": False" in source


def test_rejected_and_deferred_revisions_are_proven_blocked() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert 'for outcome in ("reject", "defer")' in source
    assert "SpecialistCapabilityGrowthHistoryAppendCommand(" in source
    assert "except SpecialistCapabilityGrowthDurableHistoryError" in source
    test_text = TEST.read_text(encoding="utf-8")
    assert "test_reject_and_defer_are_blocked_before_history_port" in test_text


def test_r8_requires_sql_authority_and_keeps_qdrant_github_non_authoritative() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    assert 'history_port.authority_contract != "sql"' in source
    assert "history_port.durable is not True" in source
    assert '"qdrant_authoritative": False' in source
    assert '"github_mutation_performed": False' in source


def test_installation_guide_remains_safe_and_needs_no_r8_change() -> None:
    text = INSTALLATION.read_text(encoding="utf-8")
    assert "Version du guide : `0284-r9`." in text
    assert "AUTODOC_COPILOT_ADVISORY_ENABLED=false" in text
    assert "--delete" in text
    report = REPORT.read_text(encoding="utf-8")
    assert "No update is needed" in report
    assert "no workflow" in report
