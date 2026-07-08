#!/usr/bin/env python3
"""Audit reusable EventBus/Scheduler/passive supervision surfaces for phase 0228.

This tool is intentionally read-only. It scans repository text for existing
surfaces that should be reused before implementing a direct EventBus passive
supervision sink. It does not import runtime modules, open sockets, write SQL,
query Qdrant, touch GitHub, read /dev/shm, or call Scheduler.run().
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

TEXT_SUFFIXES = {
    ".py",
    ".md",
    ".rst",
    ".txt",
    ".dot",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
}

DEFAULT_SCAN_DIRS = ("src", "tools", "doc", "tests")

SURFACE_PATTERNS: Mapping[str, tuple[str, ...]] = {
    "eventbus": (
        r"\bEventBus\b",
        r"\bevent[_-]?bus\b",
        r"\bpublish\s*\(",
        r"\bsubscribe\s*\(",
        r"\bemit\s*\(",
        r"\bBusEvent\b",
    ),
    "scheduler": (
        r"\bScheduler\b",
        r"\bscheduler\b",
        r"\bScheduler\.run\b",
        r"def\s+run\s*\(",
    ),
    "passive_supervisor": (
        r"passive[_-]?bus[_-]?supervisor",
        r"PassiveSupervisor",
        r"PassiveSupervisorSink",
        r"CellularState",
        r"cellular[_-]?snapshot",
        r"build_cellular_snapshot",
    ),
    "runtime_surfaces": (
        r"RouteProxy",
        r"ControlProxy",
        r"SHM",
        r"shm",
        r"Policy",
        r"policy_decision",
    ),
    "data_surfaces": (
        r"GitHub",
        r"SourceCandidate",
        r"sql_ref",
        r"qdrant_ref",
        r"rehydrat",
        r"pushback",
    ),
}

FORBIDDEN_RUNTIME_PATTERNS: Mapping[str, tuple[str, ...]] = {
    "scheduler_run_invocation": (
        r"Scheduler\s*\([^\n]*\)\.run\s*\(",
        r"\.run\s*\(\s*\)\s*#\s*supervisor",
    ),
    "supervisor_authority_mutation": (
        r"PassiveSupervisor.*(?:write_sql|upsert|qdrant|github|control_proxy|claim_lease)",
        r"supervisor.*(?:policy_decision|decide_policy|mutate_github|write_shm)",
    ),
    "file_path_as_runtime_spine": (
        r"EventBus\s*->\s*events\.jsonl\s*->\s*supervisor",
        r"status\.json\s*->\s*supervisor\s*->\s*runtime",
    ),
}


@dataclass(frozen=True)
class Match:
    surface: str
    path: str
    line: int
    pattern: str
    text: str


def iter_text_files(root: Path, scan_dirs: Sequence[str]) -> Iterable[Path]:
    for scan_dir in scan_dirs:
        base = root / scan_dir
        if not base.exists():
            continue
        if base.is_file():
            candidates = (base,)
        else:
            candidates = (path for path in base.rglob("*") if path.is_file())
        for path in candidates:
            if path.suffix in TEXT_SUFFIXES and ".git" not in path.parts:
                yield path


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def collect_matches(root: Path, patterns: Mapping[str, tuple[str, ...]], scan_dirs: Sequence[str]) -> list[Match]:
    matches: list[Match] = []
    for path in iter_text_files(root, scan_dirs):
        rel = path.relative_to(root).as_posix()
        text = read_text(path)
        lines = text.splitlines()
        for surface, regexes in patterns.items():
            compiled = [re.compile(regex, re.IGNORECASE) for regex in regexes]
            for line_no, line in enumerate(lines, start=1):
                for regex, raw_pattern in zip(compiled, regexes):
                    if regex.search(line):
                        matches.append(
                            Match(
                                surface=surface,
                                path=rel,
                                line=line_no,
                                pattern=raw_pattern,
                                text=line.strip()[:180],
                            )
                        )
    return matches


def group_matches(matches: Sequence[Match]) -> dict[str, list[dict[str, object]]]:
    grouped: dict[str, list[dict[str, object]]] = {}
    for match in matches:
        grouped.setdefault(match.surface, []).append(
            {
                "path": match.path,
                "line": match.line,
                "pattern": match.pattern,
                "text": match.text,
            }
        )
    return grouped


def summarize_surface(grouped: Mapping[str, list[dict[str, object]]]) -> dict[str, dict[str, object]]:
    summary: dict[str, dict[str, object]] = {}
    for surface in SURFACE_PATTERNS:
        entries = grouped.get(surface, [])
        paths = sorted({str(entry["path"]) for entry in entries})
        summary[surface] = {
            "found": bool(entries),
            "match_count": len(entries),
            "files": paths[:25],
            "truncated_files": max(0, len(paths) - 25),
        }
    return summary


def build_reuse_recommendations(summary: Mapping[str, Mapping[str, object]]) -> list[str]:
    recommendations: list[str] = []
    if summary["eventbus"]["found"]:
        recommendations.append("reuse_or_extend_existing_eventbus_surface_before_adding_any_bus")
    else:
        recommendations.append("document_missing_eventbus_surface_before_adding_any_bus")
    if summary["scheduler"]["found"]:
        recommendations.append("keep_scheduler_upstream_authority_and_do_not_call_scheduler_run_from_supervisor")
    else:
        recommendations.append("audit_scheduler_location_before_functional_supervisor_integration")
    if summary["passive_supervisor"]["found"]:
        recommendations.append("extend_existing_passive_supervisor_cellular_state_instead_of_parallel_bridge")
    else:
        recommendations.append("create_passive_supervisor_only_after_documenting_no_existing_surface")
    recommendations.append("keep_snapshot_and_events_jsonl_optional_audit_replay_outputs")
    recommendations.append("keep_supervisor_downstream_only_no_proxy_shm_policy_sql_qdrant_github_mutation")
    return recommendations


def build_report(root: Path, scan_dirs: Sequence[str]) -> dict[str, object]:
    root = root.resolve()
    matches = collect_matches(root, SURFACE_PATTERNS, scan_dirs)
    forbidden = collect_matches(root, FORBIDDEN_RUNTIME_PATTERNS, scan_dirs)
    grouped = group_matches(matches)
    forbidden_grouped = group_matches(forbidden)
    summary = summarize_surface(grouped)
    return {
        "phase": "0228",
        "name": "eventbus_supervision_reuse_audit",
        "repo_root": str(root),
        "scan_dirs": list(scan_dirs),
        "read_only": True,
        "runtime_side_effects": False,
        "scheduler_run_called": False,
        "authority_boundary": {
            "eventbus_is_transport": True,
            "scheduler_is_upstream_authority": True,
            "supervisor_is_downstream_observer": True,
            "snapshot_optional": True,
            "audit_replay_optional": True,
            "allows_new_bus_without_audit": False,
            "allows_scheduler_run": False,
            "allows_proxy_control": False,
            "allows_shm_mutation": False,
            "allows_policy_decision": False,
            "allows_sql_write": False,
            "allows_qdrant_write": False,
            "allows_github_mutation": False,
        },
        "surface_summary": summary,
        "matches": grouped,
        "forbidden_runtime_evidence": forbidden_grouped,
        "forbidden_runtime_evidence_count": len(forbidden),
        "reuse_recommendations": build_reuse_recommendations(summary),
        "functional_resumption_gate": {
            "audit_executed": True,
            "reuse_decision_required_before_runtime_patch": True,
            "may_implement_direct_sink_after_review": True,
        },
    }


def write_json(path: Path, report: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Repository root to scan.")
    parser.add_argument(
        "--scan-dir",
        action="append",
        dest="scan_dirs",
        default=None,
        help="Directory or file to scan. May be provided multiple times. Defaults to src/tools/doc/tests.",
    )
    parser.add_argument("--output", type=Path, help="Optional JSON report output path.")
    parser.add_argument("--format", choices=("json", "summary"), default="json")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    scan_dirs = tuple(args.scan_dirs or DEFAULT_SCAN_DIRS)
    report = build_report(args.root, scan_dirs)
    if args.output:
        write_json(args.output, report)
    if args.format == "summary":
        summary = report["surface_summary"]
        assert isinstance(summary, dict)
        for surface, data in summary.items():
            assert isinstance(data, dict)
            print(f"{surface}: found={data['found']} matches={data['match_count']}")
        print(f"forbidden_runtime_evidence_count: {report['forbidden_runtime_evidence_count']}")
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
