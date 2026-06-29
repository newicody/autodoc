from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from .adapter import InferenceAdapter
from .e5_profile import MultilingualE5SmallLocalConfig
from .embedding_pipeline import OpenVINOEmbeddingPipeline, OpenVINOEmbeddingPipelineConfig
from .embedding_raw import OpenVINOEmbeddingOutputConfig
from .model_profile import OpenVINOModelProfileRegistry
from .openvino_backend import OpenVINORuntime
from .openvino_factory import OpenVINOBackendFactory
from .openvino_runtime import RealOpenVINORuntime
from .registry import BackendRegistry
from .tokenizer_contract import TextTokenizer, TokenizerRegistry
from .transformers_tokenizer import TransformersAutoTokenizer, TransformersTokenizerAdapterConfig


def _empty_mapping() -> Mapping[str, Any]:
    return MappingProxyType({})


def _default_local_config() -> MultilingualE5SmallLocalConfig:
    return MultilingualE5SmallLocalConfig()


RuntimeFactory = Callable[[], OpenVINORuntime]
TokenizerFactory = Callable[[TransformersTokenizerAdapterConfig], TextTokenizer]


@dataclass(frozen=True, slots=True)
class MultilingualE5SmallPipelineConfig:
    """Configuration de construction du pipeline local E5.

    Cette structure assemble les décisions déjà prises pour le premier modèle
    réel : profil multilingual-e5-small, tokenizer local Transformers optionnel,
    runtime OpenVINO injecté et pipeline embedding mono-texte. Elle ne lance pas
    de téléchargement et ne dépend pas de l'environnement tant que l'appelant ne
    choisit pas ``MultilingualE5SmallLocalConfig(model_dir=None)``.
    """

    local: MultilingualE5SmallLocalConfig = field(default_factory=_default_local_config)
    require_model_exists: bool = False
    make_backend_default: bool = True
    make_tokenizer_default: bool = True
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@dataclass(frozen=True, slots=True)
class MultilingualE5SmallPipelineBuildSummary:
    """Résumé immuable d'une construction de pipeline local E5.

    Le résumé ne contient aucun objet vivant : pas de tokenizer, pas de runtime,
    pas de backend, pas de pipeline. Il peut donc être exposé dans un rapport ou
    un diagnostic sans casser les règles d'observabilité.
    """

    profile_name: str
    tokenizer_name: str
    backend_name: str
    model_path: str
    device: str
    model_exists: bool
    backend_registered: bool
    tokenizer_registered: bool
    metadata: Mapping[str, Any] = field(default_factory=_empty_mapping)

    def __post_init__(self) -> None:
        if not self.profile_name:
            raise ValueError("MultilingualE5SmallPipelineBuildSummary.profile_name must not be empty")
        if not self.tokenizer_name:
            raise ValueError("MultilingualE5SmallPipelineBuildSummary.tokenizer_name must not be empty")
        if not self.backend_name:
            raise ValueError("MultilingualE5SmallPipelineBuildSummary.backend_name must not be empty")
        if not self.model_path:
            raise ValueError("MultilingualE5SmallPipelineBuildSummary.model_path must not be empty")
        if not self.device:
            raise ValueError("MultilingualE5SmallPipelineBuildSummary.device must not be empty")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


class MultilingualE5SmallPipelineBundle:
    """Objets vivants nécessaires pour exécuter le pipeline local E5.

    Cette classe n'est pas un contrat d'observabilité : elle transporte les
    registres et le pipeline exécutables utilisés par le code d'intégration.
    """

    def __init__(
        self,
        *,
        pipeline: OpenVINOEmbeddingPipeline,
        profile_registry: OpenVINOModelProfileRegistry,
        tokenizer_registry: TokenizerRegistry,
        backend_registry: BackendRegistry,
        summary: MultilingualE5SmallPipelineBuildSummary,
    ) -> None:
        self.pipeline = pipeline
        self.profile_registry = profile_registry
        self.tokenizer_registry = tokenizer_registry
        self.backend_registry = backend_registry
        self.summary = summary


class MultilingualE5SmallPipelineFactory:
    """Construit le pipeline local E5 depuis une configuration explicite.

    La factory évite de laisser le test d'intégration assembler à la main les
    mêmes pièces à chaque fois. Les dépendances externes restent optionnelles :
    par défaut, la factory utilise Transformers et RealOpenVINORuntime, mais les
    tests peuvent injecter un tokenizer et un runtime factices.
    """

    def __init__(
        self,
        *,
        runtime_factory: RuntimeFactory | None = None,
        tokenizer_factory: TokenizerFactory | None = None,
    ) -> None:
        self._runtime_factory = runtime_factory or RealOpenVINORuntime.with_imported_openvino
        self._tokenizer_factory = tokenizer_factory or TransformersAutoTokenizer.from_pretrained

    def build(
        self,
        config: MultilingualE5SmallPipelineConfig | None = None,
    ) -> MultilingualE5SmallPipelineBundle:
        """Construit les registres, le backend et le pipeline E5 local."""

        resolved = config or MultilingualE5SmallPipelineConfig()
        local = resolved.local
        if resolved.require_model_exists and not local.model_path.exists():
            raise FileNotFoundError(f"missing OpenVINO E5 model: {local.model_path}")

        profile_registry = OpenVINOModelProfileRegistry()
        profile = local.to_embedding_profile_config().to_model_profile()
        profile_registry.register(profile)

        tokenizer_registry = TokenizerRegistry()
        tokenizer = self._tokenizer_factory(local.to_transformers_tokenizer_adapter_config())
        tokenizer_registry.register(tokenizer, make_default=resolved.make_tokenizer_default)

        backend_registry = BackendRegistry()
        runtime = self._runtime_factory()
        backend_result = OpenVINOBackendFactory(lambda _profile, _config: runtime).build_selected_and_register(
            profile_registry,
            profile.name,
            backend_registry,
            make_default=resolved.make_backend_default,
        )

        pipeline = OpenVINOEmbeddingPipeline(
            tokenizer_registry=tokenizer_registry,
            inference_adapter=InferenceAdapter(backend_registry),
            config=OpenVINOEmbeddingPipelineConfig(
                model=profile.name,
                tokenizer_name=local.tokenizer_name,
                tokenizer_config=local.to_tokenizer_config(),
                input_names=profile.input_names,
                output_config=OpenVINOEmbeddingOutputConfig(
                    output_names=profile.output_names,
                    pooling="mean",
                    normalize=True,
                ),
                metadata=MappingProxyType(
                    {
                        **dict(resolved.metadata),
                        "pipeline_kind": "openvino.embedding.e5-small.local",
                    }
                ),
            ),
        )

        summary = MultilingualE5SmallPipelineBuildSummary(
            profile_name=profile.name,
            tokenizer_name=local.tokenizer_name,
            backend_name=backend_result.backend_name,
            model_path=str(local.model_path),
            device=local.device,
            model_exists=local.model_path.exists(),
            backend_registered=backend_result.registered,
            tokenizer_registered=local.tokenizer_name in tokenizer_registry.tokenizer_names(),
            metadata=MappingProxyType(
                {
                    "profile_task": profile.task,
                    "input_names": profile.input_names,
                    "output_names": profile.output_names,
                    "requires_token_type_ids": True,
                }
            ),
        )

        return MultilingualE5SmallPipelineBundle(
            pipeline=pipeline,
            profile_registry=profile_registry,
            tokenizer_registry=tokenizer_registry,
            backend_registry=backend_registry,
            summary=summary,
        )


def build_multilingual_e5_small_pipeline(
    config: MultilingualE5SmallPipelineConfig | None = None,
    *,
    runtime_factory: RuntimeFactory | None = None,
    tokenizer_factory: TokenizerFactory | None = None,
) -> MultilingualE5SmallPipelineBundle:
    """Raccourci explicite pour construire le pipeline local E5."""

    return MultilingualE5SmallPipelineFactory(
        runtime_factory=runtime_factory,
        tokenizer_factory=tokenizer_factory,
    ).build(config)
