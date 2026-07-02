from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import os
import tempfile

from .source_candidate_projection_preview import (
    SourceCandidateProjectionPreview,
    SourceCandidateProjectionPreviewPolicy,
    build_source_candidate_projection_preview,
    read_operator_report,
    write_source_candidate_projection_preview,
)


_BUNDLE_SCHEMA = "missipy.source_candidate.projection_bundle.v1"


@dataclass(frozen=True)
class SourceCandidateProjectionBundlePolicy:
    """Local projection bundle policy.

    A projection bundle is a local artifact directory. It prepares a future
    operator/project handoff without contacting any external service.
    """

    path: Path
    preview_name: str = "projection_preview.json"
    manifest_name: str = "manifest.json"
    target_name: str = "operator_project_surface"
    max_items: int = 50
    include_terminal: bool = False


@dataclass(frozen=True)
class SourceCandidateProjectionBundleArtifact:
    role: str
    path: Path
    byte_count: int
    schema: str | None

    def to_json_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "path": str(self.path),
            "byte_count": self.byte_count,
            "schema": self.schema,
        }


@dataclass(frozen=True)
class SourceCandidateProjectionBundle:
    path: Path
    manifest_path: Path
    preview_path: Path
    item_count: int
    artifact_count: int
    byte_count: int
    artifacts: tuple[SourceCandidateProjectionBundleArtifact, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _BUNDLE_SCHEMA,
            "path": str(self.path),
            "manifest_path": str(self.manifest_path),
            "preview_path": str(self.preview_path),
            "item_count": self.item_count,
            "artifact_count": self.artifact_count,
            "byte_count": self.byte_count,
            "artifacts": [artifact.to_json_dict() for artifact in self.artifacts],
        }


def build_source_candidate_projection_bundle(
    operator_report_path: Path,
    policy: SourceCandidateProjectionBundlePolicy,
) -> SourceCandidateProjectionBundle:
    """Build a local projection preview bundle from an operator report file."""

    if not policy.preview_name.strip():
        raise ValueError("preview_name must not be empty")
    if not policy.manifest_name.strip():
        raise ValueError("manifest_name must not be empty")
    if policy.preview_name == policy.manifest_name:
        raise ValueError("preview_name and manifest_name must be distinct")

    report_payload = read_operator_report(operator_report_path)
    preview = build_source_candidate_projection_preview(
        report_payload,
        SourceCandidateProjectionPreviewPolicy(
            target_name=policy.target_name,
            max_items=policy.max_items,
            include_terminal=policy.include_terminal,
        ),
    )

    policy.path.mkdir(parents=True, exist_ok=True)
    preview_path = policy.path / policy.preview_name
    manifest_path = policy.path / policy.manifest_name

    write_source_candidate_projection_preview(preview_path, preview)
    preview_artifact = _artifact("projection_preview", preview_path)

    manifest_payload = _manifest_payload(
        path=policy.path,
        manifest_path=manifest_path,
        preview=preview,
        preview_artifact=preview_artifact,
    )
    _atomic_write_json(manifest_path, manifest_payload)
    manifest_artifact = _artifact("manifest", manifest_path)

    artifacts = (manifest_artifact, preview_artifact)
    return SourceCandidateProjectionBundle(
        path=policy.path,
        manifest_path=manifest_path,
        preview_path=preview_path,
        item_count=preview.item_count,
        artifact_count=len(artifacts),
        byte_count=sum(artifact.byte_count for artifact in artifacts),
        artifacts=artifacts,
    )


def _manifest_payload(
    *,
    path: Path,
    manifest_path: Path,
    preview: SourceCandidateProjectionPreview,
    preview_artifact: SourceCandidateProjectionBundleArtifact,
) -> dict[str, object]:
    return {
        "schema": _BUNDLE_SCHEMA,
        "path": str(path),
        "manifest_path": str(manifest_path),
        "preview_path": str(preview_artifact.path),
        "item_count": preview.item_count,
        "target_name": preview.target_name,
        "source_report_schema": preview.source_report_schema,
        "artifacts": [preview_artifact.to_json_dict()],
    }


def _artifact(role: str, path: Path) -> SourceCandidateProjectionBundleArtifact:
    payload: dict[str, Any] | None = None
    schema: str | None = None
    if path.suffix == ".json":
        try:
            parsed = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            payload = parsed
    if payload is not None and isinstance(payload.get("schema"), str):
        schema = payload["schema"]
    return SourceCandidateProjectionBundleArtifact(
        role=role,
        path=path,
        byte_count=path.stat().st_size,
        schema=schema,
    )


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        tmp_name = handle.name
        handle.write(text)
    os.replace(tmp_name, path)
