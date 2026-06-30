from __future__ import annotations

import pytest

from inference.e5_answer_prompt import E5AnswerPromptPolicy, build_e5_answer_prompt
from inference.e5_context_consumer import E5ConsumedContext, E5ConsumedContextItem


def _consumed() -> E5ConsumedContext:
    return E5ConsumedContext(
        query="OpenVINO local",
        prefixed_query="query: OpenVINO local",
        max_chars=200,
        used_chars=len("[1] doc/a.md:10-12\nOpenVINO E5 local search"),
        available_item_count=1,
        selected_items=(
            E5ConsumedContextItem(
                rank=1,
                id="a",
                score=0.91,
                source_path="doc/a.md",
                line_range="10-12",
                chunk_index=0,
                text="[1] doc/a.md:10-12\nOpenVINO E5 local search",
            ),
        ),
    )


def test_build_e5_answer_prompt_creates_deterministic_prompt() -> None:
    packet = build_e5_answer_prompt(_consumed())

    assert packet.query == "OpenVINO local"
    assert packet.selected_item_count == 1
    assert "[SYSTEM]" in packet.prompt_text
    assert "[QUESTION]\nOpenVINO local" in packet.prompt_text
    assert "[CONTEXT]\n[1] doc/a.md:10-12\nOpenVINO E5 local search" in packet.prompt_text
    assert packet.to_text() == packet.prompt_text


def test_build_e5_answer_prompt_json_is_stable() -> None:
    packet = build_e5_answer_prompt(
        _consumed(),
        E5AnswerPromptPolicy(system_instruction="S", answer_instruction="A", empty_context_notice="N"),
    )

    assert packet.to_json_dict() == {
        "query": "OpenVINO local",
        "prefixed_query": "query: OpenVINO local",
        "system_instruction": "S",
        "answer_instruction": "A",
        "selected_item_count": 1,
        "max_context_chars": 200,
        "used_context_chars": len("[1] doc/a.md:10-12\nOpenVINO E5 local search"),
        "context_text": "[1] doc/a.md:10-12\nOpenVINO E5 local search",
        "prompt_text": "[SYSTEM]\nS\n\n[QUESTION]\nOpenVINO local\n\n[CONTEXT]\n[1] doc/a.md:10-12\nOpenVINO E5 local search\n\n[INSTRUCTIONS]\nA",
    }


def test_build_e5_answer_prompt_inserts_empty_context_notice() -> None:
    consumed = E5ConsumedContext(
        query="OpenVINO local",
        prefixed_query="query: OpenVINO local",
        max_chars=20,
        used_chars=0,
        available_item_count=2,
        selected_items=(),
        skipped_item_count=2,
    )

    packet = build_e5_answer_prompt(
        consumed,
        E5AnswerPromptPolicy(system_instruction="S", answer_instruction="A", empty_context_notice="Pas de contexte"),
    )

    assert packet.selected_item_count == 0
    assert packet.context_text == "Pas de contexte"
    assert "[CONTEXT]\nPas de contexte" in packet.prompt_text


def test_e5_answer_prompt_policy_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="system_instruction"):
        E5AnswerPromptPolicy(system_instruction=" ")
    with pytest.raises(ValueError, match="answer_instruction"):
        E5AnswerPromptPolicy(answer_instruction=" ")
    with pytest.raises(ValueError, match="empty_context_notice"):
        E5AnswerPromptPolicy(empty_context_notice=" ")
