import json
from pathlib import Path

from context.baby_fork_runtime_flow import run_baby_fork_runtime_flow


def _report() -> dict:
    return {
        "retrieval": {
            "retrieved_ids": ["baby-silicone-fork", "rounded-stainless-soft-handle"],
            "rejected_ids": ["nasa-antenna"],
        },
        "variant_generator_stub": {
            "generated_variants": [
                {"variant_id": "variant-1"},
                {"variant_id": "variant-2"},
            ]
        },
        "final_context": {
            "context_id": "ctx-baby-fork-001",
            "context_version": 2,
            "selected_variant_id": "variant-1",
        },
    }


def test_runtime_flow_writes_measured_controlproxy_sizing_hints(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(_report()), encoding="utf-8")

    summary = run_baby_fork_runtime_flow(
        report_path,
        tmp_path / "fake_runtime",
        tmp_path / "fake_runtime" / "runtime_journal.jsonl",
        controlfs_root=tmp_path / "controlfs",
    )

    assert summary.controlfs is not None

    retrieval = json.loads(
        (tmp_path / "controlfs" / "desired" / "routes" / "baby_fork.retrieval" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )

    assert retrieval["transport"] == "mmap.fixed_slot"
    assert retrieval["notify"] == "semaphore"
    assert retrieval["overflow_policy"] == "reject"
    assert retrieval["sizing_source"] == "controlproxy.prepare"
    assert retrieval["observed_frame_bytes"] > 0
    assert retrieval["slot_size"] >= retrieval["observed_frame_bytes"]
    assert retrieval["max_frame_bytes"] == retrieval["slot_size"]
