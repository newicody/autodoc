from __future__ import annotations

from dataclasses import dataclass

from .e5_context_consumer import E5ConsumedContext

DEFAULT_E5_ANSWER_SYSTEM_INSTRUCTION = (
    "Tu es un composant de préparation de réponse. "
    "Tu dois utiliser uniquement le contexte fourni, signaler les limites du contexte "
    "et conserver les références de source quand elles sont présentes."
)

DEFAULT_E5_ANSWER_INSTRUCTION = (
    "Réponds à la question en utilisant le contexte. "
    "Si le contexte ne permet pas de répondre, indique clairement ce qui manque."
)


@dataclass(frozen=True, slots=True)
class E5AnswerPromptPolicy:
    """Politique explicite de construction d'un prompt depuis un contexte E5 consommé."""

    system_instruction: str = DEFAULT_E5_ANSWER_SYSTEM_INSTRUCTION
    answer_instruction: str = DEFAULT_E5_ANSWER_INSTRUCTION
    empty_context_notice: str = "Aucun contexte E5 sélectionné dans le budget."

    def __post_init__(self) -> None:
        if not self.system_instruction.strip():
            raise ValueError("system_instruction must not be empty")
        if not self.answer_instruction.strip():
            raise ValueError("answer_instruction must not be empty")
        if not self.empty_context_notice.strip():
            raise ValueError("empty_context_notice must not be empty")


@dataclass(frozen=True, slots=True)
class E5AnswerPromptPacket:
    """Paquet de prompt déterministe prêt pour un futur adaptateur d'inférence."""

    query: str
    prefixed_query: str
    system_instruction: str
    answer_instruction: str
    context_text: str
    selected_item_count: int
    max_context_chars: int
    used_context_chars: int

    def __post_init__(self) -> None:
        if not self.query.strip():
            raise ValueError("E5AnswerPromptPacket.query must not be empty")
        if not self.prefixed_query.startswith("query:"):
            raise ValueError("E5AnswerPromptPacket.prefixed_query must start with 'query:'")
        if not self.system_instruction.strip():
            raise ValueError("E5AnswerPromptPacket.system_instruction must not be empty")
        if not self.answer_instruction.strip():
            raise ValueError("E5AnswerPromptPacket.answer_instruction must not be empty")
        if self.selected_item_count < 0:
            raise ValueError("E5AnswerPromptPacket.selected_item_count must not be negative")
        if self.max_context_chars <= 0:
            raise ValueError("E5AnswerPromptPacket.max_context_chars must be positive")
        if self.used_context_chars < 0:
            raise ValueError("E5AnswerPromptPacket.used_context_chars must not be negative")
        if self.used_context_chars > self.max_context_chars:
            raise ValueError("E5AnswerPromptPacket.used_context_chars must not exceed max_context_chars")

    @property
    def prompt_text(self) -> str:
        """Prompt texte stable, sans appel modèle et sans effet de bord."""
        return "\n\n".join(
            (
                "[SYSTEM]\n" + self.system_instruction,
                "[QUESTION]\n" + self.query,
                "[CONTEXT]\n" + self.context_text,
                "[INSTRUCTIONS]\n" + self.answer_instruction,
            )
        )

    def to_json_dict(self) -> dict[str, object]:
        """Projection JSON stable."""
        return {
            "query": self.query,
            "prefixed_query": self.prefixed_query,
            "system_instruction": self.system_instruction,
            "answer_instruction": self.answer_instruction,
            "selected_item_count": self.selected_item_count,
            "max_context_chars": self.max_context_chars,
            "used_context_chars": self.used_context_chars,
            "context_text": self.context_text,
            "prompt_text": self.prompt_text,
        }

    def to_text(self) -> str:
        """Projection texte stable."""
        return self.prompt_text


def build_e5_answer_prompt(
    consumed: E5ConsumedContext,
    policy: E5AnswerPromptPolicy | None = None,
) -> E5AnswerPromptPacket:
    """Construit un paquet de prompt depuis un contexte E5 consommé."""
    effective = policy or E5AnswerPromptPolicy()
    context_text = consumed.context_text
    if not context_text:
        context_text = effective.empty_context_notice

    return E5AnswerPromptPacket(
        query=consumed.query,
        prefixed_query=consumed.prefixed_query,
        system_instruction=effective.system_instruction,
        answer_instruction=effective.answer_instruction,
        context_text=context_text,
        selected_item_count=consumed.selected_item_count,
        max_context_chars=consumed.max_chars,
        used_context_chars=consumed.used_chars,
    )
