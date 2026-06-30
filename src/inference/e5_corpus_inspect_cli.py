from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO

from .e5_corpus import E5CorpusJsonStore
from .e5_corpus_inspect import (
    DEFAULT_E5_CORPUS_TOP_SOURCES_LIMIT,
    E5CorpusDiagnostics,
    inspect_e5_corpus,
)


@dataclass(frozen=True, slots=True)
class E5CorpusInspectCliOutput:
    """Sortie CLI stable du diagnostic de corpus E5."""

    index_path: str
    diagnostics: E5CorpusDiagnostics

    def to_json_dict(self) -> dict[str, object]:
        """Convertit la sortie CLI vers JSON stable."""
        return {
            "index": self.index_path,
            "diagnostics": self.diagnostics.to_json_dict(),
        }

    def to_text(self) -> str:
        """Produit la sortie texte utilisateur."""
        return f"index: {self.index_path}\n{self.diagnostics.to_text()}"


def build_inspect_parser() -> argparse.ArgumentParser:
    """Construit le parser de la commande d'inspection E5 locale."""
    parser = argparse.ArgumentParser(
        prog="missipy-inspect-e5-corpus",
        description="Inspecte un corpus E5 local déjà vectorisé.",
    )
    parser.add_argument("--index", required=True, help="Fichier JSON du corpus local à inspecter.")
    parser.add_argument(
        "--top-sources-limit",
        type=int,
        default=DEFAULT_E5_CORPUS_TOP_SOURCES_LIMIT,
        help="Nombre maximal de sources dominantes affichées.",
    )
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
    args = build_inspect_parser().parse_args(list(argv) if argv is not None else None)

    if args.top_sources_limit <= 0:
        err.write("--top-sources-limit must be positive\n")
        return 2

    corpus_store = store or E5CorpusJsonStore()
    try:
        index = corpus_store.read(Path(args.index))
        diagnostics = inspect_e5_corpus(index, top_sources_limit=args.top_sources_limit)
    except Exception as exc:
        err.write(f"missipy-inspect-e5-corpus failed: {exc}\n")
        return 1

    output = E5CorpusInspectCliOutput(index_path=str(args.index), diagnostics=diagnostics)
    _write_output(out, args.format, output.to_json_dict(), output.to_text())
    return 0


def main(argv: list[str] | tuple[str, ...] | None = None) -> int:
    """Point d'entrée console."""
    return run_inspect(argv)


def _write_output(stdout: TextIO, output_format: str, payload: dict[str, object], text: str) -> None:
    if output_format == "json":
        stdout.write(json.dumps(payload, ensure_ascii=False, sort_keys=True))
        stdout.write("\n")
        return
    stdout.write(text)
    stdout.write("\n")


if __name__ == "__main__":
    raise SystemExit(main())
