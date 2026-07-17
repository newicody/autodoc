from __future__ import annotations

import asyncio
from types import SimpleNamespace

from context.love_specialist_live_projection_binding_0287 import (
    LOVE_SPECIALIST_LIVE_PROJECTION_BINDING_SCHEMA,
    bind_love_specialist_analyses_live,
)


class _Store:
    def __init__(self, base_revision):
        self.base_revision = base_revision
        self.objects = []
        self.artifacts = []
        self.revisions = []
        self.relations = []
        self.projections = []

    def get_revision(self, revision_ref):
        return self.base_revision if revision_ref == self.base_revision.revision_ref else None

    def put_object(self, value):
        self.objects.append(value)

    def put_artifact(self, value):
        self.artifacts.append(value)

    def put_revision(self, value):
        self.revisions.append(value)

    def put_relation(self, value):
        self.relations.append(value)

    def put_projection(self, value):
        self.projections.append(value)


class _AsyncProjection:
    def __init__(self):
        self.calls = []

    async def project(self, authority_object, **kwargs):
        self.calls.append((authority_object, kwargs))
        projection = SimpleNamespace(
            source_ref=authority_object.object_ref,
            source_content_digest=authority_object.content_digest,
            to_mapping=lambda: {
                "source_ref": authority_object.object_ref,
                "source_content_digest": authority_object.content_digest,
            },
        )
        return SimpleNamespace(
            schema="missipy.love.analysis_projection_receipt.v1",
            projection=projection,
            to_mapping=lambda: {"projection": projection.to_mapping()},
        )


def test_binding_source_is_async_and_scheduler_neutral() -> None:
    import inspect
    import context.love_specialist_live_projection_binding_0287 as module

    text = inspect.getsource(module)
    assert "async def bind_love_specialist_analyses_live" in text
    assert "await projection_port.project" in text
    assert "security_scope=command.security_scope" in text
    assert "authority_store.put_projection" in text
    for forbidden in (
        "Scheduler(",
        "asyncio.run(",
        "QdrantClient(",
        "RealOpenVINORuntime(",
        "psycopg.connect(",
        "LaboratoryManager",
    ):
        assert forbidden not in text


def test_two_projection_calls_keep_stable_order(monkeypatch) -> None:
    import context.love_specialist_live_projection_binding_0287 as module

    first_analysis = SimpleNamespace(
        specialist_ref="specialist:love-concept-affect",
        evidence_refs=("evidence:first",),
    )
    second_analysis = SimpleNamespace(
        specialist_ref="specialist:love-relational-dynamics",
        evidence_refs=("evidence:second",),
    )
    base_membership = SimpleNamespace(object_ref="sql:source", state="active")
    base_revision = SimpleNamespace(
        revision_ref="context-revision:base",
        context_ref="context:love",
        memberships=(base_membership,),
    )
    first_object = SimpleNamespace(
        object_ref="sql:love-analysis:first",
        content_digest="sha256:" + "1" * 64,
        to_mapping=lambda: {"object_ref": "sql:love-analysis:first"},
    )
    second_object = SimpleNamespace(
        object_ref="sql:love-analysis:second",
        content_digest="sha256:" + "2" * 64,
        to_mapping=lambda: {"object_ref": "sql:love-analysis:second"},
    )
    first_artifact = SimpleNamespace(
        artifact_ref="artifact:first",
        to_mapping=lambda: {"artifact_ref": "artifact:first"},
    )
    second_artifact = SimpleNamespace(
        artifact_ref="artifact:second",
        to_mapping=lambda: {"artifact_ref": "artifact:second"},
    )
    active_memberships = (
        base_membership,
        SimpleNamespace(object_ref=first_object.object_ref, state="active"),
        SimpleNamespace(object_ref=second_object.object_ref, state="active"),
        SimpleNamespace(object_ref=first_artifact.artifact_ref, state="active"),
        SimpleNamespace(object_ref=second_artifact.artifact_ref, state="active"),
    )
    revision = SimpleNamespace(
        revision_ref="context-revision:analysis",
        context_ref="context:love",
        memberships=active_memberships,
        to_mapping=lambda: {"revision_ref": "context-revision:analysis"},
    )

    monkeypatch.setattr(
        module,
        "concept_analysis_from_visit_result",
        lambda result: first_analysis,
    )
    monkeypatch.setattr(module, "_validate_chain", lambda *args: None)
    monkeypatch.setattr(
        module,
        "_analysis_object",
        lambda analysis, title: (
            first_object if analysis is first_analysis else second_object
        ),
    )
    monkeypatch.setattr(
        module,
        "build_concept_analysis_artifact",
        lambda *args, **kwargs: object(),
    )
    artifacts = iter((first_artifact, second_artifact))
    monkeypatch.setattr(module, "_artifact_descriptor", lambda *args, **kwargs: next(artifacts))
    monkeypatch.setattr(module, "_merge_memberships", lambda *args: active_memberships)
    monkeypatch.setattr(
        module,
        "build_context_revision_ref",
        lambda **kwargs: revision.revision_ref,
    )
    monkeypatch.setattr(module, "ContextRevision", lambda **kwargs: revision)
    monkeypatch.setattr(module, "_put_relations", lambda *args, **kwargs: None)

    command = SimpleNamespace(
        command_ref="love-synthesis-command:test",
        base_revision_ref=base_revision.revision_ref,
        branch_ref="branch:main",
        project_ref="project:autodoc",
        security_scope="security-scope:project",
        created_at="2026-07-17T00:00:00Z",
        study=SimpleNamespace(study_ref="love-study:test"),
        collaboration=SimpleNamespace(
            first_execution=SimpleNamespace(
                result=object(),
                request=SimpleNamespace(visit_ref="laboratory-visit:first"),
            ),
            second_analysis=second_analysis,
            second_artifact=object(),
            second_execution=SimpleNamespace(
                request=SimpleNamespace(objective_ref="specialist-task:second")
            ),
            conversation=SimpleNamespace(
                conversation_ref="laboratory-conversation:test"
            ),
        ),
    )
    store = _Store(base_revision)
    projector = _AsyncProjection()

    result = asyncio.run(
        bind_love_specialist_analyses_live(
            command,
            authority_store=store,
            projection_port=projector,
        )
    )

    assert result.schema == LOVE_SPECIALIST_LIVE_PROJECTION_BINDING_SCHEMA
    assert result.authority_objects == (first_object, second_object)
    assert [item[0].object_ref for item in projector.calls] == [
        first_object.object_ref,
        second_object.object_ref,
    ]
    assert all(
        call[1]["security_scope"] == command.security_scope
        for call in projector.calls
    )
    assert store.projections == [
        result.projection_receipts[0].projection,
        result.projection_receipts[1].projection,
    ]
    assert result.to_mapping()["boundaries"]["synthesis_performed"] is False
