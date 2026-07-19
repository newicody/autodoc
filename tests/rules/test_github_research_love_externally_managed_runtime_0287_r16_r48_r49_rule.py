from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src/context/github_research_love_externally_managed_runtime_0287.py"
CONTINUATION = ROOT / "src/kernel/scheduler_canonical_continuation.py"
DOC = ROOT / "doc/architecture/GITHUB_RESEARCH_LOVE_EXTERNALLY_MANAGED_RUNTIME_0287_R16_R48_R49.md"


def test_r16_r48_r49_locks_external_runtime_and_passive_temporal_memory() -> None:
    text = MODULE.read_text(encoding="utf-8")
    continuation = CONTINUATION.read_text(encoding="utf-8")
    documentation = DOC.read_text(encoding="utf-8")
    for token in (
        "claim_next_for_running_canonical_scheduler",
        "SchedulerCanonicalBoundedCycle",
        "scheduler_handler_temporal_observations",
        "BufferedPersistentHandlerInformationSink",
        "len(self.bootstrap.handler_refs) != 10",
        "observation-only",
    ):
        assert token in text
    assert '"handler-outcome:",' in continuation
    assert '"scheduler-handler-outcome:",' not in continuation
    assert "OpenRC possède le processus" in documentation
    assert "VisPy reste observation-only" in documentation
    for forbidden in ("while True", "threading.Thread", "jsonl", "LaboratoryManager"):
        assert forbidden not in text
