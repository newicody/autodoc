#!/usr/bin/env python3
"""Publish one validated exchange envelope to a GitHub repository commit.

The script is a one-shot adapter around the GitHub Contents API (gh CLI).
It never overwrites an existing path: identical content is a replay, different
content is a collision.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
from typing import Any, Mapping

import sys

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from contracts.copilot_scientific_framing import (
    FramingHandshake,
    validate_initial_advisory,
    validate_refined_request,
    validate_server_response,
)
from contracts.git_artifact_exchange import (
    GitArtifactExchangeError,
    build_git_exchange_artifact,
    canonical_payload_digest,
    classify_existing_path,
    validate_git_exchange_artifact,
)


def _gh(args: list[str], *, allow_404: bool = False) -> dict[str, Any] | None:
    env = dict(os.environ)
    if env.get("GH_TOKEN"):
        env["GH_TOKEN"] = env["GH_TOKEN"]
    process = subprocess.run(
        ["gh", "api", *args],
        cwd=_REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if process.returncode:
        if allow_404 and ("404" in process.stderr or "Not Found" in process.stderr):
            return None
        raise RuntimeError(f"GitHub API request failed: {process.stderr.strip()}")
    try:
        payload = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("GitHub API returned invalid JSON") from exc
    if not isinstance(payload, Mapping):
        raise RuntimeError("GitHub API response must be an object")
    return dict(payload)


def _read_remote(repository: str, branch: str, path: str) -> dict[str, Any] | None:
    result = _gh(
        ["-X", "GET", "repos/" + repository + "/contents/" + path, "-f", "ref=" + branch],
        allow_404=True,
    )
    if result is None:
        return None
    if result.get("encoding") != "base64" or not isinstance(result.get("content"), str):
        raise RuntimeError("GitHub Contents response is not base64 content")
    raw = base64.b64decode(result["content"])
    value = json.loads(raw.decode("utf-8"))
    if not isinstance(value, Mapping):
        raise RuntimeError("existing exchange artifact must be a JSON object")
    return dict(value)


def _publish(repository: str, branch: str, envelope: Mapping[str, Any]) -> tuple[str, str]:
    path = str(envelope["artifact_path"])
    existing = _read_remote(repository, branch, path)
    action = classify_existing_path(existing, envelope)
    if action == "replay":
        return "replay-noop", ""
    if action == "collision":
        raise GitArtifactExchangeError("append-only Git artifact path collision")
    content = json.dumps(
        dict(envelope), ensure_ascii=False, sort_keys=True, indent=2
    ) + "\n"
    write_result = _gh([
        "-X", "PUT",
        "repos/" + repository + "/contents/" + path,
        "-f", "message=autodoc: publish " + str(envelope["role"])
             + " issue " + str(envelope["issue_number"])
             + " cycle " + str(envelope["cycle_ordinal"]),
        "-f", "content=" + content,
        "-f", "branch=" + branch,
    ])
    readback = _read_remote(repository, branch, path)
    if readback is None:
        raise RuntimeError("published Git artifact is missing on readback")
    validate_git_exchange_artifact(readback)
    if readback.get("payload_digest") != envelope.get("payload_digest"):
        raise RuntimeError("published Git artifact readback digest mismatch")
    commit = write_result.get("commit")
    commit_sha = str(commit.get("sha", "")).strip() if isinstance(commit, Mapping) else ""
    if not commit_sha:
        raise RuntimeError("GitHub Contents API did not return the publication commit SHA")
    return "created", commit_sha


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must contain a JSON object")
    return dict(value)


def _handshake(initial_envelope: Mapping[str, Any]) -> FramingHandshake:
    validate_git_exchange_artifact(initial_envelope)
    if initial_envelope.get("role") != "copilot_initial":
        raise ValueError("initial artifact role mismatch")
    advisory = initial_envelope["payload"]
    request = {"artifact_ref": advisory.get("request_artifact_ref")}
    return validate_initial_advisory(request, advisory)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--issue-number", type=int, required=True)
    parser.add_argument("--cycle-ordinal", type=int, required=True)
    parser.add_argument("--role", choices=("copilot_initial", "server_response", "copilot_refined"), required=True)
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--envelope", type=Path)
    parser.add_argument("--initial-envelope", type=Path)
    parser.add_argument("--server-response-envelope", type=Path)
    parser.add_argument("--created-at", default="")
    args = parser.parse_args(argv)

    payload = _load(args.payload)
    predecessor_ref = ""
    predecessor_digest = ""
    if args.role == "server_response":
        if args.initial_envelope is None:
            parser.error("--initial-envelope is required for server_response")
        handshake = _handshake(_load(args.initial_envelope))
        validate_server_response(handshake, payload)
        initial = _load(args.initial_envelope)
        predecessor_ref = str(initial["artifact_ref"])
        predecessor_digest = str(initial["payload_digest"])
    elif args.role == "copilot_refined":
        if args.initial_envelope is None or args.server_response_envelope is None:
            parser.error("refined role requires both predecessor envelopes")
        initial = _load(args.initial_envelope)
        response_envelope = _load(args.server_response_envelope)
        handshake = _handshake(initial)
        validate_git_exchange_artifact(response_envelope)
        if response_envelope.get("role") != "server_response":
            raise ValueError("server response artifact role mismatch")
        response = response_envelope["payload"]
        validate_server_response(handshake, response)
        if response_envelope.get("predecessor_ref") != initial.get("artifact_ref"):
            raise ValueError("server response does not reference the initial artifact")
        if response_envelope.get("predecessor_digest") != initial.get("payload_digest"):
            raise ValueError("server response predecessor digest does not match initial artifact")
        validate_refined_request(handshake, response, payload)
        predecessor_ref = str(response_envelope["artifact_ref"])
        predecessor_digest = str(response_envelope["payload_digest"])
    if args.envelope is not None:
        if args.role != "copilot_initial":
            parser.error("--envelope is currently reserved for the initial Copilot artifact")
        envelope = _load(args.envelope)
        validate_git_exchange_artifact(envelope)
        if (
            envelope.get("repository") != args.repository
            or envelope.get("issue_number") != args.issue_number
            or envelope.get("cycle_ordinal") != args.cycle_ordinal
            or envelope.get("role") != args.role
        ):
            raise ValueError("provided envelope identity does not match publication arguments")
        if envelope.get("payload_digest") != canonical_payload_digest(payload):
            raise ValueError("provided envelope payload digest does not match payload")
    else:
        envelope = build_git_exchange_artifact(
            repository=args.repository,
            issue_number=args.issue_number,
            cycle_ordinal=args.cycle_ordinal,
            role=args.role,
            payload=payload,
            created_at=args.created_at or datetime.now(timezone.utc).isoformat(),
            predecessor_ref=predecessor_ref,
            predecessor_digest=predecessor_digest,
        ).to_mapping()
    result, commit_sha = _publish(args.repository, args.branch, envelope)
    print(json.dumps({
        "schema": "missipy.github.git_artifact_publication_result.v1",
        "valid": True,
        "status": result,
        "commit_sha": commit_sha,
        "artifact_ref": envelope["artifact_ref"],
        "artifact_path": envelope["artifact_path"],
        "payload_digest": envelope["payload_digest"],
        "commit_push_transport": True,
        "overwrite_performed": False,
    }, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
