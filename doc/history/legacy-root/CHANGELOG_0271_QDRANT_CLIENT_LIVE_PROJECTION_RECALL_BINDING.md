# Changelog — 0271-r3 qdrant-client live projection/recall binding

- Extended the existing 0262 projection CLI with a gated `qdrant-client` live
  mode.
- Extended the existing 0263 recall/SQL-rehydrate CLI with a gated live mode.
- Extended the existing 0269 one-shot composition with mutually exclusive demo
  and live Qdrant modes.
- Added secret-safe connection argument propagation and live proof checks.
- Kept SQL authority, OpenRC service ownership and SHM boundaries unchanged.
