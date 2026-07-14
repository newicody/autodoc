import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/specialist_capability_growth_reuse_audit_0285.py"
CLI = ROOT / "tools/run_specialist_capability_growth_reuse_audit_0285.py"
REPORT = ROOT / "PHASE0285_R1_SPECIALIST_CAPABILITY_GROWTH_REUSE_AUDIT_REPORT.md"
ARCHITECTURE = ROOT / "doc/architecture/SPECIALIST_CAPABILITY_GROWTH_REUSE_AUDIT_0285.md"
PLAN = ROOT / "doc/architecture/SPECIALIST_CAPABILITY_GROWTH_DEVELOPMENT_PLAN_0285.md"
DOT = ROOT / "doc/architecture/SPECIALIST_CAPABILITY_GROWTH_REUSE_AUDIT_0285.dot"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0285_R1_SPECIALIST_CAPABILITY_GROWTH_REUSE_AUDIT.md"
CHANGELOG = ROOT / "doc/CHANGELOG_0285_R1_SPECIALIST_CAPABILITY_GROWTH_REUSE_AUDIT.md"
INSTALLATION = ROOT / "templates/github/projects-repository/INSTALLATION.md"


def _imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    result: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            result.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            result.add(node.module)
    return result


def test_r1_audit_is_source_only_and_adds_no_parallel_runtime() -> None:
    imports = _imports(SOURCE)
    forbidden = {
        "subprocess",
        "requests",
        "urllib",
        "psycopg",
        "qdrant_client",
        "openvino",
    }

    assert not (imports & forbidden)
    text = SOURCE.read_text(encoding="utf-8")
    assert "dataclass(frozen=True, slots=True)" in text
    assert "PortableSpecialistDescriptor" in text
    assert "Scheduler(" not in text
    assert "LaboratoryManager" not in text
    assert "EventBus(" not in text
    assert "automatic_capability_learning_enabled" in text
    assert '"new_global_specialist_registry_added": False' in text


def test_r1_cli_is_read_only_and_has_no_execution_or_network_switch() -> None:
    imports = _imports(CLI)
    text = CLI.read_text(encoding="utf-8")

    assert "--root" in text
    assert "--format" in text
    assert "--execute" not in text
    assert "--apply" not in text
    assert "--publish" not in text
    assert "subprocess" not in imports
    assert "requests" not in imports
    assert "urllib" not in imports


def test_architecture_documents_lock_the_controlled_growth_boundary() -> None:
    architecture = ARCHITECTURE.read_text(encoding="utf-8")
    plan = PLAN.read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")

    required = (
        "proposal → evidence → operator decision → immutable revision",
        "Scheduler remains the only orchestration authority",
        "SQL remains the durable authority",
        "Qdrant remains projection and recall only",
        "EventBus remains observation only",
        "no global specialist registry",
        "0285-r2-specialist-capability-growth-proposal-contract",
        "0285-r8-specialist-capability-growth-closed-loop-smoke",
    )
    joined = "\n".join((architecture, plan, report))
    for token in required:
        assert token in joined


def test_systematic_deliverables_exist_and_reference_the_same_patch() -> None:
    for path in (REPORT, ARCHITECTURE, PLAN, DOT, MANIFEST, CHANGELOG):
        assert path.is_file()
        assert "0285-r1" in path.read_text(encoding="utf-8")

    manifest = MANIFEST.read_text(encoding="utf-8")
    for path in (SOURCE, CLI, REPORT, ARCHITECTURE, PLAN, DOT, CHANGELOG):
        assert path.relative_to(ROOT).as_posix() in manifest


def test_projects_installation_was_reviewed_and_needs_no_r1_deployment_change() -> None:
    guide = INSTALLATION.read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")

    assert "Version du guide : `0284-r9`." in guide
    assert "AUTODOC_COPILOT_ADVISORY_ENABLED=false" in guide
    assert "verify_specialists_laboratories_live_path_evidence_0284.py" in guide
    assert "Ne pas utiliser `--delete`" in guide
    assert "INSTALLATION reviewed: yes" in report
    assert "INSTALLATION modified: no" in report
    assert "no Projects deployment surface changes in 0285-r1" in report
