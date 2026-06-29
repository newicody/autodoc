from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Protocol

from .embedding_raw import OpenVINOEmbeddingRawInputs


SUPPORTED_TOKENIZER_PADDING = frozenset({"none", "longest", "max_length"})
SUPPORTED_TOKENIZER_TRUNCATION = frozenset({"none", "longest_first", "only_first"})


def _empty_mapping() -> Mapping[str, Any]:
    return MappingProxyType({})


@dataclass(frozen=True, slots=True)
class TokenizerConfig:
    """Configuration stable d'un tokenizer injectable.

    Cette structure ne charge aucun vocabulaire et ne dépend d'aucune librairie
    externe. Elle décrit seulement le contrat attendu par un tokenizer concret
    futur : Hugging Face, SentencePiece, tokenizer maison ou wrapper OpenVINO.
    """

    name: str
    max_length: int | None = None
    padding: str = "none"
    truncation: str = "none"
    add_special_tokens: bool = True
    pad_token_id: int = 0
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("TokenizerConfig.name must not be empty")
        if self.max_length is not None and self.max_length <= 0:
            raise ValueError("TokenizerConfig.max_length must be positive when set")
        if self.padding not in SUPPORTED_TOKENIZER_PADDING:
            allowed = ", ".join(sorted(SUPPORTED_TOKENIZER_PADDING))
            raise ValueError(f"Unsupported tokenizer padding {self.padding!r}. Allowed: {allowed}")
        if self.truncation not in SUPPORTED_TOKENIZER_TRUNCATION:
            allowed = ", ".join(sorted(SUPPORTED_TOKENIZER_TRUNCATION))
            raise ValueError(
                f"Unsupported tokenizer truncation {self.truncation!r}. Allowed: {allowed}"
            )
        if isinstance(self.pad_token_id, bool) or not isinstance(self.pad_token_id, int):
            raise TypeError("TokenizerConfig.pad_token_id must be an integer")
        if self.pad_token_id < 0:
            raise ValueError("TokenizerConfig.pad_token_id must be non-negative")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @classmethod
    def from_mapping(cls, config: Mapping[str, Any]) -> TokenizerConfig:
        """Construit une configuration depuis un mapping JSON-like."""

        return cls(
            name=str(config.get("name", "")),
            max_length=_optional_int(config.get("max_length")),
            padding=str(config.get("padding", "none")),
            truncation=str(config.get("truncation", "none")),
            add_special_tokens=bool(config.get("add_special_tokens", True)),
            pad_token_id=_required_int(config.get("pad_token_id", 0), field_name="pad_token_id"),
            metadata=_mapping_value(config.get("metadata", MappingProxyType({}))),
        )


@dataclass(frozen=True, slots=True)
class TokenizationRequest:
    """Demande de tokenization indépendante de tout moteur concret."""

    texts: tuple[str, ...]
    text_pairs: tuple[str, ...] | None = None
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        texts = _to_text_tuple(self.texts, field_name="texts")
        text_pairs = (
            _to_text_tuple(self.text_pairs, field_name="text_pairs")
            if self.text_pairs is not None
            else None
        )
        if text_pairs is not None and len(text_pairs) != len(texts):
            raise ValueError("TokenizationRequest.text_pairs must have the same batch size as texts")
        object.__setattr__(self, "texts", texts)
        object.__setattr__(self, "text_pairs", text_pairs)
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @classmethod
    def from_text(
        cls,
        text: str,
        *,
        text_pair: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> TokenizationRequest:
        """Construit une demande mono-texte."""

        return cls(
            texts=(text,),
            text_pairs=(text_pair,) if text_pair is not None else None,
            metadata=metadata or MappingProxyType({}),
        )

    @property
    def batch_size(self) -> int:
        """Nombre de textes à tokenizer."""

        return len(self.texts)


@dataclass(frozen=True, slots=True)
class TokenizationResult:
    """Résultat tokenisé stable, sans dépendance au tokenizer concret."""

    tokenizer_name: str
    input_ids: tuple[tuple[int, ...], ...]
    attention_mask: tuple[tuple[int, ...], ...]
    token_type_ids: tuple[tuple[int, ...], ...] | None = None
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        if not self.tokenizer_name:
            raise ValueError("TokenizationResult.tokenizer_name must not be empty")
        input_ids = _to_int_matrix(self.input_ids, field_name="input_ids")
        attention_mask = _to_int_matrix(self.attention_mask, field_name="attention_mask")
        token_type_ids = (
            _to_int_matrix(self.token_type_ids, field_name="token_type_ids")
            if self.token_type_ids is not None
            else None
        )
        _assert_same_shape(input_ids, attention_mask, "input_ids", "attention_mask")
        if token_type_ids is not None:
            _assert_same_shape(input_ids, token_type_ids, "input_ids", "token_type_ids")
        if any(value not in (0, 1) for row in attention_mask for value in row):
            raise ValueError("attention_mask must contain only 0 or 1 values")
        if any(value < 0 for row in input_ids for value in row):
            raise ValueError("input_ids must contain non-negative integers")

        object.__setattr__(self, "input_ids", input_ids)
        object.__setattr__(self, "attention_mask", attention_mask)
        object.__setattr__(self, "token_type_ids", token_type_ids)
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def batch_size(self) -> int:
        """Nombre de séquences tokenisées."""

        return len(self.input_ids)

    @property
    def sequence_length(self) -> int:
        """Longueur fixe des séquences tokenisées."""

        return len(self.input_ids[0])

    def to_embedding_raw_inputs(self) -> OpenVINOEmbeddingRawInputs:
        """Projette le résultat vers le contrat embedding raw Phase 3.3."""

        metadata = {
            **dict(self.metadata),
            "tokenizer_name": self.tokenizer_name,
            "tokenized_batch_size": self.batch_size,
            "tokenized_sequence_length": self.sequence_length,
        }
        return OpenVINOEmbeddingRawInputs(
            input_ids=self.input_ids,
            attention_mask=self.attention_mask,
            token_type_ids=self.token_type_ids,
            metadata=MappingProxyType(metadata),
        )


class TextTokenizer(Protocol):
    """Interface minimale d'un tokenizer texte injectable."""

    name: str

    def tokenize(
        self,
        request: TokenizationRequest,
        *,
        config: TokenizerConfig,
    ) -> TokenizationResult:
        """Transforme du texte en matrices de tokens stables."""
        ...


@dataclass(frozen=True, slots=True)
class TokenizerRegistrySnapshot:
    """Vue immuable des tokenizers connus."""

    tokenizer_names: tuple[str, ...]
    default_name: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        object.__setattr__(self, "tokenizer_names", tuple(sorted(self.tokenizer_names)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


class TokenizerRegistry:
    """Registre explicite de tokenizers disponibles.

    Le registre ne construit pas les tokenizers et ne choisit pas de modèle. Il
    contient seulement les instances injectées par la configuration de lancement
    ou par une phase future spécialisée.
    """

    def __init__(self) -> None:
        self._tokenizers: dict[str, TextTokenizer] = {}
        self._default_name: str | None = None

    @property
    def tokenizers(self) -> Mapping[str, TextTokenizer]:
        """Vue immuable des tokenizers enregistrés."""

        return MappingProxyType(self._tokenizers)

    def register(self, tokenizer: TextTokenizer, *, make_default: bool = False) -> None:
        """Enregistre un tokenizer sans fallback implicite."""

        if not tokenizer.name:
            raise ValueError("Tokenizer name must not be empty")
        if tokenizer.name in self._tokenizers:
            raise ValueError(f"Tokenizer {tokenizer.name!r} is already registered")
        self._tokenizers[tokenizer.name] = tokenizer
        if make_default or self._default_name is None:
            self._default_name = tokenizer.name

    def select(self, name: str | None = None) -> TextTokenizer:
        """Retourne un tokenizer explicitement nommé ou le défaut enregistré."""

        selected_name = name or self._default_name
        if selected_name is None:
            raise LookupError("No tokenizer registered")
        tokenizer = self._tokenizers.get(selected_name)
        if tokenizer is None:
            available = ", ".join(self.tokenizer_names()) or "none"
            raise LookupError(f"No tokenizer {selected_name!r}. Available tokenizers: {available}")
        return tokenizer

    def tokenizer_names(self) -> tuple[str, ...]:
        """Noms triés des tokenizers connus."""

        return tuple(sorted(self._tokenizers))

    def snapshot(self) -> TokenizerRegistrySnapshot:
        """Construit une vue immuable du registre."""

        return TokenizerRegistrySnapshot(
            tokenizer_names=self.tokenizer_names(),
            default_name=self._default_name,
            metadata=MappingProxyType({"count": len(self._tokenizers)}),
        )


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    return _required_int(value, field_name="max_length")


def _required_int(value: object, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int | str):
        raise TypeError(f"{field_name} must be an integer")
    if isinstance(value, str):
        if not value:
            raise ValueError(f"{field_name} must not be empty")
        return int(value)
    return value


def _mapping_value(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    raise TypeError("metadata must be a mapping")


def _to_text_tuple(value: object, *, field_name: str) -> tuple[str, ...]:
    if isinstance(value, str):
        values = (value,)
    elif isinstance(value, Sequence):
        values = tuple(value)
    else:
        raise TypeError(f"{field_name} must be a string or a sequence of strings")
    if not values:
        raise ValueError(f"{field_name} must not be empty")
    if not all(isinstance(item, str) and item for item in values):
        raise ValueError(f"{field_name} must contain only non-empty strings")
    return values


def _to_int_matrix(value: object, *, field_name: str) -> tuple[tuple[int, ...], ...]:
    if value is None or isinstance(value, str) or not isinstance(value, Sequence):
        raise TypeError(f"{field_name} must be a 2D sequence of integers")

    rows: list[tuple[int, ...]] = []
    for row in value:
        if isinstance(row, str) or not isinstance(row, Sequence):
            raise TypeError(f"{field_name} must be a 2D sequence of integers")
        converted = tuple(_matrix_int(item, field_name=field_name) for item in row)
        if not converted:
            raise ValueError(f"{field_name} rows must not be empty")
        rows.append(converted)

    if not rows:
        raise ValueError(f"{field_name} must not be empty")
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise ValueError(f"{field_name} must be rectangular")
    return tuple(rows)


def _matrix_int(value: object, *, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must contain integers")
    return value


def _assert_same_shape(
    left: tuple[tuple[int, ...], ...],
    right: tuple[tuple[int, ...], ...],
    left_name: str,
    right_name: str,
) -> None:
    if len(left) != len(right) or any(len(a) != len(b) for a, b in zip(left, right, strict=True)):
        raise ValueError(f"{left_name} and {right_name} must have the same shape")
