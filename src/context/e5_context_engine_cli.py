from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from .e5_context_attachment import E5ContextAttachmentPolicy
from .e5_context_engine_status import E5ContextEngineStatusPolicy, inspect_e5_context_engine
from .e5_local_context_runtime import E5LocalContextRuntimePolicy
from .e5_runtime_bridge import E5RuntimeBridgePolicy
from .engine import ContextEngine, E5ContextEngineIntakePolicy, E5ContextEngineIntakeResult


@dataclass(frozen=True, slots=True)
class E5ContextEngineCliRenderPolicy:
    """Politique de rendu CLI pour l'intake manuel E5 dans ContextEngine."""

    output_format: str = "text"

    def __post_init__(self) -> None:
        if self.output_format not in {"text", "json"}:
            raise ValueError("output_format must be text or json")


@dataclass(frozen=True, slots=True)
class E5ContextEngineCliReportPolicy:
    """Politique d'écriture optionnelle du rapport CLI ContextEngine."""

    path: Path | None = None

    def __post_init__(self) -> None:
        if self.path is not None and not self.path.name:
            raise ValueError("report_file must target a filename")


@dataclass(frozen=True, slots=True)
class E5ContextEngineCliCommand:
    """Commande typée : artifact-dir Phase 4 -> ContextEngine -> statut E5."""

    artifact_dir: Path
    intake: E5ContextEngineIntakePolicy = E5ContextEngineIntakePolicy()
    status: E5ContextEngineStatusPolicy = E5ContextEngineStatusPolicy()
    render: E5ContextEngineCliRenderPolicy = E5ContextEngineCliRenderPolicy()
    report: E5ContextEngineCliReportPolicy = E5ContextEngineCliReportPolicy()

    def __post_init__(self) -> None:
        if not str(self.artifact_dir).strip():
            raise ValueError("artifact_dir must not be empty")


def build_e5_context_engine_parser() -> argparse.ArgumentParser:
    """Construit le parser de l'intake manuel ContextEngine."""
    parser = argparse.ArgumentParser(
        prog="missipy-e5-context-engine",
        description="Attache un artifact-dir E5 Phase 4 à un ContextEngine local et affiche son statut.",
    )
    parser.add_argument("artifact_dir", help="Dossier contenant report.json, context.json, consumed_context.json et prompt.json.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Format de sortie.")
    parser.add_argument("--component-name", default="e5_local_context", help="Nom de composant E5 dans InferenceContext.features.")
    parser.add_argument("--priority", type=int, default=20, help="Priorité associée au contexte E5 attaché.")
    parser.add_argument("--include-context-text", action="store_true", help="Inclut context_text dans la feature E5 attachée.")
    parser.add_argument("--hide-prompt-text", action="store_true", help="N'inclut pas prompt_text dans la feature E5 attachée.")
    parser.add_argument("--require-ready", action="store_true", help="Échoue si le contexte E5 attaché n'est pas prêt.")
    parser.add_argument("--report-file", help="Écrit le payload CLI JSON dans un fichier atomique optionnel.")
    return parser


def command_from_args(args: argparse.Namespace) -> E5ContextEngineCliCommand:
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
    return E5ContextEngineCliCommand(
        artifact_dir=Path(args.artifact_dir),
        intake=E5ContextEngineIntakePolicy(
            runtime_policy=runtime_policy,
            attachment_policy=attachment_policy,
        ),
        status=E5ContextEngineStatusPolicy(component_name=args.component_name),
        render=E5ContextEngineCliRenderPolicy(output_format=args.format),
        report=E5ContextEngineCliReportPolicy(path=_optional_output_file(args.report_file, "--report-file")),
    )


def run_e5_context_engine(
    argv: list[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Point d'entrée testable : artifact-dir -> intake ContextEngine -> status."""
    out = stdout or sys.stdout
    err = stderr or sys.stderr
    parser = build_e5_context_engine_parser()

    try:
        command = command_from_args(parser.parse_args(argv))
        engine = ContextEngine()
        intake = engine.attach_e5_artifact_dir(command.artifact_dir, command.intake)
        status = inspect_e5_context_engine(engine, command.status)
        payload = _payload(command, intake, status)
    except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
        err.write(f"missipy-e5-context-engine failed: {exc}\n")
        return 1

    try:
        _write_report(command.report, payload)
    except OSError as exc:
        err.write(f"missipy-e5-context-engine failed to write report: {exc}\n")
        return 1

    _write_output(out, command, payload)
    return 0


def main() -> int:
    """Entrée console pour `python -m context.e5_context_engine_cli`."""
    return run_e5_context_engine()


def _write_output(
    out: TextIO,
    command: E5ContextEngineCliCommand,
    payload: dict[str, object],
) -> None:
    if command.render.output_format == "json":
        out.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        out.write("\n")
        return
    out.write(_to_text(payload))
    out.write("\n")


def _optional_output_file(value: str | None, option_name: str) -> Path | None:
    if value is None:
        return None
    path = Path(value)
    if not path.name:
        raise ValueError(f"{option_name} must target a filename")
    return path


def _write_report(policy: E5ContextEngineCliReportPolicy, payload: dict[str, object]) -> None:
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


def _payload(command: E5ContextEngineCliCommand, intake: E5ContextEngineIntakeResult, status: object) -> dict[str, object]:
    if not hasattr(status, "to_json_dict"):
        raise TypeError("status must expose to_json_dict")
    return {
        "schema": "missipy.e5.context_engine_cli.v1",
        "artifact_dir": str(command.artifact_dir),
        "intake": intake.to_json_dict(),
        "status": status.to_json_dict(),
    }


def _to_text(payload: dict[str, object]) -> str:
    intake = payload["intake"]
    status = payload["status"]
    if not isinstance(intake, dict):
        raise TypeError("intake payload must be a mapping")
    if not isinstance(status, dict):
        raise TypeError("status payload must be a mapping")

    lines = [
        "schema: missipy.e5.context_engine_cli.v1",
        f"artifact_dir: {payload['artifact_dir']}",
        f"ready: {str(intake.get('ready', False)).lower()}",
        f"changed: {str(intake.get('changed', False)).lower()}",
        f"feature_count: {intake.get('feature_count', 0)}",
        f"component: {status.get('component_name', '')}",
        f"attached: {str(status.get('attached', False)).lower()}",
        f"query: {status.get('query', '')}",
        f"selected_item_count: {status.get('selected_item_count', 0)}",
        f"prompt_chars: {status.get('prompt_chars', 0)}",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
