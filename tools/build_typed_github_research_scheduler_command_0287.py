#!/usr/bin/env python3
"""Build one typed GitHub research Scheduler command without persistence."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from context.github_research_scheduler_command_0287 import (  # noqa: E402
    ResearchExecutionBudget,
    build_typed_github_research_scheduler_command,
)


def _load_mapping(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("input report must contain a JSON object")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Convert one authorized GitHub research intake boundary report "
            "into immutable typed classes. No filesystem handoff or SQL write "
            "is performed."
        )
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--max-scheduler-steps", required=True, type=int)
    parser.add_argument("--max-specialist-visits", required=True, type=int)
    parser.add_argument("--max-wall-time-s", required=True, type=float)
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    args = parser.parse_args(argv)

    result = build_typed_github_research_scheduler_command(
        scheduler_intake_report=_load_mapping(Path(args.input)),
        execution_budget=ResearchExecutionBudget(
            max_scheduler_steps=args.max_scheduler_steps,
            max_specialist_visits=args.max_specialist_visits,
            max_wall_time_s=args.max_wall_time_s,
        ),
    )
    mapping = result.to_mapping()
    if args.format == "json":
        print(json.dumps(mapping, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        command = result.command
        print(
            " ".join(
                (
                    f"valid={str(result.valid).lower()}",
                    f"status={result.status}",
                    f"command_ref={command.command_ref if command else ''}",
                    f"command_digest={command.command_digest if command else ''}",
                    "legacy_filesystem_handoff_is_canonical=false",
                    "sql_write_performed=false",
                )
            )
        )
        for issue in result.issues:
            print(f"issue: {issue}", file=sys.stderr)
    return 0 if result.valid else 2


if __name__ == "__main__":
    raise SystemExit(main())
