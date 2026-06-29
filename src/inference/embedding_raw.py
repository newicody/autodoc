from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from contracts.inference import InferenceRequest

from .embedding_profile import (
    DEFAULT_EMBEDDING_INPUT_NAMES,
    DEFAULT_EMBEDDING_OUTPUT_NAMES,
    SUPPORTED_EMBEDDING_POOLING,
)


def _empty_mapping() -> Mapping[str, Any]:
    return MappingProxyType({})


@dataclass(frozen=True, slots=True)
class OpenVINOEmbeddingRawInputs:
    """Entrées tokenisées déjà prêtes pour un modèle embedding OpenVINO.

    Cette structure ne tokenise pas le texte. Elle transporte uniquement des
    tenseurs Python simples, déterministes et testables, destinés à être placés
    dans ``InferenceRequest.context['inputs']`` avant passage au runtime brut.
    """

    input_ids: tuple[tuple[int, ...], ...]
    attention_mask: tuple[tuple[int, ...], ...]
    token_type_ids: tuple[tuple[int, ...], ...] | None = None
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
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
        """Nombre de séquences dans le batch."""

        return len(self.input_ids)

    @property
    def sequence_length(self) -> int:
        """Longueur de séquence fixe du batch."""

        return len(self.input_ids[0])

    @classmethod
    def from_mapping(cls, mapping: Mapping[str, Any]) -> OpenVINOEmbeddingRawInputs:
        """Construit les entrées depuis un mapping JSON-like explicite."""

        return cls(
            input_ids=mapping.get("input_ids", ()),
            attention_mask=mapping.get("attention_mask", ()),
            token_type_ids=mapping.get("token_type_ids"),
            metadata=_mapping_value(mapping.get("metadata", MappingProxyType({}))),
        )

    def to_openvino_inputs(
        self,
        input_names: Sequence[str] = DEFAULT_EMBEDDING_INPUT_NAMES,
    ) -> Mapping[str, tuple[tuple[int, ...], ...]]:
        """Projette les tenseurs vers les noms d'entrées OpenVINO du profil.

        La convention reste volontairement simple : le premier nom reçoit
        ``input_ids``, le second ``attention_mask`` et le troisième optionnel
        ``token_type_ids``. Aucun tableau NumPy n'est créé ici.
        """

        names = _to_name_tuple(input_names, field_name="input_names")
        if len(names) < 2:
            raise ValueError("embedding input_names must contain at least input_ids and attention_mask")
        if len(names) > 2 and self.token_type_ids is None:
            raise ValueError("token_type_ids input requested but token_type_ids is not provided")

        values: dict[str, tuple[tuple[int, ...], ...]] = {
            names[0]: self.input_ids,
            names[1]: self.attention_mask,
        }
        if len(names) > 2:
            assert self.token_type_ids is not None
            values[names[2]] = self.token_type_ids
        return MappingProxyType(values)

    def to_inference_request(
        self,
        *,
        model: str,
        prompt: str = "",
        input_names: Sequence[str] = DEFAULT_EMBEDDING_INPUT_NAMES,
        metadata: Mapping[str, Any] | None = None,
    ) -> InferenceRequest:
        """Construit une InferenceRequest raw-input pour OpenVINO."""

        request_metadata = dict(metadata or {})
        request_metadata.update(
            {
                "embedding_batch_size": self.batch_size,
                "embedding_sequence_length": self.sequence_length,
                "embedding_raw_inputs": True,
            }
        )
        return InferenceRequest(
            prompt=prompt,
            model=model,
            context=MappingProxyType({"inputs": self.to_openvino_inputs(input_names)}),
            metadata=MappingProxyType(request_metadata),
        )


@dataclass(frozen=True, slots=True)
class OpenVINOEmbeddingVector:
    """Vecteur embedding stable, sans dépendance NumPy."""

    values: tuple[float, ...]
    normalized: bool
    pooling: str
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        values = tuple(float(value) for value in self.values)
        if not values:
            raise ValueError("OpenVINOEmbeddingVector.values must not be empty")
        if not all(math.isfinite(value) for value in values):
            raise ValueError("OpenVINOEmbeddingVector.values must contain only finite floats")
        if self.pooling not in SUPPORTED_EMBEDDING_POOLING:
            allowed = ", ".join(sorted(SUPPORTED_EMBEDDING_POOLING))
            raise ValueError(f"Unsupported embedding pooling {self.pooling!r}. Allowed: {allowed}")

        object.__setattr__(self, "values", values)
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def dimension(self) -> int:
        """Dimension du vecteur."""

        return len(self.values)

    @property
    def l2_norm(self) -> float:
        """Norme L2 du vecteur."""

        return math.sqrt(sum(value * value for value in self.values))


@dataclass(frozen=True, slots=True)
class OpenVINOEmbeddingOutputConfig:
    """Configuration de post-traitement d'une sortie embedding brute."""

    output_names: tuple[str, ...] = DEFAULT_EMBEDDING_OUTPUT_NAMES
    pooling: str = "model"
    normalize: bool = True

    def __post_init__(self) -> None:
        output_names = _to_name_tuple(self.output_names, field_name="output_names")
        if not output_names:
            raise ValueError("OpenVINOEmbeddingOutputConfig.output_names must not be empty")
        if self.pooling not in SUPPORTED_EMBEDDING_POOLING:
            allowed = ", ".join(sorted(SUPPORTED_EMBEDDING_POOLING))
            raise ValueError(f"Unsupported embedding pooling {self.pooling!r}. Allowed: {allowed}")

        object.__setattr__(self, "output_names", output_names)


class OpenVINOEmbeddingOutputAdapter:
    """Transforme une sortie OpenVINO brute en vecteur embedding stable.

    L'adapter accepte des listes, tuples ou objets exposant ``tolist()``. Il ne
    connaît pas OpenVINO directement et reste donc testable sans runtime réel.
    """

    def __init__(self, config: OpenVINOEmbeddingOutputConfig) -> None:
        self._config = config

    @property
    def config(self) -> OpenVINOEmbeddingOutputConfig:
        """Configuration immuable de post-traitement."""

        return self._config

    def extract(
        self,
        raw_outputs: Any,
        inputs: OpenVINOEmbeddingRawInputs,
    ) -> OpenVINOEmbeddingVector:
        """Extrait puis post-traite le premier vecteur du batch."""

        selected = _select_output(raw_outputs, self._config.output_names)
        nested = _to_python_nested(selected)
        pooled = _pool_first_batch(
            nested,
            inputs.attention_mask[0],
            pooling=self._config.pooling,
        )
        values = _normalize(pooled) if self._config.normalize else tuple(pooled)
        return OpenVINOEmbeddingVector(
            values=values,
            normalized=self._config.normalize,
            pooling=self._config.pooling,
            metadata=MappingProxyType(
                {
                    "batch_size": inputs.batch_size,
                    "sequence_length": inputs.sequence_length,
                    "source_output_names": self._config.output_names,
                }
            ),
        )


def _to_int_matrix(value: object, *, field_name: str) -> tuple[tuple[int, ...], ...]:
    if value is None or isinstance(value, str) or not isinstance(value, Sequence):
        raise TypeError(f"{field_name} must be a 2D sequence of integers")

    rows: list[tuple[int, ...]] = []
    for row in value:
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


def _assert_same_shape(
    left: tuple[tuple[int, ...], ...],
    right: tuple[tuple[int, ...], ...],
    left_name: str,
    right_name: str,
) -> None:
    if len(left) != len(right) or any(len(a) != len(b) for a, b in zip(left, right, strict=True)):
        raise ValueError(f"{left_name} and {right_name} must have the same shape")


def _to_name_tuple(value: Sequence[str], *, field_name: str) -> tuple[str, ...]:
    if isinstance(value, str):
        names = (value,)
    else:
        names = tuple(value)
    if not all(isinstance(name, str) and name for name in names):
        raise ValueError(f"{field_name} must contain only non-empty strings")
    return names


def _mapping_value(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    raise TypeError("metadata must be a mapping")


def _select_output(raw_outputs: Any, output_names: tuple[str, ...]) -> Any:
    if not isinstance(raw_outputs, Mapping):
        return raw_outputs

    for name in output_names:
        if name in raw_outputs:
            return raw_outputs[name]

    if len(raw_outputs) == 1:
        return next(iter(raw_outputs.values()))

    available = ", ".join(str(key) for key in raw_outputs)
    expected = ", ".join(output_names)
    raise KeyError(f"No embedding output found. Expected one of: {expected}. Available: {available}")


def _to_python_nested(value: Any) -> Any:
    if hasattr(value, "tolist"):
        return value.tolist()
    return value


def _pool_first_batch(value: Any, attention_mask: tuple[int, ...], *, pooling: str) -> tuple[float, ...]:
    if pooling in {"model", "none"}:
        return _first_model_vector(value)
    if pooling == "cls":
        token_embeddings = _first_token_matrix(value)
        return _float_vector(token_embeddings[0], field_name="cls vector")
    if pooling == "mean":
        token_embeddings = _first_token_matrix(value)
        return _mean_pool(token_embeddings, attention_mask)
    raise ValueError(f"Unsupported embedding pooling {pooling!r}")


def _first_model_vector(value: Any) -> tuple[float, ...]:
    if isinstance(value, Sequence) and not isinstance(value, str):
        if _is_number_sequence(value):
            return _float_vector(value, field_name="embedding vector")
        if value and isinstance(value[0], Sequence) and not isinstance(value[0], str):
            first = value[0]
            if _is_number_sequence(first):
                return _float_vector(first, field_name="embedding batch vector")
    raise TypeError("model/none pooling expects a vector or a batch of vectors")


def _first_token_matrix(value: Any) -> tuple[tuple[float, ...], ...]:
    if not isinstance(value, Sequence) or isinstance(value, str) or not value:
        raise TypeError("token pooling expects a batch of token embeddings")
    first_batch = value[0]
    if not isinstance(first_batch, Sequence) or isinstance(first_batch, str) or not first_batch:
        raise TypeError("token pooling expects a non-empty token matrix")

    rows: list[tuple[float, ...]] = []
    width: int | None = None
    for row in first_batch:
        vector = _float_vector(row, field_name="token embedding")
        if width is None:
            width = len(vector)
        elif len(vector) != width:
            raise ValueError("token embeddings must be rectangular")
        rows.append(vector)
    return tuple(rows)


def _mean_pool(
    token_embeddings: tuple[tuple[float, ...], ...],
    attention_mask: tuple[int, ...],
) -> tuple[float, ...]:
    if len(token_embeddings) != len(attention_mask):
        raise ValueError("token embeddings and attention_mask must have the same sequence length")

    selected = [row for row, mask in zip(token_embeddings, attention_mask, strict=True) if mask == 1]
    if not selected:
        raise ValueError("mean pooling requires at least one unmasked token")

    dimension = len(selected[0])
    return tuple(sum(row[index] for row in selected) / len(selected) for index in range(dimension))


def _normalize(values: Sequence[float]) -> tuple[float, ...]:
    vector = _float_vector(values, field_name="embedding vector")
    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0.0:
        raise ValueError("Cannot normalize a zero embedding vector")
    return tuple(value / norm for value in vector)


def _float_vector(value: Any, *, field_name: str) -> tuple[float, ...]:
    if not isinstance(value, Sequence) or isinstance(value, str):
        raise TypeError(f"{field_name} must be a sequence of numbers")
    result = tuple(_float_value(item, field_name=field_name) for item in value)
    if not result:
        raise ValueError(f"{field_name} must not be empty")
    return result


def _float_value(value: object, *, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(f"{field_name} must contain numbers")
    converted = float(value)
    if not math.isfinite(converted):
        raise ValueError(f"{field_name} must contain finite numbers")
    return converted


def _is_number_sequence(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, str) and all(
        isinstance(item, int | float) and not isinstance(item, bool) for item in value
    )
