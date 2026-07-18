#!/usr/bin/env python3
"""Build authorized Scheduler requests from admissible GitHub research results.

The command accepts either:
- one r16-r6 route candidate;
- one r16-r6 admissibility result;
- one r16-r7 report containing multiple evaluated results.

It writes an optional local JSON report but never emits into Scheduler and
never executes the laboratory.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from context.github_research_scheduler_intake_0287 import (  # noqa: E402
    GitHubResearchAutomaticSchedulerPolicy,
    GitHubResearchSchedulerIntakeCommand,
    build_authorized_scheduler_intake_for_admissible_research,
)
from context.github_research_work_package_admissibility_0287 import (  # noqa: E402
    ROUTE_CANDIDATE_SCHEMA,
)

SCHEMA = "missipy.github.research_scheduler_intake_report.v1"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Transform admissible GitHub research candidates into authorized "
            "Scheduler route requests without dispatching them."
        )
    )
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--requested-at")
    parser.add_argument("--priority", type=int, default=60)
    parser.add_argument("--disable-automatic-policy", action="store_true")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--format", choices=("json", "summary"), default="summary")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    source_path = _absolute(args.input)
    issues: list[str] = []
    payload = _read_json_mapping(source_path, issues)
    candidates = _extract_route_candidates(payload, issues)
    requested_at = args.requested_at or _utc_now()

    results: list[dict[str, Any]] = []
    if not issues:
        try:
            policy = GitHubResearchAutomaticSchedulerPolicy(
                enabled=not args.disable_automatic_policy,
                priority=args.priority,
            )
            for candidate in candidates:
                result = build_authorized_scheduler_intake_for_admissible_research(
                    GitHubResearchSchedulerIntakeCommand(
                        route_candidate=candidate,
                        requested_at=requested_at,
                        policy=policy,
                    )
                )
                results.append(result.to_mapping())
        except (TypeError, ValueError) as exc:
            issues.append(str(exc))

    valid = not issues and all(result.get("valid") is True for result in results)
    authorized_count = sum(
        1 for result in results if result.get("authorized") is True
    )
    report = {
        "schema": SCHEMA,
        "valid": valid,
        "status": (
            "rejected"
            if issues
            else "scheduler-requests-ready"
            if results and authorized_count == len(results)
            else "partially-ready"
            if results
            else "nothing-admissible"
        ),
        "issues": issues,
        "source": str(source_path),
        "requested_at": requested_at,
        "counts": {
            "candidate_count": len(candidates),
            "authorized_count": authorized_count,
            "rejected_count": len(results) - authorized_count,
        },
        "results": results,
        "boundaries": {
            "automatic_policy_is_explicit": True,
            "existing_scheduler_intake_reused": True,
            "existing_scheduler_route_adapter_reused": True,
            "scheduler_modified": False,
            "scheduler_dispatch_started": False,
            "laboratory_execution_started": False,
            "sql_write_performed": False,
            "qdrant_write_performed": False,
            "github_mutation_performed": False,
        },
    }
    if args.output is not None:
        _write_json_atomic(_absolute(args.output), report)
    _emit(report, args.format)
    return 0 if valid else 2


def _extract_route_candidates(
    payload: Mapping[str, Any],
    issues: list[str],
) -> list[dict[str, Any]]:
    if payload.get("schema") == ROUTE_CANDIDATE_SCHEMA:
        return [dict(payload)]

    direct = payload.get("route_candidate")
    if isinstance(direct, Mapping):
        if payload.get("admissible") is not True:
            issues.append("admissibility result is not admissible")
            return []
        return [dict(direct)]

    results = payload.get("results")
    if isinstance(results, list):
        candidates: list[dict[str, Any]] = []
        for index, result in enumerate(results):
            if not isinstance(result, Mapping):
                issues.append(f"results[{index}] must be an object")
                continue
            if result.get("admissible") is not True:
                continue
            admissibility = result.get("admissibility")
            if not isinstance(admissibility, Mapping):
                issues.append(
                    f"results[{index}] has no admissibility object"
                )
                continue
            candidate = admissibility.get("route_candidate")
            if not isinstance(candidate, Mapping):
                issues.append(
                    f"results[{index}] has no route_candidate"
                )
                continue
            candidates.append(dict(candidate))
        return candidates

    issues.append("input contains no supported admissible route candidate")
    return []


def _read_json_mapping(path: Path, issues: list[str]) -> dict[str, Any]:
    if not path.is_file():
        issues.append(f"input not found: {path}")
        return {}
    try:
        decoded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        issues.append(f"input is unreadable: {exc}")
        return {}
    if not isinstance(decoded, Mapping):
        issues.append("input must contain a JSON object")
        return {}
    return dict(decoded)


def _absolute(path: Path) -> Path:
    return path if path.is_absolute() else _REPO_ROOT / path


def _utc_now() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _emit(payload: Mapping[str, Any], output_format: str) -> None:
    if output_format == "json":
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return
    counts = payload.get("counts")
    counts = counts if isinstance(counts, Mapping) else {}
    print(
        " ".join(
            (
                f"valid={payload.get('valid')}",
                f"status={payload.get('status')}",
                f"candidates={counts.get('candidate_count', 0)}",
                f"authorized={counts.get('authorized_count', 0)}",
                "scheduler_dispatch_started=false",
                "laboratory_execution_started=false",
            )
        )
    )
    for issue in payload.get("issues", []):
        print(f"issue: {issue}")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
