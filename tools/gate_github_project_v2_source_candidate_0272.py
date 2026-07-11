#!/usr/bin/env python3
"""Apply one local operator decision to one ProjectV2 SourceCandidate handoff."""
from __future__ import annotations

import argparse
import configparser
import json
from pathlib import Path
import sys
from typing import Any, Mapping, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC_ROOT = _REPO_ROOT / "src"
if str(_SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(_SRC_ROOT))

from context.github_project_v2_source_candidate_gate_0272 import (  # noqa: E402
    GitHubProjectV2SourceCandidateGateCommand,
    build_gate_plan,
    build_gate_record,
    close_gate_result,
)
from context.source_candidate import allowed_source_candidate_decisions  # noqa: E402

_DEFAULT_CONFIG = Path("config/github_project_v2_query_only.example.ini")
_DEFAULT_REPORT = Path(".var/reports/github_project_v2_source_candidate_gate_0272.json")


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=_DEFAULT_CONFIG)
    parser.add_argument("--handoff-batch", type=Path)
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--action", required=True, choices=allowed_source_candidate_decisions())
    parser.add_argument("--reason", default="")
    parser.add_argument("--target-context-id")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--policy-decision-id", default="")
    parser.add_argument("--output", type=Path, default=_DEFAULT_REPORT)
    parser.add_argument("--format", choices=("summary", "json"), default="summary")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(tuple(sys.argv[1:] if argv is None else argv))
    config = _load_config(args.config)
    handoff_path, selection_issues = _select_handoff_batch(
        explicit=args.handoff_batch,
        handoff_dir=config["handoff_dir"],
    )
    command = GitHubProjectV2SourceCandidateGateCommand(
        candidate_id=args.candidate_id,
        action=args.action,
        reason=args.reason,
        target_context_id=args.target_context_id,
        execute=args.execute,
        policy_decision_id=args.policy_decision_id,
    )
    plan = build_gate_plan(
        command,
        handoff_batch_path=str(handoff_path or ""),
    )
    gate_record: Mapping[str, Any] | None = None
    gate_path = ""
    errors = list(selection_issues)
    if args.execute and plan.valid and handoff_path is not None and not errors:
        try:
            handoff_batch = _read_json(handoff_path)
            gate_record = build_gate_record(
                handoff_batch=handoff_batch,
                command=command,
            )
            gate_path = str(
                _write_immutable_gate_record(
                    Path(config["decision_dir"]),
                    gate_record,
                )
            )
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            errors.append(f"{type(exc).__name__}:{exc}")
    result = close_gate_result(
        plan,
        gate_record=gate_record,
        gate_path=gate_path,
        errors=errors,
    )
    payload = result.to_json_dict()
    _write_json_atomic(_repo_path(str(args.output)), payload)
    print(json.dumps(payload, indent=2, sort_keys=True) if args.format == "json" else result.to_summary())
    return 0 if result.valid else 2


def _load_config(path: Path) -> dict[str, Path]:
    parser = configparser.ConfigParser(interpolation=None)
    if not parser.read(path, encoding="utf-8"):
        raise ValueError(f"config not found: {path}")
    gate = parser["candidate_gate"]
    return {
        "handoff_dir": _repo_path(gate.get("handoff_dir", ".var/github/project_v2/handoffs")),
        "decision_dir": _repo_path(gate.get("decision_dir", ".var/github/project_v2/decisions")),
    }


def _select_handoff_batch(
    *,
    explicit: Path | None,
    handoff_dir: Path,
) -> tuple[Path | None, tuple[str, ...]]:
    if explicit is not None:
        return _repo_path(str(explicit)), ()
    if not handoff_dir.exists():
        return None, (f"handoff directory not found: {handoff_dir}",)
    candidates = [
        path
        for path in handoff_dir.glob("project-v2-handoff-batch-*.json")
        if path.is_file()
    ]
    candidates.sort(key=lambda path: (path.stat().st_mtime_ns, path.name))
    if not candidates:
        return None, (f"no ProjectV2 handoff batches found in {handoff_dir}",)
    return candidates[-1], ()


def _read_json(path: Path) -> Mapping[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"handoff batch must be a JSON object: {path}")
    return payload


def _write_immutable_gate_record(
    output_dir: Path,
    payload: Mapping[str, Any],
) -> Path:
    gate_ref = str(payload.get("gate_ref", ""))
    digest = gate_ref.rsplit(":", 1)[-1]
    if not digest:
        raise ValueError("gate_ref missing")
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"project-v2-source-candidate-gate-{digest}.json"
    serialized = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != serialized:
            raise ValueError(f"immutable gate-record collision: {path}")
        return path
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(serialized, encoding="utf-8")
    temporary.replace(path)
    return path


def _write_json_atomic(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _repo_path(value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else _REPO_ROOT / path


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
