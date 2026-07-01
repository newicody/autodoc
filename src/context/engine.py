from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
from pathlib import Path
from inspect import isawaitable

from contracts.context import GlobalContextSnapshot, InferenceContext, freeze_mapping

from .builder import InferenceContextBuilder
from .collector import ContextCollector
from .reducer import ContextReducer

from .e5_context_attachment import (
    E5ContextAttachmentPolicy,
    E5ContextAttachmentResult,
    attach_e5_artifact_dir_to_context,
    attach_e5_runtime_context,
)
from .e5_local_context_runtime import E5LocalContextRuntimePolicy, E5LocalContextRuntimeResult


@dataclass(frozen=True, slots=True)
class E5ContextEngineIntakePolicy:
    """Politique explicite d'entrée E5 dans ContextEngine.

    Cette politique ne déclenche aucun Scheduler, aucun daemon et aucun réseau. Elle
    décrit uniquement comment un appel manuel d'intake E5 doit fusionner le contexte.
    """

    runtime_policy: E5LocalContextRuntimePolicy | None = None
    attachment_policy: E5ContextAttachmentPolicy | None = None


@dataclass(frozen=True, slots=True)
class E5ContextEngineIntakeResult:
    """Résultat stable d'un intake E5 explicite dans ContextEngine."""

    inference_context: InferenceContext
    attachment_result: E5ContextAttachmentResult
    previous_feature_count: int

    @property
    def feature_count(self) -> int:
        return len(self.inference_context.features)

    @property
    def changed(self) -> bool:
        return self.feature_count != self.previous_feature_count or bool(
            self.attachment_result.replaced_components
        )

    @property
    def ready(self) -> bool:
        return self.attachment_result.ready

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": "missipy.e5.context_engine_intake.v1",
            "ready": self.ready,
            "changed": self.changed,
            "previous_feature_count": self.previous_feature_count,
            "feature_count": self.feature_count,
            "attachment": self.attachment_result.to_json_dict(),
        }


class ContextEngine:
    """Point de coordination local du Context Fabric.

    La Phase 5.6-r1 restaure le contrat historique du micro-kernel : le
    Scheduler construit encore ``ContextEngine(registry, scheduler, event_bus)``.
    L'intake E5 reste une entrée explicite et ne déclenche aucun Scheduler,
    daemon, réseau ou backend.
    """

    def __init__(
        self,
        registry: object | InferenceContext | None = None,
        scheduler: object | None = None,
        event_bus: object | None = None,
        inference_context: InferenceContext | None = None,
    ) -> None:
        if isinstance(registry, InferenceContext) and scheduler is None and event_bus is None and inference_context is None:
            inference_context = registry
            registry = None

        self.registry = registry
        self.scheduler = scheduler
        self.event_bus = event_bus
        self.collector = _build_context_helper(ContextCollector, registry, scheduler, event_bus)
        self.reducer = _build_context_helper(ContextReducer, registry, scheduler, event_bus)
        self.builder = _build_context_helper(InferenceContextBuilder, registry, scheduler, event_bus)
        self.last_snapshot: object | None = None
        self.last_inference_context = inference_context or _empty_inference_context()

    @property
    def current_inference_context(self) -> InferenceContext:
        """Retourne le dernier contexte connu par le moteur."""
        return self.last_inference_context

    def set_inference_context(self, inference_context: InferenceContext) -> None:
        """Remplace explicitement le contexte courant."""
        self.last_inference_context = inference_context

    async def execute_tick(self) -> GlobalContextSnapshot | InferenceContext | object:
        """Exécute le tick de contexte historique du micro-kernel.

        Le contrat historique retourne le snapshot collecté/réduit afin que les
        appelants puissent inspecter ``snapshot.components``. Le
        ``InferenceContext`` construit reste mémorisé dans
        ``last_inference_context`` pour les phases runtime.
        """
        collected = await _call_context_helper(
            self.collector,
            "collect",
            (),
            (self.registry, self.scheduler, self.event_bus),
            (self.registry, self.scheduler),
            (self.registry,),
        )

        if isinstance(collected, InferenceContext):
            self.last_snapshot = None
            self.last_inference_context = collected
            return collected

        snapshot = collected
        if self.reducer is not None and hasattr(self.reducer, "reduce"):
            snapshot = await _call_context_helper(
                self.reducer,
                "reduce",
                (collected,),
                (collected, self.registry, self.scheduler, self.event_bus),
            )

        self.last_snapshot = snapshot

        if isinstance(snapshot, InferenceContext):
            self.last_inference_context = snapshot
            return snapshot

        if self.builder is not None and hasattr(self.builder, "build"):
            built = await _call_context_helper(
                self.builder,
                "build",
                (snapshot,),
                (snapshot, self.registry, self.scheduler, self.event_bus),
            )
            if isinstance(built, InferenceContext):
                self.last_inference_context = built
                return snapshot

        fallback = _inference_context_from_collected(snapshot)
        self.last_inference_context = fallback
        return snapshot if snapshot is not None else fallback

    def attach_e5_runtime_context(
        self,
        runtime_result: E5LocalContextRuntimeResult,
        policy: E5ContextEngineIntakePolicy | None = None,
    ) -> E5ContextEngineIntakeResult:
        """Attache un résultat runtime E5 déjà construit au contexte courant."""
        effective = policy or E5ContextEngineIntakePolicy()
        previous = self.last_inference_context
        attachment = attach_e5_runtime_context(
            previous,
            runtime_result,
            effective.attachment_policy,
        )
        self.last_inference_context = attachment.inference_context
        return E5ContextEngineIntakeResult(
            inference_context=attachment.inference_context,
            attachment_result=attachment,
            previous_feature_count=len(previous.features),
        )

    def attach_e5_artifact_dir(
        self,
        artifact_dir: str | Path,
        policy: E5ContextEngineIntakePolicy | None = None,
    ) -> E5ContextEngineIntakeResult:
        """Charge un artifact-dir Phase 4 puis l'attache explicitement au contexte courant."""
        effective = policy or E5ContextEngineIntakePolicy()
        previous = self.last_inference_context
        attachment = attach_e5_artifact_dir_to_context(
            previous,
            artifact_dir,
            runtime_policy=effective.runtime_policy,
            attachment_policy=effective.attachment_policy,
        )
        self.last_inference_context = attachment.inference_context
        return E5ContextEngineIntakeResult(
            inference_context=attachment.inference_context,
            attachment_result=attachment,
            previous_feature_count=len(previous.features),
        )


def _empty_inference_context() -> InferenceContext:
    return InferenceContext(features=freeze_mapping({}), priorities=freeze_mapping({}))



def _build_context_helper(helper_type: type, registry: object | None, scheduler: object | None, event_bus: object | None) -> object | None:
    for args in (
        (registry, scheduler, event_bus),
        (registry, scheduler),
        (registry,),
        (),
    ):
        try:
            return helper_type(*args)
        except TypeError:
            continue
    return None


async def _call_context_helper(target: object | None, method_name: str, *argument_sets: tuple[object, ...]) -> object:
    if target is None or not hasattr(target, method_name):
        return None
    method = getattr(target, method_name)
    last_error: TypeError | None = None
    for args in argument_sets:
        try:
            result = method(*args)
        except TypeError as exc:
            last_error = exc
            continue
        if isawaitable(result):
            return await result
        return result
    if last_error is not None:
        raise last_error
    return None


def _inference_context_from_collected(value: object) -> InferenceContext:
    if isinstance(value, Mapping):
        features = dict(value)
    elif hasattr(value, "components"):
        components = getattr(value, "components")
        features = dict(components) if isinstance(components, Mapping) else {"snapshot": value}
    elif value is None:
        features = {}
    else:
        features = {"context": value}
    return InferenceContext(features=freeze_mapping(features), priorities=freeze_mapping({}))
