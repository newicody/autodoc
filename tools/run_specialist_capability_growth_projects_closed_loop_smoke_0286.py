#!/usr/bin/env python3
"""Run the pure 0286 Projects closed-loop smoke from JSON artifacts."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
import json
from pathlib import Path
import sys
from typing import Any

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
for _path in (_REPO_ROOT, _SRC_ROOT):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from context.specialist_capability_growth_projects_closed_loop_smoke_0286 import (  # noqa: E402
    SpecialistCapabilityGrowthProjectsClosedLoopSmokeCommand,
    run_specialist_capability_growth_projects_closed_loop_smoke,
)
from context.specialist_capability_growth_projects_readback_readiness_0286 import (  # noqa: E402
    SPECIALIST_CAPABILITY_GROWTH_PROJECTS_READBACK_SCHEMA,
    SpecialistCapabilityGrowthProjectsReadbackEvidence,
)
from tools.apply_specialist_capability_growth_projects_projection_0286 import (  # noqa: E402
    load_publication_plan,
)
from tools.check_specialist_capability_growth_projects_readback_0286 import (  # noqa: E402
    load_execution_result,
)

CLOSED_LOOP_CLI_SCHEMA = (
    "missipy.specialist.capability_growth.projects_closed_loop_smoke_cli.v1"
)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Correlate r5 plan, r6 execution and r7 readback artifacts "
            "without performing any remote effect."
        )
    )
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--execution-result", type=Path, required=True)
    parser.add_argument("--readback", type=Path, required=True)
    parser.add_argument(
        "--require-live-readback",
        action="store_true",
        help=(
            "fail unless the r7 artifact proves a successful live "
            "query-only readback"
        ),
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--format",
        choices=("json", "summary"),
        default="summary",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    for path, label in (
        (args.plan, "r5 publication plan"),
        (args.execution_result, "r6 execution result"),
        (args.readback, "r7 readback evidence"),
    ):
        if not path.is_file():
            raise SystemExit(f"{label} not found: {path}")

    result = run_specialist_capability_growth_projects_closed_loop_smoke(
        SpecialistCapabilityGrowthProjectsClosedLoopSmokeCommand(
            publication_plan=load_publication_plan(args.plan),
            execution_result=load_execution_result(args.execution_result),
            readback_evidence=load_readback_evidence(args.readback),
            require_live_readback=args.require_live_readback,
        )
    )
    report = {
        "schema": CLOSED_LOOP_CLI_SCHEMA,
        "result": result.to_mapping(),
        "boundaries": {
            "smoke_performs_remote_mutation": False,
            "github_projects_authoritative": False,
            "sql_remains_durable_authority": True,
            "scheduler_remains_only_orchestrator": True,
            "qdrant_authoritative": False,
        },
    }
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
    _emit(report, args.format)
    return 0 if result.valid else 3


def load_readback_evidence(
    path: Path,
) -> SpecialistCapabilityGrowthProjectsReadbackEvidence:
    payload = _read_mapping(path)
    raw = _mapping(payload.get("evidence")) or payload
    if raw.get("schema") != (
        SPECIALIST_CAPABILITY_GROWTH_PROJECTS_READBACK_SCHEMA
    ):
        raise ValueError("unexpected r7 readback evidence schema")
    expected = _field_pairs(
        raw.get("expected_projectv2_field_values"),
        "expected_projectv2_field_values",
    )
    actual = _field_pairs(
        raw.get("actual_projectv2_field_values"),
        "actual_projectv2_field_values",
    )
    return SpecialistCapabilityGrowthProjectsReadbackEvidence(
        schema=str(raw["schema"]),
        valid=raw.get("valid") is True,
        action=_required_text(raw.get("action"), "action"),
        issues=tuple(str(item) for item in _sequence(raw.get("issues"))),
        source_mode=_required_text(raw.get("source_mode"), "source_mode"),
        repository=_required_text(raw.get("repository"), "repository"),
        issue_number=_positive_int(
            raw.get("issue_number"),
            "issue_number",
        ),
        project_id=_required_text(raw.get("project_id"), "project_id"),
        project_item_id=_required_text(
            raw.get("project_item_id"),
            "project_item_id",
        ),
        plan_digest=_required_text(
            raw.get("plan_digest"),
            "plan_digest",
        ),
        marker=_required_text(raw.get("marker"), "marker"),
        sql_ref=_required_text(raw.get("sql_ref"), "sql_ref"),
        revision_ref=_required_text(
            raw.get("revision_ref"),
            "revision_ref",
        ),
        decision_ref=_required_text(
            raw.get("decision_ref"),
            "decision_ref",
        ),
        matched_comment_id=_optional_positive_int(
            raw.get("matched_comment_id")
        ),
        matched_comment_url=str(raw.get("matched_comment_url", "")),
        comment_body_sha256=_required_text(
            raw.get("comment_body_sha256"),
            "comment_body_sha256",
        ),
        expected_projectv2_field_values=expected,
        actual_projectv2_field_values=actual,
        publication_execution_verified=(
            raw.get("publication_execution_verified") is True
        ),
        issue_comment_verified=(
            raw.get("issue_comment_verified") is True
        ),
        projectv2_fields_verified=(
            raw.get("projectv2_fields_verified") is True
        ),
        readback_ready=raw.get("readback_ready") is True,
        deployment_ready=raw.get("deployment_ready") is True,
        readback_digest=_required_text(
            raw.get("readback_digest"),
            "readback_digest",
        ),
        remote_query_performed=(
            raw.get("remote_query_performed") is True
        ),
    )


def _read_mapping(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError("JSON input must be an object")
    return dict(payload)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sequence(value: object) -> Sequence[Any]:
    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        return value
    return ()


def _field_pairs(value: object, label: str) -> tuple[tuple[str, str], ...]:
    if isinstance(value, Mapping):
        return tuple(sorted((str(key), str(item)) for key, item in value.items()))
    pairs: list[tuple[str, str]] = []
    for raw in _sequence(value):
        pair = _sequence(raw)
        if len(pair) != 2:
            raise ValueError(f"{label} entries must contain name/value")
        pairs.append((str(pair[0]), str(pair[1])))
    return tuple(sorted(pairs))


def _required_text(value: object, label: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise ValueError(f"{label} is required")
    return text


def _positive_int(value: object, label: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} must be an integer") from exc
    if parsed <= 0:
        raise ValueError(f"{label} must be positive")
    return parsed


def _optional_positive_int(value: object) -> int | None:
    if value is None:
        return None
    return _positive_int(value, "matched_comment_id")


def _emit(report: Mapping[str, object], output_format: str) -> None:
    if output_format == "json":
        print(
            json.dumps(
                report,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return
    result = _mapping(report.get("result"))
    print(f"valid: {result.get('valid', False)}")
    print(f"action: {result.get('action', '-')}")
    print(
        "phase_0286_closed: "
        f"{result.get('phase_0286_closed', False)}"
    )
    print(
        "deployment_closed: "
        f"{result.get('deployment_closed', False)}"
    )
    print(f"plan_digest: {result.get('plan_digest', '-')}")
    print(f"smoke_digest: {result.get('smoke_digest', '-')}")
    for issue in _sequence(result.get("issues")):
        print(f"issue: {issue}")


if __name__ == "__main__":
    raise SystemExit(main())
