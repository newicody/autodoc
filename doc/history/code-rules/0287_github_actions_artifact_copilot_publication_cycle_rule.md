# Code rule 0287 — local artifact/Copilot publication cycle

1. The cycle MUST compose the existing artifact scan and existing ready-run
   Issue publisher; it MUST NOT duplicate either implementation.
2. The cycle MUST be one-shot and MUST NOT add a polling loop, daemon, worker,
   Scheduler, laboratory manager, or service lifecycle.
3. An external process authority such as `fcron` MAY invoke the cycle.
4. Concurrent invocations MUST be rejected by a non-blocking local lock.
5. The scan child report and publication child report MUST be persisted
   separately before the combined cycle report.
6. Publication MUST run only after a valid scan result.
7. Execute mode MUST require the remote mutation and Issue publication gates.
8. GitHub Actions MUST remain `issues: read`.
9. SQL, Qdrant, Scheduler, and laboratory execution MUST remain closed.
10. A publication replay MUST remain idempotent through the existing child
    publication state and marked-comment readback contract.
