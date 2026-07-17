# Phase 0287-r7-r15-r2-r3-r1 report

## Goal

Restore the locked historical workflow markers without reverting readable
Actions artifact names.

## Result

The workflow keeps dynamic upload names produced by the artifact identity step.
A nearby compatibility note records the three fixed historical names that remain
indexed in `artifact_identity.json` and accepted by the local importer.

## Compatibility

The correction satisfies the 0275 static workflow contract while preserving the
new runtime behavior:

- no duplicate legacy uploads;
- no change to artifact selection or digests;
- old runs remain importable;
- new runs keep human-readable names.

## Phase review

```text
code_rule_review: done
code_rule_update_required: false
live_path_status: compatibility-fix
external_dependencies_added: false
scheduler_modified: false
network_added: false
github_permissions_changed: false
artifact_upload_behavior_changed: false
```
