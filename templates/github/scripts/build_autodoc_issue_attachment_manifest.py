#!/usr/bin/env python3
"""Standalone external-repository attachment manifest builder.

Copy this file to `scripts/build_autodoc_issue_attachment_manifest.py` in the
external idea repository. It intentionally has no Autodoc import, no GitHub
API call, and no remote mutation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.parse import unquote, urlparse


MARKDOWN_LINK_RE = re.compile(r"(!?)\[([^\]]*)\]\((https?://github\.com/user-attachments/[^\s)]+)\)")
BARE_ATTACHMENT_RE = re.compile(r"(?<!\()https?://github\.com/user-attachments/[^\s)>'\"]+")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--event-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("out/autodoc-artifacts"))
    args = parser.parse_args()
    event = json.loads(args.event_path.read_text(encoding="utf-8"))
    issue = event.get("issue") or {}
    repository = (event.get("repository") or {}).get("full_name", "")
    body = issue.get("body") or ""
    origin_frame_id = f"github-frame:{repository}/issues/{issue.get('number', 0)}"
    ticket_revision_id = f"github-ticket-revision:{digest(origin_frame_id + ':' + (os.environ.get('GITHUB_SHA') or issue.get('updated_at', '') or body))}"
    manifest = {
        "schema": "missipy.github_issue.attachment_manifest.v1",
        "repository": repository,
        "issue": {"number": issue.get("number", 0), "url": issue.get("html_url", "")},
        "origin_frame_id": origin_frame_id,
        "ticket_revision_id": ticket_revision_id,
        "attachments": parse_attachments(body),
        "counts": {"attachment_count": 0},
        "boundary": [
            "GitHub issue attachment references only",
            "no GitHub API call",
            "no remote mutation",
            "GitHub Actions artifacts remain the source system",
            "no user artifacts in Autodoc repository",
        ],
    }
    manifest["counts"]["attachment_count"] = len(manifest["attachments"])
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "attachment_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0


def parse_attachments(body: str) -> list[dict]:
    refs = []
    seen = set()
    for match in MARKDOWN_LINK_RE.finditer(body):
        image_marker, label, url = match.groups()
        refs.append(build_ref(url, label, match.group(0), bool(image_marker)))
        seen.add(url)
    for match in BARE_ATTACHMENT_RE.finditer(body):
        url = match.group(0).rstrip(".,;")
        if url in seen:
            continue
        refs.append(build_ref(url, "", match.group(0), False))
        seen.add(url)
    return refs


def build_ref(url: str, label: str, raw_text: str, image_hint: bool) -> dict:
    filename = filename_from_label_or_url(label, url)
    return {
        "schema": "missipy.github_issue.attachment_reference.v1",
        "url": url,
        "filename": filename,
        "kind": kind_from_filename(filename, image_hint),
        "source": "github_issue_attachment_reference",
        "label": label,
        "raw_text": raw_text,
        "processed": False,
    }


def filename_from_label_or_url(label: str, url: str) -> str:
    if looks_like_filename(label):
        return sanitize_filename(label)
    path_name = unquote(urlparse(url).path.rstrip("/").split("/")[-1])
    if looks_like_filename(path_name):
        return sanitize_filename(path_name)
    return f"github-attachment-{digest(url)[:12]}.bin"


def kind_from_filename(filename: str, image_hint: bool) -> str:
    lower = filename.lower()
    if image_hint or lower.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg", ".heic", ".heif")):
        return "image"
    if lower.endswith((".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".opus")):
        return "audio"
    if lower.endswith((".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v")):
        return "video"
    if lower.endswith(".pdf"):
        return "pdf"
    if lower.endswith((".zip", ".tar", ".tgz", ".gz", ".bz2", ".xz", ".7z", ".rar")):
        return "archive"
    if lower.endswith((".txt", ".md", ".rst", ".csv", ".json", ".yaml", ".yml", ".toml", ".ini", ".log")):
        return "text"
    return "binary"


def looks_like_filename(value: str) -> bool:
    stripped = value.strip().strip("`")
    return bool(stripped and "." in stripped and "/" not in stripped and "\\" not in stripped)


def sanitize_filename(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip().strip("`"))
    return cleaned.strip("._") or "attachment.bin"


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


if __name__ == "__main__":
    raise SystemExit(main())
