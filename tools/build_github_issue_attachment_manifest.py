#!/usr/bin/env python3
"""Build a GitHub issue attachment manifest from an event payload.

0170 performs no GitHub API call and no remote mutation. It only parses the
event payload produced by GitHub Actions and writes attachment-reference
metadata that can be uploaded as a GitHub Actions artifact.
"""

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


from context.github_issue_attachment_manifest import build_github_issue_attachment_manifest  # noqa: E402


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an attachment manifest from a GitHub issue event payload.")
    parser.add_argument("--event-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("out/autodoc-artifacts"))
    parser.add_argument("--format", choices=("json", "text"), default="text")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    event = json.loads(args.event_path.read_text(encoding="utf-8"))
    issue = event.get("issue") if isinstance(event.get("issue"), Mapping) else {}
    repository = _repository_full_name(event)
    issue_number = int(issue.get("number", 0))
    issue_url = str(issue.get("html_url", ""))
    body = str(issue.get("body", "") or "")
    manifest = build_github_issue_attachment_manifest(
        repository=repository,
        issue_number=issue_number,
        issue_url=issue_url,
        body=body,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_path = args.output_dir / "attachment_manifest.json"
    output_path.write_text(json.dumps(manifest.to_json_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")

    report = {
        "schema": "missipy.github_issue.attachment_manifest_build_report.v1",
        "status": "ok",
        "repository": repository,
        "issue_number": issue_number,
        "output_path": str(output_path),
        "attachment_count": len(manifest.attachments),
        "github_api_called": False,
        "remote_mutation_performed": False,
        "boundary": [
            "event payload only",
            "attachment references only",
            "no GitHub API call",
            "no remote mutation",
            "no user artifacts in Autodoc repository",
        ],
    }
    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"status: {report['status']}")
        print(f"attachment_count: {report['attachment_count']}")
        print(f"output_path: {output_path}")
    return 0


def _repository_full_name(event: Mapping[str, Any]) -> str:
    repository = event.get("repository")
    if isinstance(repository, Mapping) and repository.get("full_name"):
        return str(repository["full_name"])
    return ""


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
