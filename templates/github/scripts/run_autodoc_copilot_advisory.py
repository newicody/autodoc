#!/usr/bin/env python3
"""Build an optional and non-authoritative Copilot advisory artifact."""

from __future__ import annotations

from pathlib import Path

import hashlib
import json
import os
import subprocess
import sys
from typing import Any

_REQUIRED_RESPONSE_KEYS = (
    "summary",
    "suggested_route",
    "assumptions",
    "questions",
    "risks",
    "confidence",
)


def canonical(payload: dict[str, Any]) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ) + "\n"


def parse(text: str) -> dict[str, Any]:
    candidate = text.strip()
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if len(lines) < 3 or lines[-1].strip() != "```":
            raise ValueError("Copilot response has an unterminated code fence")
        candidate = "\n".join(lines[1:-1]).strip()
        if candidate.startswith("json"):
            candidate = candidate.removeprefix("json").lstrip()

    payload = json.loads(candidate)
    if not isinstance(payload, dict):
        raise ValueError("Copilot response must be a JSON object")
    for key in _REQUIRED_RESPONSE_KEYS:
        if key not in payload:
            raise ValueError(f"Copilot response missing {key}")
    for key in ("assumptions", "questions", "risks"):
        if not isinstance(payload[key], list):
            raise ValueError(f"Copilot response {key} must be a JSON array")
    return payload


def _enabled(name: str, *, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _unavailable(output_path: Path, reason: str, *, required: bool) -> int:
    output_path.unlink(missing_ok=True)
    print(f"Copilot advisory unavailable: {reason}", file=sys.stderr)
    return 1 if required else 0


def main() -> int:
    request_path = Path(
        os.environ.get("AUTODOC_REQUEST", "out/authoritative_request.json")
    )
    request = json.loads(request_path.read_text(encoding="utf-8"))
    if not isinstance(request, dict):
        raise ValueError("authoritative request must be a JSON object")

    output_path = Path(
        os.environ.get("AUTODOC_ADVISORY", "out/copilot_advisory.json")
    )
    output_path.unlink(missing_ok=True)

    prompt = (
        "Return one JSON object only with keys summary, suggested_route, "
        "assumptions, questions, risks, confidence. Treat the following GitHub "
        "request as authoritative. Do not modify it, do not call tools, do not "
        "authorize publication.\n"
        + json.dumps(
            {
                "title": request["title"],
                "body": request["body"],
                "labels": request.get("labels", []),
            },
            ensure_ascii=False,
        )
    )
    command = os.environ.get("AUTODOC_COPILOT_COMMAND", "copilot")
    timeout_seconds = int(os.environ.get("AUTODOC_COPILOT_TIMEOUT", "180"))
    required = _enabled("AUTODOC_COPILOT_REQUIRED")

    try:
        process = subprocess.run(
            [
                command,
                "-p",
                prompt,
                "-s",
                "--no-ask-user",
                "--deny-tool=write",
                "--deny-tool=shell",
            ],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return _unavailable(output_path, "timeout", required=required)
    except OSError as exc:
        return _unavailable(
            output_path,
            f"command_error:{type(exc).__name__}",
            required=required,
        )

    if process.returncode != 0:
        return _unavailable(
            output_path,
            f"exit_status:{process.returncode}",
            required=required,
        )

    try:
        parsed = parse(process.stdout)
        response_digest = hashlib.sha256(process.stdout.encode()).hexdigest()
        prompt_digest = hashlib.sha256(prompt.encode()).hexdigest()
        artifact_ref = "github-advisory:" + hashlib.sha256(
            (str(request["artifact_ref"]) + response_digest).encode()
        ).hexdigest()[:16]
        payload = {
            "schema": "missipy.github.copilot_advisory.v1",
            "origin_frame_id": request["origin_frame_id"],
            "ticket_revision_id": request["ticket_revision_id"],
            "artifact_ref": artifact_ref,
            "request_artifact_ref": request["artifact_ref"],
            "prompt_digest": prompt_digest,
            "response_digest": response_digest,
            "summary": str(parsed["summary"]),
            "suggested_route": str(parsed["suggested_route"]),
            "assumptions": list(parsed["assumptions"]),
            "questions": list(parsed["questions"]),
            "risks": list(parsed["risks"]),
            "confidence": float(parsed["confidence"]),
            "producer_kind": "github_copilot_cli",
            "trusted": False,
            "usable_as_hint": True,
            "usable_as_authority": False,
        }
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        return _unavailable(
            output_path,
            f"invalid_response:{type(exc).__name__}",
            required=required,
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(canonical(payload), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
