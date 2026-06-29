from __future__ import annotations

import hashlib
import re
from collections.abc import Sequence
from dataclasses import dataclass

from .tokenizer_contract import (
    TokenizationRequest,
    TokenizationResult,
    TokenizerConfig,
    TokenizerRegistry,
)

_TOKEN_PATTERN = re.compile(r"\S+")


@dataclass(frozen=True, slots=True)
class DeterministicTokenizer:
    """Tokenizer de test déterministe, pure stdlib.

    Ce tokenizer n'est pas compatible avec un vrai modèle BGE/E5/MiniLM. Il sert
    à valider le pipeline texte -> tokens -> embedding sans dépendance externe,
    sans vocabulaire local et sans téléchargement. Les identifiants sont stables
    car dérivés de SHA-256, pas de ``hash()`` Python.
    """

    name: str = "test.deterministic"
    lowercase: bool = True
    vocab_seed: str = "missipy.phase3.6"
    cls_token_id: int = 101
    sep_token_id: int = 102
    hash_offset: int = 1_000
    hash_bucket_size: int = 100_000

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("DeterministicTokenizer.name must not be empty")
        if not self.vocab_seed:
            raise ValueError("DeterministicTokenizer.vocab_seed must not be empty")
        for field_name in ("cls_token_id", "sep_token_id", "hash_offset", "hash_bucket_size"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"DeterministicTokenizer.{field_name} must be an integer")
            if value < 0:
                raise ValueError(f"DeterministicTokenizer.{field_name} must be non-negative")
        if self.hash_bucket_size <= 0:
            raise ValueError("DeterministicTokenizer.hash_bucket_size must be positive")

    def tokenize(
        self,
        request: TokenizationRequest,
        *,
        config: TokenizerConfig,
    ) -> TokenizationResult:
        """Tokenise une demande texte avec un vocabulaire synthétique stable."""

        if config.name != self.name:
            raise ValueError(
                f"TokenizerConfig.name {config.name!r} does not match tokenizer {self.name!r}"
            )

        rows: list[tuple[int, ...]] = []
        token_types: list[tuple[int, ...]] = []
        for index, text in enumerate(request.texts):
            pair = None if request.text_pairs is None else request.text_pairs[index]
            first = self._token_ids(text)
            second = self._token_ids(pair) if pair is not None else ()
            first, second = _truncate_tokens(first, second, config)
            ids, types = self._build_sequence(first, second, has_pair=pair is not None, config=config)
            if not ids:
                raise ValueError("Tokenized sequence must not be empty")
            rows.append(ids)
            token_types.append(types)

        target_length = _target_length(rows, config)
        padded_ids: list[tuple[int, ...]] = []
        padded_masks: list[tuple[int, ...]] = []
        padded_types: list[tuple[int, ...]] = []
        for ids, types in zip(rows, token_types, strict=True):
            pad_count = target_length - len(ids)
            if pad_count < 0:
                raise ValueError("Tokenized sequence is longer than target_length")
            padded_ids.append(ids + (config.pad_token_id,) * pad_count)
            padded_masks.append((1,) * len(ids) + (0,) * pad_count)
            padded_types.append(types + (0,) * pad_count)

        return TokenizationResult(
            tokenizer_name=self.name,
            input_ids=tuple(padded_ids),
            attention_mask=tuple(padded_masks),
            token_type_ids=tuple(padded_types),
            metadata={
                "tokenizer_kind": type(self).__name__,
                "padding": config.padding,
                "truncation": config.truncation,
                "max_length": config.max_length,
            },
        )

    def _token_ids(self, text: str | None) -> tuple[int, ...]:
        if text is None:
            return ()
        normalized = text.lower() if self.lowercase else text
        return tuple(self._stable_token_id(token) for token in _TOKEN_PATTERN.findall(normalized))

    def _stable_token_id(self, token: str) -> int:
        digest = hashlib.sha256(f"{self.vocab_seed}:{token}".encode("utf-8")).digest()
        value = int.from_bytes(digest[:8], "big") % self.hash_bucket_size
        return self.hash_offset + value

    def _build_sequence(
        self,
        first: tuple[int, ...],
        second: tuple[int, ...],
        *,
        has_pair: bool,
        config: TokenizerConfig,
    ) -> tuple[tuple[int, ...], tuple[int, ...]]:
        if not config.add_special_tokens:
            ids = first + second
            types = (0,) * len(first) + (1,) * len(second)
            return ids, types

        if has_pair:
            ids = (self.cls_token_id,) + first + (self.sep_token_id,) + second + (self.sep_token_id,)
            types = (0,) * (len(first) + 2) + (1,) * (len(second) + 1)
            return ids, types

        ids = (self.cls_token_id,) + first + (self.sep_token_id,)
        return ids, (0,) * len(ids)


def register_deterministic_test_tokenizer(
    registry: TokenizerRegistry,
    *,
    name: str = "test.deterministic",
    make_default: bool = True,
) -> DeterministicTokenizer:
    """Enregistre le tokenizer déterministe de test dans un registre explicite."""

    tokenizer = DeterministicTokenizer(name=name)
    registry.register(tokenizer, make_default=make_default)
    return tokenizer


def _truncate_tokens(
    first: tuple[int, ...],
    second: tuple[int, ...],
    config: TokenizerConfig,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    if config.max_length is None:
        return first, second

    reserve = _special_token_reserve(has_pair=bool(second), add_special_tokens=config.add_special_tokens)
    budget = config.max_length - reserve
    if budget < 0:
        raise ValueError("TokenizerConfig.max_length is too small for special tokens")

    if len(first) + len(second) <= budget:
        return first, second

    if config.truncation == "none":
        raise ValueError("Tokenized sequence exceeds max_length and truncation is none")

    if config.truncation == "only_first":
        remaining_for_first = budget - len(second)
        if remaining_for_first < 0:
            raise ValueError("Cannot satisfy max_length with truncation='only_first'")
        return first[:remaining_for_first], second

    if config.truncation == "longest_first":
        mutable_first = list(first)
        mutable_second = list(second)
        while len(mutable_first) + len(mutable_second) > budget:
            if len(mutable_second) > len(mutable_first):
                mutable_second.pop()
            elif mutable_first:
                mutable_first.pop()
            elif mutable_second:
                mutable_second.pop()
            else:
                break
        return tuple(mutable_first), tuple(mutable_second)

    raise ValueError(f"Unsupported truncation mode {config.truncation!r}")


def _target_length(rows: Sequence[tuple[int, ...]], config: TokenizerConfig) -> int:
    lengths = tuple(len(row) for row in rows)
    if config.padding == "max_length":
        if config.max_length is None:
            raise ValueError("padding='max_length' requires TokenizerConfig.max_length")
        return config.max_length
    if config.padding == "longest":
        return max(lengths)
    if len(set(lengths)) != 1:
        raise ValueError("padding='none' cannot build a rectangular batch with variable lengths")
    return lengths[0]


def _special_token_reserve(*, has_pair: bool, add_special_tokens: bool) -> int:
    if not add_special_tokens:
        return 0
    return 3 if has_pair else 2
