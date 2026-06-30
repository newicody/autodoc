from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from .e5_cli_contracts import E5DiagnosticGatePolicy, E5InspectCommand
from .e5_corpus import E5CorpusJsonStore
from .e5_corpus_inspect import (
    DEFAULT_E5_CORPUS_TOP_SOURCES_LIMIT,
    E5CorpusDiagnosticGateResult,
    E5CorpusDiagnostics,
    evaluate_e5_corpus_diagnostic_gate,
    inspect_e5_corpus,
)


@dataclass(frozen=True, slots=True)
class E5CorpusInspectCliOutput:
    """Sortie CLI stable du diagnostic de corpus E5."""

    index_path: str
    diagnostics: E5CorpusDiagnostics
    gate: E5CorpusDiagnosticGateResult | None = None

    def to_json_dict(self) -> dict[str, object]:
        """Convertit la sortie CLI vers JSON stable."""
        payload: dict[str, object] = {
            "index": self.index_path,
            "diagnostics": self.diagnostics.to_json_dict(),
        }
        if self.gate is not None:
            payload["gate"] = self.gate.to_json_dict()
        return payload

    def to_text(self) -> str:
        """Produit la sortie texte utilisateur."""
        text = f"index: {self.index_path}\n{self.diagnostics.to_text()}"
        if self.gate is not None:
            text = f"{text}\n{self.gate.to_text()}"
        return text


def build_inspect_parser() -> argparse.ArgumentParser:
    """Construit le parser de la commande d'inspection E5 locale."""
    parser = argparse.ArgumentParser(
        prog="missipy-inspect-e5-corpus",
        description="Inspecte un corpus E5 local déjà vectorisé.",
    )
    parser.add_argument("--index", required=True, help="Fichier JSON du corpus local à inspecter.")
    parser.add_argument("--top-sources-limit", type=int, default=DEFAULT_E5_CORPUS_TOP_SOURCES_LIMIT, help="Nombre maximal de sources dominantes affichées.")
    parser.add_argument("--min-chunks", type=int, default=None, help="Nombre minimal de chunks requis.")
    parser.add_argument("--max-missing-source-metadata", type=int, default=None, help="Nombre maximal de chunks sans métadonnée source_path.")
    parser.add_argument("--max-empty-texts", type=int, default=None, help="Nombre maximal de chunks à texte vide tolérés.")
    parser.add_argument("--max-dimension-mismatches", type=int, default=None, help="Nombre maximal de vecteurs dont la dimension diffère de l'index.")
    parser.add_argument("--fail-on-warning", action="store_true", help="Retourne le code 2 si le diagnostic contient des avertissements.")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="Format de sortie CLI.")
    return parser


def run_inspect(
    argv: list[str] | tuple[str, ...] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    store: E5CorpusJsonStore | None = None,
) -> int:
    """Point d'entrée testable de la CLI d'inspection."""
    out = stdout or sys.stdout
    err = stderr or sys.stderr
    raw_args = build_inspect_parser().parse_args(list(argv) if argv is not None else None)
    try:
        command = _inspect_command(raw_args)
    except ValueError as exc:
        err.write(f"{exc}\n")
        return 2

    corpus_store = store or E5CorpusJsonStore()
    try:
        index = corpus_store.read(command.index)
        diagnostics = inspect_e5_corpus(index, top_sources_limit=command.top_sources_limit)
    except Exception as exc:
        err.write(f"missipy-inspect-e5-corpus failed: {exc}\n")
        return 1

    gate_config = command.diagnostic_gate.to_config()
    gate = evaluate_e5_corpus_diagnostic_gate(diagnostics, gate_config) if gate_config.enabled else None
    output = E5CorpusInspectCliOutput(index_path=str(command.index), diagnostics=diagnostics, gate=gate)
    _write_output(out, command.output_format, output.to_json_dict(), output.to_text())
    if gate is not None and not gate.passed:
        return 2
    return 0


def main(argv: list[str] | tuple[str, ...] | None = None) -> int:
    """Point d'entrée console."""
    return run_inspect(argv)


def _inspect_command(args: argparse.Namespace) -> E5InspectCommand:
    return E5InspectCommand(
        index=Path(args.index),
        top_sources_limit=args.top_sources_limit,
        output_format=args.format,
        diagnostic_gate=E5DiagnosticGatePolicy(
            min_chunks=args.min_chunks,
            max_missing_source_metadata=args.max_missing_source_metadata,
            max_empty_texts=args.max_empty_texts,
            max_dimension_mismatches=args.max_dimension_mismatches,
            fail_on_warning=args.fail_on_warning,
        ),
    )


def _write_output(stdout: TextIO, output_format: str, payload: dict[str, object], text: str) -> None:
    if output_format == "json":
        stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        stdout.write("\n")
        return
    stdout.write(text)
    stdout.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
