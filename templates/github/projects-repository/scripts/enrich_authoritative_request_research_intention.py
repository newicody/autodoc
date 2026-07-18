#!/usr/bin/env python3

"""Attach the controlled research intention to an authoritative request."""

from __future__ import annotations

from pathlib import Path
import json
import os
from typing import Any, Mapping


_ALLOWED_REQUESTED_STATUSES = frozenset(
    {"Recherche", "Développement", "Production"}
)
_ALLOWED_REQUEST_MODES = frozenset({"initial", "continuation", "transversal"})


def _load_mapping(path: Path, *, name: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{name} must be a JSON object")
    return payload


def _mapping(value: object, *, name: str) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{name} must be a JSON object")
    return value


def _nonempty_text(value: object, *, name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{name} must be non-empty")
    return text


def _set_consistent(metadata: dict[str, Any], key: str, value: str) -> None:
    previous = metadata.get(key)
    if previous is not None and str(previous) != value:
        raise ValueError(f"authoritative metadata collision for {key}")
    metadata[key] = value


def enrich_authoritative_request(
    request: Mapping[str, Any],
    event: Mapping[str, Any],
) -> dict[str, Any]:
    """Return the request with validated dispatch provenance in metadata."""

    if request.get("schema") != "missipy.github.authoritative_request.v1":
        raise ValueError("unsupported authoritative request schema")
    if request.get("authoritative") is not True:
        raise ValueError("request must remain authoritative")

    repository = _nonempty_text(request.get("repository"), name="repository")
    issue_number = int(request.get("issue_number") or 0)
    if issue_number <= 0:
        raise ValueError("issue_number must be positive")

    event_repository = _mapping(
        event.get("repository"),
        name="controlled event repository",
    )
    event_repository_name = _nonempty_text(
        event_repository.get("full_name"),
        name="controlled event repository full_name",
    )
    if event_repository_name != repository:
        raise ValueError("controlled event repository does not match request")

    dispatch = _mapping(
        event.get("autodoc_dispatch"),
        name="controlled event autodoc_dispatch",
    )
    dispatch_issue_number = int(dispatch.get("issue_number") or 0)
    if dispatch_issue_number != issue_number:
        raise ValueError("controlled event issue_number does not match request")

    requested_status = _nonempty_text(
        dispatch.get("requested_status"),
        name="requested_status",
    )
    if requested_status not in _ALLOWED_REQUESTED_STATUSES:
        raise ValueError("unsupported requested_status")

    request_mode = _nonempty_text(dispatch.get("request_mode"), name="request_mode")
    if request_mode not in _ALLOWED_REQUEST_MODES:
        raise ValueError("unsupported request_mode")

    parent_event_ref = str(dispatch.get("parent_event_ref") or "").strip()
    raw_metadata = request.get("metadata") or {}
    metadata = dict(_mapping(raw_metadata, name="authoritative request metadata"))
    _set_consistent(metadata, "requested_status", requested_status)
    _set_consistent(metadata, "request_mode", request_mode)
    _set_consistent(metadata, "parent_event_ref", parent_event_ref)

    enriched = dict(request)
    enriched["metadata"] = metadata
    return enriched


def _canonical(payload: Mapping[str, Any]) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"


def main() -> int:
    request_path = Path(
        os.environ.get("AUTODOC_REQUEST", "out/authoritative_request.json")
    )
    event_path = Path(
        os.environ.get("AUTODOC_EVENT_PATH", "out/autodoc_issue_event.json")
    )
    output_path = Path(os.environ.get("AUTODOC_OUTPUT", str(request_path)))

    enriched = enrich_authoritative_request(
        _load_mapping(request_path, name="authoritative request"),
        _load_mapping(event_path, name="controlled event"),
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = output_path.with_name(f".{output_path.name}.tmp")
    temporary_path.write_text(_canonical(enriched), encoding="utf-8")
    temporary_path.replace(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
