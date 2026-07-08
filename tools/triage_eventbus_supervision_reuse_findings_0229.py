#!/usr/bin/env python3
"""Triage the 0228 EventBus supervision reuse audit findings.

This tool is intentionally read-only. It does not inspect live runtime state, does
not import project runtime modules, and does not call Scheduler.run(). It consumes
the JSON report produced by tools/audit_eventbus_supervision_reuse_0228.py and
classifies forbidden evidence so the next functional patch can reuse existing
surfaces without inventing a parallel bus or supervisor.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

DOC_OR_TRACE_PREFIXES = (
    "doc/",
    "tests/",
    "patch/",
    "bad_",
    ".var/",
)
DOC_OR_TRACE_FILENAMES = (
    "README",
    "CHANGELOG",
    "MANIFEST",
    "PHASE",
)
RUNTIME_PREFIXES = (
    "src/",
    "tools/",
)
FORBIDDEN_KEY_PARTS = (
    "forbidden",
    "violation",
    "evidence",
)
DEFAULT_REPORT = ".var/reports/eventbus_supervision_reuse_0228.json"


@dataclass(frozen=True)
class Finding:
    """One evidence item extracted from the 0228 audit report."""

    path: str
    line: int | None
    category: str
    evidence: str
    raw: Mapping[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "line": self.line,
            "category": self.category,
            "evidence": self.evidence,
            "raw": dict(self.raw),
        }


def _stringify(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, sort_keys=True, ensure_ascii=False)


def _first_text(mapping: Mapping[str, Any], names: Sequence[str]) -> str:
    for name in names:
        value = mapping.get(name)
        text = _stringify(value).strip()
        if text:
            return text
    return ""


def _first_int(mapping: Mapping[str, Any], names: Sequence[str]) -> int | None:
    for name in names:
        value = mapping.get(name)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return None


def _looks_like_evidence_mapping(mapping: Mapping[str, Any]) -> bool:
    keys = {str(key).lower() for key in mapping.keys()}
    has_path = any(key in keys for key in ("path", "file", "file_path", "source_path"))
    has_text = any(
        key in keys
        for key in (
            "evidence",
            "match",
            "line_text",
            "snippet",
            "text",
            "pattern",
            "reason",
        )
    )
    return has_path and has_text


def _walk_forbidden_objects(value: Any, parent_key: str = "") -> Iterable[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        lowered = parent_key.lower()
        if _looks_like_evidence_mapping(value) and any(part in lowered for part in FORBIDDEN_KEY_PARTS):
            yield value
        for key, child in value.items():
            child_key = f"{parent_key}.{key}" if parent_key else str(key)
            yield from _walk_forbidden_objects(child, child_key)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_forbidden_objects(child, parent_key)


def _classify_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    name = Path(normalized).name
    if normalized.startswith(DOC_OR_TRACE_PREFIXES) or name.startswith(DOC_OR_TRACE_FILENAMES):
        return "allowed_doc_test_trace"
    if normalized.startswith(RUNTIME_PREFIXES):
        return "runtime_review_required"
    if not normalized:
        return "unknown_review_required"
    return "review_required"


def _finding_from_mapping(mapping: Mapping[str, Any]) -> Finding:
    path = _first_text(mapping, ("path", "file", "file_path", "source_path"))
    line = _first_int(mapping, ("line", "lineno", "line_number", "start_line"))
    evidence = _first_text(
        mapping,
        ("evidence", "match", "line_text", "snippet", "text", "pattern", "reason"),
    )
    return Finding(
        path=path,
        line=line,
        category=_classify_path(path),
        evidence=evidence,
        raw=mapping,
    )


def extract_findings(report: Mapping[str, Any]) -> list[Finding]:
    """Extract forbidden evidence findings from likely 0228 report shapes."""

    explicit = report.get("forbidden_runtime_evidence")
    if explicit is None:
        explicit = report.get("forbidden_runtime_evidence_matches")
    if explicit is None:
        explicit = report.get("forbidden_evidence")

    candidates: list[Mapping[str, Any]] = []
    if isinstance(explicit, list):
        candidates.extend(item for item in explicit if isinstance(item, Mapping))
    else:
        candidates.extend(_walk_forbidden_objects(report))

    findings = [_finding_from_mapping(candidate) for candidate in candidates]
    seen: set[tuple[str, int | None, str]] = set()
    unique: list[Finding] = []
    for finding in findings:
        key = (finding.path, finding.line, finding.evidence)
        if key not in seen:
            seen.add(key)
            unique.append(finding)
    return unique


def build_triage(report: Mapping[str, Any]) -> dict[str, Any]:
    findings = extract_findings(report)
    runtime_review = [item for item in findings if item.category.endswith("review_required")]
    allowed = [item for item in findings if item.category == "allowed_doc_test_trace"]
    return {
        "eventbus_supervision_reuse_findings_triaged": True,
        "source_report_kind": report.get("report_kind") or report.get("kind") or "eventbus_supervision_reuse_0228",
        "input_forbidden_runtime_evidence_count": report.get("forbidden_runtime_evidence_count"),
        "extracted_forbidden_evidence_count": len(findings),
        "allowed_doc_test_trace_count": len(allowed),
        "runtime_review_required_count": len(runtime_review),
        "may_resume_functional_supervision_patch": len(runtime_review) == 0,
        "next_action": (
            "resume EventBus -> PassiveSupervisorSink functional patch"
            if len(runtime_review) == 0
            else "inspect runtime_review_required findings before coding"
        ),
        "findings": [item.as_dict() for item in findings],
        "authority_boundary": {
            "read_only_report_triage": True,
            "uses_scheduler_run": False,
            "creates_eventbus": False,
            "controls_proxy": False,
            "mutates_shm": False,
            "decides_policy": False,
            "writes_sql": False,
            "writes_qdrant": False,
            "mutates_github": False,
            "requires_non_stdlib": False,
        },
    }


def _load_json(path: Path) -> Mapping[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, Mapping):
        raise ValueError(f"expected a JSON object in {path}")
    return data


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", default=DEFAULT_REPORT, help="0228 audit report JSON path")
    parser.add_argument("--output", help="optional output JSON path")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    report = _load_json(Path(args.report))
    triage = build_triage(report)
    if args.output:
        _write_json(Path(args.output), triage)
    if args.format == "summary":
        print(
            "triaged="
            f"{triage['eventbus_supervision_reuse_findings_triaged']} "
            f"extracted={triage['extracted_forbidden_evidence_count']} "
            f"allowed_doc_test_trace={triage['allowed_doc_test_trace_count']} "
            f"runtime_review_required={triage['runtime_review_required_count']} "
            f"may_resume={triage['may_resume_functional_supervision_patch']}"
        )
    else:
        print(json.dumps(triage, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
