#!/usr/bin/env python3
"""Publish the server's single framing assessment after a Git initial-artifact fetch.

The caller supplies an assessment assembled from server-owned component data.
This adapter validates its shape and provenance; it does not invent capabilities,
query components, or make Scheduler decisions.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from contracts.copilot_scientific_framing import (
    SERVER_RESPONSE_SCHEMA,
    validate_initial_advisory,
    validate_server_response,
)
from contracts.git_artifact_exchange import validate_git_exchange_artifact
from context.server_scientific_framing_assessment_0287 import (
    build_server_scientific_framing_assessment,
)
from contracts.server_component_state import ServerComponentStateSnapshot


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise ValueError(f"{path} must contain a JSON object")
    return dict(value)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--issue-number", type=int, required=True)
    parser.add_argument("--cycle-ordinal", type=int, required=True)
    assessment_group = parser.add_mutually_exclusive_group(required=True)
    assessment_group.add_argument("--assessment", type=Path)
    assessment_group.add_argument("--component-snapshots", type=Path)
    parser.add_argument("--work-dir", type=Path, default=Path(".var/git_exchange"))
    args = parser.parse_args(argv)
    args.assessment = args.assessment.resolve()
    args.work_dir = args.work_dir.resolve()

    args.work_dir.mkdir(parents=True, exist_ok=True)
    initial_path = args.work_dir / f"issue-{args.issue_number}-cycle-{args.cycle_ordinal}-initial.json"
    fetch = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).with_name("fetch_git_exchange_artifact.py")),
            "--repository", args.repository,
            "--branch", args.branch,
            "--issue-number", str(args.issue_number),
            "--cycle-ordinal", str(args.cycle_ordinal),
            "--role", "copilot_initial",
            "--output", str(initial_path),
        ],
        text=True,
        capture_output=True,
        check=False,
        env=dict(os.environ),
    )
    if fetch.returncode:
        raise RuntimeError(f"initial Git artifact fetch failed: {fetch.stderr.strip()}")
    initial = _load(initial_path)
    validate_git_exchange_artifact(initial)
    advisory = initial["payload"]
    handshake = validate_initial_advisory(
        {"artifact_ref": advisory.get("request_artifact_ref")},
        advisory,
    )

    if args.component_snapshots is not None:
        snapshot_payload = json.loads(args.component_snapshots.resolve().read_text(encoding="utf-8"))
        if isinstance(snapshot_payload, Mapping):
            snapshot_payload = snapshot_payload.get("snapshots")
        if not isinstance(snapshot_payload, list):
            raise ValueError("component snapshot file must contain an array or {snapshots: [...]}")
        snapshots = tuple(ServerComponentStateSnapshot.from_mapping(item) for item in snapshot_payload)
        assessment = build_server_scientific_framing_assessment(snapshots)
    else:
        assessment = _load(args.assessment)
    required = {
        "coherence_status", "assessment", "supported_representations",
        "unsupported_representations", "available_data", "missing_data",
        "verified_capabilities", "constraints", "report_outline", "provenance",
    }
    if set(assessment) != required:
        raise ValueError(
            "assessment fields must match exactly: " + ", ".join(sorted(required))
        )
    response = {
        "schema": SERVER_RESPONSE_SCHEMA,
        "handshake_ref": handshake.handshake_ref,
        "request_artifact_ref": handshake.request_artifact_ref,
        "initial_advisory_ref": handshake.initial_advisory_ref,
        "initial_advisory_digest": handshake.initial_advisory_digest,
        **assessment,
        "execution_authorized": False,
        "recursive_clarification_allowed": False,
    }
    validate_server_response(handshake, response)
    response_path = args.work_dir / f"issue-{args.issue_number}-cycle-{args.cycle_ordinal}-server-response.json"
    response_path.write_text(
        json.dumps(response, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    publish = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).with_name("publish_git_exchange_artifact.py")),
            "--repository", args.repository,
            "--branch", args.branch,
            "--issue-number", str(args.issue_number),
            "--cycle-ordinal", str(args.cycle_ordinal),
            "--role", "server_response",
            "--payload", str(response_path),
            "--initial-envelope", str(initial_path),
        ],
        text=True,
        capture_output=True,
        check=False,
        env=dict(os.environ),
    )
    if publish.returncode:
        raise RuntimeError(f"server response Git publication failed: {publish.stderr.strip()}")
    sys.stdout.write(publish.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
