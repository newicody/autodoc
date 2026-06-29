from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Any

from .embedding_profile import OpenVINOEmbeddingProfileConfig
from .tokenizer_contract import TokenizerConfig
from .transformers_tokenizer import TransformersTokenizerAdapterConfig

MULTILINGUAL_E5_SMALL_PROFILE_NAME = "openvino.embedding.e5-small"
MULTILINGUAL_E5_SMALL_TOKENIZER_NAME = "transformers.multilingual-e5-small"
MULTILINGUAL_E5_SMALL_ENV = "MISSIPY_E5_SMALL_DIR"
MULTILINGUAL_E5_SMALL_DEFAULT_DIR = "/home/eric/model/openvino/multilingual-e5-small"


def _empty_mapping() -> Mapping[str, Any]:
    return MappingProxyType({})


@dataclass(frozen=True, slots=True)
class MultilingualE5SmallLocalConfig:
    """Configuration locale du premier profil embedding réel.

    Le modèle reste optionnel : cette structure ne vérifie pas l'existence du
    chemin et ne charge ni OpenVINO ni Transformers. Elle décrit simplement le
    profil observé localement : ``last_hidden_state`` en sortie, dimension 384,
    pooling ``mean`` et ``token_type_ids`` requis côté modèle OpenVINO.
    """

    model_dir: str | None = None
    name: str = MULTILINGUAL_E5_SMALL_PROFILE_NAME
    tokenizer_name: str = MULTILINGUAL_E5_SMALL_TOKENIZER_NAME
    device: str = "CPU"
    max_length: int = 128
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("MultilingualE5SmallLocalConfig.name must not be empty")
        if not self.tokenizer_name:
            raise ValueError("MultilingualE5SmallLocalConfig.tokenizer_name must not be empty")
        if not self.device:
            raise ValueError("MultilingualE5SmallLocalConfig.device must not be empty")
        if self.max_length <= 0:
            raise ValueError("MultilingualE5SmallLocalConfig.max_length must be positive")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    @property
    def resolved_model_dir(self) -> Path:
        """Résout le dossier local depuis la config ou l'environnement."""
        return Path(
            self.model_dir
            or os.environ.get(MULTILINGUAL_E5_SMALL_ENV)
            or MULTILINGUAL_E5_SMALL_DEFAULT_DIR
        )

    @property
    def model_path(self) -> Path:
        """Chemin du fichier IR OpenVINO XML attendu."""
        return self.resolved_model_dir / "openvino_model.xml"

    def to_embedding_profile_config(self) -> OpenVINOEmbeddingProfileConfig:
        """Construit la configuration OpenVINO embedding générique."""
        return OpenVINOEmbeddingProfileConfig(
            model_path=str(self.model_path),
            name=self.name,
            device=self.device,
            input_names=("input_ids", "attention_mask", "token_type_ids"),
            output_names=("last_hidden_state",),
            dimension=384,
            pooling="mean",
            normalize=True,
            metadata=MappingProxyType(
                {
                    **dict(self.metadata),
                    "profile_kind": "openvino.embedding.e5-small.local",
                    "model_family": "multilingual-e5",
                    "model_size": "small",
                    "tokenizer_name": self.tokenizer_name,
                    "requires_transformers_tokenizer": True,
                    "requires_token_type_ids": True,
                    "local_model_dir": str(self.resolved_model_dir),
                }
            ),
        )

    def to_tokenizer_config(self) -> TokenizerConfig:
        """Construit la configuration de tokenization attendue par le pipeline."""
        return TokenizerConfig(
            name=self.tokenizer_name,
            max_length=self.max_length,
            padding="max_length",
            truncation="longest_first",
            add_special_tokens=True,
            pad_token_id=0,
            metadata=MappingProxyType(
                {
                    "profile_name": self.name,
                    "model_family": "multilingual-e5",
                    "input_prefix_expected": "query: or passage:",
                }
            ),
        )

    def to_transformers_tokenizer_adapter_config(self) -> TransformersTokenizerAdapterConfig:
        """Construit la configuration du tokenizer Transformers local."""
        return TransformersTokenizerAdapterConfig(
            model_dir=str(self.resolved_model_dir),
            name=self.tokenizer_name,
            force_token_type_ids=True,
            metadata=MappingProxyType(
                {
                    "profile_name": self.name,
                    "model_family": "multilingual-e5",
                    "requires_token_type_ids": True,
                }
            ),
        )
