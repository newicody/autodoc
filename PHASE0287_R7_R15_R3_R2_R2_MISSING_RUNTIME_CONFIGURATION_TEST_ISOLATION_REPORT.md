# Phase 0287 R7 R15 R3 R2 R2 — missing runtime configuration test isolation

## Failure

The global suite failed only in
`test_missing_runtime_configuration_has_operator_facing_error`.  The test used
`config=None`, which intentionally tells the production command to inspect the
installed default `.var/config/love_actions_closed_loop.ini`.

On a configured operator machine that file exists and contains the canonical
runtime factory, so the test no longer represented a missing-configuration
case.

## Resolution

The test now creates and explicitly supplies an empty local configuration file.
The ProjectV2 fixture remains explicit.  Therefore the test still verifies the
operator-facing `real runtime factory is not configured` error, while remaining
independent of all files under the operator's `.var/` directory.

## Boundaries

- no production code change;
- no runtime-provider behavior change;
- no fallback removal or addition;
- no Scheduler, SQL, Qdrant or OpenVINO change;
- installed local configuration remains usable by the real command;
- tests no longer inspect operator state accidentally.
