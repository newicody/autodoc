"""Server dataset contracts for GitHub Actions artifact fetch/sync.

0167 invariant: conversion is queued only after complete sync.

0167 keeps user data out of the Autodoc development repository. GitHub Actions
artifacts and their attachments are synchronized by the server into a configured
server dataset. Conversion is queued only after the raw artifact sync is complete.

This module is data-only and stdlib-only. It does not call GitHub, does not
mutate remote state, and does not write SQL or qdrant.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from pathlib import Path
from typing import Any, Mapping


_DATASET_CONFIG_SCHEMA = "missipy.github_artifact.server_dataset_config.v1"
_FETCH_RECORD_SCHEMA = "missipy.github_artifact.server_fetch_record.v1"
_ATTACHMENT_RECORD_SCHEMA = "missipy.github_artifact.attachment_record.v1"
_SYNC_REPORT_SCHEMA = "missipy.github_artifact.server_dataset_sync_report.v1"
_QUEUE_RECORD_SCHEMA = "missipy.github_artifact.conversion_queue_record.v1"


@dataclass(frozen=True, slots=True)
class ServerDatasetLayout:
    root: Path
    raw_dir: str = "raw"
    index_dir: str = "index"
    history_dir: str = "history"
    conversion_queue_dir: str = "conversion_queue"
    converted_dir: str = "converted"
    vispy_events_dir: str = "vispy_events"
    state_file: str = "index/fetch_state.json"

    @property
    def raw_path(self) -> Path:
        return self.root / self.raw_dir

    @property
    def index_path(self) -> Path:
        return self.root / self.index_dir

    @property
    def history_path(self) -> Path:
        return self.root / self.history_dir

    @property
    def conversion_queue_path(self) -> Path:
        return self.root / self.conversion_queue_dir

    @property
    def converted_path(self) -> Path:
        return self.root / self.converted_dir

    @property
    def vispy_events_path(self) -> Path:
        return self.root / self.vispy_events_dir

    @property
    def state_path(self) -> Path:
        return self.root / self.state_file

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": _DATASET_CONFIG_SCHEMA,
            "root": str(self.root),
            "raw_dir": self.raw_dir,
            "index_dir": self.index_dir,
            "history_dir": self.history_dir,
            "conversion_queue_dir": self.conversion_queue_dir,
            "converted_dir": self.converted_dir,
            "vispy_events_dir": self.vispy_events_dir,
            "state_file": self.state_file,
        }


@dataclass(frozen=True, slots=True)
class GitHubFetchedArtifactRecord:
    repository: str
    artifact_name: str
    artifact_id: str
    run_id: str
    origin_frame_id: str
    ticket_revision_id: str
    raw_dataset_ref: str
    sha256: str
    byte_count: int
    files: tuple[str, ...]
    status: str = "synced"

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": _FETCH_RECORD_SCHEMA,
            "repository": self.repository,
            "artifact_name": self.artifact_name,
            "artifact_id": self.artifact_id,
            "run_id": self.run_id,
            "origin_frame_id": self.origin_frame_id,
            "ticket_revision_id": self.ticket_revision_id,
            "raw_dataset_ref": self.raw_dataset_ref,
            "sha256": self.sha256,
            "byte_count": self.byte_count,
            "files": list(self.files),
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class AttachmentRecord:
    filename: str
    kind: str
    source: str
    raw_dataset_ref: str
    sha256: str
    byte_count: int
    processed: bool = False

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": _ATTACHMENT_RECORD_SCHEMA,
            "filename": self.filename,
            "kind": self.kind,
            "source": self.source,
            "raw_dataset_ref": self.raw_dataset_ref,
            "sha256": self.sha256,
            "byte_count": self.byte_count,
            "processed": self.processed,
        }


@dataclass(frozen=True, slots=True)
class ConversionQueueRecord:
    queue_ref: str
    origin_frame_id: str
    ticket_revision_id: str
    raw_dataset_ref: str
    kind: str
    sha256: str
    status: str = "pending"

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": _QUEUE_RECORD_SCHEMA,
            "queue_ref": self.queue_ref,
            "origin_frame_id": self.origin_frame_id,
            "ticket_revision_id": self.ticket_revision_id,
            "raw_dataset_ref": self.raw_dataset_ref,
            "kind": self.kind,
            "sha256": self.sha256,
            "status": self.status,
        }


@dataclass(frozen=True, slots=True)
class ServerDatasetSyncReport:
    repository: str
    origin_frame_id: str
    ticket_revision_id: str
    artifact_record: GitHubFetchedArtifactRecord
    attachments: tuple[AttachmentRecord, ...] = field(default_factory=tuple)
    queue_records: tuple[ConversionQueueRecord, ...] = field(default_factory=tuple)
    vispy_event_path: str = ""
    status: str = "ok"

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": _SYNC_REPORT_SCHEMA,
            "status": self.status,
            "repository": self.repository,
            "origin_frame_id": self.origin_frame_id,
            "ticket_revision_id": self.ticket_revision_id,
            "artifact_record": self.artifact_record.to_json_dict(),
            "attachments": [attachment.to_json_dict() for attachment in self.attachments],
            "queue_records": [record.to_json_dict() for record in self.queue_records],
            "counts": {
                "attachment_count": len(self.attachments),
                "queued_count": len(self.queue_records),
            },
            "vispy_event_path": self.vispy_event_path,
            "boundary": [
                "GitHub Actions artifacts remain the source system",
                "raw files are stored in the configured server dataset",
                "conversion is queued only after complete raw sync",
                "no repository user-data storage",
                "no remote mutation",
            ],
        }


def infer_attachment_kind(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    if suffix in {"jpg", "jpeg", "png", "gif", "webp", "heic", "tif", "tiff"}:
        return "image"
    if suffix in {"mp3", "wav", "flac", "ogg", "m4a"}:
        return "audio"
    if suffix in {"mp4", "mov", "mkv", "webm", "avi"}:
        return "video"
    if suffix == "pdf":
        return "pdf"
    if suffix in {"zip", "tar", "gz", "xz", "7z", "rar"}:
        return "archive"
    if suffix in {"txt", "md", "rst", "json", "yaml", "yml", "csv"}:
        return "text"
    return "binary"


def build_raw_dataset_ref(repository: str, run_id: str, artifact_id: str, relative_path: str) -> str:
    normalized_repo = repository.replace("/", "__")
    return f"server-dataset:github-artifacts/raw/{normalized_repo}/{run_id}/{artifact_id}/{relative_path}"


def build_conversion_queue_ref(raw_dataset_ref: str, sha256: str) -> str:
    return f"server-dataset:github-artifacts/conversion-queue/{_digest(raw_dataset_ref + ':' + sha256)}"


def hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
