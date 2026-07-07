#!/usr/bin/env python3
"""Check GitHub project push frame config and render/update fcron table text."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from typing import Sequence


_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))


from context.github_project_push_frame_config import (  # noqa: E402
    build_fcron_entry,
    build_fcron_marker,
    load_github_artifact_scan_config,
    render_config_check,
    upsert_fcron_table,
    validate_github_artifact_scan_config,
)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate project push frame ConfigObj config and fcron table block.")
    parser.add_argument("--config", type=Path, default=Path("config/github_project_push_frame.example.ini"))
    parser.add_argument("--output-dir", type=Path, default=Path(".var/smoke/artifacts/0165"))
    parser.add_argument("--fcrontab-path", type=Path, default=None)
    parser.add_argument("--write-fcrontab", action="store_true")
    parser.add_argument("--format", choices=("json", "markdown"), default="markdown")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    config = load_github_artifact_scan_config(args.config)
    validation = validate_github_artifact_scan_config(config)
    marker = build_fcron_marker(config)
    entry = build_fcron_entry(config)

    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    table_target = args.fcrontab_path or config.fcron_table_path
    existing = table_target.read_text(encoding="utf-8") if table_target.exists() else ""
    table_candidate = upsert_fcron_table(existing, entry, marker)

    candidate_path = output_dir / "fcrontab_candidate.txt"
    report_json_path = output_dir / "github_project_push_frame_config_check.json"
    report_md_path = output_dir / "github_project_push_frame_config_check.md"
    candidate_path.write_text(table_candidate, encoding="utf-8")
    if args.write_fcrontab:
        table_target.parent.mkdir(parents=True, exist_ok=True)
        table_target.write_text(table_candidate, encoding="utf-8")

    report = {
        "schema": "missipy.github_project.project_push_frame_fcron_config_check.v1",
        "status": "ok" if validation["allowed"] else "blocked",
        "config": config.to_json_dict(),
        "validation": validation,
        "fcron": {
            "marker": marker,
            "entry": entry,
            "table_target": str(table_target),
            "candidate_path": str(candidate_path),
            "write_fcrontab": bool(args.write_fcrontab),
            "started_fcron": False,
            "openrc_touched": False,
            "idempotent": table_candidate == upsert_fcron_table(table_candidate, entry, marker),
        },
        "boundary": [
            "ConfigObj config is the source of scheduling intent",
            "fcron table text is updated idempotently without duplicates",
            "fcron service is not started or managed here",
            "scan command is scan-once and then exit",
            "no GitHub API call",
            "no SQL write",
            "no qdrant write",
            "no remote mutation",
        ],
    }
    report_json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    report_md_path.write_text(render_config_check(config), encoding="utf-8")

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(render_config_check(config), end="")
        print(f"fcron_candidate: `{candidate_path}`")
        print(f"idempotent: `{report['fcron']['idempotent']}`")
    return 0 if validation["allowed"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
