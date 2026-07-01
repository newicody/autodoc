
from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

from context.source_candidate import SourceCandidateInput, SourceCandidateOrigin, build_source_candidate
from context.source_candidate_review_cli import command_from_args, main
from context.source_candidate_store import SourceCandidateStorePolicy, upsert_source_candidate


def _seed_store(path: Path) -> None:
    policy = SourceCandidateStorePolicy(path)
    candidate = build_source_candidate(
        SourceCandidateInput(
            title="CLI review candidate",
            body="visible from operator projection",
            origin=SourceCandidateOrigin(kind="manual", reference="pytest-cli"),
        )
    ).candidate
    upsert_source_candidate(policy, candidate)


def test_source_candidate_review_cli_builds_typed_command(tmp_path: Path) -> None:
    args = Namespace(
        store_file=str(tmp_path / "source_candidates.json"),
        repository="newicody/autodoc",
        include_terminal=False,
        status=["new"],
        limit=5,
        body_preview_chars=80,
        format="json",
    )

    command = command_from_args(args)

    assert command.store_policy.path == tmp_path / "source_candidates.json"
    assert command.review_policy.status_filter == ("new",)
    assert command.review_policy.limit == 5


def test_source_candidate_review_cli_json_stdout(tmp_path: Path, capsys) -> None:
    store_file = tmp_path / "source_candidates.json"
    _seed_store(store_file)

    exit_code = main(
        [
            "--store-file",
            str(store_file),
            "--format",
            "json",
            "--limit",
            "1",
        ]
    )

    payload = json.loads(capsys.readouterr().out)
    assert exit_code == 0
    assert payload["schema"] == "missipy.source_candidate.review.v1"
    assert payload["returned_count"] == 1
    assert payload["items"][0]["title"] == "CLI review candidate"
