from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Sequence

from .source_candidate_operator_report_cli import (
    audit_policy_from_args,
    report_policy_from_args,
    review_command_from_args,
    run_source_candidate_operator_report_via_scheduler,
)
from .source_candidate_operator_report_file import (
    SourceCandidateOperatorReportFilePolicy,
    SourceCandidateOperatorReportFileResult,
    write_source_candidate_operator_report_file,
)


def build_parser() -> argparse.ArgumentParser:
    from .source_candidate_operator_report_cli import build_parser as build_report_parser

    parser = build_report_parser()
    parser.description = "Build and write a local SourceCandidate operator report artifact."
    parser.add_argument("--output-file", required=True, help="Path to the report artifact to write")
    parser.add_argument(
        "--output-format",
        choices=("json", "text"),
        default=None,
        help="Artifact format. Defaults to --format.",
    )
    return parser


def file_policy_from_args(args: argparse.Namespace) -> SourceCandidateOperatorReportFilePolicy:
    return SourceCandidateOperatorReportFilePolicy(
        path=args.output_file,
        output_format=args.output_format or args.format,
    )


async def run_source_candidate_operator_report_file_via_scheduler(
    args: argparse.Namespace,
) -> SourceCandidateOperatorReportFileResult:
    report = await run_source_candidate_operator_report_via_scheduler(
        review_command_from_args(args),
        audit_policy_from_args(args),
        report_policy_from_args(args),
    )
    return write_source_candidate_operator_report_file(report, file_policy_from_args(args))


def render_source_candidate_operator_report_file_result(
    result: SourceCandidateOperatorReportFileResult,
    output_format: str,
) -> str:
    if output_format == "json":
        return json.dumps(result.to_json_dict(), ensure_ascii=False, sort_keys=True, indent=2)
    if output_format == "text":
        return (
            "SourceCandidate operator report artifact\n"
            f"path: {result.path}\n"
            f"format: {result.output_format}\n"
            f"bytes: {result.byte_count}"
        )
    raise ValueError("format must be text or json")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = asyncio.run(run_source_candidate_operator_report_file_via_scheduler(args))
    print(render_source_candidate_operator_report_file_result(result, args.format))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
