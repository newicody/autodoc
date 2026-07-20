from __future__ import annotations

from types import SimpleNamespace

import pytest

from context.love_externally_managed_installed_backend_foundation_0287 import (
    LoveExternallyManagedInstalledBackendFoundationError,
    validate_love_externally_managed_backend_alignment,
)


def _settings(*, lifecycle: str = "externally-managed") -> SimpleNamespace:
    return SimpleNamespace(
        runtime_ref="runtime:love-installed",
        scheduler_ref="scheduler:main",
        scheduler_lifecycle=lifecycle,
        sql_authority_ref="sql-authority:postgresql-love",
        projection_backend_ref="projection:qdrant-live",
        embedding_backend_ref="openvino:multilingual-e5-small",
        retrieval_backend_ref="qdrant:hybrid-live",
        model_ref="model:intfloat-multilingual-e5-small",
        model_revision="main",
        base_revision_ref="context-revision:base",
        qdrant_collection="autodoc-love",
    )


def _manual(*, lifecycle: str = "externally-managed", dimension: int = 384):
    settings = _settings(lifecycle=lifecycle)
    return SimpleNamespace(
        runtime_ref=settings.runtime_ref,
        scheduler_ref=settings.scheduler_ref,
        scheduler_lifecycle=lifecycle,
        sql_authority_ref=settings.sql_authority_ref,
        projection_backend_ref=settings.projection_backend_ref,
        embedding_backend_ref=settings.embedding_backend_ref,
        retrieval_backend_ref=settings.retrieval_backend_ref,
        model_ref=settings.model_ref,
        model_revision=settings.model_revision,
        base_revision_ref=settings.base_revision_ref,
        qdrant=SimpleNamespace(
            named_vectors_enabled=True,
            physical_collection="autodoc-love",
            dimension=dimension,
        ),
        openvino=SimpleNamespace(dimension=dimension),
    )


def test_externally_managed_alignment_accepts_dimension_384() -> None:
    validate_love_externally_managed_backend_alignment(_settings(), _manual())


def test_tool_bounded_lifecycle_is_rejected() -> None:
    with pytest.raises(
        LoveExternallyManagedInstalledBackendFoundationError,
        match="externally-managed",
    ):
        validate_love_externally_managed_backend_alignment(
            _settings(lifecycle="tool-bounded"),
            _manual(lifecycle="tool-bounded"),
        )


def test_non_384_embedding_is_rejected() -> None:
    with pytest.raises(
        LoveExternallyManagedInstalledBackendFoundationError,
        match="dimension 384",
    ):
        validate_love_externally_managed_backend_alignment(
            _settings(),
            _manual(dimension=385),
        )
