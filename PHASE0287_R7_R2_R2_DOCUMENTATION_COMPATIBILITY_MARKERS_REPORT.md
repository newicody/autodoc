# Phase 0287-r7-r2-r2 — documentation compatibility markers report

## Status

- code_rule_review: done
- code_rule_update_required: false
- live_path_status: corrective documentation boundary
- runtime_change: false
- remote_mutation: false

## Cause

The 0287-r7-r2 patch changed stable documentation tokens that are consumed by
existing executable rules. The runtime contract v2 was valid, but the guide
version markers and one historical roadmap token were not free to be rewritten.

## Correction

- restore `Version du guide : 0287-r5-r1` as the cumulative guide baseline;
- restore `Version actuelle du guide : 0287-r5` as a compatibility token;
- keep `0287-r5-r2-r2` as the cumulative compatibility heading;
- record `0287-r7-r2` separately as the Copilot contract extension;
- retain the exact historical Chalouf token while explicitly marking it retired
  from the active roadmap and excluding phase 0288;
- align the new r7-r2 rule with those stable compatibility markers.

No Scheduler, laboratory, SQL, Qdrant, OpenVINO, GitHub API or ProjectV2 code is
changed. No external library was added.
