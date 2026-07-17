# Manifest 0287-r7-r15-r3-r16-r3

## Modified

- `src/context/github_actions_artifact_scan_once_live_0272.py`

## Added

- focused correlation tests;
- architecture boundary rules;
- phase report;
- changelog;
- architecture note and DOT graph;
- changed-files manifest.

## Locked boundaries

- existing GitHub GET/download transport reused;
- existing local dataset sync and artifact state reused;
- exactly three artifact roles required per ready run;
- legacy and readable names accepted through the existing matcher;
- incomplete or ambiguous runs deferred;
- no polling loop;
- no local closed-loop execution;
- no remote mutation;
- no SQL or Qdrant write.
