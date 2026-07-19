#!/usr/bin/env python3
"""Valider les preuves d'un cycle recherche/amour réellement fermé."""

from __future__ import annotations

import argparse
import csv
import json
from collections.abc import Mapping, Sequence
from pathlib import Path
import sys
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from context.github_research_love_end_to_end_acceptance_0287 import (  # noqa: E402
    EndToEndAcceptanceCommand,
    validate_github_research_love_end_to_end,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--issue-number", type=int, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--fetch-cycle-report", type=Path, required=True)
    parser.add_argument("--prepared-report", type=Path, required=True)
    parser.add_argument("--completed-report", type=Path, required=True)
    parser.add_argument("--temporal-observations-csv", type=Path, required=True)
    parser.add_argument("--minimum-handler-count", type=int, default=10)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(tuple(sys.argv[1:] if argv is None else argv))
    try:
        report = validate_github_research_love_end_to_end(
            EndToEndAcceptanceCommand(
                repository=args.repository,
                issue_number=args.issue_number,
                run_id=str(args.run_id),
                fetch_cycle=_read_mapping(args.fetch_cycle_report),
                prepared_report=_read_mapping(args.prepared_report),
                completed_report=_read_mapping(args.completed_report),
                temporal_observations=_read_csv(args.temporal_observations_csv),
                minimum_handler_count=args.minimum_handler_count,
            )
        )
        payload = report.to_mapping()
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        payload = {
            "schema": "missipy.github.research_love_end_to_end_acceptance.v1",
            "valid": False,
            "status": "rejected",
            "repository": args.repository,
            "issue_number": args.issue_number,
            "run_id": str(args.run_id),
            "issues": [f"{type(exc).__name__}: {exc}"],
            "checks": {},
            "evidence": {},
            "boundaries": {
                "validation_only": True,
                "remote_mutation_performed": False,
            },
        }

    _write_json_atomic(args.output, payload)
    _emit(payload, args.format)
    return 0 if payload.get("valid") is True else 2


def _read_mapping(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, Mapping):
        raise TypeError(f"{path} doit contenir un objet JSON")
    return dict(value)


def _read_csv(path: Path) -> tuple[Mapping[str, str], ...]:
    with path.open("r", encoding="utf-8", newline="") as stream:
        rows = tuple(dict(row) for row in csv.DictReader(stream))
    if not rows:
        raise ValueError(f"{path} ne contient aucune observation")
    return rows


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    target = path if path.is_absolute() else _REPO_ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(target.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(target)


def _emit(payload: Mapping[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return
    print(
        " ".join(
            (
                f"valid={str(payload.get('valid')).lower()}",
                f"status={payload.get('status', '')}",
                f"repository={payload.get('repository', '')}",
                f"issue_number={payload.get('issue_number', '')}",
                f"run_id={payload.get('run_id', '')}",
            )
        )
    )
    for issue in payload.get("issues", ()):
        print(f"issue: {issue}")


if __name__ == "__main__":
    raise SystemExit(main())
