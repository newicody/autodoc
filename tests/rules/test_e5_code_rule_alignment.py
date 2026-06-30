from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_code_rule_preserves_kernel_identity_and_adds_only_e5_addendum() -> None:
    text = _read("doc/code_rule.md")

    assert "# Header de recherche / Philosophie du projet" in text
    assert "## Micro-Kernel Coopératif IA" in text
    assert "Aucun composant n'appelle directement un autre composant" in text
    assert "Toutes les interactions transitent exclusivement par des événements" in text
    assert "Le Scheduler constitue le cœur du système" in text
    assert "Contrat d'un composant" in text

    assert "Addendum Phase 4.12-r2" in text
    assert "ne remplace pas les règles précédentes" in text
    assert "ne sont pas une exception au style kernel" in text
    assert "futur composant pilotable par événement" in text
    assert "code_rule_review" in text

    assert "Outillage CLI hors kernel" not in text


def test_e5_cli_use_cases_do_not_accept_argparse_namespace() -> None:
    corpus_cli = _read("src/inference/e5_corpus_cli.py")
    rebuild_cli = _read("src/inference/e5_rebuild_cli.py")

    assert "async def _build_and_write_corpus(\n    args" not in corpus_cli
    assert "async def _rebuild_candidate(\n    args" not in rebuild_cli
    assert "def _pipeline_config(args" not in corpus_cli
    assert "def _pipeline_config(args" not in rebuild_cli


def test_e5_report_writes_are_centralized() -> None:
    for relative in ("src/inference/e5_corpus_cli.py", "src/inference/e5_rebuild_cli.py"):
        text = _read(relative)
        assert "_write_report_file" not in text
        assert "write_json_report_atomic" in text


def test_e5_contract_module_contains_command_and_policy_dataclasses() -> None:
    text = _read("src/inference/e5_cli_contracts.py")

    for name in (
        "class E5BuildCommand",
        "class E5SearchCommand",
        "class E5RebuildCommand",
        "class E5InspectCommand",
        "class E5SearchPolicy",
        "class E5DiagnosticGatePolicy",
        "class E5SearchValidationPolicy",
    ):
        assert name in text
