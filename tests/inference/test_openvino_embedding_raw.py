from __future__ import annotations

import math

import pytest

from inference.embedding_raw import (
    OpenVINOEmbeddingOutputAdapter,
    OpenVINOEmbeddingOutputConfig,
    OpenVINOEmbeddingRawInputs,
    OpenVINOEmbeddingVector,
)


def test_raw_inputs_project_to_openvino_inputs_and_request() -> None:
    raw = OpenVINOEmbeddingRawInputs(
        input_ids=((101, 42, 102),),
        attention_mask=((1, 1, 0),),
        token_type_ids=((0, 0, 0),),
        metadata={"source": "test"},
    )

    inputs = raw.to_openvino_inputs(("ids", "mask", "types"))
    request = raw.to_inference_request(
        model="openvino.embedding.local",
        prompt="ignored once tokenized",
        input_names=("ids", "mask", "types"),
        metadata={"trace": "raw"},
    )

    assert raw.batch_size == 1
    assert raw.sequence_length == 3
    assert inputs == {
        "ids": ((101, 42, 102),),
        "mask": ((1, 1, 0),),
        "types": ((0, 0, 0),),
    }
    assert request.model == "openvino.embedding.local"
    assert request.context["inputs"] == inputs
    assert request.metadata["embedding_raw_inputs"] is True
    assert request.metadata["embedding_batch_size"] == 1
    assert request.metadata["trace"] == "raw"

    with pytest.raises(TypeError):
        raw.metadata["source"] = "mutated"  # type: ignore[index]


def test_raw_inputs_from_mapping_accepts_json_like_values() -> None:
    raw = OpenVINOEmbeddingRawInputs.from_mapping(
        {
            "input_ids": [[1, 2, 3], [4, 5, 6]],
            "attention_mask": [[1, 1, 1], [1, 0, 0]],
            "metadata": {"family": "bge"},
        }
    )

    assert raw.input_ids == ((1, 2, 3), (4, 5, 6))
    assert raw.attention_mask == ((1, 1, 1), (1, 0, 0))
    assert raw.token_type_ids is None
    assert raw.metadata["family"] == "bge"


def test_raw_inputs_reject_invalid_shapes_and_values() -> None:
    with pytest.raises(ValueError, match="same shape"):
        OpenVINOEmbeddingRawInputs(
            input_ids=((1, 2),),
            attention_mask=((1,),),
        )

    with pytest.raises(ValueError, match="rectangular"):
        OpenVINOEmbeddingRawInputs(
            input_ids=((1, 2), (3,)),
            attention_mask=((1, 1), (1, 0)),
        )

    with pytest.raises(ValueError, match="0 or 1"):
        OpenVINOEmbeddingRawInputs(
            input_ids=((1, 2),),
            attention_mask=((1, 2),),
        )

    with pytest.raises(ValueError, match="non-negative"):
        OpenVINOEmbeddingRawInputs(
            input_ids=((1, -2),),
            attention_mask=((1, 1),),
        )

    with pytest.raises(ValueError, match="token_type_ids"):
        OpenVINOEmbeddingRawInputs(
            input_ids=((1, 2),),
            attention_mask=((1, 1),),
        ).to_openvino_inputs(("input_ids", "attention_mask", "token_type_ids"))


def test_output_adapter_extracts_model_level_vector_and_normalizes() -> None:
    raw = OpenVINOEmbeddingRawInputs(
        input_ids=((1, 2),),
        attention_mask=((1, 1),),
    )
    adapter = OpenVINOEmbeddingOutputAdapter(
        OpenVINOEmbeddingOutputConfig(output_names=("embedding",), pooling="model", normalize=True)
    )

    vector = adapter.extract({"embedding": [[3.0, 4.0]]}, raw)

    assert vector.normalized is True
    assert vector.pooling == "model"
    assert vector.dimension == 2
    assert vector.values == (0.6, 0.8)
    assert math.isclose(vector.l2_norm, 1.0)
    assert vector.metadata["batch_size"] == 1


def test_output_adapter_supports_cls_pooling_without_normalization() -> None:
    raw = OpenVINOEmbeddingRawInputs(
        input_ids=((1, 2, 3),),
        attention_mask=((1, 1, 0),),
    )
    adapter = OpenVINOEmbeddingOutputAdapter(
        OpenVINOEmbeddingOutputConfig(output_names=("last_hidden_state",), pooling="cls", normalize=False)
    )

    vector = adapter.extract(
        {"last_hidden_state": [[[10.0, 20.0], [30.0, 40.0], [50.0, 60.0]]]},
        raw,
    )

    assert vector.values == (10.0, 20.0)
    assert vector.normalized is False
    assert vector.pooling == "cls"


def test_output_adapter_supports_mean_pooling_with_attention_mask() -> None:
    raw = OpenVINOEmbeddingRawInputs(
        input_ids=((1, 2, 3),),
        attention_mask=((1, 1, 0),),
    )
    adapter = OpenVINOEmbeddingOutputAdapter(
        OpenVINOEmbeddingOutputConfig(output_names=("tokens",), pooling="mean", normalize=False)
    )

    vector = adapter.extract(
        {"tokens": [[[1.0, 3.0], [5.0, 7.0], [99.0, 99.0]]]},
        raw,
    )

    assert vector.values == (3.0, 5.0)
    assert vector.normalized is False


def test_output_adapter_accepts_single_unnamed_mapping_output() -> None:
    raw = OpenVINOEmbeddingRawInputs(
        input_ids=((1,),),
        attention_mask=((1,),),
    )
    adapter = OpenVINOEmbeddingOutputAdapter(OpenVINOEmbeddingOutputConfig(output_names=("missing",)))

    vector = adapter.extract({"some_openvino_output": [1.0, 0.0]}, raw)

    assert vector.values == (1.0, 0.0)


def test_output_adapter_rejects_ambiguous_or_invalid_outputs() -> None:
    raw = OpenVINOEmbeddingRawInputs(
        input_ids=((1, 2),),
        attention_mask=((0, 0),),
    )
    adapter = OpenVINOEmbeddingOutputAdapter(
        OpenVINOEmbeddingOutputConfig(output_names=("tokens",), pooling="mean")
    )

    with pytest.raises(KeyError, match="No embedding output"):
        adapter.extract({"a": [1.0], "b": [2.0]}, raw)

    with pytest.raises(ValueError, match="unmasked"):
        adapter.extract({"tokens": [[[1.0, 2.0], [3.0, 4.0]]]}, raw)

    with pytest.raises(ValueError, match="zero embedding"):
        OpenVINOEmbeddingOutputAdapter(
            OpenVINOEmbeddingOutputConfig(output_names=("embedding",), pooling="model")
        ).extract({"embedding": [0.0, 0.0]}, raw)


def test_embedding_vector_validates_contract() -> None:
    vector = OpenVINOEmbeddingVector(values=(1, 2.5), normalized=False, pooling="none")

    assert vector.values == (1.0, 2.5)
    assert vector.dimension == 2

    with pytest.raises(ValueError, match="must not be empty"):
        OpenVINOEmbeddingVector(values=(), normalized=False, pooling="none")

    with pytest.raises(ValueError, match="finite"):
        OpenVINOEmbeddingVector(values=(float("nan"),), normalized=False, pooling="none")
