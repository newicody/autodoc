from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROVIDER = ROOT / "src/context/native_love_laboratory_second_specialist_0287.py"
BINDING = (
    ROOT
    / "src/context/native_love_laboratory_collaboration_scheduler_binding_0287.py"
)
README = ROOT / "doc/README_CURRENT.md"
REPORT = ROOT / "PHASE0287_R7_R11_NATIVE_LOVE_SECOND_SPECIALIST_COLLABORATION_REPORT.md"
ARCH = (
    ROOT
    / "doc/architecture/NATIVE_LOVE_SECOND_SPECIALIST_COLLABORATION_0287_R7_R11.md"
)
DOT = (
    ROOT
    / "doc/architecture/NATIVE_LOVE_SECOND_SPECIALIST_COLLABORATION_0287_R7_R11.dot"
)
MANIFEST = (
    ROOT
    / "doc/manifests/MANIFEST_0287_R7_R11_NATIVE_LOVE_SECOND_SPECIALIST_COLLABORATION.md"
)
CHANGELOG = (
    ROOT
    / "doc/CHANGELOG_0287_R7_R11_NATIVE_LOVE_SECOND_SPECIALIST_COLLABORATION.md"
)


def test_r11_reuses_existing_contracts_and_scheduler() -> None:
    source = PROVIDER.read_text(encoding="utf-8")
    binding = BINDING.read_text(encoding="utf-8")

    for token in (
        "NativeLoveLaboratoryProvider",
        "SpecialistLaboratoryMessageV2",
        "SpecialistLaboratoryConversationV2",
        "SpecialistArtifactReference",
        "LOVE_RELATIONAL_DYNAMICS_SPECIALIST_REF",
        "direct_followup_execution",
        "global_synthesis_created",
    ):
        assert token in source
    for token in (
        "SchedulerContract",
        "LABORATORY_VISIT_REQUEST",
        "followup_visit_submitted",
        "direct_specialist_invocation",
    ):
        assert token in binding
    forbidden = (
        "class LaboratoryManager",
        "class SpecialistManager",
        "class CollaborationScheduler",
        "import torch",
        "import transformers",
        "import openvino",
        "import qdrant_client",
    )
    for token in forbidden:
        assert token not in source
        assert token not in binding


def test_r11_deliverables_and_roadmap_are_complete() -> None:
    for path in (REPORT, ARCH, DOT, MANIFEST, CHANGELOG):
        assert path.exists(), path
        assert path.read_text(encoding="utf-8").strip()
    current = README.read_text(encoding="utf-8")
    assert "0287-r7-r11" in current
    assert "second specialist" in current.lower()
    assert "0287-r7-r12" in current


def test_installation_is_explicitly_unchanged() -> None:
    report = REPORT.read_text(encoding="utf-8")
    manifest = MANIFEST.read_text(encoding="utf-8")
    assert "INSTALLATION.md" in report
    assert "unchanged" in report
    assert "INSTALLATION.md" in manifest
    assert "not modified" in manifest
