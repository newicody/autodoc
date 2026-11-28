# Report — local artifact/Copilot publication cycle r16-r4-r3

## Audit conclusion

The fetcher and Issue publisher already existed as separate one-shot commands.
The missing operational surface was a bounded composition suitable for the
existing external periodic process authority.

## Implementation

The new cycle:

- acquires a non-blocking local file lock;
- invokes the existing artifact scan/fetch;
- persists its exact JSON result;
- invokes the existing ready-run publisher only after a valid execute scan;
- persists the publication result;
- emits and stores a combined report;
- exits after one pass.

## Failure behavior

- invalid configuration or disabled mutation gates: rejected before child calls;
- overlapping run: successful `overlap-skipped`;
- invalid scan: publication is not called;
- failed publication: cycle reports `publication-failed`;
- successful replay remains a child-level idempotent no-op.

## Deferred work

- ProjectV2 `Avis Copilot` summary projection;
- durable SQL intake;
- operator decision and laboratory execution;
- final specialist-result publication;
- final fcron installation/readiness and full walking-skeleton validation.
