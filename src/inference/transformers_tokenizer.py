from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .tokenizer_contract import (
    TokenizationRequest,
    TokenizationResult,
    TokenizerConfig,
)


def _empty_mapping() -> Mapping[str, Any]:
    return MappingProxyType({})


@dataclass(frozen=True, slots=True)
class TransformersTokenizerAdapterConfig:
    """Configuration d'un tokenizer Transformers chargé localement.

    Cette configuration ne télécharge rien. Elle décrit uniquement le dossier
    local à passer à ``AutoTokenizer.from_pretrained`` quand l'utilisateur a déjà
    préparé le modèle et son tokenizer sur disque.
    """

    model_dir: str
    name: str = "transformers.local"
    force_token_type_ids: bool = True
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        if not self.model_dir:
            raise ValueError("TransformersTokenizerAdapterConfig.model_dir must not be empty")
        if not self.name:
            raise ValueError("TransformersTokenizerAdapterConfig.name must not be empty")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


class TransformersAutoTokenizer:
    """Adapter optionnel vers un tokenizer Hugging Face Transformers.

    Le module n'importe pas ``transformers`` au chargement. L'import reste isolé
    dans ``from_pretrained`` pour ne pas rendre la dépendance obligatoire aux
    tests et aux environnements qui n'exécutent pas de modèle réel.
    """

    def __init__(
        self,
        *,
        name: str,
        tokenizer: Any,
        force_token_type_ids: bool = True,
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        if not name:
            raise ValueError("TransformersAutoTokenizer.name must not be empty")
        self.name = name
        self._tokenizer = tokenizer
        self._force_token_type_ids = force_token_type_ids
        self._metadata = MappingProxyType(dict(metadata or {}))

    @classmethod
    def from_pretrained(
        cls,
        config: TransformersTokenizerAdapterConfig,
        **kwargs: Any,
    ) -> TransformersAutoTokenizer:
        """Charge un tokenizer local depuis un dossier déjà préparé.

        Aucun fallback réseau n'est ajouté ici : le chemin doit être explicite et
        le chargement reste sous le contrôle de l'appelant.
        """

        try:
            from transformers import AutoTokenizer
        except ModuleNotFoundError as exc:  # pragma: no cover - dépend de l'env local.
            raise RuntimeError(
                "transformers is not installed; install it before using "
                "TransformersAutoTokenizer.from_pretrained()."
            ) from exc

        tokenizer = AutoTokenizer.from_pretrained(Path(config.model_dir), **kwargs)
        return cls(
            name=config.name,
            tokenizer=tokenizer,
            force_token_type_ids=config.force_token_type_ids,
            metadata=config.metadata,
        )

    @property
    def metadata(self) -> Mapping[str, Any]:
        """Métadonnées stables de l'adapter."""
        return self._metadata

    def tokenize(
        self,
        request: TokenizationRequest,
        *,
        config: TokenizerConfig,
    ) -> TokenizationResult:
        """Tokenise une demande en matrices Python stables.

        Si le tokenizer ne renvoie pas ``token_type_ids`` alors que le modèle
        OpenVINO local en a besoin, l'adapter peut créer une matrice de zéros de
        même forme que ``input_ids``. C'est le cas observé avec
        ``multilingual-e5-small`` exporté OpenVINO.
        """

        encoded = self._tokenizer(
            list(request.texts),
            text_pair=list(request.text_pairs) if request.text_pairs is not None else None,
            padding=_hf_padding(config.padding),
            truncation=_hf_truncation(config.truncation),
            max_length=config.max_length,
            add_special_tokens=config.add_special_tokens,
            return_attention_mask=True,
        )

        input_ids = _to_int_matrix(encoded["input_ids"], field_name="input_ids")
        attention_mask = _to_int_matrix(encoded["attention_mask"], field_name="attention_mask")
        token_type_ids_value = encoded.get("token_type_ids")
        token_type_ids = (
            _to_int_matrix(token_type_ids_value, field_name="token_type_ids")
            if token_type_ids_value is not None
            else None
        )

        if token_type_ids is None and self._force_token_type_ids:
            token_type_ids = tuple(tuple(0 for _ in row) for row in input_ids)

        return TokenizationResult(
            tokenizer_name=self.name,
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            metadata=MappingProxyType(
                {
                    **dict(config.metadata),
                    **dict(request.metadata),
                    **dict(self._metadata),
                    "adapter": type(self).__name__,
                    "force_token_type_ids": self._force_token_type_ids,
                    "token_type_ids_synthesized": token_type_ids_value is None
                    and token_type_ids is not None,
                }
            ),
        )


def _hf_padding(value: str) -> bool | str:
    if value == "none":
        return False
    if value == "longest":
        return True
    if value == "max_length":
        return "max_length"
    raise ValueError(f"Unsupported tokenizer padding {value!r}")


def _hf_truncation(value: str) -> bool | str:
    if value == "none":
        return False
    if value == "longest_first":
        return True
    if value == "only_first":
        return "only_first"
    raise ValueError(f"Unsupported tokenizer truncation {value!r}")


def _to_int_matrix(value: Any, *, field_name: str) -> tuple[tuple[int, ...], ...]:
    if hasattr(value, "tolist"):
        value = value.tolist()
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise TypeError(f"{field_name} must be a 2D sequence of integers")

    rows: list[tuple[int, ...]] = []
    for row in value:
        if hasattr(row, "tolist"):
            row = row.tolist()
        if isinstance(row, str) or not isinstance(row, Sequence):
            raise TypeError(f"{field_name} must be a 2D sequence of integers")
        converted = tuple(_int_value(item, field_name=field_name) for item in row)
        if not converted:
            raise ValueError(f"{field_name} rows must not be empty")
        rows.append(converted)

    if not rows:
        raise ValueError(f"{field_name} must not be empty")
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError(f"{field_name} must be rectangular")
    return tuple(rows)


def _int_value(value: object, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must contain integers")
    return value
