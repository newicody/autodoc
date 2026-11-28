#!/usr/bin/env python3
"""Fetch and validate one Git-backed Copilot/server exchange artifact."""
from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any, Mapping

from contracts.git_artifact_exchange import artifact_path, validate_git_exchange_artifact


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", required=True)
    parser.add_argument("--branch", required=True)
    parser.add_argument("--issue-number", type=int, required=True)
    parser.add_argument("--cycle-ordinal", type=int, required=True)
    parser.add_argument("--role", choices=("copilot_initial", "server_response", "copilot_refined"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    path = artifact_path(args.issue_number, args.cycle_ordinal, args.role)
    env = dict(os.environ)
    process = subprocess.run(
        ["gh", "api", "repos/" + args.repository + "/contents/" + path, "-f", "ref=" + args.branch],
        text=True, capture_output=True, env=env, check=False,
    )
    if process.returncode:
        raise RuntimeError(f"Git artifact fetch failed: {process.stderr.strip()}")
    content = json.loads(process.stdout)
    if not isinstance(content, Mapping) or content.get("encoding") != "base64":
        raise ValueError("GitHub Contents response has unexpected shape")
    raw = base64.b64decode(content["content"])
    envelope = json.loads(raw.decode("utf-8"))
    if not isinstance(envelope, Mapping):
        raise ValueError("Git artifact envelope must be a JSON object")
    validate_git_exchange_artifact(envelope)
    if envelope.get("role") != args.role:
        raise ValueError("fetched artifact role mismatch")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(raw)
    print(json.dumps({
        "schema": "missipy.github.git_artifact_fetch_result.v1",
        "valid": True,
        "artifact_ref": envelope["artifact_ref"],
        "artifact_path": path,
        "payload_digest": envelope["payload_digest"],
        "output": str(args.output),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
