# Changelog — 0273-r2 laboratory framework contract

## Added

- immutable `missipy.laboratory.v1` descriptor, budget, visit request and result
  contracts;
- deep freezing and JSON-compatible result projection;
- bounded validation for context, evidence, output and follow-up requests;
- reserved mediated inter-laboratory identities;
- inactive binding plan targeting the existing 0257 Scheduler-owned registry;
- architecture, release, manifest, phase report and executable tests.

## Not added

- no provider implementation;
- no new registry, manager, Scheduler, bus or backend;
- no network access;
- no external dependency.
