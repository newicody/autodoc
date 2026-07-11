from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from context.scheduler_managed_sql_ref_openvino_embedding_usage_0261 import (
    SchedulerManagedSqlRefOpenVinoEmbeddingRequest,
    build_openvino_text_from_sql_record,
    run_scheduler_managed_sql_ref_openvino_embedding_usage,
)


@dataclass(frozen=True)
class Record:
    context_ref: str = "sql:github_artifact:query-role"
    kind: str = "github_artifact"
    title: str = "Query role propagation"
    body: str = "The query prefix and role must stay explicit through 0261."
    parent_ref: str | None = None
    metadata: tuple[tuple[str, str], ...] = ()

    def to_mapping(self) -> dict[str, Any]:
        return {
            "context_ref": self.context_ref,
            "kind": self.kind,
            "title": self.title,
            "body": self.body,
            "parent_ref": self.parent_ref,
            "metadata": dict(self.metadata),
        }


class Store:
    def get_record(self, context_ref: str) -> Record | None:
        return Record() if context_ref == Record().context_ref else None


def test_role_aware_sql_text_builder_keeps_e5_query_prefix() -> None:
    text = build_openvino_text_from_sql_record(Record().to_mapping(), role="query")
    assert text.startswith("query: Query role propagation\n")


def test_0261_propagates_query_role_to_injected_embedding_surface() -> None:
    observed: dict[str, str] = {}

    def embedder(
        text: str,
        sql_ref: str,
        model_dir: str | None,
        device: str,
    ) -> Mapping[str, Any]:
        observed["text"] = text
        observed["sql_ref"] = sql_ref
        return {
            "schema": "missipy.scheduler_managed_sql_ref_openvino_embedding.v1",
            "embedding_ref": "embedding:query:role-propagation",
            "source_ref": f"ctx-fragment:{sql_ref}",
            "sql_ref": sql_ref,
            "backend_ref": "openvino:model:multilingual-e5-small",
            "role": "query",
            "dimension": 384,
            "normalized": True,
            "l2_norm": 1.0,
            "metadata": {
                "context_ref": sql_ref,
                "model": "test.e5",
                "tokenizer": "test.tokenizer",
                "device": device,
            },
            "vector": [1.0] + [0.0] * 383,
        }

    result = run_scheduler_managed_sql_ref_openvino_embedding_usage(
        Store(),
        SchedulerManagedSqlRefOpenVinoEmbeddingRequest(
            sql_ref=Record().context_ref,
            role="query",
            policy_decision_id="policy:0272:r10:query-role",
        ),
        execute=True,
        embedder=embedder,
    )

    assert result.valid is True
    assert result.embedding_text.startswith("query:")
    assert observed["text"].startswith("query:")
    assert result.embedding["role"] == "query"
