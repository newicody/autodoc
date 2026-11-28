#!/usr/bin/env python3
"""Ask Copilot once to refine a request against one server response artifact."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

from contracts.copilot_scientific_framing import (
    canonical_digest,
    validate_initial_advisory,
    validate_refined_request,
)
from contracts.git_artifact_exchange import validate_git_exchange_artifact


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must contain a JSON object")
    return dict(value)


def _walk_json(value: object):
    yield value
    if isinstance(value, Mapping):
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


def _candidate(value: object) -> dict[str, Any] | None:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            return None
    if not isinstance(value, Mapping):
        return None
    expected = {
        "concrete_objective", "expected_result", "provided_constraints",
        "success_criteria", "scientific_representations",
    }
    if set(value) != expected:
        return None
    normalized = dict(value)
    for field in ("concrete_objective", "expected_result"):
        if not isinstance(normalized[field], str) or not normalized[field].strip():
            raise ValueError(f"{field} must be non-empty")
    for field in ("provided_constraints", "success_criteria", "scientific_representations"):
        values = normalized[field]
        if not isinstance(values, list) or not all(
            isinstance(item, str) and item.strip() for item in values
        ):
            raise ValueError(f"{field} must be an array of non-empty strings")
        normalized[field] = [item.strip() for item in values]
    if not normalized["success_criteria"]:
        raise ValueError("success_criteria must not be empty")
    normalized["concrete_objective"] = normalized["concrete_objective"].strip()
    normalized["expected_result"] = normalized["expected_result"].strip()
    return normalized


def _extract(stdout: str) -> dict[str, Any]:
    try:
        direct = json.loads(stdout.strip())
    except json.JSONDecodeError:
        direct = None
    candidates: list[dict[str, Any]] = []
    for item in _walk_json(direct) if direct is not None else ():
        candidate = _candidate(item)
        if candidate is not None:
            candidates.append(candidate)
    if not candidates:
        decoder = json.JSONDecoder()
        for offset, character in enumerate(stdout):
            if character != "{":
                continue
            try:
                embedded, _ = decoder.raw_decode(stdout[offset:])
            except json.JSONDecodeError:
                continue
            for item in _walk_json(embedded):
                candidate = _candidate(item)
                if candidate is not None:
                    candidates.append(candidate)
    if not candidates:
        raise ValueError("Copilot output contains no exact refinement object")
    return candidates[-1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--initial-envelope", type=Path, required=True)
    parser.add_argument("--server-response-envelope", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    initial = _load(args.initial_envelope)
    response_envelope = _load(args.server_response_envelope)
    validate_git_exchange_artifact(initial)
    validate_git_exchange_artifact(response_envelope)
    if initial.get("role") != "copilot_initial" or response_envelope.get("role") != "server_response":
        raise ValueError("unexpected predecessor artifact roles")
    for identity_field in ("repository", "issue_number", "cycle_ordinal"):
        if initial.get(identity_field) != response_envelope.get(identity_field):
            raise ValueError("server response research-cycle identity mismatch")
    if response_envelope.get("predecessor_ref") != initial.get("artifact_ref"):
        raise ValueError("server response does not reference the initial artifact")
    if response_envelope.get("predecessor_digest") != initial.get("payload_digest"):
        raise ValueError("server response predecessor digest mismatch")
    advisory = initial["payload"]
    request = {"artifact_ref": advisory.get("request_artifact_ref")}
    handshake = validate_initial_advisory(request, advisory)
    response = response_envelope["payload"]
    # Revalidate the server response against the exact first opinion.
    from contracts.copilot_scientific_framing import validate_server_response
    validate_server_response(handshake, response)

    prompt = (
        "Return exactly one JSON object with exactly these fields: "
        '{"concrete_objective":"string","expected_result":"string",'
        '"provided_constraints":["string"],"success_criteria":["string"],'
        '"scientific_representations":["string"]}. '
        "Reformulate the request once using the server assessment below. "
        "Keep unsupported representations and missing data explicit; do not "
        "invent capabilities or data. Do not call tools, modify files, publish, "
        "or authorize execution.\n"
        + json.dumps({
            "initial_copilot_advisory": advisory,
            "server_response": response,
        }, ensure_ascii=False, sort_keys=True)
    )
    command = os.environ.get("AUTODOC_COPILOT_COMMAND", "copilot")
    process = subprocess.run(
        [
            command, "-p", prompt, "--output-format=json", "--stream=off",
            "--no-color", "--no-custom-instructions", "--no-ask-user",
            "--deny-tool=read", "--deny-tool=write", "--deny-tool=shell",
            "--deny-tool=url", "--deny-tool=memory",
        ],
        capture_output=True, text=True, timeout=int(os.environ.get("AUTODOC_COPILOT_TIMEOUT", "180")),
        check=False,
    )
    if process.returncode:
        raise RuntimeError(f"Copilot refinement failed with status {process.returncode}")
    fields = _extract(process.stdout)
    refined = {
        "schema": "missipy.github.copilot_refined_research_request.v1",
        "handshake_ref": handshake.handshake_ref,
        "request_artifact_ref": handshake.request_artifact_ref,
        "initial_advisory_ref": handshake.initial_advisory_ref,
        "server_response_digest": canonical_digest(response),
        **fields,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "producer_kind": "github_copilot_cli",
        "trusted": False,
        "usable_as_authority": False,
    }
    validate_refined_request(handshake, response, refined)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(refined, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
