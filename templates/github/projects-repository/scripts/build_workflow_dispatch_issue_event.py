#!/usr/bin/env python3
"""Build a synthetic GitHub issue event for a controlled workflow_dispatch run."""

from __future__ import annotations

from pathlib import Path
import json
import os
from typing import Any, Mapping


def _load_mapping(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("issue payload must be a JSON object")
    return payload


def build_event(
    issue: Mapping[str, Any],
    *,
    repository: str,
    actor: str,
    requested_status: str,
    request_mode: str,
    parent_event_ref: str,
) -> dict[str, Any]:
    number = int(issue.get("number") or 0)
    if number <= 0:
        raise ValueError("issue number must be positive")
    if requested_status not in {"Recherche", "Développement", "Production"}:
        raise ValueError("unsupported requested_status")
    if request_mode not in {"initial", "continuation", "transversal"}:
        raise ValueError("unsupported request_mode")
    return {
        "action": "workflow_dispatch",
        "issue": dict(issue),
        "repository": {"full_name": repository},
        "sender": {"login": actor},
        "autodoc_dispatch": {
            "issue_number": number,
            "requested_status": requested_status,
            "request_mode": request_mode,
            "parent_event_ref": parent_event_ref,
        },
    }


def main() -> int:
    issue_path = Path(os.environ["AUTODOC_ISSUE_JSON"])
    output_path = Path(
        os.environ.get("AUTODOC_EVENT_OUTPUT", "out/autodoc_issue_event.json")
    )
    event = build_event(
        _load_mapping(issue_path),
        repository=os.environ["GITHUB_REPOSITORY"],
        actor=os.environ.get("GITHUB_ACTOR", ""),
        requested_status=os.environ["AUTODOC_REQUESTED_STATUS"],
        request_mode=os.environ["AUTODOC_REQUEST_MODE"],
        parent_event_ref=os.environ.get("AUTODOC_PARENT_EVENT_REF", ""),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(event, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
