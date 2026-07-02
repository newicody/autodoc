#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from context.source_candidate_external_probe_bundle import (  # noqa: E402
    build_source_candidate_external_probe_bundle,
    render_source_candidate_external_probe_bundle,
)


_PLAN_SCHEMA = "missipy.source_candidate.external_probe_bundle_cli_plan.v1"


@dataclass(frozen=True)
class SourceCandidateExternalProbeBundleCliPlan:
    output_dir: Path
    operator_review_report_path: Path
    probe_request_path: Path
    probe_result_path: Path
    apply: bool

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _PLAN_SCHEMA,
            "output_dir": str(self.output_dir),
            "operator_review_report_path": str(self.operator_review_report_path),
            "probe_request_path": str(self.probe_request_path),
            "probe_result_path": str(self.probe_result_path),
            "apply": self.apply,
            "writes_bundle": self.apply,
        }


def build_source_candidate_external_probe_bundle_cli_plan(
    *,
    output_dir: Path,
    operator_review_report_path: Path,
    probe_request_path: Path,
    probe_result_path: Path,
    apply: bool = False,
) -> SourceCandidateExternalProbeBundleCliPlan:
    return SourceCandidateExternalProbeBundleCliPlan(
        output_dir=output_dir,
        operator_review_report_path=operator_review_report_path,
        probe_request_path=probe_request_path,
        probe_result_path=probe_result_path,
        apply=apply,
    )


def render_source_candidate_external_probe_bundle_cli_plan(
    plan: SourceCandidateExternalProbeBundleCliPlan,
) -> str:
    mode = "apply" if plan.apply else "dry-run"
    return "\n".join(
        [
            f"external probe bundle cli: {mode}",
            f"output_dir: {plan.output_dir}",
            f"operator_review_report_path: {plan.operator_review_report_path}",
            f"probe_request_path: {plan.probe_request_path}",
            f"probe_result_path: {plan.probe_result_path}",
            f"writes_bundle: {plan.apply}",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Plan or create a local SourceCandidate external probe bundle."
    )
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--operator-review-report", type=Path, required=True)
    parser.add_argument("--probe-request", type=Path, required=True)
    parser.add_argument("--probe-result", type=Path, required=True)
    parser.add_argument("--apply", action="store_true", help="write the local bundle")
    parser.add_argument("--json", action="store_true", help="print JSON output")
    args = parser.parse_args(argv)

    plan = build_source_candidate_external_probe_bundle_cli_plan(
        output_dir=args.output_dir,
        operator_review_report_path=args.operator_review_report,
        probe_request_path=args.probe_request,
        probe_result_path=args.probe_result,
        apply=args.apply,
    )

    if not plan.apply:
        if args.json:
            print(json.dumps(plan.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(render_source_candidate_external_probe_bundle_cli_plan(plan))
        return 0

    bundle = build_source_candidate_external_probe_bundle(
        output_dir=plan.output_dir,
        operator_review_report_path=plan.operator_review_report_path,
        probe_request_path=plan.probe_request_path,
        probe_result_path=plan.probe_result_path,
    )

    if args.json:
        print(json.dumps(bundle.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(render_source_candidate_external_probe_bundle(bundle))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
