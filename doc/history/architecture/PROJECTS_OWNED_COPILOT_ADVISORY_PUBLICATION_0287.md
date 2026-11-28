# Projects-owned Copilot advisory publication — 0287 r16-r4-r3-r2

## Ownership

`newicody/projects` owns both production and immediate presentation of the
first Copilot advisory. Autodoc later fetches the three correlated artifacts
and must not republish that same advisory.

## Token boundary

The workflow-level `GITHUB_TOKEN` remains `issues: read`. Only the bounded
comment steps receive `AUTODOC_ISSUE_COMMENT_TOKEN`, a repository secret whose
credential must be limited to `newicody/projects` with Issues read/write.

The token is not used for ProjectV2, repository contents, workflow dispatch,
SQL, Qdrant, Scheduler or laboratory mutations.

## Order

1. build authoritative request;
2. build optional Copilot advisory;
3. build correlated manifest;
4. upload the three artifacts;
5. build publication preview;
6. compute and confirm the publication plan digest;
7. create or replay the marked Issue comment;
8. verify the comment by GitHub readback.

The Issue body remains authoritative. The advisory comment remains untrusted,
consultative and non-authoritative.
