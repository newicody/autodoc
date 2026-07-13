#!/usr/bin/env python3
"""Build an authoritative request artifact from a real GitHub Issue event."""

from __future__ import annotations

from pathlib import Path

import hashlib
import json
import os
from typing import Any


def canonical(payload: dict[str, Any]) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"


def _require_mapping(value: object, *, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object")
    return value


def main() -> int:
    event_path = Path(os.environ["GITHUB_EVENT_PATH"])
    event = _require_mapping(
        json.loads(event_path.read_text(encoding="utf-8")),
        name="GitHub event",
    )
    issue = _require_mapping(event.get("issue"), name="GitHub event issue")
    repository_block = event.get("repository") or {}
    if not isinstance(repository_block, dict):
        raise ValueError("GitHub event repository must be a JSON object")

    repository = str(
        os.environ.get("GITHUB_REPOSITORY")
        or repository_block.get("full_name")
        or ""
    ).strip()
    number = int(issue.get("number") or 0)
    title = str(issue.get("title") or "").strip()
    body = str(issue.get("body") or "")

    if not repository:
        raise ValueError("authoritative request requires a repository")
    if number <= 0:
        raise ValueError("authoritative request requires a positive issue number")
    if not title:
        raise ValueError("authoritative request requires an issue title")

    updated = str(issue.get("updated_at") or issue.get("created_at") or "")
    origin_frame_id = (
        f"github-frame:{repository}:{number}:"
        f"{os.environ.get('GITHUB_RUN_ID', 'local')}"
    )
    revision_digest = hashlib.sha256(
        (repository + str(number) + updated + title + body).encode()
    ).hexdigest()[:16]
    ticket_revision_id = f"github-ticket-revision:{revision_digest}"
    artifact_ref = f"github-request:{repository}:{number}:{revision_digest}"

    labels = issue.get("labels") or []
    if not isinstance(labels, list):
        raise ValueError("GitHub issue labels must be a JSON array")

    sender = event.get("sender") or {}
    if not isinstance(sender, dict):
        raise ValueError("GitHub event sender must be a JSON object")

    payload = {
        "schema": "missipy.github.authoritative_request.v1",
        "origin_frame_id": origin_frame_id,
        "ticket_revision_id": ticket_revision_id,
        "artifact_ref": artifact_ref,
        "repository": repository,
        "issue_number": number,
        "title": title,
        "body": body,
        "issue_url": str(issue.get("html_url") or ""),
        "labels": [
            str(label.get("name"))
            for label in labels
            if isinstance(label, dict) and label.get("name")
        ],
        "actor": str(sender.get("login") or ""),
        "event_name": os.environ.get("GITHUB_EVENT_NAME", "issues"),
        "metadata": {"github_sha": os.environ.get("GITHUB_SHA", "")},
        "authoritative": True,
        "advisory_content_embedded": False,
        "remote_mutation_requested": False,
    }
    output_path = Path(
        os.environ.get("AUTODOC_OUTPUT", "out/authoritative_request.json")
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(canonical(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
