# Changelog — 0287 r16-r4-r3

## Added

- One bounded local cycle composing artifact fetch and Copilot Issue publication.
- Non-blocking overlap lock suitable for external periodic invocation.
- Separate persisted child reports and one combined cycle report.
- Explicit execute gates and child-status propagation.
- Architecture, code rule, manifest, report, and rule tests.

## Reused

- Existing GitHub Actions scan/fetch.
- Existing ready-run Copilot Issue publisher.
- Existing publication state and replay/readback behavior.

## Preserved

- GitHub Actions `issues: read`.
- No new scheduler, daemon, loop, SQL/Qdrant write, or laboratory execution.
