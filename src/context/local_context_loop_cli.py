from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from .e5_context_attachment import E5ContextAttachmentPolicy
from .e5_context_engine_status import E5ContextEngineStatus, E5ContextEngineStatusPolicy, inspect_e5_context_engine
from .e5_local_context_runtime import E5LocalContextRuntimePolicy
from .e5_runtime_bridge import E5RuntimeBridgePolicy
from .engine import ContextEngine, E5ContextEngineIntakePolicy, E5ContextEngineIntakeResult


_ALLOWED_NEXT_ACTIONS = frozenset({"inspect", "relaunch", "reject", "archive", "promote", "merge"})


@dataclass(frozen=True, slots=True)
class LocalContextLoopDecisionPolicy:
    """Décision opérateur enregistrée dans le rapport de boucle locale.

    La Phase 5.13 ne persiste pas et n'applique pas cette décision. Elle la
    transporte uniquement dans le payload CLI pour préparer les contrats
    SourceCandidate futurs.
    """

    next_action: str = "inspect"

    def __post_init__(self) -> None:
        if self.next_action not in _ALLOWED_NEXT_ACTIONS:
            raise ValueError("next_action must be inspect, relaunch, reject, archive, promote or merge")


@dataclass(frozen=True, slots=True)
class LocalContextLoopRenderPolicy:
    """Politique de rendu de la CLI de boucle locale."""

    output_format: str = "text"

    def __post_init__(self) -> None:
        if self.output_format not in {"text", "json"}:
            raise ValueError("output_format must be text or json")


@dataclass(frozen=True, slots=True)
class LocalContextLoopReportPolicy:
    """Politique d'écriture optionnelle du rapport de boucle locale."""

    path: Path | None = None

    def __post_init__(self) -> None:
        if self.path is not None and not self.path.name:
            raise ValueError("report_file must target a filename")


@dataclass(frozen=True, slots=True)
class LocalContextLoopCommand:
    """Commande typée : artifact-dir Phase 4 -> ContextEngine -> statut -> décision reportée."""

    artifact_dir: Path
    intake: E5ContextEngineIntakePolicy = E5ContextEngineIntakePolicy()
    status: E5ContextEngineStatusPolicy = E5ContextEngineStatusPolicy()
    decision: LocalContextLoopDecisionPolicy = LocalContextLoopDecisionPolicy()
    render: LocalContextLoopRenderPolicy = LocalContextLoopRenderPolicy()
    report: LocalContextLoopReportPolicy = LocalContextLoopReportPolicy()

    def __post_init__(self) -> None:
        if not str(self.artifact_dir).strip():
            raise ValueError("artifact_dir must not be empty")


@dataclass(frozen=True, slots=True)
class LocalContextLoopResult:
    """Résultat sérialisable de la boucle locale manuelle 5.13."""

    artifact_dir: Path
    intake: E5ContextEngineIntakeResult
    status: E5ContextEngineStatus
    decision: LocalContextLoopDecisionPolicy

    @property
    def ready(self) -> bool:
        return self.intake.ready and self.status.ready

    @property
    def mutation_applied(self) -> bool:
        return False

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema": "missipy.local_context_loop_cli.v1",
            "phase": "5.13",
            "artifact_dir": str(self.artifact_dir),
            "ready": self.ready,
            "mutation_applied": self.mutation_applied,
            "next_action": self.decision.next_action,
            "steps": [
                "load_e5_artifact_dir",
                "build_e5_local_runtime",
                "attach_context_engine",
                "inspect_context_engine_status",
                "report_operator_next_action",
            ],
            "intake": self.intake.to_json_dict(),
            "status": self.status.to_json_dict(),
            "decision_options": sorted(_ALLOWED_NEXT_ACTIONS),
        }

    def to_text(self) -> str:
        payload = self.to_json_dict()
        intake = payload["intake"]
        status = payload["status"]
        if not isinstance(intake, dict):
            raise TypeError("intake payload must be a mapping")
        if not isinstance(status, dict):
            raise TypeError("status payload must be a mapping")
        lines = [
            "schema: missipy.local_context_loop_cli.v1",
            "phase: 5.13",
            f"artifact_dir: {payload['artifact_dir']}",
            f"ready: {str(payload['ready']).lower()}",
            f"mutation_applied: {str(payload['mutation_applied']).lower()}",
            f"next_action: {payload['next_action']}",
            f"intake_changed: {str(intake.get('changed', False)).lower()}",
            f"feature_count: {intake.get('feature_count', 0)}",
            f"component: {status.get('component_name', '')}",
            f"attached: {str(status.get('attached', False)).lower()}",
            f"query: {status.get('query', '')}",
            f"selected_item_count: {status.get('selected_item_count', 0)}",
            f"prompt_chars: {status.get('prompt_chars', 0)}",
        ]
        return "\n".join(lines)


def build_local_context_loop_parser() -> argparse.ArgumentParser:
    """Construit le parser de la boucle locale manuelle."""
    parser = argparse.ArgumentParser(
        prog="missipy-local-context-loop",
        description="Exécute une boucle locale manuelle depuis un artifact-dir E5 Phase 4.",
    )
    parser.add_argument("artifact_dir", help="Dossier contenant report.json, context.json, consumed_context.json et prompt.json.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Format de sortie.")
    parser.add_argument("--component-name", default="e5_local_context", help="Nom de composant E5 dans InferenceContext.features.")
    parser.add_argument("--priority", type=int, default=20, help="Priorité associée au contexte E5 attaché.")
    parser.add_argument("--include-context-text", action="store_true", help="Inclut context_text dans la feature E5 attachée.")
    parser.add_argument("--hide-prompt-text", action="store_true", help="N'inclut pas prompt_text dans la feature E5 attachée.")
    parser.add_argument("--require-ready", action="store_true", help="Échoue si le contexte E5 attaché n'est pas prêt.")
    parser.add_argument(
        "--next-action",
        choices=tuple(sorted(_ALLOWED_NEXT_ACTIONS)),
        default="inspect",
        help="Décision opérateur reportée dans le payload seulement ; aucun effet n'est appliqué en 5.13.",
    )
    parser.add_argument("--report-file", help="Écrit le payload de boucle locale dans un fichier JSON atomique optionnel.")
    return parser


def command_from_args(args: argparse.Namespace) -> LocalContextLoopCommand:
    """Traduit argparse.Namespace en contrat typé à la frontière CLI."""
    if args.priority < 0:
        raise ValueError("--priority must not be negative")

    runtime_policy = E5LocalContextRuntimePolicy(
        bridge_policy=E5RuntimeBridgePolicy(
            component_name=args.component_name,
            priority=args.priority,
            include_prompt_text=not args.hide_prompt_text,
            include_context_text=args.include_context_text,
        ),
        require_ready=args.require_ready,
    )
    attachment_policy = E5ContextAttachmentPolicy(
        minimum_priority=args.priority,
    )
    return LocalContextLoopCommand(
        artifact_dir=Path(args.artifact_dir),
        intake=E5ContextEngineIntakePolicy(
            runtime_policy=runtime_policy,
            attachment_policy=attachment_policy,
        ),
        status=E5ContextEngineStatusPolicy(component_name=args.component_name),
        decision=LocalContextLoopDecisionPolicy(next_action=args.next_action),
        render=LocalContextLoopRenderPolicy(output_format=args.format),
        report=LocalContextLoopReportPolicy(path=_optional_output_file(args.report_file, "--report-file")),
    )


def run_local_context_loop(
    argv: list[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Point d'entrée testable : artifact-dir -> ContextEngine -> status -> next_action."""
    out = stdout or sys.stdout
    err = stderr or sys.stderr
    parser = build_local_context_loop_parser()

    try:
        command = command_from_args(parser.parse_args(argv))
        result = execute_local_context_loop(command)
        payload = result.to_json_dict()
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        err.write(f"missipy-local-context-loop failed: {exc}\n")
        return 1

    try:
        _write_report(command.report, payload)
    except OSError as exc:
        err.write(f"missipy-local-context-loop failed to write report: {exc}\n")
        return 1

    _write_output(out, command, result, payload)
    return 0


def execute_local_context_loop(command: LocalContextLoopCommand) -> LocalContextLoopResult:
    """Exécute la boucle locale manuelle sans daemon ni Scheduler vivant."""
    engine = ContextEngine()
    intake = engine.attach_e5_artifact_dir(command.artifact_dir, command.intake)
    status = inspect_e5_context_engine(engine, command.status)
    return LocalContextLoopResult(
        artifact_dir=command.artifact_dir,
        intake=intake,
        status=status,
        decision=command.decision,
    )


def main() -> int:
    """Entrée console pour `python -m context.local_context_loop_cli`."""
    return run_local_context_loop()


def _write_output(
    out: TextIO,
    command: LocalContextLoopCommand,
    result: LocalContextLoopResult,
    payload: dict[str, object],
) -> None:
    if command.render.output_format == "json":
        out.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        out.write("\n")
        return
    out.write(result.to_text())
    out.write("\n")


def _optional_output_file(value: str | None, option_name: str) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    if not path.name:
        raise ValueError(f"{option_name} must target a filename")
    return path


def _write_report(policy: LocalContextLoopReportPolicy, payload: dict[str, object]) -> None:
    if policy.path is None:
        return
    target = policy.path
    temporary = target.with_name(f".{target.name}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(target)
    finally:
        if temporary.exists():
            temporary.unlink()


if __name__ == "__main__":
    raise SystemExit(main())
