import json
from pathlib import Path

from context.baby_fork_runtime_flow import run_baby_fork_runtime_flow


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


def _write_report(tmp_path: Path) -> Path:
    path = tmp_path / "baby_fork_report.json"
    path.write_text(json.dumps(_report()), encoding="utf-8")
    return path


def test_runtime_flow_writes_fake_runtime_and_journal(tmp_path: Path) -> None:
    report = _write_report(tmp_path)
    fake_runtime = tmp_path / "fake_runtime"
    journal = fake_runtime / "runtime_journal.jsonl"

    summary = run_baby_fork_runtime_flow(report, fake_runtime, journal)

    assert summary.projection == {
        "data_handle_count": 1,
        "event_count": 2,
        "context_count": 1,
        "route_message_count": 3,
    }
    assert summary.fake_runtime["route_message_count"] == 3
    assert summary.recorder["record_count"] == 7
    assert journal.exists()
    assert len(journal.read_text(encoding="utf-8").splitlines()) == 7


def test_runtime_flow_can_include_controlfs_routeproxy_plan(tmp_path: Path) -> None:
    report = _write_report(tmp_path)
    fake_runtime = tmp_path / "fake_runtime"
    journal = fake_runtime / "runtime_journal.jsonl"
    controlfs = tmp_path / "controlfs"

    summary = run_baby_fork_runtime_flow(
        report,
        fake_runtime,
        journal,
        controlfs_root=controlfs,
    )

    assert summary.controlfs is not None
    assert summary.controlfs["action_counts"] == {
        "create": 3,
        "delete": 0,
        "update": 0,
        "noop": 0,
        "error": 0,
    }
    assert (controlfs / "desired" / "routes" / "baby_fork.retrieval" / "manifest.json").exists()
    assert (controlfs / "desired" / "routes" / "baby_fork.variant_stub" / "manifest.json").exists()
    assert (controlfs / "desired" / "routes" / "baby_fork.context_gate" / "manifest.json").exists()


def test_runtime_flow_uses_context_id_from_report_for_controlfs(tmp_path: Path) -> None:
    report = _write_report(tmp_path)
    fake_runtime = tmp_path / "fake_runtime"
    journal = fake_runtime / "runtime_journal.jsonl"
    controlfs = tmp_path / "controlfs"

    run_baby_fork_runtime_flow(report, fake_runtime, journal, controlfs_root=controlfs)

    manifest = json.loads(
        (controlfs / "desired" / "routes" / "baby_fork.retrieval" / "manifest.json").read_text(
            encoding="utf-8"
        )
    )
    assert manifest["task_id"] == "ctx-baby-fork-001"
