from __future__ import annotations

from types import SimpleNamespace

import pytest

from context import source_candidate_operator_cli as cli


def test_command_names_are_stable() -> None:
    assert cli.command_names() == (
        "bundle",
        "decide",
        "intake",
        "report",
        "report-file",
        "review",
        "review-audit",
    )


def test_dispatch_forwards_arguments_to_selected_module(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, tuple[str, ...]] = {}

    def fake_import(name: str) -> object:
        assert name == "fake.review"

        def fake_main(argv: tuple[str, ...]) -> int:
            captured["argv"] = argv
            return 7

        return SimpleNamespace(main=fake_main)

    monkeypatch.setattr(cli.importlib, "import_module", fake_import)
    monkeypatch.setattr(
        cli,
        "_COMMANDS",
        {"review": cli.SourceCandidateOperatorCommandSpec("fake.review", "review fake")},
    )

    assert cli.main(("review", "--store-file", "source_candidates.json", "--format", "json")) == 7
    assert captured["argv"] == ("--store-file", "source_candidates.json", "--format", "json")


def test_dispatch_accepts_separator_before_forwarded_arguments(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, tuple[str, ...]] = {}

    def fake_import(name: str) -> object:
        def fake_main(argv: tuple[str, ...]) -> int:
            captured["argv"] = argv
            return 0

        return SimpleNamespace(main=fake_main)

    monkeypatch.setattr(cli.importlib, "import_module", fake_import)
    monkeypatch.setattr(
        cli,
        "_COMMANDS",
        {"bundle": cli.SourceCandidateOperatorCommandSpec("fake.bundle", "bundle fake")},
    )

    assert cli.main(("bundle", "--", "--store-file", "x", "--bundle-dir", "out")) == 0
    assert captured["argv"] == ("--store-file", "x", "--bundle-dir", "out")


def test_dispatch_rejects_unknown_command() -> None:
    with pytest.raises(ValueError, match="unknown source candidate operator command"):
        cli.dispatch_source_candidate_operator_command("missing", ())
