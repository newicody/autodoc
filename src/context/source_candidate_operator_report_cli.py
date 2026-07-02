from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Sequence

from .source_candidate import allowed_source_candidate_statuses
from .source_candidate_operator_report import (
    SourceCandidateOperatorReportPolicy,
    SourceCandidateOperatorReportResult,
    build_source_candidate_operator_report,
)
from .source_candidate_review import SourceCandidateReviewCommand, SourceCandidateReviewPolicy
from .source_candidate_review_audit import SourceCandidateReviewAuditPolicy
from .source_candidate_review_audit_cli import run_source_candidate_review_audit_via_scheduler
from .source_candidate_store import SourceCandidateStorePolicy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build a local SourceCandidate operator report from review and audit summaries."
    )
    parser.add_argument("--store-file", required=True, help="Path to source_candidates.json")
    parser.add_argument("--repository", default="newicody/autodoc")
    parser.add_argument("--include-terminal", action="store_true")
    parser.add_argument(
        "--status",
        action="append",
        choices=allowed_source_candidate_statuses(),
        default=[],
        help="Filter by status. May be repeated.",
    )
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--body-preview-chars", type=int, default=160)
    parser.add_argument("--audit-file", action="append", default=[])
    parser.add_argument("--audit-dir")
    parser.add_argument("--max-next-actions", type=int, default=20)
    parser.add_argument("--hide-items", action="store_true")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def review_command_from_args(args: argparse.Namespace) -> SourceCandidateReviewCommand:
    return SourceCandidateReviewCommand(
        store_policy=SourceCandidateStorePolicy(
            path=args.store_file,
            repository=args.repository,
        ),
        review_policy=SourceCandidateReviewPolicy(
            include_terminal=args.include_terminal,
            status_filter=tuple(args.status or ()),
            limit=args.limit,
            body_preview_chars=args.body_preview_chars,
        ),
    )


def audit_policy_from_args(args: argparse.Namespace) -> SourceCandidateReviewAuditPolicy:
    return SourceCandidateReviewAuditPolicy(
        audit_paths=tuple(args.audit_file or ()),
        audit_dir=args.audit_dir,
    )


def report_policy_from_args(args: argparse.Namespace) -> SourceCandidateOperatorReportPolicy:
    return SourceCandidateOperatorReportPolicy(
        include_items=not args.hide_items,
        max_next_actions=args.max_next_actions,
    )


async def run_source_candidate_operator_report_via_scheduler(
    command: SourceCandidateReviewCommand,
    audit_policy: SourceCandidateReviewAuditPolicy,
    report_policy: SourceCandidateOperatorReportPolicy,
) -> SourceCandidateOperatorReportResult:
    review_audit = await run_source_candidate_review_audit_via_scheduler(
        command,
        audit_policy,
    )
    return build_source_candidate_operator_report(review_audit, report_policy)


def render_source_candidate_operator_report_result(
    result: SourceCandidateOperatorReportResult,
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
    result = asyncio.run(
        run_source_candidate_operator_report_via_scheduler(
            review_command_from_args(args),
            audit_policy_from_args(args),
            report_policy_from_args(args),
        )
    )
    print(render_source_candidate_operator_report_result(result, args.format))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
