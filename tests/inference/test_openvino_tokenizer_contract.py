from __future__ import annotations

from dataclasses import dataclass

import pytest

from inference.tokenizer_contract import (
    TextTokenizer,
    TokenizationRequest,
    TokenizationResult,
    TokenizerConfig,
    TokenizerRegistry,
)


@dataclass(frozen=True)
class FakeTokenizer:
    name: str = "fake.tokens"

    def tokenize(
        self,
        request: TokenizationRequest,
        *,
        config: TokenizerConfig,
    ) -> TokenizationResult:
        del config
        return TokenizationResult(
            tokenizer_name=self.name,
            input_ids=tuple((101, len(text), 102) for text in request.texts),
            attention_mask=tuple((1, 1, 1) for _ in request.texts),
            metadata={"source_batch": request.batch_size},
        )


def test_tokenizer_config_is_stable_and_validates_values() -> None:
    config = TokenizerConfig.from_mapping(
        {
            "name": "local.bge.tokenizer",
            "max_length": "128",
            "padding": "max_length",
            "truncation": "longest_first",
            "pad_token_id": 0,
            "metadata": {"family": "bge"},
        }
    )

    assert config.name == "local.bge.tokenizer"
    assert config.max_length == 128
    assert config.padding == "max_length"
    assert config.truncation == "longest_first"
    assert config.metadata["family"] == "bge"

    with pytest.raises(TypeError):
        config.metadata["family"] = "mutated"  # type: ignore[index]

    with pytest.raises(ValueError, match="Unsupported tokenizer padding"):
        TokenizerConfig(name="bad", padding="dynamic")

    with pytest.raises(ValueError, match="Unsupported tokenizer truncation"):
        TokenizerConfig(name="bad", truncation="tail")

    with pytest.raises(ValueError, match="max_length"):
        TokenizerConfig(name="bad", max_length=0)


def test_tokenization_request_accepts_single_text_and_batch_pairs() -> None:
    single = TokenizationRequest.from_text("hello", text_pair="world", metadata={"kind": "pair"})
    batch = TokenizationRequest(texts=("a", "b"), text_pairs=("c", "d"))

    assert single.texts == ("hello",)
    assert single.text_pairs == ("world",)
    assert single.batch_size == 1
    assert single.metadata["kind"] == "pair"
    assert batch.batch_size == 2

    with pytest.raises(ValueError, match="same batch size"):
        TokenizationRequest(texts=("a", "b"), text_pairs=("c",))

    with pytest.raises(ValueError, match="non-empty"):
        TokenizationRequest(texts=("",))


def test_tokenization_result_projects_to_embedding_raw_inputs() -> None:
    result = TokenizationResult(
        tokenizer_name="fake.tokens",
        input_ids=((101, 42, 102),),
        attention_mask=((1, 1, 0),),
        token_type_ids=((0, 0, 0),),
        metadata={"source": "unit"},
    )

    raw = result.to_embedding_raw_inputs()

    assert result.batch_size == 1
    assert result.sequence_length == 3
    assert raw.input_ids == ((101, 42, 102),)
    assert raw.attention_mask == ((1, 1, 0),)
    assert raw.token_type_ids == ((0, 0, 0),)
    assert raw.metadata["tokenizer_name"] == "fake.tokens"
    assert raw.metadata["source"] == "unit"
    assert raw.metadata["tokenized_sequence_length"] == 3


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"input_ids": ((1, 2),), "attention_mask": ((1,),)}, "same shape"),
        ({"input_ids": ((1, 2), (3,)), "attention_mask": ((1, 1), (1, 0))}, "rectangular"),
        ({"input_ids": ((1, 2),), "attention_mask": ((1, 2),)}, "0 or 1"),
        ({"input_ids": ((1, -2),), "attention_mask": ((1, 1),)}, "non-negative"),
    ],
)
def test_tokenization_result_rejects_invalid_matrices(kwargs: dict[str, object], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        TokenizationResult(tokenizer_name="fake.tokens", **kwargs)


def test_tokenizer_registry_registers_and_selects_explicit_tokenizers() -> None:
    registry = TokenizerRegistry()
    fake = FakeTokenizer()
    other = FakeTokenizer(name="other.tokens")

    registry.register(fake)
    registry.register(other, make_default=True)

    assert registry.select("fake.tokens") is fake
    assert registry.select() is other
    assert registry.tokenizer_names() == ("fake.tokens", "other.tokens")
    assert registry.snapshot().default_name == "other.tokens"
    assert registry.snapshot().metadata["count"] == 2

    with pytest.raises(TypeError):
        registry.tokenizers["new"] = fake  # type: ignore[index]

    with pytest.raises(ValueError, match="already registered"):
        registry.register(fake)

    with pytest.raises(LookupError, match="missing"):
        registry.select("missing")


def test_tokenizer_protocol_can_be_used_by_embedding_flow() -> None:
    tokenizer: TextTokenizer = FakeTokenizer()
    request = TokenizationRequest(texts=("alpha", "beta"))
    config = TokenizerConfig(name="fake.tokens", padding="longest")

    result = tokenizer.tokenize(request, config=config)
    raw = result.to_embedding_raw_inputs()

    assert result.tokenizer_name == "fake.tokens"
    assert result.input_ids == ((101, 5, 102), (101, 4, 102))
    assert raw.batch_size == 2
    assert raw.sequence_length == 3
    assert raw.metadata["source_batch"] == 2
