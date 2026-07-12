# Changelog — 0275-r8-r1 ProjectV2 0272 config compatibility fix

## Fixed

- restored the locked 0272 artifact-source trigger;
- restored the locked ten-minute 0272 scan interval;
- restored the original 0272 query-only scan command;
- restored the 0272 safety allow-list and optional Actions bridge;
- kept the new 0275-r8 `[workflow_dispatch]` scope unchanged.

## Root cause

0275-r8 reused the existing 0272 configuration file but replaced values
validated by `github_project_push_frame_config.py`. This caused all consumers
of the established 0272 loader to reject the example config before reaching
their own logic.

## Boundaries

- no runtime contract change;
- no Project or issue mutation;
- no workflow-template change;
- no Scheduler change;
- no dependency change.
