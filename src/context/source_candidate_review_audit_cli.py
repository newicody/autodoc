from __future__ import annotations

import argparse
import asyncio
import json
from collections.abc import Sequence
from pathlib import Path

from .source_candidate import allowed_source_candidate_statuses
from .source_candidate_review import SourceCandidateReviewCommand, SourceCandidateReviewPolicy
from .source_candidate_review_audit import (
    SourceCandidateReviewAuditPolicy,
    SourceCandidateReviewAuditResult,
    enrich_source_candidate_review_with_audit,
)
from .source_candidate_review_cli import run_source_candidate_review_via_scheduler
from .source_candidate_store import SourceCandidateStorePolicy


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Review local SourceCandidate store with decision/audit summaries."
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
    parser.add_argument("--format", choices=("text", "json"), default="text")
    return parser


def command_from_args(args: argparse.Namespace) -> SourceCandidateReviewCommand:
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
        audit_paths=tuple(Path(path) for path in args.audit_file),
        audit_dir=Path(args.audit_dir) if args.audit_dir else None,
    )


async def run_source_candidate_review_audit_via_scheduler(
    command: SourceCandidateReviewCommand,
    audit_policy: SourceCandidateReviewAuditPolicy,
) -> SourceCandidateReviewAuditResult:
    review = await run_source_candidate_review_via_scheduler(command)
    return enrich_source_candidate_review_with_audit(review, audit_policy)


def render_source_candidate_review_audit_result(
    result: SourceCandidateReviewAuditResult,
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
    command = command_from_args(args)
    result = asyncio.run(
        run_source_candidate_review_audit_via_scheduler(command, audit_policy_from_args(args))
    )
    print(render_source_candidate_review_audit_result(result, args.format))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
