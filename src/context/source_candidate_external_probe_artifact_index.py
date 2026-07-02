from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import json
import os
import tempfile


_INDEX_SCHEMA = "missipy.source_candidate.external_probe_artifact_index.v1"
_ENTRY_SCHEMA = "missipy.source_candidate.external_probe_artifact_index_entry.v1"
_BUNDLE_SCHEMA = "missipy.source_candidate.external_probe_bundle.v1"


@dataclass(frozen=True)
class SourceCandidateExternalProbeArtifactIndexEntry:
    bundle_path: Path
    manifest_path: Path
    repository: str
    read_only: bool
    external_call_performed: bool
    probe_allowed: bool
    artifact_count: int
    byte_count: int

    def to_json_dict(self, root: Path) -> dict[str, object]:
        return {
            "schema": _ENTRY_SCHEMA,
            "bundle_path": self.bundle_path.resolve().relative_to(root.resolve()).as_posix(),
            "manifest_path": self.manifest_path.resolve().relative_to(root.resolve()).as_posix(),
            "repository": self.repository,
            "read_only": self.read_only,
            "external_call_performed": self.external_call_performed,
            "probe_allowed": self.probe_allowed,
            "artifact_count": self.artifact_count,
            "byte_count": self.byte_count,
        }


@dataclass(frozen=True)
class SourceCandidateExternalProbeArtifactIndex:
    root: Path
    scan_root: Path
    bundle_count: int
    total_artifact_count: int
    total_byte_count: int
    entries: tuple[SourceCandidateExternalProbeArtifactIndexEntry, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _INDEX_SCHEMA,
            "root": str(self.root),
            "scan_root": str(self.scan_root),
            "bundle_count": self.bundle_count,
            "total_artifact_count": self.total_artifact_count,
            "total_byte_count": self.total_byte_count,
            "entries": [entry.to_json_dict(self.root) for entry in self.entries],
        }


def build_source_candidate_external_probe_artifact_index(
    root: Path,
    *,
    scan_root: Path,
) -> SourceCandidateExternalProbeArtifactIndex:
    """Build a local index of SourceCandidate external probe bundles."""

    root = root.resolve()
    resolved_scan_root = scan_root if scan_root.is_absolute() else root / scan_root
    resolved_scan_root = resolved_scan_root.resolve()

    entries: list[SourceCandidateExternalProbeArtifactIndexEntry] = []
    if resolved_scan_root.exists():
        for manifest_path in sorted(resolved_scan_root.rglob("manifest.json")):
            payload = _try_read_json_object(manifest_path)
            if payload is None or payload.get("schema") != _BUNDLE_SCHEMA:
                continue
            entries.append(_entry_from_manifest(root, manifest_path, payload))

    return SourceCandidateExternalProbeArtifactIndex(
        root=root,
        scan_root=resolved_scan_root,
        bundle_count=len(entries),
        total_artifact_count=sum(entry.artifact_count for entry in entries),
        total_byte_count=sum(entry.byte_count for entry in entries),
        entries=tuple(entries),
    )


def write_source_candidate_external_probe_artifact_index(
    path: Path,
    index: SourceCandidateExternalProbeArtifactIndex,
) -> Path:
    _atomic_write_json(path, index.to_json_dict())
    return path


def read_source_candidate_external_probe_artifact_index(path: Path) -> dict[str, Any]:
    payload = _read_json_object(path)
    if payload.get("schema") != _INDEX_SCHEMA:
        raise ValueError("external probe artifact index schema mismatch")
    return dict(payload)


def render_source_candidate_external_probe_artifact_index(
    index: SourceCandidateExternalProbeArtifactIndex,
) -> str:
    lines = [
        "external probe artifact index",
        f"root: {index.root}",
        f"scan_root: {index.scan_root}",
        f"bundle_count: {index.bundle_count}",
        f"total_artifact_count: {index.total_artifact_count}",
        f"total_byte_count: {index.total_byte_count}",
    ]
    for entry in index.entries:
        status = "PASS" if entry.read_only and not entry.external_call_performed and entry.probe_allowed else "CHECK"
        lines.append(
            f"- {status}: {entry.repository} "
            f"{entry.bundle_path.relative_to(index.root).as_posix()} "
            f"artifacts={entry.artifact_count} bytes={entry.byte_count}"
        )
    return "\n".join(lines)


def _entry_from_manifest(
    root: Path,
    manifest_path: Path,
    payload: Mapping[str, Any],
) -> SourceCandidateExternalProbeArtifactIndexEntry:
    bundle_path = _path_from_payload(payload.get("path"), fallback=manifest_path.parent)
    if not bundle_path.is_absolute():
        bundle_path = (root / bundle_path).resolve()

    return SourceCandidateExternalProbeArtifactIndexEntry(
        bundle_path=bundle_path,
        manifest_path=manifest_path.resolve(),
        repository=_string(payload.get("repository"), default="<unknown>"),
        read_only=bool(payload.get("read_only")),
        external_call_performed=bool(payload.get("external_call_performed")),
        probe_allowed=bool(payload.get("probe_allowed")),
        artifact_count=_int(payload.get("artifact_count")),
        byte_count=_int(payload.get("byte_count")),
    )


def _path_from_payload(raw: object, *, fallback: Path) -> Path:
    if isinstance(raw, str) and raw.strip():
        return Path(raw)
    return fallback


def _try_read_json_object(path: Path) -> Mapping[str, Any] | None:
    try:
        return _read_json_object(path)
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def _read_json_object(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"JSON payload must be an object: {path}")
    return payload


def _string(raw: object, *, default: str) -> str:
    if isinstance(raw, str) and raw.strip():
        return raw
    return default


def _int(raw: object) -> int:
    if isinstance(raw, int):
        return raw
    return 0


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
