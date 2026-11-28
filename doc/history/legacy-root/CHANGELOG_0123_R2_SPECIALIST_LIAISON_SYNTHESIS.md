# Changelog — 0123-r2 Specialist Liaison Synthesis

Added a corrected local liaison layer for specialist outputs.

## Added

- `src/context/specialist_liaison_synthesis.py`
- runtime tests for thermal-analysis style specialist output, context influence, review requests, validation refs, bus-ready path observations, and final packet creation.
- rule tests locking the corrected direction.

## Corrected

- Removed the 0123 direction that framed the next step as a GitHub publication review.
- Publication is now represented only as an optional final packet after local liaison synthesis.
- Specialist paths are represented as bus-ready observation facts and are suitable for later VisPy representation.

## Guardrails

No GitHub client, HTTP, socket, Qdrant client, OpenVINO runtime, PostgreSQL driver, watcher, service, live bus subscription, or kernel mutation is added.
