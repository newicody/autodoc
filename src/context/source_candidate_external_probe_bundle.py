from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
import json
import os
import tempfile


_BUNDLE_SCHEMA = "missipy.source_candidate.external_probe_bundle.v1"
_OPERATOR_REVIEW_SCHEMA = "missipy.source_candidate.operator_external_review_report.v1"
_PROBE_REQUEST_SCHEMA = "missipy.source_candidate.read_only_external_probe_request.v1"
_PROBE_RESULT_SCHEMA = "missipy.source_candidate.read_only_external_probe_result.v1"


@dataclass(frozen=True)
class SourceCandidateExternalProbeBundleArtifact:
    role: str
    path: Path
    schema: str
    byte_count: int

    def to_json_dict(self, bundle_root: Path) -> dict[str, object]:
        return {
            "role": self.role,
            "path": self.path.resolve().relative_to(bundle_root.resolve()).as_posix(),
            "schema": self.schema,
            "byte_count": self.byte_count,
        }


@dataclass(frozen=True)
class SourceCandidateExternalProbeBundle:
    path: Path
    manifest_path: Path
    repository: str
    read_only: bool
    external_call_performed: bool
    probe_allowed: bool
    artifact_count: int
    byte_count: int
    artifacts: tuple[SourceCandidateExternalProbeBundleArtifact, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _BUNDLE_SCHEMA,
            "path": str(self.path),
            "manifest_path": str(self.manifest_path),
            "repository": self.repository,
            "read_only": self.read_only,
            "external_call_performed": self.external_call_performed,
            "probe_allowed": self.probe_allowed,
            "artifact_count": self.artifact_count,
            "byte_count": self.byte_count,
            "artifacts": [artifact.to_json_dict(self.path) for artifact in self.artifacts],
        }


def build_source_candidate_external_probe_bundle(
    *,
    output_dir: Path,
    operator_review_report_path: Path,
    probe_request_path: Path,
    probe_result_path: Path,
) -> SourceCandidateExternalProbeBundle:
    """Create a local bundle for operator review of read-only external probing.

    The bundle copies existing local JSON artifacts into one deterministic
    directory and writes a manifest. It does not create, contact or mutate any
    external resource.
    """

    output_dir.mkdir(parents=True, exist_ok=True)

    operator_review_report = _read_json_object(operator_review_report_path)
    probe_request = _read_json_object(probe_request_path)
    probe_result = _read_json_object(probe_result_path)

    _expect_schema(operator_review_report, _OPERATOR_REVIEW_SCHEMA, operator_review_report_path)
    _expect_schema(probe_request, _PROBE_REQUEST_SCHEMA, probe_request_path)
    _expect_schema(probe_result, _PROBE_RESULT_SCHEMA, probe_result_path)

    repository = _same_repository(
        operator_review_report.get("repository"),
        probe_request.get("repository"),
        probe_result.get("repository"),
    )

    read_only = bool(probe_result.get("read_only"))
    external_call_performed = bool(probe_result.get("external_call_performed"))
    probe_allowed = bool(probe_result.get("probe_allowed"))

    artifacts = (
        _copy_json_artifact(
            source=operator_review_report_path,
            target=output_dir / "operator_external_review_report.json",
            role="operator_external_review_report",
            schema=_OPERATOR_REVIEW_SCHEMA,
            bundle_root=output_dir,
        ),
        _copy_json_artifact(
            source=probe_request_path,
            target=output_dir / "read_only_external_probe_request.json",
            role="read_only_external_probe_request",
            schema=_PROBE_REQUEST_SCHEMA,
            bundle_root=output_dir,
        ),
        _copy_json_artifact(
            source=probe_result_path,
            target=output_dir / "read_only_external_probe_result.json",
            role="read_only_external_probe_result",
            schema=_PROBE_RESULT_SCHEMA,
            bundle_root=output_dir,
        ),
    )

    manifest_path = output_dir / "manifest.json"
    bundle = SourceCandidateExternalProbeBundle(
        path=output_dir,
        manifest_path=manifest_path,
        repository=repository,
        read_only=read_only,
        external_call_performed=external_call_performed,
        probe_allowed=probe_allowed,
        artifact_count=len(artifacts),
        byte_count=sum(artifact.byte_count for artifact in artifacts),
        artifacts=artifacts,
    )
    _atomic_write_json(manifest_path, bundle.to_json_dict())
    return bundle


def read_source_candidate_external_probe_bundle_manifest(path: Path) -> dict[str, Any]:
    payload = _read_json_object(path)
    _expect_schema(payload, _BUNDLE_SCHEMA, path)
    return dict(payload)


def render_source_candidate_external_probe_bundle(bundle: SourceCandidateExternalProbeBundle) -> str:
    status = "PASS" if bundle.probe_allowed and bundle.read_only and not bundle.external_call_performed else "CHECK"
    lines = [
        f"external probe bundle: {status}",
        f"repository: {bundle.repository}",
        f"path: {bundle.path}",
        f"read_only: {bundle.read_only}",
        f"external_call_performed: {bundle.external_call_performed}",
        f"probe_allowed: {bundle.probe_allowed}",
        f"artifacts: {bundle.artifact_count}",
        f"bytes: {bundle.byte_count}",
    ]
    for artifact in bundle.artifacts:
        lines.append(f"- {artifact.role}: {artifact.path.name} ({artifact.byte_count} bytes)")
    return "\n".join(lines)


def _copy_json_artifact(
    *,
    source: Path,
    target: Path,
    role: str,
    schema: str,
    bundle_root: Path,
) -> SourceCandidateExternalProbeBundleArtifact:
    payload = _read_json_object(source)
    _expect_schema(payload, schema, source)
    _atomic_write_json(target, dict(payload))
    return SourceCandidateExternalProbeBundleArtifact(
        role=role,
        path=target,
        schema=schema,
        byte_count=target.stat().st_size,
    )


def _same_repository(*values: object) -> str:
    repositories = []
    for value in values:
        if isinstance(value, str) and value.strip():
            repositories.append(value)
    if not repositories:
        raise ValueError("missing repository")
    if len(set(repositories)) != 1:
        raise ValueError("repository mismatch across external probe bundle artifacts")
    return repositories[0]


def _expect_schema(payload: Mapping[str, Any], schema: str, path: Path) -> None:
    if payload.get("schema") != schema:
        raise ValueError(f"schema mismatch for {path}: expected {schema}")


def _read_json_object(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON payload must be an object: {path}")
    return payload


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
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
