from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "src/context/native_love_laboratory_first_specialist_0287.py"
BINDING = ROOT / "src/context/native_love_laboratory_scheduler_binding_0287.py"
CURRENT = ROOT / "doc/README_CURRENT.md"


def test_native_love_provider_reuses_existing_architecture() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    for marker in (
        "SchedulerOwnedRuntimeComponentRegistration",
        "SchedulerOwnedRuntimeRegistry",
        "LaboratoryProvider",
        "LaboratoryVisitRequest",
        "LaboratoryVisitResult",
        "SpecialistTaskRequest",
        "LoveStudyRequest",
        "LOVE_CONCEPT_AFFECT_SPECIALIST_REF",
        "provider_kind != \"autodoc_native\"",
        "network-enabled visits are refused",
        "openvino_backend_reimplemented",
    ):
        assert marker in text

    for forbidden in (
        "class LaboratoryManager",
        "class RuntimeManager",
        "class Scheduler(",
        "qdrant_client",
        "torch",
        "transformers",
        "openvino.runtime.Core",
        "requests.",
    ):
        assert forbidden not in text


def test_first_specialist_is_content_dependent_not_scenario_driven() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    assert "stdlib_lexical_v1" in text
    assert "_CONCEPT_LEXICON" in text
    assert "_AFFECT_LEXICON" in text
    assert "_extract_sentences" in text
    assert "_lexicon_hits" in text
    assert "fake_scenario" not in text
    assert '"real_specialist_executed": self.real_specialist_executed' in text
    assert '"content_dependent_result": self.content_dependent_result' in text


def test_r10_does_not_claim_second_specialist_or_global_synthesis() -> None:
    text = SOURCE.read_text(encoding="utf-8")

    assert "r10 provider enables only the first love specialist" in text
    assert '"global_synthesis_created": False' in text
    assert "later_liaison_step" in text


def test_current_roadmap_moves_to_second_specialist_after_r10() -> None:
    text = CURRENT.read_text(encoding="utf-8")

    assert "0287-r7-r10" in text
    assert "laboratory:love-studies-local" in text
    assert "specialist:love-concept-and-affect-analyst" in text
    assert "0287-r7-r11" in text


def test_native_binding_uses_existing_scheduler_dispatcher_path() -> None:
    text = BINDING.read_text(encoding="utf-8")

    for marker in (
        "Scheduler.emit()",
        "PolicyEngine.decide()",
        "PriorityQueue",
        "Dispatcher",
        "LABORATORY_VISIT_REQUEST",
        "register_native_love_laboratory_visit_handler",
        "submit_native_love_laboratory_visit",
    ):
        assert marker in text

    for forbidden in (
        "Scheduler(",
        "PriorityQueue(",
        "EventBus(",
        "Registry(",
        "asyncio.create_task",
    ):
        assert forbidden not in text
