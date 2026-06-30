from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .e5_runtime_bridge import (
    E5RuntimeArtifactBundle,
    E5RuntimeBridge,
    E5RuntimeBridgePolicy,
    E5RuntimeBridgeResult,
)

JsonPayload = Mapping[str, Any]


@dataclass(frozen=True, slots=True)
class E5RuntimeArtifactDirectoryPolicy:
    """Politique explicite de lecture des artefacts E5 Phase 4 depuis un dossier."""

    report_filename: str = "report.json"
    context_filename: str = "context.json"
    consumed_context_filename: str = "consumed_context.json"
    prompt_filename: str = "prompt.json"
    encoding: str = "utf-8"

    def __post_init__(self) -> None:
        _validate_filename(self.report_filename, "report_filename")
        _validate_filename(self.context_filename, "context_filename")
        _validate_filename(self.consumed_context_filename, "consumed_context_filename")
        _validate_filename(self.prompt_filename, "prompt_filename")
        if not self.encoding.strip():
            raise ValueError("encoding must not be empty")


@dataclass(frozen=True, slots=True)
class E5RuntimeArtifactDirectoryReadResult:
    """Résultat stable de la lecture contrôlée d'un dossier d'artefacts E5."""

    artifact_dir: Path
    report_path: Path
    context_path: Path
    consumed_context_path: Path
    prompt_path: Path
    artifacts: E5RuntimeArtifactBundle

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": "missipy.e5.runtime_artifact_directory.v1",
            "artifact_dir": str(self.artifact_dir),
            "files": {
                "report": str(self.report_path),
                "context": str(self.context_path),
                "consumed_context": str(self.consumed_context_path),
                "prompt": str(self.prompt_path),
            },
            "loaded": {
                "report": True,
                "context": True,
                "consumed_context": True,
                "prompt": True,
            },
        }


class E5RuntimeArtifactDirectoryLoader:
    """Bordure IO contrôlée pour charger les artefacts Phase 4 depuis un dossier."""

    def __init__(self, policy: E5RuntimeArtifactDirectoryPolicy | None = None) -> None:
        self._policy = policy or E5RuntimeArtifactDirectoryPolicy()

    def load(self, artifact_dir: str | Path) -> E5RuntimeArtifactDirectoryReadResult:
        """Lit les quatre JSON attendus et retourne un bundle runtime typé."""
        directory = Path(artifact_dir)
        if not directory.is_dir():
            raise NotADirectoryError(str(directory))

        report_path = directory / self._policy.report_filename
        context_path = directory / self._policy.context_filename
        consumed_context_path = directory / self._policy.consumed_context_filename
        prompt_path = directory / self._policy.prompt_filename

        artifacts = E5RuntimeArtifactBundle(
            report=_read_json_object(report_path, "report", self._policy.encoding),
            context=_read_json_object(context_path, "context", self._policy.encoding),
            consumed_context=_read_json_object(
                consumed_context_path,
                "consumed_context",
                self._policy.encoding,
            ),
            prompt=_read_json_object(prompt_path, "prompt", self._policy.encoding),
        )

        return E5RuntimeArtifactDirectoryReadResult(
            artifact_dir=directory,
            report_path=report_path,
            context_path=context_path,
            consumed_context_path=consumed_context_path,
            prompt_path=prompt_path,
            artifacts=artifacts,
        )


class E5RuntimeArtifactDirectoryBridge:
    """Compose la bordure de lecture 5.2 avec le pont pur 5.1."""

    def __init__(
        self,
        *,
        loader_policy: E5RuntimeArtifactDirectoryPolicy | None = None,
        bridge_policy: E5RuntimeBridgePolicy | None = None,
    ) -> None:
        self._loader = E5RuntimeArtifactDirectoryLoader(loader_policy)
        self._bridge = E5RuntimeBridge(bridge_policy)

    def build(self, artifact_dir: str | Path) -> E5RuntimeBridgeResult:
        """Charge le dossier puis construit l'InferenceContext correspondant."""
        read_result = self._loader.load(artifact_dir)
        return self._bridge.build(read_result.artifacts)


def load_e5_runtime_artifacts_from_directory(
    artifact_dir: str | Path,
    policy: E5RuntimeArtifactDirectoryPolicy | None = None,
) -> E5RuntimeArtifactBundle:
    """Raccourci : charge seulement le bundle d'artefacts runtime."""
    return E5RuntimeArtifactDirectoryLoader(policy).load(artifact_dir).artifacts


def build_e5_runtime_bridge_from_directory(
    artifact_dir: str | Path,
    *,
    loader_policy: E5RuntimeArtifactDirectoryPolicy | None = None,
    bridge_policy: E5RuntimeBridgePolicy | None = None,
) -> E5RuntimeBridgeResult:
    """Raccourci : lit un artifact-dir Phase 4 et produit le résultat bridge 5.1."""
    return E5RuntimeArtifactDirectoryBridge(
        loader_policy=loader_policy,
        bridge_policy=bridge_policy,
    ).build(artifact_dir)


def _validate_filename(value: str, field_name: str) -> None:
    path = Path(value)
    if not value.strip():
        raise ValueError(f"{field_name} must not be empty")
    if path.name != value:
        raise ValueError(f"{field_name} must be a filename")


def _read_json_object(path: Path, artifact_name: str, encoding: str) -> dict[str, Any]:
    with path.open("r", encoding=encoding) as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise TypeError(f"{artifact_name} artifact must be a JSON object")
    return payload
