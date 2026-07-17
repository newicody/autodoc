# 0272-r1 — GitHub real read-only scan reuse audit

Base: `02416d5e7b93f907258d826a9f60af65687d25d1`.

This patch performs an offline source audit before adding a real GitHub issue
scan. It reuses and records the existing GitHub Actions GET transport,
`token_env` safety checks, repository allow-list, 0267 local handoff and remote
mutation gate. It confirms that no typed repository issue scan client exists.

No GitHub API request, token read, remote mutation, polling loop, dependency,
SQL/Qdrant write, SHM change or Scheduler modification is introduced.

Expected smoke:

```bash
PYTHONPATH=src:. python \
  tools/audit_github_real_read_only_scan_reuse_0272.py \
  --repo-root . \
  --output .var/reports/github_real_read_only_scan_reuse_audit_0272.json \
  --format summary
```
