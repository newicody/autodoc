#!/usr/bin/env python3
"""Repair and validate a workflow_dispatch Issue envelope before request build.

The controlled workflow already creates a synthetic event and the existing
authoritative-request builder remains the single payload authority. This
adapter only normalizes the event boundary, invokes that builder, then verifies
that the resulting artifact still refers to the selected Issue.
"""

from __future__ import annotations

from collections.abc import Mapping
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


def _load_mapping(path: Path, *, name: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{name} must be a JSON object")
    return dict(payload)


def _mapping_or_json_object(value: object) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, str) and value.strip():
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return dict(decoded) if isinstance(decoded, Mapping) else {}
    return {}


def normalize_dispatch_event(
    event: Mapping[str, Any],
    issue_payload: Mapping[str, Any],
    *,
    repository: str,
    actor: str,
) -> dict[str, Any]:
    """Return the strict event shape expected by the existing builder."""

    raw_issue = dict(issue_payload)
    raw_number = int(raw_issue.get("number") or 0)
    if raw_number <= 0:
        raise ValueError("selected Issue number must be positive")

    embedded_issue = _mapping_or_json_object(event.get("issue"))
    issue = embedded_issue or raw_issue
    embedded_number = int(issue.get("number") or 0)
    if embedded_number != raw_number:
        raise ValueError(
            "synthetic event Issue number does not match selected Issue"
        )

    repository_block = _mapping_or_json_object(event.get("repository"))
    repository_block["full_name"] = (
        str(repository or repository_block.get("full_name") or "").strip()
    )
    if not repository_block["full_name"]:
        raise ValueError("repository full_name is required")

    sender = _mapping_or_json_object(event.get("sender"))
    sender["login"] = str(actor or sender.get("login") or "")

    dispatch = _mapping_or_json_object(event.get("autodoc_dispatch"))
    dispatch["issue_number"] = raw_number

    normalized = dict(event)
    normalized.update(
        {
            "schema": "missipy.github.workflow_dispatch_issue_event.v1",
            "action": "workflow_dispatch",
            "issue": issue,
            "repository": repository_block,
            "sender": sender,
            "autodoc_dispatch": dispatch,
        }
    )
    return normalized


def main() -> int:
    issue_path = Path(os.environ["AUTODOC_ISSUE_JSON"])
    event_value = (
        os.environ.get("AUTODOC_EVENT_PATH")
        or os.environ.get("GITHUB_EVENT_PATH")
        or ""
    ).strip()
    if not event_value:
        raise ValueError(
            "AUTODOC_EVENT_PATH or GITHUB_EVENT_PATH is required"
        )
    event_path = Path(event_value)
    output_path = Path(
        os.environ.get(
            "AUTODOC_NORMALIZED_EVENT_OUTPUT",
            str(event_path.with_name("normalized_autodoc_issue_event.json")),
        )
    )
    authoritative_output = Path(
        os.environ.get("AUTODOC_OUTPUT", "out/authoritative_request.json")
    )

    issue = _load_mapping(issue_path, name="selected Issue payload")
    event = _load_mapping(event_path, name="synthetic GitHub event")
    normalized = normalize_dispatch_event(
        event,
        issue,
        repository=os.environ.get("GITHUB_REPOSITORY", ""),
        actor=os.environ.get("GITHUB_ACTOR", ""),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            normalized,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    builder = (
        Path(__file__).resolve().parents[2]
        / "scripts/build_autodoc_authoritative_request.py"
    )
    environment = dict(os.environ)
    environment["AUTODOC_EVENT_PATH"] = str(output_path)
    environment["AUTODOC_OUTPUT"] = str(authoritative_output)
    environment.pop("GITHUB_EVENT_PATH", None)
    subprocess.run(
        [sys.executable, str(builder)],
        env=environment,
        check=True,
    )

    artifact = _load_mapping(
        authoritative_output,
        name="authoritative request artifact",
    )
    expected_repository = normalized["repository"]["full_name"]
    expected_issue = int(normalized["issue"]["number"])
    if artifact.get("schema") != "missipy.github.authoritative_request.v1":
        raise ValueError("unexpected authoritative request schema")
    if artifact.get("repository") != expected_repository:
        raise ValueError("authoritative request repository mismatch")
    if int(artifact.get("issue_number") or 0) != expected_issue:
        raise ValueError("authoritative request Issue mismatch")
    if artifact.get("authoritative") is not True:
        raise ValueError("authoritative request flag must remain true")

    print(
        json.dumps(
            {
                "status": "ok",
                "repository": expected_repository,
                "issue_number": expected_issue,
                "normalized_event_path": str(output_path),
                "authoritative_output": str(authoritative_output),
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
