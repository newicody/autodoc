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


def test_repeated_baby_fork_runtime_flow_replaces_fake_route_files(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(_report()), encoding="utf-8")

    fake_runtime = tmp_path / "fake_runtime"
    journal = fake_runtime / "runtime_journal.jsonl"

    first = run_baby_fork_runtime_flow(report_path, fake_runtime, journal)
    second = run_baby_fork_runtime_flow(report_path, fake_runtime, journal)

    assert first.fake_runtime["route_message_count"] == 3
    assert first.recorder["record_count"] == 7
    assert second.fake_runtime["route_message_count"] == 3
    assert second.recorder["record_count"] == 7
    assert len(journal.read_text(encoding="utf-8").splitlines()) == 7


def test_repeated_baby_fork_runtime_flow_with_controlfs_still_replaces_routes(tmp_path: Path) -> None:
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(_report()), encoding="utf-8")

    fake_runtime = tmp_path / "fake_runtime"
    journal = fake_runtime / "runtime_journal.jsonl"
    controlfs = tmp_path / "controlfs"

    run_baby_fork_runtime_flow(report_path, fake_runtime, journal, controlfs_root=controlfs)
    second = run_baby_fork_runtime_flow(report_path, fake_runtime, journal, controlfs_root=controlfs)

    assert second.fake_runtime["route_message_count"] == 3
    assert second.recorder["record_count"] == 7
    assert second.controlfs is not None
    assert second.controlfs["action_counts"]["create"] == 3
