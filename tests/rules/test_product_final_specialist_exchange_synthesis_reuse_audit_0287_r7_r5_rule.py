from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CURRENT = ROOT / "doc/README_CURRENT.md"
REPORT = ROOT / (
    "PHASE0287_R7_R5_PRODUCT_FINAL_SPECIALIST_EXCHANGE_SYNTHESIS_"
    "REUSE_AUDIT_REPORT.md"
)
MESSAGE = ROOT / "src/context/specialist_laboratory_message_contract_0284.py"
TRANSFER = ROOT / "src/context/specialist_laboratory_transfer_contract_0284.py"
LIAISON = ROOT / "src/context/specialist_liaison_synthesis.py"
DELIBERATION = ROOT / "src/context/server_oriented_deliberation_cycle.py"
FAKE_PROVIDER = ROOT / "src/context/deterministic_fake_laboratory_provider_0273.py"
MEMORY = ROOT / "src/context/portable_specialist_real_memory_closure_0284.py"


def test_existing_specialist_exchange_contract_is_the_canonical_base() -> None:
    source = MESSAGE.read_text(encoding="utf-8")
    for token in (
        "missipy.specialist.laboratory_message.v1",
        "message_ref",
        "conversation_ref",
        "visit_ref",
        "sequence_no",
        "reply_to_message_ref",
        "context_refs",
        "evidence_refs",
        "scheduler_remains_orchestrator",
        "SpecialistLaboratoryConversation",
    ):
        assert token in source
    assert "SpecialistExchangeEnvelope" not in source
    assert "SpecialistLaboratoryConversation" in TRANSFER.read_text(encoding="utf-8")


def test_existing_liaison_and_final_artifact_surfaces_are_reused() -> None:
    liaison = LIAISON.read_text(encoding="utf-8")
    deliberation = DELIBERATION.read_text(encoding="utf-8")
    for token in (
        "SpecialistOutputFragment",
        "SpecialistLiaisonSynthesis",
        "FinalSynthesisPacket",
        "build_specialist_liaison_synthesis",
        "build_final_synthesis_packet",
    ):
        assert token in liaison
    for token in (
        "ServerOrientation",
        "SpecialistPreliminaryOpinion",
        "RefinedSpecialistDemand",
        "DeliberationRound",
        "FinalArtifactEnvelope",
    ):
        assert token in deliberation


def test_fake_provider_remains_fake_and_real_memory_boundary_is_preserved() -> None:
    fake = FAKE_PROVIDER.read_text(encoding="utf-8")
    memory = MEMORY.read_text(encoding="utf-8")
    for token in ("local_fake", "real_backend_used", "deterministic"):
        assert token in fake
    for token in (
        "OpenVINO",
        "Qdrant",
        "SQL",
        "dimension",
        "authorize_real_memory",
    ):
        assert token in memory


def test_current_roadmap_locks_the_product_final_chain() -> None:
    current = CURRENT.read_text(encoding="utf-8")
    report = REPORT.read_text(encoding="utf-8")
    for token in (
        "0287-r7-r5 — specialist exchange, synthesis and product-chain reuse audit",
        "laboratory:love-studies-local",
        "specialist:love-concept-and-affect-analyst",
        "specialist:love-relational-dynamics-analyst",
        "specialists primarily produce deep analyses",
        "0287-r7-r16 — recovery, installation and prototype closure",
        "no phase 0288",
        "code_rule_review: done",
        "live_path_status: audit",
    ):
        assert token in current or token in report


def test_audit_does_not_claim_runtime_or_remote_mutation() -> None:
    report = REPORT.read_text(encoding="utf-8")
    for token in (
        "runtime registration",
        "GitHub mutation",
        "ProjectV2 mutation",
        "INSTALLATION.md",
    ):
        assert token in report
