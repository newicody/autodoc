# Phase 0287 R7 R15 R3 R2 R1 — Installed runtime provider default compatibility

## Problem

The r15-r3-r1 architecture rule intentionally required the example installation
configuration to retain a literal blank `factory =` marker.  r15-r3-r2 replaced
that line with the canonical provider path and therefore failed the historical
rule even though the provider itself was valid.

## Resolution

The example keeps `factory =` blank.  The canonical installed runtime factory
resolves an empty value to
`context.love_manual_installed_runtime_provider_0287:build_installed_runtime_ports`.
The provider path remains documented in the example and no operator Python
configuration is required.

## Boundaries

- no fake or dummy fallback;
- no new Scheduler or runtime manager;
- no backend construction;
- a non-empty explicit provider remains supported for installation-owned
  compatible compositions;
- PostgreSQL, Qdrant and OpenVINO coordinates remain manually configured.
