#!/usr/bin/env python3
"""Build the initial Git exchange envelope from the existing Copilot v2 output."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Mapping

from contracts.git_artifact_exchange import build_git_exchange_artifact


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--advisory", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--issue-number", type=int, required=True)
    parser.add_argument("--cycle-ordinal", type=int, default=1)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    advisory = json.loads(args.advisory.read_text(encoding="utf-8"))
    if not isinstance(advisory, Mapping):
        raise ValueError("Copilot advisory must be a JSON object")
    if advisory.get("schema") != "missipy.github.copilot_advisory.v2":
        raise ValueError("unexpected Copilot advisory schema")
    envelope = build_git_exchange_artifact(
        repository=args.repository,
        issue_number=args.issue_number,
        cycle_ordinal=args.cycle_ordinal,
        role="copilot_initial",
        payload=advisory,
        created_at=datetime.now(timezone.utc).isoformat(),
    ).to_mapping()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(envelope, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
