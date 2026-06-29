from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from contracts.inference import InferenceResult

from .adapter import InferenceAdapter
from .embedding_profile import DEFAULT_EMBEDDING_INPUT_NAMES
from .embedding_raw import (
    OpenVINOEmbeddingOutputAdapter,
    OpenVINOEmbeddingOutputConfig,
    OpenVINOEmbeddingRawInputs,
    OpenVINOEmbeddingVector,
)
from .tokenizer_contract import (
    TokenizationRequest,
    TokenizationResult,
    TokenizerConfig,
    TokenizerRegistry,
)


def _empty_mapping() -> Mapping[str, Any]:
    return MappingProxyType({})


def _default_output_config() -> OpenVINOEmbeddingOutputConfig:
    return OpenVINOEmbeddingOutputConfig()


@dataclass(frozen=True, slots=True)
class OpenVINOEmbeddingPipelineConfig:
    """Configuration stable du pipeline embedding abstrait.

    Le pipeline assemble des briques déjà définies : tokenizer injectable,
    projection raw-input OpenVINO, backend sélectionné par InferenceAdapter et
    adapter de sortie embedding. Il ne charge aucun modèle et n'impose aucune
    implémentation concrète de tokenizer.
    """

    model: str
    tokenizer_config: TokenizerConfig
    tokenizer_name: str | None = None
    input_names: tuple[str, ...] = DEFAULT_EMBEDDING_INPUT_NAMES
    output_config: OpenVINOEmbeddingOutputConfig = field(default_factory=_default_output_config)
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        if not self.model:
            raise ValueError("OpenVINOEmbeddingPipelineConfig.model must not be empty")
        tokenizer_name = self.tokenizer_name or self.tokenizer_config.name
        if not tokenizer_name:
            raise ValueError("OpenVINOEmbeddingPipelineConfig.tokenizer_name must not be empty")
        input_names = _to_name_tuple(self.input_names, field_name="input_names")
        if len(input_names) < 2:
            raise ValueError("OpenVINO embedding pipeline input_names must contain at least two names")

        object.__setattr__(self, "tokenizer_name", tokenizer_name)
        object.__setattr__(self, "input_names", input_names)
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True, slots=True)
class OpenVINOEmbeddingPipelineResult:
    """Résultat immuable d'un pipeline embedding mono-texte."""

    text: str
    model: str
    tokenizer_name: str
    backend: str
    vector: OpenVINOEmbeddingVector
    tokenization: TokenizationResult
    raw_inputs: OpenVINOEmbeddingRawInputs
    inference: InferenceResult
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        if not self.text:
            raise ValueError("OpenVINOEmbeddingPipelineResult.text must not be empty")
        if not self.model:
            raise ValueError("OpenVINOEmbeddingPipelineResult.model must not be empty")
        if not self.tokenizer_name:
            raise ValueError("OpenVINOEmbeddingPipelineResult.tokenizer_name must not be empty")
        if not self.backend:
            raise ValueError("OpenVINOEmbeddingPipelineResult.backend must not be empty")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


class OpenVINOEmbeddingPipeline:
    """Pipeline embedding abstrait, sans tokenizer concret imposé.

    La classe est une composition explicite. Elle ne passe pas par le Scheduler,
    ne publie aucun événement et ne connaît pas Qdrant. Elle délègue l'exécution
    au chemin d'inférence déjà existant via InferenceAdapter.
    """

    def __init__(
        self,
        *,
        tokenizer_registry: TokenizerRegistry,
        inference_adapter: InferenceAdapter,
        config: OpenVINOEmbeddingPipelineConfig,
    ) -> None:
        self._tokenizer_registry = tokenizer_registry
        self._inference_adapter = inference_adapter
        self._config = config
        self._output_adapter = OpenVINOEmbeddingOutputAdapter(config.output_config)

    @property
    def config(self) -> OpenVINOEmbeddingPipelineConfig:
        """Configuration immuable du pipeline."""

        return self._config

    async def embed_text(self, text: str) -> OpenVINOEmbeddingPipelineResult:
        """Produit un embedding pour un texte unique."""

        return await self.embed_request(TokenizationRequest.from_text(text))

    async def embed_request(self, request: TokenizationRequest) -> OpenVINOEmbeddingPipelineResult:
        """Exécute le pipeline depuis une demande de tokenization explicite.

        Phase 3.5 limite volontairement la sortie à un seul vecteur. Le batch
        sera ajouté plus tard avec un contrat dédié, afin d'éviter une sortie
        ambiguë pour les backends et les futurs index vectoriels.
        """

        if request.batch_size != 1:
            raise ValueError("OpenVINOEmbeddingPipeline Phase 3.5 supports one text at a time")

        tokenizer = self._tokenizer_registry.select(self._config.tokenizer_name)
        tokenization = tokenizer.tokenize(request, config=self._config.tokenizer_config)
        raw_inputs = tokenization.to_embedding_raw_inputs()
        inference_request = raw_inputs.to_inference_request(
            model=self._config.model,
            prompt=request.texts[0],
            input_names=self._config.input_names,
            metadata=MappingProxyType(
                {
                    **dict(self._config.metadata),
                    "embedding_pipeline": True,
                    "tokenizer_name": tokenization.tokenizer_name,
                }
            ),
        )
        inference = await self._inference_adapter.infer(inference_request)
        raw_outputs = _extract_raw_outputs(inference)
        vector = self._output_adapter.extract(raw_outputs, raw_inputs)

        return OpenVINOEmbeddingPipelineResult(
            text=request.texts[0],
            model=self._config.model,
            tokenizer_name=tokenization.tokenizer_name,
            backend=inference.backend,
            vector=vector,
            tokenization=tokenization,
            raw_inputs=raw_inputs,
            inference=inference,
            metadata=MappingProxyType(
                {
                    "pipeline": type(self).__name__,
                    "vector_dimension": vector.dimension,
                    "normalized": vector.normalized,
                    "pooling": vector.pooling,
                }
            ),
        )


def _extract_raw_outputs(inference: InferenceResult) -> Any:
    """Récupère les sorties brutes nécessaires à l'adapter embedding."""

    for key in ("raw_outputs", "openvino_raw_outputs", "outputs"):
        if key in inference.metadata:
            return inference.metadata[key]
    raise KeyError(
        "Embedding pipeline requires raw outputs in InferenceResult.metadata "
        "under 'raw_outputs', 'openvino_raw_outputs' or 'outputs'."
    )


def _to_name_tuple(value: Sequence[str], *, field_name: str) -> tuple[str, ...]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise TypeError(f"{field_name} must be a sequence of strings")
    names = tuple(value)
    if not names or not all(isinstance(name, str) and name for name in names):
        raise ValueError(f"{field_name} must contain only non-empty strings")
    return names
