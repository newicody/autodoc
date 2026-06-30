from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from contracts.context import InferenceContext

from .e5_artifact_loader import (
    E5RuntimeArtifactDirectoryLoader,
    E5RuntimeArtifactDirectoryPolicy,
    E5RuntimeArtifactDirectoryReadResult,
)
from .e5_runtime_bridge import (
    E5RuntimeBridge,
    E5RuntimeBridgePolicy,
    E5RuntimeBridgeResult,
)


@dataclass(frozen=True, slots=True)
class E5LocalContextRuntimePolicy:
    """Politique explicite de la façade locale artifact-dir -> InferenceContext."""

    artifact_policy: E5RuntimeArtifactDirectoryPolicy = field(default_factory=E5RuntimeArtifactDirectoryPolicy)
    bridge_policy: E5RuntimeBridgePolicy = field(default_factory=E5RuntimeBridgePolicy)
    require_ready: bool = False


@dataclass(frozen=True, slots=True)
class E5LocalContextRuntimeRequest:
    """Requête typée pour construire un contexte local E5 depuis un artifact-dir."""

    artifact_dir: Path

    def __post_init__(self) -> None:
        if not str(self.artifact_dir).strip():
            raise ValueError("artifact_dir must not be empty")


@dataclass(frozen=True, slots=True)
class E5LocalContextRuntimeResult:
    """Résultat stable de la façade runtime locale E5."""

    artifact_dir: Path
    read_result: E5RuntimeArtifactDirectoryReadResult
    bridge_result: E5RuntimeBridgeResult

    @property
    def inference_context(self) -> InferenceContext:
        return self.bridge_result.inference_context

    @property
    def component_name(self) -> str:
        return self.bridge_result.component_name

    @property
    def feature(self) -> Mapping[str, Any]:
        value = self.inference_context.features.get(self.component_name, {})
        if isinstance(value, Mapping):
            return value
        return {}

    @property
    def status(self) -> str:
        value = self.feature.get("status")
        if isinstance(value, str):
            return value
        return "unknown"

    @property
    def is_ready(self) -> bool:
        return self.status == "ready"

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": "missipy.e5.local_context_runtime.v1",
            "artifact_dir": str(self.artifact_dir),
            "component_name": self.component_name,
            "status": self.status,
            "ready": self.is_ready,
            "read": self.read_result.to_json_dict(),
            "bridge": self.bridge_result.to_json_dict(),
        }


class E5LocalContextRuntime:
    """Façade locale stable pour intégrer un artifact-dir E5 au Context Fabric."""

    def __init__(self, policy: E5LocalContextRuntimePolicy | None = None) -> None:
        self._policy = policy or E5LocalContextRuntimePolicy()
        self._loader = E5RuntimeArtifactDirectoryLoader(self._policy.artifact_policy)
        self._bridge = E5RuntimeBridge(self._policy.bridge_policy)

    def build(self, request: E5LocalContextRuntimeRequest) -> E5LocalContextRuntimeResult:
        """Charge l'artifact-dir puis construit un InferenceContext local."""
        read_result = self._loader.load(request.artifact_dir)
        bridge_result = self._bridge.build(read_result.artifacts)
        result = E5LocalContextRuntimeResult(
            artifact_dir=request.artifact_dir,
            read_result=read_result,
            bridge_result=bridge_result,
        )
        if self._policy.require_ready and not result.is_ready:
            raise ValueError("e5_local_context status must be ready")
        return result

    def build_from_directory(self, artifact_dir: str | Path) -> E5LocalContextRuntimeResult:
        """Raccourci d'instance : artifact-dir -> résultat runtime local."""
        return self.build(E5LocalContextRuntimeRequest(artifact_dir=Path(artifact_dir)))


def build_e5_local_context_from_artifact_dir(
    artifact_dir: str | Path,
    policy: E5LocalContextRuntimePolicy | None = None,
) -> E5LocalContextRuntimeResult:
    """Point d'entrée court pour les futures intégrations serveur locales."""
    return E5LocalContextRuntime(policy).build_from_directory(artifact_dir)


def build_e5_local_inference_context_from_artifact_dir(
    artifact_dir: str | Path,
    policy: E5LocalContextRuntimePolicy | None = None,
) -> InferenceContext:
    """Retourne directement l'InferenceContext construit depuis l'artifact-dir."""
    return build_e5_local_context_from_artifact_dir(artifact_dir, policy).inference_context
