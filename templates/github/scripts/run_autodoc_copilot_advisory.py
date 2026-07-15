#!/usr/bin/env python3
"""Build an optional and non-authoritative Copilot advisory artifact."""

from __future__ import annotations

from pathlib import Path

import hashlib
import json
import math
import os
import subprocess
import sys
from typing import Any, Iterator

_REQUIRED_RESPONSE_KEYS = (
    "summary",
    "suggested_route",
    "assumptions",
    "questions",
    "risks",
    "confidence",
)


_FIRST_OPINION_RESPONSE_KEYS = (
    "concrete_objective",
    "expected_result",
    "provided_constraints",
    "success_criteria",
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


def _validate_advisory(payload: dict[str, Any]) -> dict[str, Any]:
    for key in ("summary", "suggested_route"):
        if not isinstance(payload[key], str):
            raise ValueError(f"Copilot response {key} must be a string")

    for key in ("assumptions", "questions", "risks"):
        values = payload[key]
        if not all(isinstance(value, str) for value in values):
            raise ValueError(
                f"Copilot response {key} entries must be strings"
            )

    raw_confidence = payload["confidence"]
    if isinstance(raw_confidence, bool):
        raise ValueError("Copilot response confidence must be numeric")

    confidence = float(raw_confidence)
    if not math.isfinite(confidence) or not 0.0 <= confidence <= 1.0:
        raise ValueError(
            "Copilot response confidence must be between 0 and 1"
        )

    normalized = dict(payload)
    normalized["confidence"] = confidence
    return normalized


def _walk_json(value: object) -> Iterator[object]:
    yield value
    if isinstance(value, dict):
        preferred = ("content", "message", "text", "response", "value")
        for key in preferred:
            if key in value:
                yield from _walk_json(value[key])
        for key, child in value.items():
            if key not in preferred:
                yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def _embedded_advisories(text: str) -> Iterator[dict[str, Any]]:
    decoder = json.JSONDecoder()
    for offset, character in enumerate(text):
        if character != "{":
            continue
        try:
            payload, _ = decoder.raw_decode(text[offset:])
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        try:
            yield _validate_advisory(parse(json.dumps(payload)))
        except (KeyError, TypeError, ValueError):
            continue


def extract_advisory(text: str) -> dict[str, Any]:
    direct_error: Exception | None = None
    try:
        return _validate_advisory(parse(text))
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        direct_error = exc

    extracted: list[dict[str, Any]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        for candidate in _walk_json(event):
            if isinstance(candidate, dict):
                try:
                    extracted.append(
                        _validate_advisory(parse(json.dumps(candidate)))
                    )
                except (KeyError, TypeError, ValueError):
                    pass
            elif isinstance(candidate, str):
                try:
                    extracted.append(_validate_advisory(parse(candidate)))
                except (
                    json.JSONDecodeError,
                    KeyError,
                    TypeError,
                    ValueError,
                ):
                    extracted.extend(_embedded_advisories(candidate))

    if not extracted:
        extracted.extend(_embedded_advisories(text))

    if extracted:
        return extracted[-1]

    if direct_error is not None:
        raise direct_error
    raise ValueError("Copilot response contains no advisory object")


def parse_first_opinion(text: str) -> dict[str, Any]:
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
        raise ValueError("Copilot first opinion must be a JSON object")
    actual = set(payload)
    expected = set(_FIRST_OPINION_RESPONSE_KEYS)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise ValueError(
            f"Copilot first opinion field mismatch: missing={missing}, extra={extra}"
        )
    return _validate_first_opinion(payload)


def _validate_first_opinion(payload: dict[str, Any]) -> dict[str, Any]:
    normalized: dict[str, Any] = {}
    for key in ("concrete_objective", "expected_result"):
        value = payload[key]
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"Copilot first opinion {key} must be non-empty")
        normalized[key] = value.strip()
    for key in ("provided_constraints", "success_criteria"):
        values = payload[key]
        if not isinstance(values, list):
            raise ValueError(f"Copilot first opinion {key} must be an array")
        if not all(isinstance(value, str) and value.strip() for value in values):
            raise ValueError(
                f"Copilot first opinion {key} entries must be non-empty strings"
            )
        normalized[key] = [value.strip() for value in values]
    if not normalized["success_criteria"]:
        raise ValueError("Copilot first opinion success_criteria must not be empty")
    return normalized


def _embedded_first_opinions(text: str) -> Iterator[dict[str, Any]]:
    decoder = json.JSONDecoder()
    for offset, character in enumerate(text):
        if character != "{":
            continue
        try:
            payload, _ = decoder.raw_decode(text[offset:])
        except json.JSONDecodeError:
            continue
        if not isinstance(payload, dict):
            continue
        try:
            yield parse_first_opinion(json.dumps(payload))
        except (KeyError, TypeError, ValueError):
            continue


def extract_first_opinion(text: str) -> dict[str, Any]:
    direct_error: Exception | None = None
    try:
        return parse_first_opinion(text)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        direct_error = exc
    extracted: list[dict[str, Any]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        for candidate in _walk_json(event):
            if isinstance(candidate, dict):
                try:
                    extracted.append(parse_first_opinion(json.dumps(candidate)))
                except (KeyError, TypeError, ValueError):
                    pass
            elif isinstance(candidate, str):
                try:
                    extracted.append(parse_first_opinion(candidate))
                except (
                    json.JSONDecodeError,
                    KeyError,
                    TypeError,
                    ValueError,
                ):
                    extracted.extend(_embedded_first_opinions(candidate))
    if not extracted:
        extracted.extend(_embedded_first_opinions(text))
    if extracted:
        return extracted[-1]
    if direct_error is not None:
        raise direct_error
    raise ValueError("Copilot response contains no first-opinion object")


def _first_opinion_prompt(request: dict[str, Any]) -> str:
    request_context: dict[str, Any] = {
        "title": request["title"],
        "body": request["body"],
        "labels": request.get("labels", []),
    }
    for key in ("autodoc_dispatch", "context"):
        if key in request:
            request_context[key] = request[key]
    return (
        "Return exactly one compact JSON object and no Markdown or commentary. "
        "The object must contain exactly these four fields: "
        '{"concrete_objective":"string","expected_result":"string",'
        '"provided_constraints":["string"],'
        '"success_criteria":["string"]}. '
        "Identify the concrete objective of the request. Distinguish the expected "
        "result from the mere subject or title of the Issue. List only constraints "
        "and elements already provided; use an empty array when none are supplied. "
        "Define one or more observable and verifiable success criteria. Do not add "
        "a route, assumptions, questions, risks, confidence or recommendations. "
        "Treat the following GitHub request as authoritative. Do not modify it, "
        "do not call tools, and do not authorize publication.\n"
        + json.dumps(
            request_context,
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )


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
        "Return exactly one compact JSON object and no Markdown or commentary. "
        "Required schema: "
        '{"summary":"string","suggested_route":"string",'
        '"assumptions":["string"],"questions":["string"],'
        '"risks":["string"],"confidence":0.0}. '
        "confidence must be a number between 0 and 1. Treat the following "
        "GitHub request as authoritative. Do not modify it, do not call tools, "
        "and do not authorize publication.\n"
        + json.dumps(
            {
                "title": request["title"],
                "body": request["body"],
                "labels": request.get("labels", []),
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )
    prompt = _first_opinion_prompt(request)
    command = os.environ.get("AUTODOC_COPILOT_COMMAND", "copilot")
    timeout_seconds = int(os.environ.get("AUTODOC_COPILOT_TIMEOUT", "180"))
    required = _enabled("AUTODOC_COPILOT_REQUIRED")

    try:
        process = subprocess.run(
            [
                command,
                "-p",
                prompt,
                "--output-format=json",
                "--stream=off",
                "--no-color",
                "--no-custom-instructions",
                "--no-ask-user",
                "--deny-tool=read",
                "--deny-tool=write",
                "--deny-tool=shell",
                "--deny-tool=url",
                "--deny-tool=memory",
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
        parsed = extract_first_opinion(process.stdout)
        semantic_response = canonical(parsed)
        response_digest = hashlib.sha256(
            semantic_response.encode("utf-8")
        ).hexdigest()
        prompt_digest = hashlib.sha256(prompt.encode()).hexdigest()
        artifact_ref = "github-advisory:" + hashlib.sha256(
            (str(request["artifact_ref"]) + response_digest).encode()
        ).hexdigest()[:16]
        payload = {
            "schema": "missipy.github.copilot_advisory.v2",
            "origin_frame_id": request["origin_frame_id"],
            "ticket_revision_id": request["ticket_revision_id"],
            "artifact_ref": artifact_ref,
            "request_artifact_ref": request["artifact_ref"],
            "prompt_digest": prompt_digest,
            "response_digest": response_digest,
            "concrete_objective": parsed["concrete_objective"],
            "expected_result": parsed["expected_result"],
            "provided_constraints": list(parsed["provided_constraints"]),
            "success_criteria": list(parsed["success_criteria"]),
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
