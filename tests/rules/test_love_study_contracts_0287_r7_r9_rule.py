from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/love_study_contracts_0287.py"
CURRENT = ROOT / "doc/README_CURRENT.md"
REPORT = ROOT / "PHASE0287_R7_R9_LOVE_STUDY_CONTRACTS_REPORT.md"
ARCH = ROOT / "doc/architecture/LOVE_STUDY_CONTRACTS_0287_R7_R9.md"
DOT = ROOT / "doc/architecture/LOVE_STUDY_CONTRACTS_0287_R7_R9.dot"
CHANGELOG = ROOT / "doc/CHANGELOG_0287_R7_R9_LOVE_STUDY_CONTRACTS.md"
MANIFEST = ROOT / "doc/manifests/MANIFEST_0287_R7_R9_LOVE_STUDY_CONTRACTS.md"


def test_contract_reuses_portable_multitask_and_laboratory_surfaces() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    for token in (
        "PortableSpecialistDescriptor",
        "ExtensibleMultitaskSpecialistDefinition",
        "LaboratoryDescriptor",
        'provider_kind="autodoc_native"',
        'availability="declared"',
        "enabled=False",
        "network_allowed=False",
        '"global_synthesis", "later_liaison_step"',
    ):
        assert token in text

    for forbidden in (
        "class LaboratoryManager",
        "class SpecialistManager",
        "from kernel.scheduler",
        "import openvino",
        "import torch",
        "import transformers",
        "qdrant_client",
        "from runtime.control_proxy",
    ):
        assert forbidden not in text


def test_domain_contracts_and_refs_are_versioned() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    for token in (
        "missipy.love.study_request.v1",
        "missipy.love.analysis_finding.v1",
        "missipy.love.concept_affect_analysis.v1",
        "missipy.love.relational_dynamics_analysis.v1",
        "missipy.love.study_result.v1",
        "laboratory:love-studies-local",
        "specialist:love-concept-and-affect-analyst",
        "specialist:love-relational-dynamics-analyst",
    ):
        assert token in text


def test_current_roadmap_closes_r9_and_keeps_product_sequence() -> None:
    text = CURRENT.read_text(encoding="utf-8")

    for token in (
        "0287-r7-r9 — love-study contracts and specialist descriptors",
        "Closure status: implemented as contract-only",
        "0287-r7-r10 — concrete native laboratory and first specialist",
        "0287-r7-r11 — second specialist and Scheduler-controlled collaboration",
        "0287-r7-r12 — memory, evidence and liaison synthesis integration",
        "0287-r7-r13 — final deliverable publication plan",
        "0287-r7-r16 — recovery, installation and prototype closure",
        "There is no phase 0288 and no Chalouf",
        "integrator phase.",
    ):
        assert token in text


def test_systematic_livrerables_exist_and_lock_boundaries() -> None:
    for path in (REPORT, ARCH, DOT, CHANGELOG, MANIFEST):
        assert path.is_file(), path

    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (REPORT, ARCH, CHANGELOG, MANIFEST)
    )
    for token in (
        "Scheduler remains the only orchestration authority",
        "SQL remains the durable context authority",
        "Qdrant remains projection and recall only",
        "OpenVINO is reused and not reimplemented",
        "ControlProxy remains transport-only",
        "No runtime is attached in r9",
        "Global synthesis remains a later liaison step",
    ):
        assert token in combined
