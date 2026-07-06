"""Audit existing runtime/integration surfaces before adding new wheels.

0132 introduces this audit helper so runtime patches first inspect what already
exists and decide whether to reuse, extend, modify, or create a new module.  The
tool is intentionally static and dependency-free: it does not import project
modules, does not run the Scheduler, and does not touch external backends.
"""

from __future__ import annotations

from dataclasses import dataclass
import argparse
import json
from pathlib import Path
import re
from typing import Iterable

_AUDIT_SCHEMA = "missipy.audit.existing_runtime_integration.v1"
_CATEGORY_ORDER = (
    "scheduler",
    "dispatcher",
    "policy_queue",
    "route_runtime",
    "route_handler",
    "openvino_adapter",
    "qdrant_adapter",
    "sql_context",
    "event_bus",
    "code_rules",
)
_CATEGORY_PATTERNS = {
    "scheduler": ("class Scheduler", "def run(", "Scheduler.run", "scheduler"),
    "dispatcher": ("Dispatcher", "dispatch", "handler"),
    "policy_queue": ("PolicyEngine", "PriorityQueue", "policy", "queue"),
    "route_runtime": ("RouteProxyRuntime", "route_dev_shm", "dev_shm", "route_proxy_runtime"),
    "route_handler": ("SchedulerRouteHandler", "handle_scheduler_route_command", "route_handler"),
    "openvino_adapter": ("OpenVINO", "openvino", "EmbeddingAdapter", "embedding_adapter"),
    "qdrant_adapter": ("Qdrant", "qdrant", "ProjectionAdapter", "projection_adapter"),
    "sql_context": ("SQLContext", "sql_context", "ContextStore", "SQL"),
    "event_bus": ("EventBus", "event_bus", "ObservationFact", "observation"),
    "code_rules": ("code_rule", "code-rules", "Scheduler.run", "anti-duplication"),
}
_ALLOWED_SUFFIXES = (".py", ".md", ".dot", ".json", ".toml", ".yaml", ".yml")
_IGNORED_DIRS = {".git", ".pytest_cache", "__pycache__", ".mypy_cache", ".ruff_cache", "dist", "build"}


@dataclass(frozen=True, slots=True)
class AuditMatch:
    """One static match for a category in a source/documentation file."""

    category: str
    path: str
    matched_terms: tuple[str, ...]

    def to_mapping(self) -> dict[str, object]:
        return {
            "category": self.category,
            "path": self.path,
            "matched_terms": list(self.matched_terms),
        }


@dataclass(frozen=True, slots=True)
class IntegrationDecision:
    """Decision hint: reuse/extend/modify when existing surfaces are present."""

    category: str
    decision: str
    reason: str
    candidate_paths: tuple[str, ...]

    def to_mapping(self) -> dict[str, object]:
        return {
            "category": self.category,
            "decision": self.decision,
            "reason": self.reason,
            "candidate_paths": list(self.candidate_paths),
        }


@dataclass(frozen=True, slots=True)
class ExistingRuntimeIntegrationAudit:
    """Static inventory report used before creating runtime modules."""

    root: Path
    matches: tuple[AuditMatch, ...]
    decisions: tuple[IntegrationDecision, ...]

    @property
    def category_counts(self) -> dict[str, int]:
        counts = {category: 0 for category in _CATEGORY_ORDER}
        for match in self.matches:
            counts[match.category] += 1
        return counts

    def to_mapping(self) -> dict[str, object]:
        return {
            "schema": _AUDIT_SCHEMA,
            "root": str(self.root),
            "category_counts": self.category_counts,
            "matches": [match.to_mapping() for match in self.matches],
            "decisions": [decision.to_mapping() for decision in self.decisions],
            "rule": "reuse_extend_or_modify_existing_before_adding_new_runtime_module",
            "new_module_default_allowed": False,
            "scheduler_run_mutation_allowed": False,
            "external_backend_runtime_calls_allowed": False,
        }

    def to_markdown(self) -> str:
        data = self.to_mapping()
        lines = ["# Existing runtime integration audit", "", f"Root: `{data['root']}`", "", "## Category counts", ""]
        for category, count in self.category_counts.items():
            lines.append(f"- `{category}`: {count}")
        lines.extend(["", "## Decisions", ""])
        for decision in self.decisions:
            paths = ", ".join(f"`{path}`" for path in decision.candidate_paths) or "none"
            lines.append(f"- `{decision.category}` -> **{decision.decision}**: {decision.reason} ({paths})")
        return "\n".join(lines) + "\n"


def audit_existing_runtime_integration(root: Path) -> ExistingRuntimeIntegrationAudit:
    """Scan source/docs/tests for reusable runtime surfaces."""

    resolved_root = root.resolve()
    matches = tuple(_scan_matches(resolved_root))
    decisions = tuple(_build_decisions(matches))
    return ExistingRuntimeIntegrationAudit(root=resolved_root, matches=matches, decisions=decisions)


def _scan_matches(root: Path) -> Iterable[AuditMatch]:
    for path in sorted(_iter_candidate_files(root)):
        text = _safe_read_text(path)
        relative = path.relative_to(root).as_posix()
        for category in _CATEGORY_ORDER:
            terms = tuple(term for term in _CATEGORY_PATTERNS[category] if term.lower() in text.lower() or term.lower() in relative.lower())
            if terms:
                yield AuditMatch(category=category, path=relative, matched_terms=terms)


def _iter_candidate_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        raise FileNotFoundError(root)
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in _IGNORED_DIRS for part in path.parts):
            continue
        if path.suffix not in _ALLOWED_SUFFIXES:
            continue
        yield path


def _safe_read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def _build_decisions(matches: tuple[AuditMatch, ...]) -> Iterable[IntegrationDecision]:
    by_category: dict[str, list[str]] = {category: [] for category in _CATEGORY_ORDER}
    for match in matches:
        by_category[match.category].append(match.path)
    for category in _CATEGORY_ORDER:
        paths = tuple(sorted(dict.fromkeys(by_category[category])))
        if paths:
            yield IntegrationDecision(
                category=category,
                decision="reuse_or_extend_existing",
                reason="candidate surfaces exist; do not create a parallel wheel without a written exception",
                candidate_paths=paths,
            )
        else:
            yield IntegrationDecision(
                category=category,
                decision="create_only_after_documented_gap",
                reason="no candidate surface found by static audit; creation still requires a documented no-reinvent justification",
                candidate_paths=(),
            )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit existing runtime integration surfaces before adding new modules.")
    parser.add_argument("root", nargs="?", default=".", help="Repository root to scan")
    parser.add_argument("--format", choices=("json", "markdown"), default="json", help="Output format")
    args = parser.parse_args(argv)
    audit = audit_existing_runtime_integration(Path(args.root))
    if args.format == "markdown":
        print(audit.to_markdown(), end="")
    else:
        print(json.dumps(audit.to_mapping(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
