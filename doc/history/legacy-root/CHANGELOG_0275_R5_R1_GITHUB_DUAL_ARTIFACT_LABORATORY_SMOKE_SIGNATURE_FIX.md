# Changelog — 0275-r5-r1 laboratory smoke signature fix

## Fixed

- removed the obsolete one-argument construction of
  `FakeLaboratoryClosedLoopSmokeCommand`;
- isolated the 0275 wrapper test from the complete 0274 laboratory runtime;
- mocked the asynchronous 0274 boundary while checking Scheduler, command and
  dependency forwarding;
- retained assertions for promotion and local-only GitHub preview behavior.

## Runtime impact

None. This patch changes tests and documentation only.
