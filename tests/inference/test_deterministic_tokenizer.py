from __future__ import annotations

import pytest

from inference.simple_tokenizer import DeterministicTokenizer, register_deterministic_test_tokenizer
from inference.tokenizer_contract import TokenizationRequest, TokenizerConfig, TokenizerRegistry


def test_deterministic_tokenizer_is_stable_without_external_vocab() -> None:
    tokenizer = DeterministicTokenizer()
    config = TokenizerConfig(name=tokenizer.name)
    request = TokenizationRequest.from_text("Alpha beta Alpha")

    first = tokenizer.tokenize(request, config=config)
    second = tokenizer.tokenize(request, config=config)

    assert first.input_ids == second.input_ids
    assert first.attention_mask == ((1, 1, 1, 1, 1),)
    assert first.input_ids[0][0] == tokenizer.cls_token_id
    assert first.input_ids[0][-1] == tokenizer.sep_token_id
    assert first.input_ids[0][1] == first.input_ids[0][3]
    assert first.metadata["tokenizer_kind"] == "DeterministicTokenizer"


def test_deterministic_tokenizer_supports_padding_to_longest_batch() -> None:
    tokenizer = DeterministicTokenizer()
    config = TokenizerConfig(name=tokenizer.name, padding="longest")
    result = tokenizer.tokenize(TokenizationRequest(texts=("a", "a b c")), config=config)

    assert result.input_ids[0][-1] == config.pad_token_id
    assert result.attention_mask == ((1, 1, 1, 0, 0), (1, 1, 1, 1, 1))
    assert result.sequence_length == 5
    assert result.batch_size == 2


def test_deterministic_tokenizer_supports_max_length_padding_and_truncation() -> None:
    tokenizer = DeterministicTokenizer()
    config = TokenizerConfig(
        name=tokenizer.name,
        max_length=5,
        padding="max_length",
        truncation="longest_first",
    )

    result = tokenizer.tokenize(TokenizationRequest.from_text("one two three four five"), config=config)

    assert result.sequence_length == 5
    assert result.input_ids[0][0] == tokenizer.cls_token_id
    assert result.input_ids[0][-1] == tokenizer.sep_token_id
    assert result.attention_mask == ((1, 1, 1, 1, 1),)


def test_deterministic_tokenizer_emits_token_type_ids_for_pairs() -> None:
    tokenizer = DeterministicTokenizer()
    config = TokenizerConfig(name=tokenizer.name, padding="longest")
    result = tokenizer.tokenize(
        TokenizationRequest.from_text("query text", text_pair="document text"),
        config=config,
    )

    assert result.token_type_ids is not None
    assert result.token_type_ids[0].count(1) == 3
    assert result.attention_mask[0] == (1, 1, 1, 1, 1, 1, 1)


def test_deterministic_tokenizer_refuses_ambiguous_unpadded_batch() -> None:
    tokenizer = DeterministicTokenizer()
    config = TokenizerConfig(name=tokenizer.name)

    with pytest.raises(ValueError, match="rectangular batch"):
        tokenizer.tokenize(TokenizationRequest(texts=("a", "a b")), config=config)


def test_deterministic_tokenizer_validates_config_identity_and_truncation() -> None:
    tokenizer = DeterministicTokenizer()

    with pytest.raises(ValueError, match="does not match tokenizer"):
        tokenizer.tokenize(TokenizationRequest.from_text("hello"), config=TokenizerConfig(name="other"))

    with pytest.raises(ValueError, match="exceeds max_length"):
        tokenizer.tokenize(
            TokenizationRequest.from_text("one two three"),
            config=TokenizerConfig(name=tokenizer.name, max_length=3, truncation="none"),
        )

    with pytest.raises(ValueError, match="max_length"):
        tokenizer.tokenize(
            TokenizationRequest.from_text("hello"),
            config=TokenizerConfig(name=tokenizer.name, padding="max_length"),
        )


def test_register_deterministic_test_tokenizer_is_explicit() -> None:
    registry = TokenizerRegistry()
    tokenizer = register_deterministic_test_tokenizer(registry, name="test.local")

    assert tokenizer.name == "test.local"
    assert registry.select() is tokenizer
    assert registry.select("test.local") is tokenizer
