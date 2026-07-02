#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path


_REPORT_SCHEMA = "missipy.dot_code_rule_reference_cleanup.v1"
_CODE_RULE_PATTERN = re.compile(r"code[_ -]?rule", re.IGNORECASE)


@dataclass(frozen=True)
class DotCodeRuleCleanupChange:
    path: Path
    removed_line_count: int

    def to_json_dict(self, root: Path) -> dict[str, object]:
        return {
            "path": self.path.resolve().relative_to(root.resolve()).as_posix(),
            "removed_line_count": self.removed_line_count,
        }


@dataclass(frozen=True)
class DotCodeRuleCleanupReport:
    root: Path
    checked_file_count: int
    changed_file_count: int
    removed_line_count: int
    changes: tuple[DotCodeRuleCleanupChange, ...]

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": _REPORT_SCHEMA,
            "root": str(self.root),
            "checked_file_count": self.checked_file_count,
            "changed_file_count": self.changed_file_count,
            "removed_line_count": self.removed_line_count,
            "changes": [change.to_json_dict(self.root) for change in self.changes],
        }


def build_dot_code_rule_cleanup_report(
    root: Path,
    *,
    apply: bool = False,
    dot_dir: Path | None = None,
) -> DotCodeRuleCleanupReport:
    """Remove code_rule clutter from Graphviz DOT architecture diagrams.

    The cleanup is intentionally narrow: it only removes DOT lines mentioning
    code_rule / code-rule / code rule. It does not touch SVG files.
    """

    root = root.resolve()
    scan_root = root / dot_dir if dot_dir is not None and not dot_dir.is_absolute() else dot_dir
    if scan_root is None:
        scan_root = root / "doc" / "docs" / "architecture"

    changes: list[DotCodeRuleCleanupChange] = []
    checked = 0

    for path in sorted(scan_root.rglob("*.dot")):
        checked += 1
        original = path.read_text(encoding="utf-8")
        cleaned, removed_line_count = remove_code_rule_reference_lines(original)
        if removed_line_count == 0:
            continue

        if apply:
            path.write_text(cleaned, encoding="utf-8")

        changes.append(
            DotCodeRuleCleanupChange(
                path=path,
                removed_line_count=removed_line_count,
            )
        )

    return DotCodeRuleCleanupReport(
        root=root,
        checked_file_count=checked,
        changed_file_count=len(changes),
        removed_line_count=sum(change.removed_line_count for change in changes),
        changes=tuple(changes),
    )


def remove_code_rule_reference_lines(text: str) -> tuple[str, int]:
    """Return DOT text with code_rule-related lines removed."""

    lines = text.splitlines(keepends=True)
    kept: list[str] = []
    removed = 0

    for line in lines:
        if _CODE_RULE_PATTERN.search(line):
            removed += 1
            continue
        kept.append(line)

    cleaned = "".join(kept)
    if text.endswith("\n") and cleaned and not cleaned.endswith("\n"):
        cleaned += "\n"
    return cleaned, removed


def assert_dot_code_rule_references_absent(root: Path, *, dot_dir: Path | None = None) -> None:
    root = root.resolve()
    scan_root = root / dot_dir if dot_dir is not None and not dot_dir.is_absolute() else dot_dir
    if scan_root is None:
        scan_root = root / "doc" / "docs" / "architecture"

    offenders: list[str] = []
    for path in sorted(scan_root.rglob("*.dot")):
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if _CODE_RULE_PATTERN.search(line):
                offenders.append(f"{path.relative_to(root).as_posix()}:{lineno}: {line.strip()}")

    if offenders:
        raise AssertionError("code_rule references remain in DOT files:\n" + "\n".join(offenders))


def write_dot_code_rule_cleanup_report(path: Path, report: DotCodeRuleCleanupReport) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def render_dot_code_rule_cleanup_report(report: DotCodeRuleCleanupReport) -> str:
    lines = [
        "dot code_rule cleanup",
        f"root: {report.root}",
        f"checked_files: {report.checked_file_count}",
        f"changed_files: {report.changed_file_count}",
        f"removed_lines: {report.removed_line_count}",
    ]
    for change in report.changes:
        lines.append(
            f"- {change.path.relative_to(report.root).as_posix()}: removed {change.removed_line_count} line(s)"
        )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Remove code_rule references from DOT architecture graphs.")
    parser.add_argument("--root", type=Path, default=Path("."), help="repository root")
    parser.add_argument(
        "--dot-dir",
        type=Path,
        default=Path("doc/docs/architecture"),
        help="DOT directory relative to root",
    )
    parser.add_argument("--apply", action="store_true", help="rewrite DOT files")
    parser.add_argument("--check", action="store_true", help="fail if code_rule references remain")
    parser.add_argument(
        "--report-file",
        type=Path,
        default=Path("doc/maintenance/dot_code_rule_cleanup_report.json"),
        help="JSON cleanup report path",
    )
    args = parser.parse_args()

    report = build_dot_code_rule_cleanup_report(args.root, apply=args.apply, dot_dir=args.dot_dir)
    write_dot_code_rule_cleanup_report(args.report_file, report)
    print(render_dot_code_rule_cleanup_report(report))

    if args.check:
        assert_dot_code_rule_references_absent(args.root, dot_dir=args.dot_dir)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
