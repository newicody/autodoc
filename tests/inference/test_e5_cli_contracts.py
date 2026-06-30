from __future__ import annotations

from pathlib import Path

import pytest

from inference.e5_cli_contracts import (
    E5CliModelPolicy,
    E5DiagnosticGatePolicy,
    E5SearchPolicy,
    E5SearchValidationPolicy,
    merge_cli_values,
    source_selection_policy_from_cli,
)


def test_model_policy_builds_pipeline_config_with_cli_metadata() -> None:
    policy = E5CliModelPolicy(cli_name="tool", model_dir="/tmp/model", device="CPU", max_length=64)

    config = policy.to_pipeline_config()

    assert config.local.model_dir == "/tmp/model"
    assert config.local.device == "CPU"
    assert config.local.max_length == 64
    assert config.metadata["cli"] == "tool"


def test_source_selection_policy_merges_defaults_and_cli_values() -> None:
    policy = source_selection_policy_from_cli(
        passages=(" alpha ", ""),
        passages_file=None,
        source_files=(),
        source_dirs=(),
        source_extensions=".md,.txt",
        recursive=True,
        chunk_chars=100,
        overlap_paragraphs=0,
        excluded_dir_names=(".git", "generated"),
        excluded_file_suffixes=(".svg", ".tmp"),
    )

    assert policy.passages == ("alpha",)
    assert policy.source_extensions == (".md", ".txt")
    assert "generated" in policy.excluded_dir_names
    assert policy.excluded_dir_names.count(".git") == 1
    assert ".tmp" in policy.excluded_file_suffixes


def test_search_policy_validates_score_and_limit() -> None:
    assert E5SearchPolicy(limit=1, min_score=0.5).min_score == 0.5
    with pytest.raises(ValueError, match="--limit"):
        E5SearchPolicy(limit=0)
    with pytest.raises(ValueError, match="--min-score"):
        E5SearchPolicy(min_score=1.1)


def test_diagnostic_gate_policy_converts_to_config() -> None:
    policy = E5DiagnosticGatePolicy(min_chunks=1, fail_on_warning=True)

    config = policy.to_config()

    assert config.min_chunks == 1
    assert config.fail_on_warning is True
    assert config.enabled is True


def test_validation_policy_reads_query_files(tmp_path) -> None:
    path = tmp_path / "queries.txt"
    path.write_text("alpha\n\nbeta\n", encoding="utf-8")
    policy = E5SearchValidationPolicy(queries=(" gamma ",), query_files=(path,))

    assert policy.collect_queries() == ("gamma", "alpha", "beta")


def test_merge_cli_values_is_stable_and_deduplicated() -> None:
    assert merge_cli_values((".git", ".svg"), (".git", "generated")) == (".git", ".svg", "generated")
