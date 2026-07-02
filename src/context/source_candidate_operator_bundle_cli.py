from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Sequence

from .source_candidate_operator_bundle import (
    SourceCandidateOperatorBundlePolicy,
    SourceCandidateOperatorBundleResult,
    write_source_candidate_operator_bundle,
)
from .source_candidate_operator_report_cli import (
    audit_policy_from_args,
    report_policy_from_args,
    review_command_from_args,
    run_source_candidate_operator_report_via_scheduler,
)


def build_parser() -> argparse.ArgumentParser:
    from .source_candidate_operator_report_cli import build_parser as build_report_parser

    parser = build_report_parser()
    parser.description = "Build a local SourceCandidate operator bundle directory."
    parser.add_argument("--bundle-dir", required=True, help="Directory where bundle artifacts are written")
    parser.add_argument("--manifest-name", default="manifest.json")
    parser.add_argument("--json-name", default="operator_report.json")
    parser.add_argument("--text-name", default="operator_report.txt")
    parser.add_argument("--no-json", action="store_true", help="Do not write the JSON report artifact")
    parser.add_argument("--no-text", action="store_true", help="Do not write the text report artifact")
    return parser


def bundle_policy_from_args(args: argparse.Namespace) -> SourceCandidateOperatorBundlePolicy:
    return SourceCandidateOperatorBundlePolicy(
        path=args.bundle_dir,
        include_json=not args.no_json,
        include_text=not args.no_text,
        manifest_name=args.manifest_name,
        json_name=args.json_name,
        text_name=args.text_name,
    )


async def run_source_candidate_operator_bundle_via_scheduler(
    args: argparse.Namespace,
) -> SourceCandidateOperatorBundleResult:
    report = await run_source_candidate_operator_report_via_scheduler(
        review_command_from_args(args),
        audit_policy_from_args(args),
        report_policy_from_args(args),
    )
    return write_source_candidate_operator_bundle(report, bundle_policy_from_args(args))


def render_source_candidate_operator_bundle_result(
    result: SourceCandidateOperatorBundleResult,
    output_format: str,
) -> str:
    if output_format == "json":
        return json.dumps(result.to_json_dict(), ensure_ascii=False, sort_keys=True, indent=2)
    if output_format == "text":
        return result.to_text()
    raise ValueError("format must be text or json")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = asyncio.run(run_source_candidate_operator_bundle_via_scheduler(args))
    print(render_source_candidate_operator_bundle_result(result, args.format))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
