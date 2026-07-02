from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping
import json
import os
import tempfile

from .source_candidate_github_adapter import FakeSourceCandidateGithubProjectionAdapter
from .source_candidate_remote_mutation_gate import (
    SourceCandidateRemoteMutationGatePolicy,
    run_source_candidate_remote_mutation_gate,
)


_BUNDLE_SCHEMA = "missipy.source_candidate.github_export_bundle.v1"


@dataclass(frozen=True)
class SourceCandidateGithubExportBundlePolicy:
    """Local GitHub export bundle policy.

    The bundle is a local inspection artifact. It does not contact GitHub and it
    does not perform remote mutation.
    """

    path: Path
    contract_name: str = "external_projection_contract.json"
    payload_name: str = "github_projection_payload.json"
    gate_name: str = "remote_mutation_gate.json"
    adapter_dry_run_name: str = "github_adapter_dry_run.json"
    manifest_name: str = "manifest.json"
    gate_policy: SourceCandidateRemoteMutationGatePolicy = SourceCandidateRemoteMutationGatePolicy()


@dataclass(frozen=True)
class SourceCandidateGithubExportBundleArtifact:
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
class SourceCandidateGithubExportBundle:
    path: Path
    manifest_path: Path
    repository: str | None
    mutation_allowed: bool
    dry_run: bool
    operation_count: int
    artifact_count: int
    byte_count: int
    artifacts: tuple[SourceCandidateGithubExportBundleArtifact, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _BUNDLE_SCHEMA,
            "path": str(self.path),
            "manifest_path": str(self.manifest_path),
            "repository": self.repository,
            "mutation_allowed": self.mutation_allowed,
            "dry_run": self.dry_run,
            "operation_count": self.operation_count,
            "artifact_count": self.artifact_count,
            "byte_count": self.byte_count,
            "artifacts": [artifact.to_json_dict() for artifact in self.artifacts],
        }


def build_source_candidate_github_export_bundle(
    *,
    contract_path: Path,
    github_payload_path: Path,
    policy: SourceCandidateGithubExportBundlePolicy,
) -> SourceCandidateGithubExportBundle:
    """Build a local GitHub export bundle for operator inspection."""

    _validate_policy(policy)
    policy.path.mkdir(parents=True, exist_ok=True)

    contract_target = policy.path / policy.contract_name
    payload_target = policy.path / policy.payload_name
    gate_target = policy.path / policy.gate_name
    adapter_dry_run_target = policy.path / policy.adapter_dry_run_name
    manifest_path = policy.path / policy.manifest_name

    _copy_text(contract_path, contract_target)
    _copy_text(github_payload_path, payload_target)

    payload = _read_json_object(payload_target)
    gate = run_source_candidate_remote_mutation_gate(payload, policy.gate_policy)
    _atomic_write_json(gate_target, gate.to_json_dict())

    adapter = FakeSourceCandidateGithubProjectionAdapter()
    adapter_dry_run = adapter.dry_run(payload, policy.gate_policy)
    _atomic_write_json(adapter_dry_run_target, adapter_dry_run.to_json_dict())

    artifacts = (
        _artifact("external_projection_contract", contract_target),
        _artifact("github_projection_payload", payload_target),
        _artifact("remote_mutation_gate", gate_target),
        _artifact("github_adapter_dry_run", adapter_dry_run_target),
    )

    manifest_payload = {
        "schema": _BUNDLE_SCHEMA,
        "path": str(policy.path),
        "manifest_path": str(manifest_path),
        "repository": _optional_string(payload.get("repository")),
        "mutation_allowed": gate.mutation_allowed,
        "dry_run": bool(payload.get("dry_run")),
        "operation_count": gate.operation_count,
        "artifact_count": len(artifacts),
        "byte_count": sum(artifact.byte_count for artifact in artifacts),
        "artifacts": [artifact.to_json_dict() for artifact in artifacts],
    }
    _atomic_write_json(manifest_path, manifest_payload)

    all_artifacts = (_artifact("manifest", manifest_path), *artifacts)
    return SourceCandidateGithubExportBundle(
        path=policy.path,
        manifest_path=manifest_path,
        repository=_optional_string(payload.get("repository")),
        mutation_allowed=gate.mutation_allowed,
        dry_run=bool(payload.get("dry_run")),
        operation_count=gate.operation_count,
        artifact_count=len(all_artifacts),
        byte_count=sum(artifact.byte_count for artifact in all_artifacts),
        artifacts=all_artifacts,
    )


def read_source_candidate_github_export_bundle_manifest(path: Path) -> dict[str, Any]:
    payload = _read_json_object(path)
    if payload.get("schema") != _BUNDLE_SCHEMA:
        raise ValueError("GitHub export bundle manifest schema mismatch")
    return dict(payload)


def _validate_policy(policy: SourceCandidateGithubExportBundlePolicy) -> None:
    names = (
        policy.contract_name,
        policy.payload_name,
        policy.gate_name,
        policy.adapter_dry_run_name,
        policy.manifest_name,
    )
    if any(not name.strip() for name in names):
        raise ValueError("bundle artifact names must not be empty")
    if len(set(names)) != len(names):
        raise ValueError("bundle artifact names must be distinct")


def _copy_text(source: Path, target: Path) -> None:
    _atomic_write_text(target, source.read_text(encoding="utf-8"))


def _artifact(role: str, path: Path) -> SourceCandidateGithubExportBundleArtifact:
    schema: str | None = None
    if path.suffix == ".json":
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            payload = None
        if isinstance(payload, Mapping) and isinstance(payload.get("schema"), str):
            schema = payload["schema"]
    return SourceCandidateGithubExportBundleArtifact(
        role=role,
        path=path,
        byte_count=path.stat().st_size,
        schema=schema,
    )


def _read_json_object(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON payload must be an object: {path}")
    return payload


def _optional_string(raw: object) -> str | None:
    if isinstance(raw, str) and raw.strip():
        return raw
    return None


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
