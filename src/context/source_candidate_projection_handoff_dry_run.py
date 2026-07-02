from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
import json
import os
import tempfile

from .source_candidate_projection_gate import SourceCandidateProjectionGatePolicy
from .source_candidate_projection_gate_report import (
    SourceCandidateProjectionGateReportPolicy,
    run_source_candidate_projection_gate_report,
)


_HANDOFF_SCHEMA = "missipy.source_candidate.projection_handoff_dry_run.v1"


@dataclass(frozen=True)
class SourceCandidateProjectionHandoffDryRunPolicy:
    """Local handoff dry-run policy.

    A handoff dry-run is a local bundle proving what would be handed over later.
    It never contacts an external surface.
    """

    path: Path
    manifest_name: str = "handoff_manifest.json"
    preview_name: str = "projection_preview.json"
    gate_report_name: str = "projection_gate_report.json"
    require_items: bool = False
    require_audit_present: bool = False


@dataclass(frozen=True)
class SourceCandidateProjectionHandoffArtifact:
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
class SourceCandidateProjectionHandoffDryRun:
    path: Path
    manifest_path: Path
    passed: bool
    item_count: int
    artifact_count: int
    byte_count: int
    artifacts: tuple[SourceCandidateProjectionHandoffArtifact, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _HANDOFF_SCHEMA,
            "path": str(self.path),
            "manifest_path": str(self.manifest_path),
            "passed": self.passed,
            "item_count": self.item_count,
            "artifact_count": self.artifact_count,
            "byte_count": self.byte_count,
            "artifacts": [artifact.to_json_dict() for artifact in self.artifacts],
        }


def build_source_candidate_projection_handoff_dry_run(
    projection_bundle_path: Path,
    policy: SourceCandidateProjectionHandoffDryRunPolicy,
) -> SourceCandidateProjectionHandoffDryRun:
    """Build a local handoff dry-run bundle from a projection bundle."""

    _validate_names(policy)
    policy.path.mkdir(parents=True, exist_ok=True)

    preview_source = _preview_path(projection_bundle_path)
    preview_target = policy.path / policy.preview_name
    gate_report_target = policy.path / policy.gate_report_name
    manifest_path = policy.path / policy.manifest_name

    _copy_text(preview_source, preview_target)

    gate_report = run_source_candidate_projection_gate_report(
        bundle_path=projection_bundle_path,
        report_policy=SourceCandidateProjectionGateReportPolicy(output_path=gate_report_target),
        gate_policy=SourceCandidateProjectionGatePolicy(
            require_items=policy.require_items,
            require_audit_present=policy.require_audit_present,
        ),
    )

    preview_artifact = _artifact("projection_preview", preview_target)
    gate_report_artifact = _artifact("projection_gate_report", gate_report_target)

    manifest_payload = {
        "schema": _HANDOFF_SCHEMA,
        "path": str(policy.path),
        "manifest_path": str(manifest_path),
        "projection_bundle_path": str(projection_bundle_path),
        "passed": gate_report.passed,
        "item_count": gate_report.item_count,
        "artifacts": [
            preview_artifact.to_json_dict(),
            gate_report_artifact.to_json_dict(),
        ],
    }
    _atomic_write_json(manifest_path, manifest_payload)
    manifest_artifact = _artifact("handoff_manifest", manifest_path)

    artifacts = (manifest_artifact, preview_artifact, gate_report_artifact)
    return SourceCandidateProjectionHandoffDryRun(
        path=policy.path,
        manifest_path=manifest_path,
        passed=gate_report.passed,
        item_count=gate_report.item_count,
        artifact_count=len(artifacts),
        byte_count=sum(artifact.byte_count for artifact in artifacts),
        artifacts=artifacts,
    )


def _validate_names(policy: SourceCandidateProjectionHandoffDryRunPolicy) -> None:
    names = (policy.manifest_name, policy.preview_name, policy.gate_report_name)
    if any(not name.strip() for name in names):
        raise ValueError("handoff artifact names must not be empty")
    if len(set(names)) != len(names):
        raise ValueError("handoff artifact names must be distinct")


def _preview_path(bundle_path: Path) -> Path:
    manifest_path = bundle_path / "manifest.json"
    manifest = _read_json_object(manifest_path)
    raw = manifest.get("preview_path")
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("projection bundle manifest preview_path is missing")
    path = Path(raw)
    if not path.is_absolute():
        path = bundle_path / path
    if not path.exists():
        raise ValueError(f"projection preview is missing: {path}")
    return path


def _read_json_object(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON payload must be an object: {path}")
    return payload


def _copy_text(source: Path, target: Path) -> None:
    _atomic_write_text(target, source.read_text(encoding="utf-8"))


def _artifact(role: str, path: Path) -> SourceCandidateProjectionHandoffArtifact:
    schema: str | None = None
    if path.suffix == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, dict) and isinstance(payload.get("schema"), str):
            schema = payload["schema"]
    return SourceCandidateProjectionHandoffArtifact(
        role=role,
        path=path,
        byte_count=path.stat().st_size,
        schema=schema,
    )


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    _atomic_write_text(path, text)


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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
