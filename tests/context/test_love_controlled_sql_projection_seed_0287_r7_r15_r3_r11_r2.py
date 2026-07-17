from __future__ import annotations

import pytest

from context.context_revision_sql_authority_0287 import (
    CONTEXT_REVISION_SCHEMA,
    ContextAuthorityObject,
    ContextRevision,
    SQLiteContextRevisionAuthorityStore,
)
from context.love_controlled_sql_projection_seed_0287 import (
    DEFAULT_OBJECT_REF,
    DEFAULT_REVISION_REF,
    LoveControlledSqlProjectionSeedError,
    LoveControlledSqlProjectionSeedGate,
    build_love_controlled_sql_projection_seed_plan,
    execute_love_controlled_sql_projection_seed,
    inspect_love_controlled_sql_projection_seed,
)

BASE_REVISION_REF = "context-revision:love-base"


def _store() -> SQLiteContextRevisionAuthorityStore:
    store = SQLiteContextRevisionAuthorityStore()
    store.initialize_schema()
    store.put_revision(
        ContextRevision(
            schema=CONTEXT_REVISION_SCHEMA,
            revision_ref=BASE_REVISION_REF,
            context_ref="context:love-base",
            parent_revision_refs=(),
            memberships=(),
            validation_status="accepted",
            significance="material",
            evidence_refs=("evidence:installed-runtime",),
            created_at="2026-07-17T00:00:00Z",
            metadata={"bootstrap_seed": True},
        )
    )
    return store


def _gate(plan_digest: str) -> LoveControlledSqlProjectionSeedGate:
    return LoveControlledSqlProjectionSeedGate(
        policy_decision_id="policy:test-controlled-sql-seed",
        operator_decision="approve",
        allow_write=True,
        confirm_plan_digest=plan_digest,
    )


def test_plan_is_deterministic_and_uses_child_revision() -> None:
    first = build_love_controlled_sql_projection_seed_plan(
        parent_revision_ref=BASE_REVISION_REF,
    )
    second = build_love_controlled_sql_projection_seed_plan(
        parent_revision_ref=BASE_REVISION_REF,
    )

    assert first.plan_digest == second.plan_digest
    assert first.authority_object.object_ref == DEFAULT_OBJECT_REF
    assert first.revision.revision_ref == DEFAULT_REVISION_REF
    assert first.revision.parent_revision_refs == (BASE_REVISION_REF,)
    assert first.revision.validation_status == "accepted"
    assert first.revision.memberships[0].object_ref == DEFAULT_OBJECT_REF
    assert first.revision.memberships[0].state == "active"
    assert first.authority_object.body
    assert first.authority_object.content_digest.startswith("sha256:")


def test_preview_is_read_only_and_ready_before_first_seed() -> None:
    store = _store()
    plan = build_love_controlled_sql_projection_seed_plan(
        parent_revision_ref=BASE_REVISION_REF,
    )

    readiness = inspect_love_controlled_sql_projection_seed(store, plan)

    assert readiness.ready is True
    assert readiness.issues == ()
    assert readiness.object_state == "missing"
    assert readiness.revision_state == "missing"
    assert store.get_object(DEFAULT_OBJECT_REF) is None
    assert store.get_revision(DEFAULT_REVISION_REF) is None
    assert readiness.boundaries["sql_write_performed"] is False


def test_execute_inserts_object_and_accepted_child_revision() -> None:
    store = _store()
    plan = build_love_controlled_sql_projection_seed_plan(
        parent_revision_ref=BASE_REVISION_REF,
    )

    receipt = execute_love_controlled_sql_projection_seed(
        store,
        plan,
        _gate(plan.plan_digest),
    )

    assert receipt.object_inserted is True
    assert receipt.revision_inserted is True
    assert receipt.boundaries["qdrant_write_performed"] is False
    assert receipt.boundaries["base_revision_mutated"] is False
    assert "body" not in receipt.to_mapping()

    seeded_object = store.get_object(DEFAULT_OBJECT_REF)
    seeded_revision = store.get_revision(DEFAULT_REVISION_REF)
    base_revision = store.get_revision(BASE_REVISION_REF)
    assert seeded_object == plan.authority_object
    assert seeded_revision == plan.revision
    assert base_revision is not None
    assert base_revision.memberships == ()


def test_replay_is_idempotent() -> None:
    store = _store()
    plan = build_love_controlled_sql_projection_seed_plan(
        parent_revision_ref=BASE_REVISION_REF,
    )

    execute_love_controlled_sql_projection_seed(
        store,
        plan,
        _gate(plan.plan_digest),
    )
    replay = execute_love_controlled_sql_projection_seed(
        store,
        plan,
        _gate(plan.plan_digest),
    )

    assert replay.object_inserted is False
    assert replay.object_idempotent_replay is True
    assert replay.revision_inserted is False
    assert replay.revision_idempotent_replay is True


def test_gate_requires_approval_environment_and_exact_digest() -> None:
    store = _store()
    plan = build_love_controlled_sql_projection_seed_plan(
        parent_revision_ref=BASE_REVISION_REF,
    )

    denied = LoveControlledSqlProjectionSeedGate(
        policy_decision_id="policy:test-controlled-sql-seed",
        operator_decision="reject",
        allow_write=True,
        confirm_plan_digest=plan.plan_digest,
    )
    with pytest.raises(LoveControlledSqlProjectionSeedError, match="approval"):
        execute_love_controlled_sql_projection_seed(store, plan, denied)

    closed = LoveControlledSqlProjectionSeedGate(
        policy_decision_id="policy:test-controlled-sql-seed",
        operator_decision="approve",
        allow_write=False,
        confirm_plan_digest=plan.plan_digest,
    )
    with pytest.raises(LoveControlledSqlProjectionSeedError, match="environment"):
        execute_love_controlled_sql_projection_seed(store, plan, closed)

    stale = LoveControlledSqlProjectionSeedGate(
        policy_decision_id="policy:test-controlled-sql-seed",
        operator_decision="approve",
        allow_write=True,
        confirm_plan_digest="sha256:" + "0" * 64,
    )
    with pytest.raises(LoveControlledSqlProjectionSeedError, match="digest"):
        execute_love_controlled_sql_projection_seed(store, plan, stale)


def test_collision_fails_before_any_revision_write() -> None:
    store = _store()
    plan = build_love_controlled_sql_projection_seed_plan(
        parent_revision_ref=BASE_REVISION_REF,
    )
    conflicting = ContextAuthorityObject(
        schema=plan.authority_object.schema,
        object_ref=plan.authority_object.object_ref,
        object_kind=plan.authority_object.object_kind,
        content_schema_ref=plan.authority_object.content_schema_ref,
        content_digest="sha256:" + "1" * 64,
        title="Conflicting seed",
        body="Different immutable content.",
        media_type="text/plain",
        byte_count=28,
    )
    store.put_object(conflicting)

    readiness = inspect_love_controlled_sql_projection_seed(store, plan)

    assert readiness.ready is False
    assert "immutable authority object collision" in readiness.issues
    with pytest.raises(LoveControlledSqlProjectionSeedError, match="collision"):
        execute_love_controlled_sql_projection_seed(
            store,
            plan,
            _gate(plan.plan_digest),
        )
    assert store.get_revision(DEFAULT_REVISION_REF) is None
