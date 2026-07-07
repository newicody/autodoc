"""Server-side attachment reference fetch contracts.

0171 resolves GitHub issue attachment references after GitHub Actions artifact
fetch. The raw referenced files are copied into the configured server dataset;
conversion is queued only after the referenced file is present locally.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from pathlib import Path
from typing import Any, Mapping

_SCHEMA_REFERENCE = "missipy.github_attachment.reference.v1"
_SCHEMA_FETCH_RECORD = "missipy.github_attachment.reference_fetch_record.v1"
_SCHEMA_QUEUE_RECORD = "missipy.github_attachment.reference_conversion_queue_record.v1"
_SCHEMA_REPORT = "missipy.github_attachment.reference_fetch_report.v1"

_IMAGE_EXTENSIONS = {".avif", ".bmp", ".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"}
_AUDIO_EXTENSIONS = {".aac", ".flac", ".m4a", ".mp3", ".ogg", ".opus", ".wav"}
_VIDEO_EXTENSIONS = {".avi", ".m4v", ".mkv", ".mov", ".mp4", ".mpeg", ".mpg", ".webm"}
_ARCHIVE_EXTENSIONS = {".7z", ".bz2", ".gz", ".rar", ".tar", ".tgz", ".xz", ".zip", ".zst"}
_TEXT_EXTENSIONS = {".csv", ".json", ".log", ".md", ".rst", ".toml", ".txt", ".xml", ".yaml", ".yml"}


@dataclass(frozen=True)
class GitHubAttachmentReference:
    """Reference to an attachment listed by a GitHub Actions artifact manifest."""

    url: str
    filename: str
    kind: str
    source: str = "github_issue_attachment_reference"
    content_type: str = ""
    expected_sha256: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": _SCHEMA_REFERENCE,
            "url": self.url,
            "filename": self.filename,
            "kind": self.kind,
            "source": self.source,
            "content_type": self.content_type,
            "expected_sha256": self.expected_sha256,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class GitHubAttachmentFetchRecord:
    """Local server dataset record for a fetched attachment reference."""

    reference: GitHubAttachmentReference
    repository: str
    run_id: str
    artifact_id: str
    origin_frame_id: str
    ticket_revision_id: str
    raw_dataset_ref: str
    local_path: str
    sha256: str
    byte_count: int
    status: str
    message: str = ""

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": _SCHEMA_FETCH_RECORD,
            "reference": self.reference.to_json_dict(),
            "repository": self.repository,
            "run_id": self.run_id,
            "artifact_id": self.artifact_id,
            "origin_frame_id": self.origin_frame_id,
            "ticket_revision_id": self.ticket_revision_id,
            "raw_dataset_ref": self.raw_dataset_ref,
            "local_path": self.local_path,
            "sha256": self.sha256,
            "byte_count": self.byte_count,
            "status": self.status,
            "message": self.message,
        }


@dataclass(frozen=True)
class GitHubAttachmentConversionQueueRecord:
    """Queue record produced only after an attachment was fetched into raw dataset."""

    raw_dataset_ref: str
    sha256: str
    kind: str
    origin_frame_id: str
    ticket_revision_id: str
    status: str = "pending"

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": _SCHEMA_QUEUE_RECORD,
            "queue_ref": build_attachment_conversion_queue_ref(self.raw_dataset_ref, self.sha256),
            "raw_dataset_ref": self.raw_dataset_ref,
            "sha256": self.sha256,
            "kind": self.kind,
            "origin_frame_id": self.origin_frame_id,
            "ticket_revision_id": self.ticket_revision_id,
            "status": self.status,
        }


@dataclass(frozen=True)
class GitHubAttachmentReferenceFetchReport:
    """Report for one attachment-reference fetch pass."""

    repository: str
    run_id: str
    artifact_id: str
    origin_frame_id: str
    ticket_revision_id: str
    records: tuple[GitHubAttachmentFetchRecord, ...]
    queue_records: tuple[GitHubAttachmentConversionQueueRecord, ...]
    vispy_event_path: str
    status: str

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": _SCHEMA_REPORT,
            "status": self.status,
            "repository": self.repository,
            "run_id": self.run_id,
            "artifact_id": self.artifact_id,
            "origin_frame_id": self.origin_frame_id,
            "ticket_revision_id": self.ticket_revision_id,
            "counts": {
                "reference_count": len(self.records),
                "fetched_count": sum(1 for record in self.records if record.status == "fetched"),
                "queued_count": len(self.queue_records),
                "failed_count": sum(1 for record in self.records if record.status != "fetched"),
            },
            "records": [record.to_json_dict() for record in self.records],
            "queue_records": [record.to_json_dict() for record in self.queue_records],
            "vispy_event_path": self.vispy_event_path,
            "boundary": [
                "GitHub issue attachment references only",
                "raw attachment bytes are stored in the configured server dataset",
                "conversion is queued only after attachment fetch completes",
                "no user artifacts in Autodoc repository",
                "no remote mutation",
            ],
        }


def attachment_kind_from_filename(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix in _IMAGE_EXTENSIONS:
        return "image"
    if suffix in _AUDIO_EXTENSIONS:
        return "audio"
    if suffix in _VIDEO_EXTENSIONS:
        return "video"
    if suffix == ".pdf":
        return "pdf"
    if suffix in _ARCHIVE_EXTENSIONS:
        return "archive"
    if suffix in _TEXT_EXTENSIONS:
        return "text"
    return "binary"


def safe_attachment_filename(value: str, fallback: str = "attachment.bin") -> str:
    name = Path(value.split("?", 1)[0].rstrip("/")).name or fallback
    safe = "".join(char if char.isalnum() or char in {".", "-", "_"} else "_" for char in name)
    if safe in {"", ".", ".."}:
        return fallback
    return safe


def attachment_reference_from_mapping(payload: Mapping[str, Any], index: int = 0) -> GitHubAttachmentReference:
    url = str(payload.get("url") or payload.get("source_url") or payload.get("href") or "")
    filename = str(payload.get("filename") or payload.get("name") or safe_attachment_filename(url, f"attachment-{index}.bin"))
    filename = safe_attachment_filename(filename, f"attachment-{index}.bin")
    kind = str(payload.get("kind") or attachment_kind_from_filename(filename))
    return GitHubAttachmentReference(
        url=url,
        filename=filename,
        kind=kind,
        source=str(payload.get("source") or "github_issue_attachment_reference"),
        content_type=str(payload.get("content_type") or payload.get("mime_type") or ""),
        expected_sha256=str(payload.get("sha256") or payload.get("expected_sha256") or ""),
        metadata={key: value for key, value in payload.items() if key not in {"url", "source_url", "href", "filename", "name", "kind", "source", "content_type", "mime_type", "sha256", "expected_sha256"}},
    )


def extract_attachment_references(manifest: Mapping[str, Any]) -> tuple[GitHubAttachmentReference, ...]:
    raw_items = manifest.get("attachments") or manifest.get("references") or []
    if isinstance(raw_items, Mapping):
        raw_items = raw_items.get("items", [])
    references: list[GitHubAttachmentReference] = []
    for index, item in enumerate(raw_items):
        if isinstance(item, Mapping):
            references.append(attachment_reference_from_mapping(item, index=index))
    return tuple(references)


def build_attachment_raw_dataset_ref(repository: str, run_id: str, artifact_id: str, filename: str) -> str:
    normalized_repo = repository.replace("/", "__")
    return f"server-dataset:github-artifacts/raw/{normalized_repo}/{run_id}/{artifact_id}/attachments/{safe_attachment_filename(filename)}"


def build_attachment_conversion_queue_ref(raw_dataset_ref: str, sha256: str) -> str:
    return f"server-dataset:github-artifacts/conversion-queue/{_digest(raw_dataset_ref + ':' + sha256)}"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]
