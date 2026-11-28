# Manifest — 0272-r1 GitHub real read-only scan reuse audit

## Added

- `src/context/github_real_read_only_scan_reuse_audit_0272.py`
- `tools/audit_github_real_read_only_scan_reuse_0272.py`
- `tests/context/test_github_real_read_only_scan_reuse_audit_0272.py`
- `tests/tools/test_audit_github_real_read_only_scan_reuse_0272.py`
- `tests/rules/test_github_real_read_only_scan_reuse_audit_0272_rule.py`
- `doc/architecture/GITHUB_REAL_READ_ONLY_SCAN_REUSE_AUDIT_0272.md`
- `doc/code-rules/0272_github_real_read_only_scan_reuse_audit_rule.md`
- `doc/docs/architecture/runtime/272_github_real_read_only_scan_reuse_audit.dot`
- `doc/CHANGELOG_0272_GITHUB_REAL_READ_ONLY_SCAN_REUSE_AUDIT.md`
- `doc/manifests/MANIFEST_0272_GITHUB_REAL_READ_ONLY_SCAN_REUSE_AUDIT_CHANGED_FILES.md`
- `PHASE0272_GITHUB_REAL_READ_ONLY_SCAN_REUSE_AUDIT_TEST_REPORT.md`

## Explicitly unchanged

- Scheduler and its loop;
- 0267 handoff behavior;
- existing GitHub Actions fetch and server sync tools;
- remote mutation gate;
- SQL, Qdrant, OpenVINO, SHM, RouteProxy and ControlProxy.
