# Changelog — 0171 Runtime bus/scheduler artifact audit

## Added

- Architecture audit for GitHub artifact/server dataset integration.
- Code-rule lock preventing parallel VisPy/bus paths.
- Rule tests proving the repository already exposes the bus visualization and
  scheduler route surfaces that future artifact patches must reuse.

## Changed

- Reclassifies dataset-local `vispy_events` style files as observation
  journals/staging, not canonical VisPy integration.

## Not changed

- No runtime implementation.
- No network.
- No GitHub mutation.
- No conversion execution.
- No inference.
