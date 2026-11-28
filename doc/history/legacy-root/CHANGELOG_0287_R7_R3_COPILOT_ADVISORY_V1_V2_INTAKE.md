# Changelog 0287-r7-r3

## Changed

- extend the existing dual-artifact contract with a strict first-opinion v2
  artifact class;
- add explicit v1/v2 advisory schema dispatch;
- make the existing read-only intake accept either public schema;
- retain the advisory schema as non-authoritative source-candidate metadata;
- prove that the unchanged 0281 run assembler delegates v2 to the intake;
- update the cumulative Copilot v2 runbook with the migration boundary.

## Preserved

- v1 public fields and meaning;
- request authority and physical artifact separation;
- no advisory content copied into `SourceCandidate`;
- no Scheduler, laboratory, backend or remote mutation changes.
