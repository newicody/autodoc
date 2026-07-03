from __future__ import annotations

from pathlib import Path

from context.baby_fork_smoke_project import (
    BabyForkTaskContext,
    apply_baby_fork_context_patch,
    baby_fork_seed_documents,
    make_two_baby_fork_variants_stub,
    retrieve_baby_fork_documents,
    run_baby_fork_smoke_project,
)
from context.cell_snapshot_journal_reader import read_cell_snapshot_jsonl


def _context() -> BabyForkTaskContext:
    return BabyForkTaskContext(
        context_id="ctx",
        task_id="task",
        version=1,
        domain="baby_utensil",
        objective="design a baby fork",
        constraints=("food contact", "rounded geometry", "baby grip"),
    )


def test_retrieval_worker_filters_to_baby_utensil_domain() -> None:
    result = retrieve_baby_fork_documents(_context(), baby_fork_seed_documents())
    assert [doc.document_id for doc in result.retrieved] == ["baby-silicone-fork", "rounded-stainless-soft-handle"]
    assert "nasa-antenna" in result.rejected_ids


def test_variant_generator_stub_produces_exactly_two_context_variants() -> None:
    context = _context()
    retrieval = retrieve_baby_fork_documents(context, baby_fork_seed_documents())
    patch = make_two_baby_fork_variants_stub(context, retrieval)
    assert len(patch.variants) == 2
    assert patch.selected_variant == "variant-1"
    assert patch.variants[0].label == "soft silicone baby fork"
    assert patch.variants[1].label == "rounded stainless with soft handle"
    assert patch.variants[0].score > patch.variants[1].score
    assert "baby" in patch.reason


def test_context_gate_versions_context_after_patch() -> None:
    context = _context()
    retrieval = retrieve_baby_fork_documents(context, baby_fork_seed_documents())
    patch = make_two_baby_fork_variants_stub(context, retrieval)
    final_context = apply_baby_fork_context_patch(context, patch)
    assert final_context.version == 2
    assert final_context.evidence_ids == ("baby-silicone-fork", "rounded-stainless-soft-handle")
    assert final_context.selected_variant == "variant-1"


def test_baby_fork_smoke_project_feeds_cell_lens_from_real_flow(tmp_path: Path) -> None:
    result = run_baby_fork_smoke_project(tmp_path)
    replay = read_cell_snapshot_jsonl(Path(result.journal_path))
    assert result.ok is True
    assert result.snapshot_count == 6
    assert len(replay.snapshots) == 6
    assert [snapshot.source_class for snapshot in replay.snapshots] == [
        "project.context", "scheduler.project", "worker.retrieval", "variant_generator.stub", "context.gate", "project.result"
    ]
