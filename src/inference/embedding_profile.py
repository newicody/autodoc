from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from .model_profile import OpenVINOModelProfile, OpenVINOModelProfileRegistry


SUPPORTED_EMBEDDING_POOLING = frozenset({"model", "cls", "mean", "none"})
DEFAULT_EMBEDDING_INPUT_NAMES = ("input_ids", "attention_mask")
DEFAULT_EMBEDDING_OUTPUT_NAMES = ("embedding",)


def _empty_mapping() -> Mapping[str, Any]:
    return MappingProxyType({})


def _tuple_from_config(value: object, *, field_name: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        values = (value,)
    elif isinstance(value, tuple | list):
        values = tuple(value)
    else:
        raise TypeError(f"{field_name} must be a string or a sequence of strings")

    if not all(isinstance(item, str) and item for item in values):
        raise ValueError(f"{field_name} must contain only non-empty strings")
    return values


@dataclass(frozen=True, slots=True)
class OpenVINOEmbeddingProfileConfig:
    """Configuration déclarative d'un profil OpenVINO embedding.

    Cette structure ne charge pas le modèle, ne vérifie pas l'existence du
    chemin et n'impose aucun tokenizer. Elle décrit seulement comment exposer un
    modèle d'embedding OpenVINO au registre de profils quand l'utilisateur aura
    choisi un chemin local explicite.
    """

    model_path: str
    name: str = "openvino.embedding"
    device: str = "CPU"
    input_names: tuple[str, ...] = DEFAULT_EMBEDDING_INPUT_NAMES
    output_names: tuple[str, ...] = DEFAULT_EMBEDDING_OUTPUT_NAMES
    dimension: int | None = None
    pooling: str = "model"
    normalize: bool = True
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        if not self.model_path:
            raise ValueError("OpenVINOEmbeddingProfileConfig.model_path must not be empty")
        if not self.name:
            raise ValueError("OpenVINOEmbeddingProfileConfig.name must not be empty")
        if not self.device:
            raise ValueError("OpenVINOEmbeddingProfileConfig.device must not be empty")
        if self.dimension is not None and self.dimension <= 0:
            raise ValueError("OpenVINOEmbeddingProfileConfig.dimension must be positive")
        if self.pooling not in SUPPORTED_EMBEDDING_POOLING:
            allowed = ", ".join(sorted(SUPPORTED_EMBEDDING_POOLING))
            raise ValueError(f"Unsupported embedding pooling {self.pooling!r}. Allowed: {allowed}")

        input_names = _tuple_from_config(self.input_names, field_name="input_names")
        output_names = _tuple_from_config(self.output_names, field_name="output_names")
        if not input_names:
            raise ValueError("OpenVINOEmbeddingProfileConfig.input_names must not be empty")
        if not output_names:
            raise ValueError("OpenVINOEmbeddingProfileConfig.output_names must not be empty")

        object.__setattr__(self, "input_names", input_names)
        object.__setattr__(self, "output_names", output_names)
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @classmethod
    def from_mapping(cls, config: Mapping[str, Any]) -> OpenVINOEmbeddingProfileConfig:
        """Construit une configuration depuis un mapping explicite.

        La méthode accepte des listes ou tuples pour les noms d'entrées/sorties,
        afin de pouvoir être alimentée plus tard par JSON, YAML, TOML ou une
        configuration Python sans ajouter de dépendance externe.
        """

        return cls(
            model_path=str(config.get("model_path", "")),
            name=str(config.get("name", "openvino.embedding")),
            device=str(config.get("device", "CPU")),
            input_names=_tuple_from_config(
                config.get("input_names", DEFAULT_EMBEDDING_INPUT_NAMES),
                field_name="input_names",
            ),
            output_names=_tuple_from_config(
                config.get("output_names", DEFAULT_EMBEDDING_OUTPUT_NAMES),
                field_name="output_names",
            ),
            dimension=_optional_int(config.get("dimension")),
            pooling=str(config.get("pooling", "model")),
            normalize=bool(config.get("normalize", True)),
            metadata=_mapping_value(config.get("metadata", MappingProxyType({}))),
        )

    def to_model_profile(self) -> OpenVINOModelProfile:
        """Convertit cette configuration en profil OpenVINO générique."""

        metadata: dict[str, Any] = {
            **dict(self.metadata),
            "profile_kind": "openvino.embedding.configurable",
            "embedding_dimension": self.dimension,
            "embedding_pooling": self.pooling,
            "embedding_normalize": self.normalize,
            "requires_tokenizer": True,
            "tokenizer_bound": False,
        }
        return OpenVINOModelProfile(
            name=self.name,
            model_path=self.model_path,
            task="embedding",
            device=self.device,
            input_names=self.input_names,
            output_names=self.output_names,
            metadata=MappingProxyType(metadata),
        )


def register_openvino_embedding_profile(
    registry: OpenVINOModelProfileRegistry,
    config: OpenVINOEmbeddingProfileConfig,
) -> OpenVINOModelProfile:
    """Enregistre explicitement un profil embedding dans le registre."""

    profile = config.to_model_profile()
    registry.register(profile)
    return profile


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise TypeError("dimension must be an integer, not a boolean")
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value:
        return int(value)
    raise TypeError("dimension must be an integer or None")


def _mapping_value(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    raise TypeError("metadata must be a mapping")
