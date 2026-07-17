from __future__ import annotations

import asyncio
from types import SimpleNamespace

import context.love_async_hybrid_recall_liaison_synthesis_0287 as module


class _Retrieval:
    def __init__(self, refs: tuple[str, str]) -> None:
        self.items = tuple(SimpleNamespace(sql_ref=item) for item in refs)

    def to_mapping(self) -> dict[str, object]:
        return {"items": [item.sql_ref for item in self.items]}


class _AsyncReceipt:
    def to_mapping(self) -> dict[str, object]:
        return {"async": True}


def test_r13_awaits_recall_without_reprojection(monkeypatch) -> None:
    first_ref = "sql:love-analysis:first"
    second_ref = "sql:love-analysis:second"
    retrieval = _Retrieval((first_ref, second_ref))
    retrieval_execution = SimpleNamespace(
        retrieval=retrieval,
        receipt=_AsyncReceipt(),
        to_mapping=lambda: {"retrieval": retrieval.to_mapping()},
    )
    captured = {}

    async def _execute(query, **kwargs):
        captured["query"] = query
        captured["kwargs"] = kwargs
        return retrieval_execution

    first_analysis = SimpleNamespace(specialist_ref="specialist:first")
    second_analysis = SimpleNamespace(specialist_ref="specialist:second")
    monkeypatch.setattr(
        module,
        "concept_analysis_from_visit_result",
        lambda result: first_analysis,
    )
    monkeypatch.setattr(module, "_validate_chain", lambda *args: None)
    monkeypatch.setattr(module, "execute_love_async_hybrid_retrieval", _execute)

    analysis_revision = SimpleNamespace(revision_ref="context-revision:analysis")
    projection_receipts = (SimpleNamespace(), SimpleNamespace())
    binding = SimpleNamespace(
        command_ref="love-synthesis-command:test",
        synthesis_performed=False,
        analysis_revision=analysis_revision,
        authority_objects=(
            SimpleNamespace(object_ref=first_ref),
            SimpleNamespace(object_ref=second_ref),
        ),
        artifact_descriptors=(SimpleNamespace(), SimpleNamespace()),
        projection_receipts=projection_receipts,
        to_mapping=lambda: {"binding": True},
    )
    command = SimpleNamespace(
        command_ref=binding.command_ref,
        branch_ref="branch:main",
        project_ref="project:autodoc",
        security_scope="security-scope:project",
        effective_query_text="relation et confiance",
        collaboration=SimpleNamespace(
            first_execution=SimpleNamespace(result=object()),
            second_analysis=second_analysis,
            second_execution=SimpleNamespace(
                request=SimpleNamespace(objective_ref="specialist-task:second")
            ),
            conversation=SimpleNamespace(
                conversation_ref="laboratory-conversation:test"
            ),
        ),
    )
    synthesis = SimpleNamespace(
        schema="missipy.love.memory_evidence_synthesis_result.v1",
        command_ref=command.command_ref,
        analysis_revision=analysis_revision,
        projection_receipts=projection_receipts,
        retrieval=retrieval,
        to_mapping=lambda: {"synthesis": True},
    )

    def _finalize(*args, **kwargs):
        captured["finalize"] = kwargs
        return synthesis

    monkeypatch.setattr(
        module,
        "finalize_love_memory_evidence_liaison_synthesis",
        _finalize,
    )

    result = asyncio.run(
        module.run_love_async_hybrid_recall_liaison_synthesis(
            command,
            binding=binding,
            collection=object(),
            embedder=object(),
            executor=object(),
            authority_store=object(),
        )
    )

    query = captured["query"]
    assert query.final_limit == 2
    assert query.group_by == "source_ref"
    assert query.filter.context_revision_ref == analysis_revision.revision_ref
    assert query.filter.sql_authority_ref == ""
    assert query.filter.artifact_kinds == ("specialist_analysis",)
    assert query.filter.contribution_kinds == ("domain_analysis",)
    assert captured["finalize"]["retrieval"] is retrieval
    assert result.analysis_reprojected is False
    assert result.synthesis is synthesis
