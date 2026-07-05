# Manifest — 0090 route message journal

0090 adds the importable Recorder/journal ingestion step for drained route messages.

## Changed files

```text
src/runtime/route_message_journal.py
tests/runtime/test_route_message_journal.py
tests/rules/test_route_message_journal_rule.py
doc/architecture/ROUTE_MESSAGE_JOURNAL_0090.md
doc/manifests/MANIFEST_0090_CHANGED_FILES.md
PHASE0090_TEST_REPORT.md
```

## Boundary statement

0090 does not change kernel-loop, queue, dispatcher, or component-contract files.
It also does not add a CLI, daemon, service, resident watcher, policy bypass, live mmap resize, Qdrant path, LLM path, or OpenVINO path.
