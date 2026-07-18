#!/usr/bin/env python3
"""Check one correlated GitHub research package without dispatching work."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from context.github_research_work_package_admissibility_0287 import (  # noqa: E402
    GitHubResearchWorkPackageAdmissibilityCommand,
    evaluate_github_research_work_package_admissibility,
)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate one already correlated GitHub research work package. "
            "No Scheduler command or laboratory execution is started."
        )
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    payload = _read_mapping(args.input)
    package = _extract_work_package(payload)
    result = evaluate_github_research_work_package_admissibility(
        GitHubResearchWorkPackageAdmissibilityCommand(work_package=package)
    ).to_mapping()
    if args.output is not None:
        _write_json_atomic(args.output, result)
    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(
            " ".join(
                (
                    f"admissible={result['admissible']}",
                    f"status={result['status']}",
                    f"repository={result['repository'] or '-'}",
                    f"run_id={result['run_id'] or '-'}",
                    f"issue={result['issue_number'] or '-'}",
                    "scheduler_dispatch_started=false",
                    "laboratory_execution_started=false",
                )
            )
        )
        for issue in result["issues"]:
            print(f"issue: {issue}")
    return 0 if result["admissible"] else 2


def _extract_work_package(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    if payload.get("schema") == "missipy.research.correlated_work_package_build.v1":
        value = payload.get("work_package")
        if not isinstance(value, Mapping):
            raise SystemExit("work-package build result has no work_package mapping")
        return value
    return payload


def _read_mapping(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise SystemExit("input must contain a JSON object")
    return payload


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
