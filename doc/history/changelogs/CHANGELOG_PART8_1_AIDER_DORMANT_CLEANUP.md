# Changelog — Part 8.1 Aider Dormant Cleanup

## Added

- `tools/local_ai_dormant_cleanup.py`
- Tests for cleanup planning and application.
- Dormant-mode documentation.
- Code-rule alignment note.
- Manifest and test report.

## Behavior

The cleanup tool removes generated Aider prompt/report artifacts and the failed
Aider-created patch directory. It can also append ignore rules for these local
artifacts.

## Not changed

- No Scheduler path.
- No EventBus path.
- No external API path.
- No remote mutation path.
