# 0171 code rule — GitHub attachment reference fetch

The 0171 attachment fetch pass is a server-side raw-data sync step.

Required boundary:

- GitHub issue attachment references only
- raw bytes must be written into the configured server dataset
- conversion is queued only after attachment fetch completes
- no user artifacts in Autodoc repository
- no remote mutation
- no SQL/qdrant write
- no inference execution
- emit a VisPy observation event after the pass

The `src/context` contract must stay network-free. Network or fixture resolution
belongs in the tool layer and must require explicit opt-in for live network use.
