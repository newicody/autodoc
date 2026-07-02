#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from tools.markdown_doc_layout import (  # noqa: E402
    MarkdownLayoutPlan,
    apply_markdown_layout_plan,
    build_markdown_layout_plan,
)


_REPORT_SCHEMA = "missipy.markdown_doc_layout_migration.v1"


@dataclass(frozen=True)
class MarkdownDocMigrationResult:
    root: Path
    move_count: int
    test_file_update_count: int
    report_path: Path | None

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _REPORT_SCHEMA,
            "root": str(self.root),
            "move_count": self.move_count,
            "test_file_update_count": self.test_file_update_count,
            "report_path": str(self.report_path) if self.report_path is not None else None,
        }


def apply_markdown_doc_layout_migration(
    root: Path,
    *,
    report_path: Path | None = None,
    apply: bool = False,
) -> MarkdownDocMigrationResult:
    """Plan/apply the Markdown doc layout migration and update tests."""

    root = root.resolve()
    plan = build_markdown_layout_plan(root)
    replacement_map = _replacement_map(plan)

    test_updates = 0
    if apply:
        apply_markdown_layout_plan(plan)
        test_updates = rewrite_python_doc_references(root, replacement_map)

    if report_path is not None:
        _write_report(report_path, plan, replacement_map, test_updates)

    return MarkdownDocMigrationResult(
        root=root,
        move_count=len(plan.moves),
        test_file_update_count=test_updates,
        report_path=report_path,
    )


def rewrite_python_doc_references(root: Path, replacements: Mapping[str, str]) -> int:
    """Rewrite Python test references to moved Markdown files."""

    tests_dir = root / "tests"
    if not tests_dir.exists():
        return 0

    updated_count = 0
    for path in sorted(tests_dir.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        updated = rewrite_python_doc_reference_text(text, replacements)
        if updated != text:
            path.write_text(updated, encoding="utf-8")
            updated_count += 1
    return updated_count


def rewrite_python_doc_reference_text(text: str, replacements: Mapping[str, str]) -> str:
    updated = text

    for old, new in sorted(replacements.items(), key=lambda item: len(item[0]), reverse=True):
        updated = updated.replace(f'"{old}"', f'"{new}"')
        updated = updated.replace(f"'{old}'", f"'{new}'")

    updated = _rewrite_phase_report_literals(updated)
    updated = _rewrite_manifest_literals(updated)
    updated = _rewrite_changelog_literals(updated)
    updated = updated.replace('"doc/code_rule.md"', '"doc/code-rules/code_rule.md"')
    updated = updated.replace("'doc/code_rule.md'", "'doc/code-rules/code_rule.md'")

    return updated


def _replacement_map(plan: MarkdownLayoutPlan) -> dict[str, str]:
    return {
        move.source.relative_to(plan.root).as_posix(): move.target.relative_to(plan.root).as_posix()
        for move in plan.moves
    }


def _rewrite_phase_report_literals(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        quote = match.group("quote")
        name = match.group("name")
        phase = match.group("phase")
        return f"{quote}doc/reports/phase{phase}/{name}{quote}"

    return re.sub(
        r'(?P<quote>["\'])(?P<name>PHASE(?P<phase>\d+)[^"\']*(?:TEST_REPORT|AUDIT_REPORT|CODE_STYLE_AUDIT|REBUILD_REPORT|REPORT)[^"\']*\.md)(?P=quote)',
        repl,
        text,
    )


def _rewrite_manifest_literals(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        quote = match.group("quote")
        name = match.group("name")
        return f"{quote}doc/manifests/{name}{quote}"

    return re.sub(
        r'(?P<quote>["\'])(?P<name>MANIFEST[^"\']*\.md)(?P=quote)',
        repl,
        text,
    )


def _rewrite_changelog_literals(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        quote = match.group("quote")
        name = match.group("name")
        return f"{quote}doc/changelogs/{name}{quote}"

    return re.sub(
        r'(?P<quote>["\'])(?P<name>CHANGELOG[^"\']*\.md)(?P=quote)',
        repl,
        text,
    )


def _write_report(
    report_path: Path,
    plan: MarkdownLayoutPlan,
    replacements: Mapping[str, str],
    test_updates: int,
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "schema": _REPORT_SCHEMA,
        "root": str(plan.root),
        "move_count": len(plan.moves),
        "test_file_update_count": test_updates,
        "moves": plan.to_json_dict()["moves"],
        "python_reference_replacements": dict(sorted(replacements.items())),
    }
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply Markdown doc layout migration and update tests.")
    parser.add_argument("--root", type=Path, default=Path("."), help="repository root")
    parser.add_argument("--apply", action="store_true", help="move files and rewrite tests")
    parser.add_argument(
        "--report-file",
        type=Path,
        default=Path("doc/maintenance/markdown_doc_migration_report.json"),
    )
    args = parser.parse_args()

    result = apply_markdown_doc_layout_migration(
        args.root,
        report_path=args.report_file,
        apply=args.apply,
    )
    print(json.dumps(result.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
