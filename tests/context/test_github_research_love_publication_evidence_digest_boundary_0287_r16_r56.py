from __future__ import annotations

import pytest

from context import github_research_love_publication_evidence_sql_0287 as module


def test_raw_publication_digest_becomes_typed_without_rehashing() -> None:
    raw = "4" * 64

    assert module._typed_sha256_digest(  # noqa: SLF001
        raw,
        name="publication_plan_digest",
    ) == f"sha256:{raw}"


def test_already_typed_publication_digest_is_preserved() -> None:
    typed = "sha256:" + ("a" * 64)

    assert module._typed_sha256_digest(  # noqa: SLF001
        typed,
        name="publication_plan_digest",
    ) == typed


@pytest.mark.parametrize(
    "value",
    (
        "",
        "a" * 63,
        "a" * 65,
        "A" * 64,
        "g" * 64,
        "sha256:" + ("a" * 63),
    ),
)
def test_invalid_publication_digest_fails_closed(value: str) -> None:
    with pytest.raises(
        module.GitHubResearchLovePublicationEvidenceError,
        match="lowercase sha256 digest|must not be empty",
    ):
        module._typed_sha256_digest(  # noqa: SLF001
            value,
            name="publication_plan_digest",
        )
