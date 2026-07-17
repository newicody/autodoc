# Changelog — 0287-r7-r15-r2-r1

- make ProjectV2 item and field identifiers optional diagnostic overrides;
- derive the source Issue from the validated authoritative request;
- resolve the exact ProjectV2, Issue item and field through the existing
  read-only GitHub CLI GraphQL adapter;
- reuse `.var/config/github_project_v2_query_only.ini` for owner, number and
  token environment;
- add one local config slot for the installation-specific real runtime factory;
- move command construction into the operator-facing error boundary;
- store resolved target metadata under `_r15_resolution`;
- keep preview mandatory and keep remote mutation absent;
- update the cumulative `newicody/projects` installation guide.
