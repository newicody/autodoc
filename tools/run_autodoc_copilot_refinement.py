#!/usr/bin/env python3
"""Ask Copilot once to refine a request against one server response artifact."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
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


def _extract(stdout: str) -> dict[str, Any]:
    candidate = stdout.strip()
    if candidate.startswith("```"):
        lines = candidate.splitlines()
        if len(lines) < 3 or lines[-1].strip() != "```":
            raise ValueError("Copilot output has an unterminated code fence")
        candidate = "\n".join(lines[1:-1]).strip()
        if candidate.startswith("json"):
            candidate = candidate.removeprefix("json").lstrip()
    value = json.loads(candidate)
    if not isinstance(value, Mapping):
        raise ValueError("Copilot refinement must be a JSON object")
    expected = {
        "concrete_objective", "expected_result", "provided_constraints",
        "success_criteria", "scientific_representations",
    }
    if set(value) != expected:
        raise ValueError("Copilot refinement fields do not match the strict schema")
    for field in ("concrete_objective", "expected_result"):
        if not isinstance(value[field], str) or not value[field].strip():
            raise ValueError(f"{field} must be non-empty")
    for field in ("provided_constraints", "success_criteria", "scientific_representations"):
        if not isinstance(value[field], list) or not all(
            isinstance(item, str) and item.strip() for item in value[field]
        ):
            raise ValueError(f"{field} must be an array of non-empty strings")
    if not value["success_criteria"]:
        raise ValueError("success_criteria must not be empty")
    return dict(value)


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
