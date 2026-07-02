from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .source_candidate_operator_report import SourceCandidateOperatorReportResult
from .source_candidate_operator_report_file import (
    SourceCandidateOperatorReportFilePolicy,
    write_source_candidate_operator_report_file,
)

_BUNDLE_SCHEMA = "missipy.source_candidate.operator_bundle.v1"


@dataclass(frozen=True, slots=True)
class SourceCandidateOperatorBundlePolicy:
    """Politique d'écriture locale d'un bundle opérateur SourceCandidate."""

    path: Path | str
    include_json: bool = True
    include_text: bool = True
    manifest_name: str = "manifest.json"
    json_name: str = "operator_report.json"
    text_name: str = "operator_report.txt"

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", Path(self.path))
        if not self.include_json and not self.include_text:
            raise ValueError("at least one report artifact must be enabled")
        for name in (self.manifest_name, self.json_name, self.text_name):
            _validate_relative_name(name)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "path": str(self.path),
            "include_json": self.include_json,
            "include_text": self.include_text,
            "manifest_name": self.manifest_name,
            "json_name": self.json_name,
            "text_name": self.text_name,
        }


@dataclass(frozen=True, slots=True)
class SourceCandidateOperatorBundleArtifact:
    """Fichier local produit dans un bundle opérateur."""

    role: str
    path: Path | str
    output_format: str
    byte_count: int

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", Path(self.path))
        if self.byte_count < 0:
            raise ValueError("byte_count must be >= 0")

    def to_json_dict(self) -> dict[str, object]:
        return {
            "role": self.role,
            "path": str(self.path),
            "output_format": self.output_format,
            "byte_count": self.byte_count,
        }


@dataclass(frozen=True, slots=True)
class SourceCandidateOperatorBundleResult:
    """Résultat stable de création d'un bundle opérateur local."""

    path: Path | str
    manifest_path: Path | str
    artifacts: tuple[SourceCandidateOperatorBundleArtifact, ...]
    report: SourceCandidateOperatorReportResult
    policy: SourceCandidateOperatorBundlePolicy

    def __post_init__(self) -> None:
        object.__setattr__(self, "path", Path(self.path))
        object.__setattr__(self, "manifest_path", Path(self.manifest_path))
        if not isinstance(self.artifacts, tuple):
            object.__setattr__(self, "artifacts", tuple(self.artifacts))

    @property
    def artifact_count(self) -> int:
        return len(self.artifacts)

    @property
    def byte_count(self) -> int:
        return sum(artifact.byte_count for artifact in self.artifacts)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _BUNDLE_SCHEMA,
            "path": str(self.path),
            "manifest_path": str(self.manifest_path),
            "artifact_count": self.artifact_count,
            "byte_count": self.byte_count,
            "report_schema": "missipy.source_candidate.operator_report.v1",
            "returned_count": self.report.returned_count,
            "actionable_count": self.report.actionable_count,
            "audit_present_count": self.report.audit_present_count,
            "artifacts": [artifact.to_json_dict() for artifact in self.artifacts],
            "policy": self.policy.to_json_dict(),
        }

    def to_text(self) -> str:
        lines = [
            "SourceCandidate operator bundle",
            f"path: {self.path}",
            f"manifest: {self.manifest_path}",
            f"artifacts: {self.artifact_count}",
            f"bytes: {self.byte_count}",
            f"returned: {self.report.returned_count}",
            f"actionable: {self.report.actionable_count}",
            f"audits: {self.report.audit_present_count}",
        ]
        for artifact in self.artifacts:
            lines.append(f"- {artifact.role}: {artifact.path} ({artifact.byte_count} bytes)")
        return "\n".join(lines)


def write_source_candidate_operator_bundle(
    report: SourceCandidateOperatorReportResult,
    policy: SourceCandidateOperatorBundlePolicy,
) -> SourceCandidateOperatorBundleResult:
    """Écrit un bundle opérateur local avec rapport JSON/texte et manifeste."""
    path = Path(policy.path)
    path.mkdir(parents=True, exist_ok=True)
    artifacts: list[SourceCandidateOperatorBundleArtifact] = []

    if policy.include_json:
        written = write_source_candidate_operator_report_file(
            report,
            SourceCandidateOperatorReportFilePolicy(path / policy.json_name, "json"),
        )
        artifacts.append(
            SourceCandidateOperatorBundleArtifact(
                role="operator_report_json",
                path=written.path,
                output_format="json",
                byte_count=written.byte_count,
            )
        )

    if policy.include_text:
        written = write_source_candidate_operator_report_file(
            report,
            SourceCandidateOperatorReportFilePolicy(path / policy.text_name, "text"),
        )
        artifacts.append(
            SourceCandidateOperatorBundleArtifact(
                role="operator_report_text",
                path=written.path,
                output_format="text",
                byte_count=written.byte_count,
            )
        )

    result = SourceCandidateOperatorBundleResult(
        path=path,
        manifest_path=path / policy.manifest_name,
        artifacts=tuple(artifacts),
        report=report,
        policy=policy,
    )
    _atomic_write_json(Path(result.manifest_path), result.to_json_dict())
    return result


def _atomic_write_json(path: Path, payload: dict[str, object]) -> None:
    content = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    )
    tmp_path = Path(handle.name)
    try:
        with handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _validate_relative_name(name: str) -> None:
    if not name or name in (".", ".."):
        raise ValueError("artifact names must be non-empty relative file names")
    candidate = Path(name)
    if candidate.is_absolute() or len(candidate.parts) != 1 or ".." in candidate.parts:
        raise ValueError("artifact names must be simple relative file names")
