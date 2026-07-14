import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/specialist_capability_growth_proposal_contract_0285.py"
CONTEXT_TEST = ROOT / "tests/context/test_specialist_capability_growth_proposal_contract_0285.py"
REPORT = ROOT / "PHASE0285_R2_SPECIALIST_CAPABILITY_GROWTH_PROPOSAL_CONTRACT_REPORT.md"
ARCHITECTURE = ROOT / "doc/architecture/SPECIALIST_CAPABILITY_GROWTH_PROPOSAL_CONTRACT_0285.md"
DOT = ROOT / "doc/architecture/SPECIALIST_CAPABILITY_GROWTH_PROPOSAL_CONTRACT_0285.dot"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0285_R2_SPECIALIST_CAPABILITY_GROWTH_PROPOSAL_CONTRACT.md"
CHANGELOG = ROOT / "doc/CHANGELOG_0285_R2_SPECIALIST_CAPABILITY_GROWTH_PROPOSAL_CONTRACT.md"
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


def test_r2_contract_is_immutable_stdlib_only_and_non_executable() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    imports = _imports(SOURCE)
    forbidden = {
        "asyncio",
        "openvino",
        "psycopg",
        "qdrant_client",
        "requests",
        "subprocess",
        "urllib",
    }
    assert not (imports & forbidden)
    assert source.count("@dataclass(frozen=True, slots=True)") == 2
    assert "class SpecialistCapabilityEvidenceRef" in source
    assert "class SpecialistCapabilityGrowthProposal" in source
    assert '"authoritative": False' in source
    assert '"approved": False' in source
    assert '"scheduler_dispatch_allowed": False' in source
    assert "Scheduler(" not in source
    assert "LaboratoryManager" not in source
    assert "BackendRegistry" not in source


def test_r2_contract_contains_no_storage_network_or_runtime_boundary() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    forbidden_tokens = (
        "INSERT INTO",
        "UPDATE ",
        "DELETE FROM",
        "http://",
        "https://",
        "workflow_dispatch",
        "qdrant_client",
        "openvino.runtime",
    )
    for token in forbidden_tokens:
        assert token not in source


def test_r2_documents_lock_proposal_evidence_operator_boundary() -> None:
    joined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (REPORT, ARCHITECTURE, CHANGELOG)
    )
    required = (
        "0285-r2-specialist-capability-growth-proposal-contract",
        "evidence-backed proposal",
        "non-authoritative",
        "operator decision",
        "Scheduler remains the only orchestration authority",
        "SQL remains the durable authority",
        "Qdrant remains projection and recall only",
        "0285-r3-portable-specialist-revision-lineage-contract",
    )
    for token in required:
        assert token in joined


def test_r2_systematic_deliverables_exist_and_manifest_them() -> None:
    deliverables = (SOURCE, CONTEXT_TEST, REPORT, ARCHITECTURE, DOT, CHANGELOG)
    for path in (*deliverables, MANIFEST):
        assert path.is_file()
    manifest = MANIFEST.read_text(encoding="utf-8")
    for path in deliverables:
        assert path.relative_to(ROOT).as_posix() in manifest


def test_projects_installation_was_reviewed_without_deployment_change() -> None:
    guide = INSTALLATION.read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")
    assert "AUTODOC_COPILOT_ADVISORY_ENABLED=false" in guide
    assert "Ne pas utiliser `--delete`" in guide
    assert "INSTALLATION reviewed: yes" in report
    assert "INSTALLATION modified: no" in report
    assert "no Projects deployment surface changes in 0285-r2" in report
