from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence
import json
import os
import tempfile


_CLOSURE_SCHEMA = "missipy.source_candidate.phase7_closure_report.v1"


DEFAULT_PHASE7_CLOSURE_ARTIFACTS: tuple[str, ...] = (
    "README.md",
    "src/context/source_candidate_external_projection_contract.py",
    "src/context/source_candidate_github_projection_payload.py",
    "src/context/source_candidate_remote_mutation_gate.py",
    "src/context/source_candidate_github_adapter.py",
    "src/context/source_candidate_github_export_bundle.py",
    "src/context/source_candidate_operator_external_review_report.py",
    "src/context/source_candidate_read_only_external_probe.py",
    "src/context/source_candidate_external_probe_bundle.py",
    "src/context/source_candidate_external_probe_artifact_index.py",
    "src/context/source_candidate_external_probe_operator_summary.py",
    "src/context/source_candidate_external_probe_local_audit_trail.py",
    "src/context/source_candidate_external_probe_local_replay.py",
    "tools/source_candidate_external_probe_bundle_cli.py",
    "tools/source_candidate_external_probe_artifact_index_cli.py",
    "tools/source_candidate_external_probe_operator_summary_cli.py",
    "tools/source_candidate_external_probe_local_audit_trail_cli.py",
    "tools/source_candidate_external_probe_local_replay_cli.py",
    "tools/docs_svg_build_policy.py",
    "doc/runbooks/SOURCE_CANDIDATE_EXTERNAL_PROBE_BUNDLE_RUNBOOK.md",
    "doc/maintenance/DOCS_SVG_BUILD_POLICY.md",
)


@dataclass(frozen=True)
class SourceCandidatePhase7ClosureArtifact:
    path: str
    exists: bool

    def to_json_dict(self) -> dict[str, object]:
        return {
            "path": self.path,
            "exists": self.exists,
        }


@dataclass(frozen=True)
class SourceCandidatePhase7ClosureReport:
    root: Path
    phase: str
    status: str
    artifact_count: int
    missing_count: int
    local_only: bool
    remote_mutation_enabled: bool
    scheduler_modified: bool
    network_enabled: bool
    next_phase: str
    artifacts: tuple[SourceCandidatePhase7ClosureArtifact, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _CLOSURE_SCHEMA,
            "root": str(self.root),
            "phase": self.phase,
            "status": self.status,
            "artifact_count": self.artifact_count,
            "missing_count": self.missing_count,
            "local_only": self.local_only,
            "remote_mutation_enabled": self.remote_mutation_enabled,
            "scheduler_modified": self.scheduler_modified,
            "network_enabled": self.network_enabled,
            "next_phase": self.next_phase,
            "artifacts": [artifact.to_json_dict() for artifact in self.artifacts],
        }


def build_source_candidate_phase7_closure_report(
    root: Path,
    *,
    required_artifacts: Sequence[str] = DEFAULT_PHASE7_CLOSURE_ARTIFACTS,
) -> SourceCandidatePhase7ClosureReport:
    root = root.resolve()
    artifacts = tuple(
        SourceCandidatePhase7ClosureArtifact(
            path=artifact_path,
            exists=(root / artifact_path).exists(),
        )
        for artifact_path in required_artifacts
    )
    missing_count = sum(1 for artifact in artifacts if not artifact.exists)

    return SourceCandidatePhase7ClosureReport(
        root=root,
        phase="7",
        status="closed" if missing_count == 0 else "incomplete",
        artifact_count=len(artifacts),
        missing_count=missing_count,
        local_only=True,
        remote_mutation_enabled=False,
        scheduler_modified=False,
        network_enabled=False,
        next_phase="8",
        artifacts=artifacts,
    )


def write_source_candidate_phase7_closure_report(
    path: Path,
    report: SourceCandidatePhase7ClosureReport,
) -> Path:
    _atomic_write_json(path, report.to_json_dict())
    return path


def read_source_candidate_phase7_closure_report(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("phase 7 closure report must be a JSON object")
    if payload.get("schema") != _CLOSURE_SCHEMA:
        raise ValueError("phase 7 closure report schema mismatch")
    return payload


def render_source_candidate_phase7_closure_report(
    report: SourceCandidatePhase7ClosureReport,
) -> str:
    lines = [
        "source candidate phase 7 closure report",
        f"root: {report.root}",
        f"phase: {report.phase}",
        f"status: {report.status}",
        f"artifact_count: {report.artifact_count}",
        f"missing_count: {report.missing_count}",
        f"local_only: {report.local_only}",
        f"remote_mutation_enabled: {report.remote_mutation_enabled}",
        f"scheduler_modified: {report.scheduler_modified}",
        f"network_enabled: {report.network_enabled}",
        f"next_phase: {report.next_phase}",
    ]
    for artifact in report.artifacts:
        marker = "ok" if artifact.exists else "missing"
        lines.append(f"- {marker}: {artifact.path}")
    return "\n".join(lines)


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
