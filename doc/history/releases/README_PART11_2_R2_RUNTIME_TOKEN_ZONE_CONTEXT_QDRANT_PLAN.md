# Part 11.2 R2 — Runtime Token, Zone, Context, Qdrant and MVTC Plan

This patch replaces the previous architecture plan with the corrected version.

## Added

- Updated global architecture plan.
- Baby fork example calibrated on the next architecture.
- R2 future development line.
- Rule tests and manifest.

## Clarified

- MVTC is a context variation engine, not only a risk engine.
- Qdrant is vector memory, not context authority.
- Language models are workers/experts, not scheduler decision makers.
- Events may feed the existing intent system.
- Forbidden path is event-to-action shortcut, not event-to-command wording.
