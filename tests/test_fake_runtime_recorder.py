from pathlib import Path

from context.baby_fork_runtime_projection import build_baby_fork_runtime_projection
from runtime.fake_route_transport import write_projection_to_fake_runtime
from runtime.fake_runtime_recorder import (
    RUNTIME_JOURNAL_RECORD_SCHEMA,
    ingest_fake_runtime_to_journal,
    load_runtime_journal,
)


def _report() -> dict:
    return {
        "ok": True,
        "retrieval": {
            "retrieved_ids": ["baby-silicone-fork", "rounded-stainless-soft-handle"],
            "rejected_ids": ["nasa-antenna"],
        },
        "variant_generator_stub": {
            "generated_variants": [
                {"variant_id": "variant-1", "label": "soft silicone baby fork", "score": 0.86},
                {"variant_id": "variant-2", "label": "rounded stainless with soft handle", "score": 0.74},
            ]
        },
        "final_context": {
            "context_id": "ctx-baby-fork-001",
            "context_version": 2,
            "selected_variant_id": "variant-1",
        },
    }


def _write_fake_runtime(tmp_path: Path) -> Path:
    runtime_root = tmp_path / "runtime"
    projection = build_baby_fork_runtime_projection(_report())
    write_projection_to_fake_runtime(
        runtime_root,
        data_handles=projection.data_handles,
        events=projection.events,
        contexts=projection.contexts,
        routes=projection.routes,
    )
    return runtime_root


def test_ingest_fake_runtime_to_journal_counts_baby_fork_messages(tmp_path: Path) -> None:
    runtime_root = _write_fake_runtime(tmp_path)
    journal_path = tmp_path / "runtime_journal.jsonl"

    summary = ingest_fake_runtime_to_journal(runtime_root, journal_path)

    assert summary.record_count == 7
    assert summary.data_handle_count == 1
    assert summary.event_count == 2
    assert summary.context_count == 1
    assert summary.route_message_count == 3
    assert summary.route_ids == (
        "baby_fork.context_gate",
        "baby_fork.retrieval",
        "baby_fork.variant_stub",
    )


def test_runtime_journal_records_are_loadable_and_schema_tagged(tmp_path: Path) -> None:
    runtime_root = _write_fake_runtime(tmp_path)
    journal_path = tmp_path / "runtime_journal.jsonl"

    ingest_fake_runtime_to_journal(runtime_root, journal_path)
    records = load_runtime_journal(journal_path)

    assert len(records) == 7
    assert {record.schema for record in records} == {RUNTIME_JOURNAL_RECORD_SCHEMA}
    assert {record.message_kind for record in records} == {
        "data_handle",
        "event",
        "context",
        "route",
    }
    assert all(record.payload_hash.startswith("sha256:") for record in records)


def test_runtime_journal_preserves_variant_count_from_route_message(tmp_path: Path) -> None:
    runtime_root = _write_fake_runtime(tmp_path)
    journal_path = tmp_path / "runtime_journal.jsonl"

    ingest_fake_runtime_to_journal(runtime_root, journal_path)
    records = load_runtime_journal(journal_path)

    variant_records = [
        record
        for record in records
        if record.source_surface == "routes/baby_fork.variant_stub"
    ]

    assert len(variant_records) == 1
    assert variant_records[0].message["payload"]["variant_count"] == 2
    assert variant_records[0].message["payload"]["variant_ids"] == ["variant-1", "variant-2"]


def test_ingest_fake_runtime_can_append_journal(tmp_path: Path) -> None:
    runtime_root = _write_fake_runtime(tmp_path)
    journal_path = tmp_path / "runtime_journal.jsonl"

    ingest_fake_runtime_to_journal(runtime_root, journal_path)
    ingest_fake_runtime_to_journal(runtime_root, journal_path, append=True)

    records = load_runtime_journal(journal_path)
    assert len(records) == 14
