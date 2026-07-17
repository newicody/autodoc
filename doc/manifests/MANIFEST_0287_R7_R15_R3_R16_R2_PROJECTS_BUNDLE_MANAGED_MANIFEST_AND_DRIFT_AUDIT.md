# Manifest 0287-r7-r15-r3-r16-r2

## Added to the Projects bundle

- `projects_bundle_manifest.json`
- `scripts/projects_bundle_manifest_contract.py`
- `scripts/audit_projects_bundle_drift.py`

## Modified in the Projects bundle

- `README.md`
- `INSTALLATION.md`

## Added to Autodoc validation

- focused drift-audit tests;
- executable architecture rules;
- phase report;
- changelog;
- architecture note and DOT graph;
- this changed-files manifest.

## Locked boundaries

- local filesystem audit only;
- no GitHub API or network access;
- no mutation;
- no `rsync --delete`;
- safe deletion candidates limited to explicit retired entries;
- unknown extra files remain review-only;
- no Scheduler, laboratory, SQL, OpenVINO or Qdrant change.
