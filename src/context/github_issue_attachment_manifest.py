"""GitHub issue attachment manifest contracts.

0170 records attachment references found in an external GitHub issue/ticket
body. It performs no GitHub API call and no remote mutation. GitHub Actions
artifacts remain the source system: this manifest is produced by the external
action as metadata, then the local server fetches the real files into the
configured server dataset before conversion.

The contract is data-only. It does not store user artifacts in the Autodoc
repository.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import re
from typing import Any, Iterable
from urllib.parse import unquote, urlparse


_MANIFEST_SCHEMA = "missipy.github_issue.attachment_manifest.v1"
_REFERENCE_SCHEMA = "missipy.github_issue.attachment_reference.v1"

_MARKDOWN_LINK_RE = re.compile(r"(!?)\[([^\]]*)\]\((https?://github\.com/user-attachments/[^\s)]+)\)")
_BARE_ATTACHMENT_RE = re.compile(r"(?<!\()https?://github\.com/user-attachments/[^\s)>'\"]+")

_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".heic", ".heif"}
_AUDIO_EXTENSIONS = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".opus"}
_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v"}
_PDF_EXTENSIONS = {".pdf"}
_ARCHIVE_EXTENSIONS = {".zip", ".tar", ".tgz", ".gz", ".bz2", ".xz", ".7z", ".rar"}
_TEXT_EXTENSIONS = {".txt", ".md", ".rst", ".csv", ".json", ".yaml", ".yml", ".toml", ".ini", ".log"}


@dataclass(frozen=True, slots=True)
class GitHubIssueAttachmentReference:
    url: str
    filename: str
    kind: str
    source: str = "github_issue_attachment_reference"
    label: str = ""
    raw_text: str = ""
    processed: bool = False

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": _REFERENCE_SCHEMA,
            "url": self.url,
            "filename": self.filename,
            "kind": self.kind,
            "source": self.source,
            "label": self.label,
            "raw_text": self.raw_text,
            "processed": self.processed,
        }


@dataclass(frozen=True, slots=True)
class GitHubIssueAttachmentManifest:
    repository: str
    issue_number: int
    issue_url: str
    origin_frame_id: str
    ticket_revision_id: str
    attachments: tuple[GitHubIssueAttachmentReference, ...]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "schema": _MANIFEST_SCHEMA,
            "repository": self.repository,
            "issue": {"number": self.issue_number, "url": self.issue_url},
            "origin_frame_id": self.origin_frame_id,
            "ticket_revision_id": self.ticket_revision_id,
            "attachments": [item.to_json_dict() for item in self.attachments],
            "counts": {"attachment_count": len(self.attachments)},
            "boundary": [
                "GitHub issue attachment references only",
                "no GitHub API call",
                "no remote mutation",
                "GitHub Actions artifacts remain the source system",
                "no user artifacts in Autodoc repository",
                "server fetch stores files in the configured server dataset before conversion",
            ],
        }


def build_github_issue_attachment_manifest(
    *,
    repository: str,
    issue_number: int,
    issue_url: str,
    body: str,
    origin_frame_id: str = "",
    ticket_revision_id: str = "",
) -> GitHubIssueAttachmentManifest:
    frame_id = origin_frame_id or f"github-frame:{repository}/issues/{issue_number}"
    revision_id = ticket_revision_id or f"github-ticket-revision:{_digest(frame_id + ':' + body)}"
    return GitHubIssueAttachmentManifest(
        repository=repository,
        issue_number=issue_number,
        issue_url=issue_url,
        origin_frame_id=frame_id,
        ticket_revision_id=revision_id,
        attachments=tuple(parse_github_issue_attachment_references(body)),
    )


def parse_github_issue_attachment_references(body: str) -> tuple[GitHubIssueAttachmentReference, ...]:
    """Parse GitHub issue attachment references without downloading files."""

    references: list[GitHubIssueAttachmentReference] = []
    seen: set[str] = set()

    for match in _MARKDOWN_LINK_RE.finditer(body):
        image_marker, label, url = match.groups()
        references.append(_build_reference(url=url, label=label, raw_text=match.group(0), image_hint=bool(image_marker)))
        seen.add(url)

    for match in _BARE_ATTACHMENT_RE.finditer(body):
        url = match.group(0).rstrip(".,;")
        if url in seen:
            continue
        references.append(_build_reference(url=url, label="", raw_text=match.group(0), image_hint=False))
        seen.add(url)

    return tuple(references)


def _build_reference(*, url: str, label: str, raw_text: str, image_hint: bool) -> GitHubIssueAttachmentReference:
    filename = _filename_from_label_or_url(label, url)
    kind = _kind_from_filename(filename, image_hint=image_hint)
    return GitHubIssueAttachmentReference(url=url, filename=filename, kind=kind, label=label, raw_text=raw_text)


def _filename_from_label_or_url(label: str, url: str) -> str:
    normalized_label = label.strip().strip("`")
    if _looks_like_filename(normalized_label):
        return _sanitize_filename(normalized_label)

    parsed = urlparse(url)
    path_name = unquote(PathLikeName(parsed.path).name)
    if _looks_like_filename(path_name):
        return _sanitize_filename(path_name)

    fallback = _digest(url)[:12]
    return f"github-attachment-{fallback}.bin"


def _kind_from_filename(filename: str, *, image_hint: bool) -> str:
    suffix = _suffix(filename)
    if suffix in _IMAGE_EXTENSIONS or image_hint:
        return "image"
    if suffix in _AUDIO_EXTENSIONS:
        return "audio"
    if suffix in _VIDEO_EXTENSIONS:
        return "video"
    if suffix in _PDF_EXTENSIONS:
        return "pdf"
    if suffix in _ARCHIVE_EXTENSIONS:
        return "archive"
    if suffix in _TEXT_EXTENSIONS:
        return "text"
    return "binary"


def _looks_like_filename(value: str) -> bool:
    stripped = value.strip()
    return bool(stripped and "." in stripped and "/" not in stripped and "\\" not in stripped)


def _sanitize_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return cleaned.strip("._") or "attachment.bin"


def _suffix(filename: str) -> str:
    lowered = filename.lower()
    for extension in sorted(_ARCHIVE_EXTENSIONS | _IMAGE_EXTENSIONS | _AUDIO_EXTENSIONS | _VIDEO_EXTENSIONS | _PDF_EXTENSIONS | _TEXT_EXTENSIONS, key=len, reverse=True):
        if lowered.endswith(extension):
            return extension
    return ""


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class PathLikeName:
    def __init__(self, path: str) -> None:
        self.path = path

    @property
    def name(self) -> str:
        parts = [part for part in self.path.split("/") if part]
        return parts[-1] if parts else ""
