from __future__ import annotations

from inference.e5_profile import (
    MULTILINGUAL_E5_SMALL_PROFILE_NAME,
    MULTILINGUAL_E5_SMALL_TOKENIZER_NAME,
    MultilingualE5SmallLocalConfig,
)


def test_e5_small_local_config_describes_observed_openvino_model() -> None:
    config = MultilingualE5SmallLocalConfig(model_dir="/tmp/e5")

    profile = config.to_embedding_profile_config()
    tokenizer_config = config.to_tokenizer_config()
    adapter_config = config.to_transformers_tokenizer_adapter_config()

    assert profile.name == MULTILINGUAL_E5_SMALL_PROFILE_NAME
    assert profile.model_path == "/tmp/e5/openvino_model.xml"
    assert profile.input_names == ("input_ids", "attention_mask", "token_type_ids")
    assert profile.output_names == ("last_hidden_state",)
    assert profile.dimension == 384
    assert profile.pooling == "mean"
    assert profile.normalize is True
    assert profile.metadata["requires_token_type_ids"] is True
    assert tokenizer_config.name == MULTILINGUAL_E5_SMALL_TOKENIZER_NAME
    assert tokenizer_config.padding == "max_length"
    assert tokenizer_config.truncation == "longest_first"
    assert adapter_config.force_token_type_ids is True
