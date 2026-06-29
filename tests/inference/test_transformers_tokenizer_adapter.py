from __future__ import annotations

from inference.tokenizer_contract import TokenizationRequest, TokenizerConfig
from inference.transformers_tokenizer import TransformersAutoTokenizer


class FakeBatchTokenizer:
    def __call__(self, texts, **kwargs):
        assert kwargs["return_attention_mask"] is True
        assert kwargs["padding"] == "max_length"
        assert kwargs["truncation"] is True
        assert kwargs["max_length"] == 4
        return {
            "input_ids": [[101, 42, 43, 0] for _ in texts],
            "attention_mask": [[1, 1, 1, 0] for _ in texts],
        }


class FakeBatchTokenizerWithTokenTypes:
    def __call__(self, texts, **kwargs):
        return {
            "input_ids": [[101, 42, 0]],
            "attention_mask": [[1, 1, 0]],
            "token_type_ids": [[0, 0, 0]],
        }


def test_transformers_adapter_synthesizes_token_type_ids_when_missing() -> None:
    tokenizer = TransformersAutoTokenizer(
        name="fake-transformers",
        tokenizer=FakeBatchTokenizer(),
        force_token_type_ids=True,
    )

    result = tokenizer.tokenize(
        TokenizationRequest.from_text("query: bonjour"),
        config=TokenizerConfig(
            name="fake-transformers",
            max_length=4,
            padding="max_length",
            truncation="longest_first",
        ),
    )

    assert result.input_ids == ((101, 42, 43, 0),)
    assert result.attention_mask == ((1, 1, 1, 0),)
    assert result.token_type_ids == ((0, 0, 0, 0),)
    assert result.metadata["token_type_ids_synthesized"] is True


def test_transformers_adapter_preserves_token_type_ids_when_present() -> None:
    tokenizer = TransformersAutoTokenizer(
        name="fake-transformers",
        tokenizer=FakeBatchTokenizerWithTokenTypes(),
        force_token_type_ids=True,
    )

    result = tokenizer.tokenize(
        TokenizationRequest.from_text("query: bonjour"),
        config=TokenizerConfig(name="fake-transformers"),
    )

    assert result.token_type_ids == ((0, 0, 0),)
    assert result.metadata["token_type_ids_synthesized"] is False
