from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/love_installed_runtime_factory_0287.py"
EXAMPLE = ROOT / "config/love_installed_runtime.example.ini"
CLOSED_LOOP = ROOT / "config/love_actions_closed_loop.example.ini"
REPORT = ROOT / "PHASE0287_R7_R15_R3_R1_INSTALLED_RUNTIME_FACTORY_COMPOSITION_REPORT.md"


def test_factory_reuses_runtime_contract_without_constructing_backends() -> None:
    text = SOURCE.read_text(encoding="utf-8")
    assert "ImportedActionsRuntimePorts" in text
    assert "ImportedActionsRealBackendAttestation" in text
    assert "validate_imported_actions_runtime_ports" in text
    for forbidden in (
        "Scheduler(",
        "QdrantClient(",
        "Core(",
        "compile_model(",
        "LaboratoryManager",
        "RuntimeManager",
        "new Scheduler",
    ):
        assert forbidden not in text


def test_factory_has_no_fake_or_dummy_fallback() -> None:
    source = SOURCE.read_text(encoding="utf-8")
    example = EXAMPLE.read_text(encoding="utf-8")
    assert "non-real marker" in source
    assert "factory =\n" in example
    assert "No dummy fallback" not in source
    assert "deterministic adapter" not in source


def test_live_closed_loop_selects_canonical_installed_factory() -> None:
    text = CLOSED_LOOP.read_text(encoding="utf-8")
    assert (
        "factory = context.love_installed_runtime_factory_0287:build_runtime"
        in text
    )
    assert "love_installed_runtime.ini" in text


def test_report_preserves_authorities_and_live_path_honesty() -> None:
    text = REPORT.read_text(encoding="utf-8")
    for marker in (
        "Scheduler reste l’unique autorité",
        "SQL reste l’autorité durable",
        "Qdrant reste une projection",
        "E5 reste verrouillé à 384 dimensions",
        "aucune preuve live n’est revendiquée",
    ):
        assert marker in text
